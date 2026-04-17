"""Kiro subscription management with multi-account support.

Region 说明:
- sso_region: Identity Center 所在区域，也是 ListUserSubscriptions 端点和签名区域
- kiro_region: Kiro/Q Developer 服务区域，用于 Create/Delete/Update Assignment

所有凭证和区域配置来自 Web 界面中用户配置的 AWS 账号信息。
"""
from typing import Dict, List, Any, Optional
from .base_client import AWSClient


class KiroSubscriptionClient:
    """Kiro subscription client for managing Q Developer subscriptions."""
    
    def __init__(
        self,
        aws_client: AWSClient,
        kiro_region: str = "us-east-1",
        sso_region: str = "us-east-2"
    ):
        """
        Initialize Kiro subscription client.
        
        Args:
            aws_client: 使用 Web 配置的 AK/SK 创建的 AWS 客户端
            kiro_region: Kiro 服务区域（Web 配置的 Kiro Region）
            sso_region: Identity Center 区域（Web 配置的 SSO Region）
        """
        self.aws_client = aws_client
        self.kiro_region = kiro_region
        self.sso_region = sso_region
        
        # Create/Delete/Update Assignment 端点使用 kiro_region
        self._kiro_url = f"https://codewhisperer.{kiro_region}.amazonaws.com/"
        # ListUserSubscriptions 端点使用 sso_region
        self._list_url = f"https://service.user-subscriptions.{sso_region}.amazonaws.com/"
    
    def create_assignment(
        self,
        instance_arn: str,
        principal_id: str,
        principal_type: str = "USER",
        subscription_type: str = "Q_DEVELOPER_STANDALONE_PRO"
    ) -> Dict[str, Any]:
        """
        Create a Kiro subscription assignment.
        
        URL: codewhisperer.{kiro_region}
        Signing: service=user-subscriptions, region=kiro_region
        """
        resp = self.aws_client.sigv4_post(
            url=self._kiro_url,
            target="AmazonQDeveloperService.CreateAssignment",
            payload={
                "instanceArn": instance_arn,
                "principalId": principal_id,
                "principalType": principal_type,
                "subscriptionType": subscription_type,
            },
            service="user-subscriptions",
            region=self.kiro_region,
        )
        
        return {
            "success": resp.status_code in (200, 201),
            "status_code": resp.status_code,
            "message": resp.text if resp.status_code not in (200, 201) else "Subscription created"
        }
    
    def delete_assignment(
        self,
        instance_arn: str,
        principal_id: str,
        principal_type: str = "USER",
        subscription_type: str = "Q_DEVELOPER_STANDALONE_PRO"
    ) -> Dict[str, Any]:
        """
        Delete a Kiro subscription assignment.
        
        URL: codewhisperer.{kiro_region}
        Signing: service=user-subscriptions, region=kiro_region
        """
        resp = self.aws_client.sigv4_post(
            url=self._kiro_url,
            target="AmazonQDeveloperService.DeleteAssignment",
            payload={
                "instanceArn": instance_arn,
                "principalId": principal_id,
                "principalType": principal_type,
                "subscriptionType": subscription_type,
            },
            service="user-subscriptions",
            region=self.kiro_region,
        )
        
        return {
            "success": resp.status_code == 200,
            "status_code": resp.status_code,
            "message": resp.text if resp.status_code != 200 else "Subscription deleted"
        }
    
    def update_assignment(
        self,
        principal_id: str,
        subscription_type: str = "Q_DEVELOPER_STANDALONE_PRO",
        principal_type: str = "USER"
    ) -> Dict[str, Any]:
        """
        Change subscription plan.
        
        URL: codewhisperer.{kiro_region}
        Signing: service=q, region=kiro_region
        """
        resp = self.aws_client.sigv4_post(
            url=self._kiro_url,
            target="AmazonQDeveloperService.UpdateAssignment",
            payload={
                "principalId": principal_id,
                "principalType": principal_type,
                "subscriptionType": subscription_type,
            },
            service="q",
            region=self.kiro_region,
        )
        
        return {
            "success": resp.status_code == 200,
            "status_code": resp.status_code,
            "message": resp.text if resp.status_code != 200 else "Subscription updated"
        }
    
    def list_subscriptions(
        self,
        instance_arn: str,
        max_results: int = 1000,
        subscription_region: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        List all subscriptions.
        
        URL: service.user-subscriptions.{sso_region}
        Signing: service=user-subscriptions, region=sso_region
        subscriptionRegion payload 字段使用 kiro_region
        """
        resp = self.aws_client.sigv4_post(
            url=self._list_url,
            target="AWSZornControlPlaneService.ListUserSubscriptions",
            payload={
                "instanceArn": instance_arn,
                "maxResults": max_results,
                "subscriptionRegion": subscription_region or self.kiro_region,
            },
            service="user-subscriptions",
            region=self.sso_region,
        )
        
        if resp.status_code == 200:
            data = resp.json()
            return {
                "success": True,
                "subscriptions": data.get("subscriptions", []),
                "total": len(data.get("subscriptions", []))
            }
        
        return {
            "success": False,
            "status_code": resp.status_code,
            "message": resp.text,
            "subscriptions": []
        }
    
    def get_subscription_by_principal(
        self,
        instance_arn: str,
        principal_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get subscription for a specific principal."""
        result = self.list_subscriptions(instance_arn)
        
        if not result["success"]:
            return None
        
        for sub in result["subscriptions"]:
            principal = sub.get("principal", {})
            if principal.get("user") == principal_id:
                return {
                    "principal_id": principal_id,
                    "subscription_type": sub.get("type", {}).get("amazonQ", ""),
                    "status": sub.get("status", ""),
                    "start_date": sub.get("createdDate")
                }
        
        return None
