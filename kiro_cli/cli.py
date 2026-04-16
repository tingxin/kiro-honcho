#!/usr/bin/env python3
"""Kiro CLI - 管理 Kiro 用户与订阅"""
import sys
import json
import click
from dotenv import load_dotenv
from . import identity_center as ic
from . import kiro_subscription as ks

load_dotenv()


# ---------------------------------------------------------------------------
# 工具函数
# ---------------------------------------------------------------------------

def _get_instance(instance_arn=None):
    try:
        return ic.get_instance_info(instance_arn)
    except Exception as e:
        click.echo(f"❌ 获取 Identity Center 实例失败: {e}", err=True)
        sys.exit(1)


def _require_user(identity_store_id, email):
    user_id = ic.find_user_by_email(identity_store_id, email)
    if not user_id:
        click.echo(f"❌ 未找到邮箱为 {email} 的用户", err=True)
        sys.exit(1)
    return user_id


# ---------------------------------------------------------------------------
# 根命令
# ---------------------------------------------------------------------------

@click.group()
def cli():
    """Kiro 用户管理 CLI"""
    pass


# ---------------------------------------------------------------------------
# user 子命令组
# ---------------------------------------------------------------------------

@cli.group("user")
def user_group():
    """Identity Center 用户管理"""
    pass


@user_group.command("add")
@click.argument("email")
@click.option("--given-name", "-g", required=True, envvar="KIRO_GIVEN_NAME", help="名")
@click.option("--family-name", "-f", required=True, envvar="KIRO_FAMILY_NAME", help="姓")
@click.option("--display-name", "-d", default=None, envvar="KIRO_DISPLAY_NAME", help="显示名称，默认 given+family")
@click.option("--instance-arn", default=None, envvar="KIRO_INSTANCE_ARN")
@click.option("--subscription", default="Q_DEVELOPER_STANDALONE_PRO", show_default=True, envvar="KIRO_SUBSCRIPTION_TYPE")
def user_add(email, given_name, family_name, display_name, instance_arn, subscription):
    """创建用户并分配 Kiro 订阅"""
    display_name = display_name or f"{given_name} {family_name}"
    instance_arn, identity_store_id = _get_instance(instance_arn)
    click.echo(f"✅ Identity Center: {instance_arn}")

    existing_id = ic.find_user_by_email(identity_store_id, email)
    if existing_id:
        click.echo(f"⚠️  用户已存在 (UserId: {existing_id})，跳过创建")
        user_id = existing_id
    else:
        click.echo(f"📝 创建用户: {email} ...")
        try:
            user_id = ic.create_user(identity_store_id, email, display_name, given_name, family_name, email)
            click.echo(f"✅ 用户创建成功 (UserId: {user_id})")
        except Exception as e:
            click.echo(f"❌ 创建用户失败: {e}", err=True)
            sys.exit(1)

        click.echo("📧 发送密码重置邮件 ...")
        resp = ic.send_password_reset_email(user_id)
        if resp.status_code == 200:
            click.echo(f"✅ 密码重置邮件已发送至 {email}")
        else:
            click.echo(f"⚠️  密码邮件发送失败 ({resp.status_code}): {resp.text}", err=True)

    click.echo(f"🔑 分配 Kiro 订阅 ({subscription}) ...")
    resp = ks.create_assignment(instance_arn, user_id, subscription_type=subscription)
    if resp.status_code in (200, 201):
        click.echo("✅ Kiro 订阅分配成功")
    else:
        click.echo(f"❌ 订阅分配失败 ({resp.status_code}): {resp.text}", err=True)
        sys.exit(1)

    click.echo(f"\n🎉 完成！用户 {email} 已创建并订阅 Kiro，请提醒用户检查邮箱设置密码。")


@user_group.command("remove")
@click.argument("email")
@click.option("--instance-arn", default=None, envvar="KIRO_INSTANCE_ARN")
@click.option("--subscription", default="Q_DEVELOPER_STANDALONE_PRO", show_default=True, envvar="KIRO_SUBSCRIPTION_TYPE")
def user_remove(email, instance_arn, subscription):
    """取消用户的 Kiro 订阅"""
    instance_arn, identity_store_id = _get_instance(instance_arn)
    user_id = _require_user(identity_store_id, email)

    click.echo(f"🗑️  取消 Kiro 订阅 (UserId: {user_id}) ...")
    resp = ks.delete_assignment(instance_arn, user_id, subscription_type=subscription)
    if resp.status_code == 200:
        click.echo(f"✅ 已取消 {email} 的 Kiro 订阅")
    else:
        click.echo(f"❌ 取消失败 ({resp.status_code}): {resp.text}", err=True)
        sys.exit(1)


@user_group.command("find")
@click.argument("prefix")
@click.option("--instance-arn", default=None, envvar="KIRO_INSTANCE_ARN")
def user_find(prefix, instance_arn):
    """通过 principalId 前缀查找用户"""
    _, identity_store_id = _get_instance(instance_arn)
    users = ic.find_user_by_principal_prefix(identity_store_id, prefix)
    if not users:
        click.echo("❌ 未找到匹配的用户")
        sys.exit(1)
    click.echo(json.dumps(users, indent=2, ensure_ascii=False))


# ---------------------------------------------------------------------------
# password 子命令组
# ---------------------------------------------------------------------------

@cli.group("password")
def password_group():
    """密码与邮箱验证管理"""
    pass


