"""后台定时同步调度器."""
import asyncio
import logging
from datetime import datetime, timezone
from sqlalchemy import select
from app.database import async_session_maker
from app.models import AWSAccount

logger = logging.getLogger("sync_scheduler")

_task: asyncio.Task | None = None


async def _sync_loop():
    """每 60 秒检查一次是否有账号需要同步."""
    from app.services.account_service import AccountService

    while True:
        try:
            await asyncio.sleep(60)  # 每分钟检查一次

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

                    # 判断是否到了同步时间
                    last = account.last_synced
                    if last is not None:
                        # last_synced 可能是 naive datetime，统一处理
                        if last.tzinfo is None:
                            from datetime import timezone as tz
                            last = last.replace(tzinfo=tz.utc)
                        elapsed = (now - last).total_seconds() / 60
                        if elapsed < interval:
                            continue

                    logger.info(f"自动同步账号: {account.name} (id={account.id})")
                    try:
                        service = AccountService(session)
                        result = await service.sync_account_data(
                            account.id, operator="system:auto_sync"
                        )
                        # 更新 last_synced
                        account.last_synced = datetime.now(timezone.utc)
                        await session.commit()
                        logger.info(
                            f"同步完成: {account.name} - "
                            f"{result.get('synced_users', 0)} 用户, "
                            f"{result.get('synced_subscriptions', 0)} 订阅"
                        )
                    except Exception as e:
                        logger.error(f"同步失败: {account.name} - {e}")

        except asyncio.CancelledError:
            logger.info("同步调度器已停止")
            break
        except Exception as e:
            logger.error(f"同步调度器异常: {e}")
            await asyncio.sleep(10)


def start_scheduler():
    """启动后台同步调度器."""
    global _task
    if _task is None or _task.done():
        _task = asyncio.create_task(_sync_loop())
        logger.info("后台同步调度器已启动")


def stop_scheduler():
    """停止后台同步调度器."""
    global _task
    if _task and not _task.done():
        _task.cancel()
        logger.info("后台同步调度器已停止")
