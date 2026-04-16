"""Kiro 订阅管理"""
import os
from enum import StrEnum
from .aws_client import sigv4_post


class SubscriptionType(StrEnum):
    PRO = "Q_DEVELOPER_STANDALONE_PRO"
    PRO_PLUS = "Q_DEVELOPER_STANDALONE_PRO_PLUS"
    PRO_POWER = "Q_DEVELOPER_STANDALONE_PRO_POWER"

KIRO_REGION = os.environ.get("KIRO_REGION", "us-east-1")

_URL = f"https://codewhisperer.{KIRO_REGION}.amazonaws.com/"
_LIST_REGION = "us-east-2"
_LIST_URL = f"https://service.user-subscriptions.{_LIST_REGION}.amazonaws.com/"
_SERVICE = "user-subscriptions"


def create_assignment(instance_arn, principal_id, principal_type="USER", subscription_type="Q_DEVELOPER_STANDALONE_PRO", subscription_region=None):
    """为用户分配 Kiro 订阅"""
    return sigv4_post(
        url=_URL,
        target="AmazonQDeveloperService.CreateAssignment",
        payload={
            "instanceArn": instance_arn,
            "principalId": principal_id,
            "principalType": principal_type,
            "subscriptionType": subscription_type,
        },
        service=_SERVICE,
        region=KIRO_REGION,
    )


def delete_assignment(instance_arn, principal_id, principal_type="USER", subscription_type="Q_DEVELOPER_STANDALONE_PRO"):
    """删除用户的 Kiro 订阅"""
    return sigv4_post(
        url=_URL,
        target="AmazonQDeveloperService.DeleteAssignment",
        payload={
            "instanceArn": instance_arn,
            "principalId": principal_id,
            "principalType": principal_type,
            "subscriptionType": subscription_type,
        },
        service=_SERVICE,
        region=KIRO_REGION,
    )


def update_assignment(principal_id, subscription_type="Q_DEVELOPER_STANDALONE_PRO", principal_type="USER"):
    """变更用户的 Kiro 订阅套餐（change plan）"""
    return sigv4_post(
        url=_URL,
        target="AmazonQDeveloperService.UpdateAssignment",
        payload={
            "principalId": principal_id,
            "principalType": principal_type,
            "subscriptionType": subscription_type,
        },
        service="q",
        region=KIRO_REGION,
    )


def list_subscriptions(instance_arn, max_results=1000, subscription_region=None):
    """列出所有订阅，subscription_region 为订阅所在区域"""
    return sigv4_post(
        url=_LIST_URL,
        target="AWSZornControlPlaneService.ListUserSubscriptions",
        payload={
            "instanceArn": instance_arn,
            "maxResults": max_results,
            "subscriptionRegion": subscription_region or KIRO_REGION,
        },
        service=_SERVICE,
        region=_LIST_REGION,
    )