@password_group.command("reset")
@click.argument("email")
@click.option("--instance-arn", default=None, envvar="KIRO_INSTANCE_ARN")
@click.option("--mode", type=click.Choice(["email", "otp"]), default="email", show_default=True, help="重置方式")
def password_reset(email, instance_arn, mode):
    """发送密码重置邮件（email: 直接设置密码 / otp: 一次性密码）"""
    _, identity_store_id = _get_instance(instance_arn)
    user_id = _require_user(identity_store_id, email)

    if mode == "otp":
        resp = ic.send_password_reset_otp(user_id)
    else:
        resp = ic.send_password_reset_email(user_id)

    if resp.status_code == 200:
        click.echo(f"✅ 密码重置邮件已发送至 {email} (mode={mode})")
    else:
        click.echo(f"❌ 发送失败 ({resp.status_code}): {resp.text}", err=True)
        sys.exit(1)


@password_group.command("verify")
@click.argument("email")
@click.option("--instance-arn", default=None, envvar="KIRO_INSTANCE_ARN")
def password_verify(email, instance_arn):
    """发送邮箱验证邮件"""
    _, identity_store_id = _get_instance(instance_arn)
    user_id = _require_user(identity_store_id, email)

    resp = ic.send_email_verification(user_id, identity_store_id)
    if resp.status_code == 200:
        click.echo(f"✅ 验证邮件已发送至 {email}")
    else:
        click.echo(f"❌ 发送失败 ({resp.status_code}): {resp.text}", err=True)
        sys.exit(1)


# ---------------------------------------------------------------------------
# group 子命令组
# ---------------------------------------------------------------------------

@cli.group("group")
def group_group():
    """Identity Center Group 管理"""
    pass


@group_group.command("list")
@click.option("--instance-arn", default=None, envvar="KIRO_INSTANCE_ARN")
def group_list(instance_arn):
    """列出所有 Group"""
    _, identity_store_id = _get_instance(instance_arn)
    groups = ic.list_groups(identity_store_id)
    for g in groups:
        click.echo(f"{g['GroupId']}  {g.get('DisplayName', '')}")


@group_group.command("add-user")
@click.argument("email")
@click.argument("group_name")
@click.option("--instance-arn", default=None, envvar="KIRO_INSTANCE_ARN")
def group_add_user(email, group_name, instance_arn):
    """将用户加入 Group"""
    _, identity_store_id = _get_instance(instance_arn)
    user_id = _require_user(identity_store_id, email)

    group_id = ic.get_group_id_by_name(identity_store_id, group_name)
    if not group_id:
        click.echo(f"❌ 未找到 Group: {group_name}", err=True)
        sys.exit(1)

    membership_id = ic.add_user_to_group(identity_store_id, user_id, group_id)
    click.echo(f"✅ 已将 {email} 加入 {group_name} (MembershipId: {membership_id})")


# ---------------------------------------------------------------------------
# subscription 子命令组
# ---------------------------------------------------------------------------

@cli.group("subscription")
def subscription_group():
    """Kiro 订阅管理"""
    pass


@subscription_group.command("list")
@click.option("--instance-arn", default=None, envvar="KIRO_INSTANCE_ARN")
def subscription_list(instance_arn):
    """列出所有 Kiro 订阅"""
    instance_arn, identity_store_id = _get_instance(instance_arn)
    resp = ks.list_subscriptions(instance_arn)
    if resp.status_code != 200:
        click.echo(f"❌ 查询失败 ({resp.status_code}): {resp.text}", err=True)
        sys.exit(1)

    subscriptions = resp.json().get("subscriptions", [])
    if not subscriptions:
        click.echo("暂无订阅")
        return

    # 批量查用户信息（缓存避免重复请求）
    user_cache = {}
    def get_user(user_id):
        if user_id not in user_cache:
            user_cache[user_id] = ic.get_user_by_id(identity_store_id, user_id)
        return user_cache[user_id]

    # 表头
    col = (36, 28, 32, 10)
    header = f"{'USER ID':<{col[0]}}  {'EMAIL':<{col[1]}}  {'USERNAME':<{col[2]}}  {'STATUS':<{col[3]}}  PLAN"
    click.echo(header)
    click.echo("-" * (sum(col) + len(col) * 2 + 10))

    for sub in subscriptions:
        user_id = sub.get("principal", {}).get("user", "")
        plan = sub.get("type", {}).get("amazonQ", "")
        status = sub.get("status", "")

        user = get_user(user_id) if user_id else None
        email = user["Email"] if user else ""
        username = user["UserName"] if user else ""

        click.echo(f"{user_id:<{col[0]}}  {email:<{col[1]}}  {username:<{col[2]}}  {status:<{col[3]}}  {plan}")


@subscription_group.command("change-plan")
@click.argument("emails", nargs=-1, required=True)
@click.option("--subscription", default="Q_DEVELOPER_STANDALONE_PRO_PLUS", show_default=True, envvar="KIRO_SUBSCRIPTION_TYPE")
@click.option("--instance-arn", default=None, envvar="KIRO_INSTANCE_ARN")
def subscription_change_plan(emails, subscription, instance_arn):
    """变更用户的 Kiro 订阅套餐"""
    _, identity_store_id = _get_instance(instance_arn)

    for email in emails:
        user_id = ic.find_user_by_email(identity_store_id, email)
        if not user_id:
            click.echo(f"❌ 未找到用户: {email}", err=True)
            continue

        resp = ks.update_assignment(user_id, subscription_type=subscription)
        if resp.status_code == 200:
            click.echo(f"✅ {email} → {subscription}")
        else:
            click.echo(f"❌ {email} 变更失败 ({resp.status_code}): {resp.text}", err=True)


if __name__ == "__main__":
    cli()
