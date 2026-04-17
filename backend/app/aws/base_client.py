"""AWS SigV4 signed request client with multi-account support."""
import json
import boto3
from typing import Dict, Any, Optional
from botocore.awsrequest import AWSRequest
from botocore.auth import SigV4Auth
import requests
from requests import Response


class AWSClient:
    """AWS client with SigV4 authentication for multi-account support."""
    
    def __init__(
        self,
        access_key_id: str,
        secret_access_key: str,
        region: str = "us-east-1"
    ):
        """Initialize AWS client with credentials."""
        self.access_key_id = access_key_id
        self.secret_access_key = secret_access_key
        self.region = region
        
        # Create session with explicit credentials
        self.session = boto3.Session(
            aws_access_key_id=access_key_id,
            aws_secret_access_key=secret_access_key,
            region_name=region
        )
        self.credentials = self.session.get_credentials()
    
    def sigv4_post(
        self,
        url: str,
        target: str,
        payload: Dict[str, Any],
        service: str,
        region: Optional[str] = None
    ) -> Response:
        """
        Make a SigV4 signed POST request.
        
        Args:
            url: The API endpoint URL
            target: The x-amz-target header value
            payload: The request payload (dict)
            service: AWS service name
            region: AWS region (uses client region if not specified)
        
        Returns:
            Response object
        """
        region = region or self.region
        
        request = AWSRequest(
            method="POST",
            url=url,
            data=json.dumps(payload),
            headers={
                "Content-Type": "application/x-amz-json-1.0",
                "x-amz-target": target,
            },
        )
        
        SigV4Auth(self.credentials, service, region).add_auth(request)
        
        return requests.post(
            request.url,
            headers=dict(request.headers),
            data=request.body
        )
    
    def get_boto3_client(self, service_name: str, region: Optional[str] = None):
        """Get a boto3 client for a specific service."""
        return self.session.client(
            service_name,
            region_name=region or self.region
        )


class MultiAccountAWSClient:
    """Manager for multiple AWS account clients."""
    
    def __init__(self):
        self._clients: Dict[int, AWSClient] = {}
    
    def get_client(self, account_id: int, access_key_id: str, secret_access_key: str, region: str = "us-east-1") -> AWSClient:
        """Get or create a client for an account."""
        if account_id not in self._clients:
            self._clients[account_id] = AWSClient(
                access_key_id=access_key_id,
                secret_access_key=secret_access_key,
                region=region
            )
        return self._clients[account_id]
    
    def clear_client(self, account_id: int):
        """Clear cached client for an account."""
        if account_id in self._clients:
            del self._clients[account_id]
    
    def clear_all(self):
        """Clear all cached clients."""
        self._clients.clear()


# Singleton instance
_aws_client_manager = MultiAccountAWSClient()


def get_aws_client_manager() -> MultiAccountAWSClient:
    """Get the global AWS client manager."""
    return _aws_client_manager
