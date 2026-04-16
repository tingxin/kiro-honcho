"""IAM Identity Center 相关操作"""
import os
import boto3
from .aws_client import sigv4_post

SSO_REGION = os.environ.get("SSO_REGION", "us-east-2")


def _identitystore():
    return boto3.client("identitystore", region_name=SSO_REGION)


# ---------------------------------------------------------------------------
# 实例
# ---------------------------------------------------------------------------

def get_instance_info(instance_arn=None):
    """返回 (instance_arn, identity_store_id)"""
    sso = boto3.client("sso-admin", region_name=SSO_REGION)
    instances = sso.list_instances()["Instances"]
    if not instances:
        raise RuntimeError("未找到 Identity Center 实例")
    if instance_arn:
        for inst in instances:
            if inst["InstanceArn"] == instance_arn:
                return inst["InstanceArn"], inst["IdentityStoreId"]
        raise RuntimeError(f"未找到指定的 instanceArn: {instance_arn}")
    inst = instances[0]
    return inst["InstanceArn"], inst["IdentityStoreId"]


# ---------------------------------------------------------------------------
# 用户管理
# ---------------------------------------------------------------------------

def create_user(identity_store_id, username, display_name, given_name, family_name, email):
    """创建 Identity Center 用户，返回 UserId"""
    resp = _identitystore().create_user(
        IdentityStoreId=identity_store_id,
        UserName=username,
        Name={"GivenName": given_name, "FamilyName": family_name},
        DisplayName=display_name,
        Emails=[{"Value": email, "Type": "Work", "Primary": True}],
    )
    return resp["UserId"]


def get_user_by_id(identity_store_id, user_id):
    """通过 UserId 获取用户信息，返回 {"UserName", "DisplayName", "Email"} 或 None"""
    try:
        resp = _identitystore().describe_user(
            IdentityStoreId=identity_store_id,
            UserId=user_id,
        )
        primary_email = next(
            (e["Value"] for e in resp.get("Emails", []) if e.get("Primary")),
            resp.get("Emails", [{}])[0].get("Value", "") if resp.get("Emails") else "",
        )
        return {
            "UserName": resp.get("UserName", ""),
            "DisplayName": resp.get("DisplayName", ""),
            "Email": primary_email,
        }
    except Exception:
        return None


def find_user_by_email(identity_store_id, email):
    """通过邮箱查找用户，返回 UserId 或 None"""
    paginator = _identitystore().get_paginator("list_users")
    for page in paginator.paginate(IdentityStoreId=identity_store_id):
        for user in page["Users"]:
            for e in user.get("Emails", []):
                if e.get("Value", "").lower() == email.lower():
                    return user["UserId"]
    return None


def find_user_by_principal_prefix(identity_store_id, prefix):
    """通过 principalId 前缀查找用户，返回匹配的用户列表（含邮箱）"""
    matched = []
    paginator = _identitystore().get_paginator("list_users")
    for page in paginator.paginate(IdentityStoreId=identity_store_id):
        for user in page["Users"]:
            if user.get("UserId", "").startswith(prefix):
                matched.append({
                    "UserId": user["UserId"],
                    "UserName": user.get("UserName", ""),
                    "DisplayName": user.get("DisplayName", ""),
                    "Emails": [
                        {"Value": e.get("Value", ""), "Primary": e.get("Primary", False)}
                        for e in user.get("Emails", [])
                    ],
                })
    return matched


# ---------------------------------------------------------------------------
# 密码 & 验证
# ---------------------------------------------------------------------------

def send_password_reset_email(user_id):
    """发送密码重置邮件（EMAIL 模式，用户点击邮件直接设置密码）"""
    return sigv4_post(
        url=f"https://identitystore.{SSO_REGION}.amazonaws.com/",
        target="SWBUPService.UpdatePassword",
        payload={"UserId": user_id, "PasswordMode": "EMAIL"},
        service="userpool",
        region=SSO_REGION,
    )


def send_password_reset_otp(user_id):
    """发送一次性密码（OTP 模式）"""
    return sigv4_post(
        url=f"https://identitystore.{SSO_REGION}.amazonaws.com/",
        target="SWBUPService.UpdatePassword",
        payload={"UserId": user_id, "PasswordMode": "OTP"},
        service="userpool",
        region=SSO_REGION,
    )


def send_email_verification(user_id, identity_store_id):
    """发送邮箱验证邮件（验证邮箱所有权，与密码重置不同）"""
    return sigv4_post(
        url=f"https://pvs-controlplane.{SSO_REGION}.prod.authn.identity.aws.dev/",
        target="AWSPasswordControlPlaneService.StartEmailVerification",
        payload={"UserId": user_id, "IdentityStoreId": identity_store_id},
        service="sso-directory",
        region=SSO_REGION,
    )


# ---------------------------------------------------------------------------
# Group 管理
# ---------------------------------------------------------------------------

def list_groups(identity_store_id):
    """列出所有 Group，返回 [{"GroupId": ..., "DisplayName": ...}]"""
    resp = _identitystore().list_groups(IdentityStoreId=identity_store_id)
    return resp.get("Groups", [])


def get_group_id_by_name(identity_store_id, group_name):
    """按显示名称查找 Group，返回 GroupId 或 None"""
    resp = _identitystore().get_group_id(
        IdentityStoreId=identity_store_id,
        AlternateIdentifier={
            "UniqueAttribute": {
                "AttributePath": "displayName",
                "AttributeValue": group_name,
            }
        },
    )
    return resp.get("GroupId")


def add_user_to_group(identity_store_id, user_id, group_id):
    """将用户加入 Group，返回 MembershipId"""
    resp = _identitystore().create_group_membership(
        IdentityStoreId=identity_store_id,
        GroupId=group_id,
        MemberId={"UserId": user_id},
    )
    return resp["MembershipId"]
