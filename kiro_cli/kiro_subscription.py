"""Kiro 订阅管理

Region 说明:
- KIRO_REGION: Kiro/Q Developer 服务区域，用于 Create/Delete/Update Assignment
  - URL: codewhisperer.{KIRO_REGION}.amazonaws.com
- SSO_REGION (来自环境变量): Identity Center 区域，用于 ListUserSubscriptions
  - URL: service.user-subscriptions.{SSO_REGION}.amazonaws.com
  - Signing region: SSO_REGION
"""
import os
from enum import StrEnum
from .aws_client import sigv4_post


class SubscriptionType(StrEnum):
    PRO = "Q_DEVELOPER_STANDALONE_PRO"
    PRO_PLUS = "Q_DEVELOPER_STANDALONE_PRO_PLUS"
    PRO_POWER = "Q_DEVELOPER_STANDALONE_PRO_POWER"
    KIRO_PRO = "KIRO_ENTERPRISE_PRO"
    KIRO_PRO_PLUS = "KIRO_ENTERPRISE_PRO_PLUS"


KIRO_REGION = os.environ.get("KIRO_REGION", "us-east-1")
SSO_REGION = os.environ.get("SSO_REGION", "us-east-2")

# Create/Delete/Update 端点使用 KIRO_REGION
_URL = f"https://codewhisperer.{KIRO_REGION}.amazonaws.com/"

# List 端点使用 SSO_REGION（Identity Center 所在区域）
_LIST_URL = f"https://service.user-subscriptions.{SSO_REGION}.amazonaws.com/"
# Create/Delete/Update 签名服务都是 q（已验证 ✅）
_ASSIGNMENT_SERVICE = "q"
# List 签名服务是 user-subscriptions（已验证 ✅）
_LIST_SERVICE = "user-subscriptions"


def create_assignment(instance_arn, principal_id, principal_type="USER", subscription_type="Q_DEVELOPER_STANDALONE_PRO", subscription_region=None):
    """为用户分配 Kiro 订阅
    
    URL: codewhisperer.{KIRO_REGION}
    Signing: service=q, region=KIRO_REGION (已验证 ✅)
    """
    return sigv4_post(
        url=_URL,
        target="AmazonQDeveloperService.CreateAssignment",
        payload={
            "instanceArn": instance_arn,
            "principalId": principal_id,
            "principalType": principal_type,
            "subscriptionType": subscription_type,
        },
        service=_ASSIGNMENT_SERVICE,
        region=KIRO_REGION,
    )


def delete_assignment(instance_arn, principal_id, principal_type="USER", subscription_type="Q_DEVELOPER_STANDALONE_PRO"):
    """删除用户的 Kiro 订阅
    
    URL: codewhisperer.{KIRO_REGION}
    Signing: service=q, region=KIRO_REGION (已验证 ✅)
    """
    return sigv4_post(
        url=_URL,
        target="AmazonQDeveloperService.DeleteAssignment",
        payload={
            "instanceArn": instance_arn,
            "principalId": principal_id,
            "principalType": principal_type,
            "subscriptionType": subscription_type,
        },
        service=_ASSIGNMENT_SERVICE,
        region=KIRO_REGION,
    )


def update_assignment(principal_id, subscription_type="Q_DEVELOPER_STANDALONE_PRO", principal_type="USER"):
    """变更用户的 Kiro 订阅套餐（change plan）
    
    URL: codewhisperer.{KIRO_REGION}
    Signing: service=q, region=KIRO_REGION (已验证 ✅)
    """
    return sigv4_post(
        url=_URL,
        target="AmazonQDeveloperService.UpdateAssignment",
        payload={
            "principalId": principal_id,
            "principalType": principal_type,
            "subscriptionType": subscription_type,
        },
        service=_ASSIGNMENT_SERVICE,
        region=KIRO_REGION,
    )


def list_subscriptions(instance_arn, max_results=1000, subscription_region=None):
    """列出所有订阅
    
    URL: service.user-subscriptions.{SSO_REGION}
    Signing: service=user-subscriptions, region=SSO_REGION (已验证 ✅)
    subscriptionRegion payload 字段使用 KIRO_REGION
    """
    return sigv4_post(
        url=_LIST_URL,
        target="AWSZornControlPlaneService.ListUserSubscriptions",
        payload={
            "instanceArn": instance_arn,
            "maxResults": max_results,
            "subscriptionRegion": subscription_region or KIRO_REGION,
        },
        service=_LIST_SERVICE,
        region=SSO_REGION,
    )
