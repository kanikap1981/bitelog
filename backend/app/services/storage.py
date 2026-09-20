import re
import uuid

import boto3
from botocore.client import Config

from app.config import Settings
from app.schemas import PresignResponse


def _safe_name(filename: str) -> str:
    value = re.sub(r"[^A-Za-z0-9._-]+", "-", filename).strip("-.")
    return value[:100] or "meal.jpg"


def presign_upload(filename: str, content_type: str, settings: Settings) -> PresignResponse:
    key = f"meals/{uuid.uuid4().hex}/{_safe_name(filename)}"
    client = boto3.client(
        "s3",
        endpoint_url=settings.s3_endpoint_url,
        region_name=settings.s3_region,
        aws_access_key_id=settings.s3_access_key_id or None,
        aws_secret_access_key=settings.s3_secret_access_key or None,
        config=Config(signature_version="s3v4"),
    )
    upload_url = client.generate_presigned_url(
        "put_object",
        Params={"Bucket": settings.s3_bucket, "Key": key, "ContentType": content_type},
        ExpiresIn=900,
    )
    return PresignResponse(object_key=key, upload_url=upload_url, headers={"Content-Type": content_type})
