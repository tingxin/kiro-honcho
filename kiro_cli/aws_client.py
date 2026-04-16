"""AWS SigV4 签名请求封装"""
import boto3
import json
import requests
from botocore.awsrequest import AWSRequest
from botocore.auth import SigV4Auth


def sigv4_post(url, target, payload, service, region):
    session = boto3.Session()
    credentials = session.get_credentials()

    request = AWSRequest(
        method="POST",
        url=url,
        data=json.dumps(payload),
        headers={
            "Content-Type": "application/x-amz-json-1.0",
            "x-amz-target": target,
        },
    )
    SigV4Auth(credentials, service, region).add_auth(request)
    return requests.post(request.url, headers=dict(request.headers), data=request.body)
