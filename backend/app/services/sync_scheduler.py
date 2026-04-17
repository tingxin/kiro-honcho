"""后台定时同步与自动订阅调度器."""
import asyncio
import logging
from datetime import datetime, timezone
from sqlalchemy import select
from app.database import async_session_maker
from app.models import AWSAccount, ICUser, KiroSubscription
from app.config import get_settings

logger = logging.getLogger("sync_scheduler")

_task: asyncio.Task | None = None


async def _check_and_auto_subscribe():
    """检查待自动订阅的用户，如果已激活则自动分配 Kiro 订阅."""
    from app.services.account_service import AccountService
    from app.services.log_service import OperationLogService
    from app.aws import AWSClient, IdentityCenterClient, KiroSubscriptionClient

    async with async_session_maker() as session:
        # 查找所有有 pending_subscription_type 且还没有订阅的用户
        query = select(ICUser).where(
            ICUser.pending_subscription_type.isnot(None),
            ICUser.pending_subscription_type != "",
        )
        result = await session.execute(query)
        pending_users = list(result.scalars().all())

        if not pending_users:
            return

        # 按账号分组处理
        account_ids = set(u.aws_account_id for u in pending_users)
        account_service = AccountService(session)

        for account_id in account_ids:
            account = await account_service.get_account(account_id)
            if not account or account.status != "active":
                continue

            access_key, secret_key = account_service.decrypt_credentials(account)
            aws_client = AWSClient(access_key, secret_key, account.sso_region)
            ic_client = IdentityCenterClient(aws_client, account.sso_region)
            kiro_client = KiroSubscriptionClient(
                aws_client,
                kiro_region=account.kiro_region,
                sso_region=account.sso_region,
            )

            users_for_account = [u for u in pending_users if u.aws_account_id == account_id]

            for user in users_for_account:
                try:
                    # 检查用户是否已有订阅
                    sub_query = select(KiroSubscription).where(
                        KiroSubscription.aws_account_id == account_id,
                        KiroSubscription.principal_id == user.user_id,
                    )
                    existing_sub = await session.scalar(sub_query)
                    if existing_sub:
                        # 已有订阅，清除 pending
                        user.pending_subscription_type = None
                        await session.commit()
                        continue

                    # 从 AWS 获取用户最新状态
                    user_info = ic_client.get_user_by_id(
                        account.identity_store_id, user.user_id
                    )
                    if not user_info:
                        logger.warning(f"用户不存在: {user.email} (id={user.user_id})")
                        continue

                    aws_status = user_info.get("Status", "disabled")
                    user.status = aws_status

                    # 只有 enabled 的用户才自动分配订阅
                    if aws_status != "enabled":
                        logger.debug(f"用户未激活: {user.email} status={aws_status}")
                        await session.commit()
                        continue

                    user.email_verified = True

                    # 自动分配 Kiro 订阅
                    sub_type = user.pending_subscription_type
                    logger.info(f"自动分配订阅: {user.email} -> {sub_type}")

                    result = kiro_client.create_assignment(
                        instance_arn=account.instance_arn,
                        principal_id=user.user_id,
                        subscription_type=sub_type,
                    )

                    if result["success"]:
                        # 保存订阅到数据库
                        new_sub = KiroSubscription(
                            aws_account_id=account_id,
                            user_id=user.id,
                            principal_id=user.user_id,
                            subscription_type=sub_type,
                            status="PENDING",
                            last_synced=datetime.now(timezone.utc),
                        )
                        session.add(new_sub)
                        user.pending_subscription_type = None  # 清除待订阅标记

                        # 记录日志
                        log_service = OperationLogService(session)
                        await log_service.log_operation(
                            account_id=account_id,
                            operation="auto_subscribe",
                            target=f"user:{user.email}",
                            status="success",
                            message=f"自动分配订阅: {user.email} -> {sub_type}",
                            operator="system:auto_subscribe",
                        )
                        logger.info(f"订阅分配成功: {user.email}")
                    else:
                        logger.error(
                            f"订阅分配失败: {user.email} - {result.get('message', '')}"
                        )

                    await session.commit()

                except Exception as e:
                    logger.error(f"处理用户 {user.email} 时出错: {e}")
                    await session.rollback()


async def _sync_loop():
    """主调度循环：定时同步 + 自动订阅检查."""
    from app.services.account_service import AccountService

    settings = get_settings()
    auto_sub_counter = 0

    while True:
        try:
            await asyncio.sleep(60)  # 每分钟检查一次
            auto_sub_counter += 1

            # 自动订阅检查
            check_interval = settings.AUTO_SUBSCRIBE_CHECK_INTERVAL
            if check_interval > 0 and auto_sub_counter >= check_interval:
                auto_sub_counter = 0
                try:
                    await _check_and_auto_subscribe()
                except Exception as e:
                    logger.error(f"自动订阅检查异常: {e}")

            # 账号数据同步
            async with async_session_maker() as session:
                query = select(AWSAccount).where(
                    AWSAccount.status == "active",
                    AWSAccount.sync_interval_minutes > 0,
                )
                result = await session.execute(query)
                accounts = list(result.scalars().all())

                now = datetime.now(timezone.utc)
                for account in accounts:
                    interval = account.sync_interval_minutes or 0
                    if interval <= 0:
                        continue

                    last = account.last_synced
                    if last is not None:
                        if last.tzinfo is None:
                            last = last.replace(tzinfo=timezone.utc)
                        elapsed = (now - last).total_seconds() / 60
                        if elapsed < interval:
                            continue

                    logger.info(f"自动同步账号: {account.name} (id={account.id})")
                    try:
                        service = AccountService(session)
                        sync_result = await service.sync_account_data(
                            account.id, operator="system:auto_sync"
                        )
                        account.last_synced = datetime.now(timezone.utc)
                        await session.commit()
                        logger.info(
                            f"同步完成: {account.name} - "
                            f"{sync_result.get('synced_users', 0)} 用户, "
                            f"{sync_result.get('synced_subscriptions', 0)} 订阅"
                        )
                    except Exception as e:
                        logger.error(f"同步失败: {account.name} - {e}")

        except asyncio.CancelledError:
            logger.info("调度器已停止")
            break
        except Exception as e:
            logger.error(f"调度器异常: {e}")
            await asyncio.sleep(10)


def start_scheduler():
    """启动后台调度器."""
    global _task
    if _task is None or _task.done():
        _task = asyncio.create_task(_sync_loop())
        logger.info("后台调度器已启动（同步 + 自动订阅）")


def stop_scheduler():
    """停止后台调度器."""
    global _task
    if _task and not _task.done():
        _task.cancel()
        logger.info("后台调度器已停止")
