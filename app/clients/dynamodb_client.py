import boto3
from botocore.config import Config

from app.core.config import get_settings

settings = get_settings()

# Keep retries small for low-latency API workloads.
boto_config = Config(region_name=settings.aws_region, retries={"max_attempts": 3, "mode": "standard"})

session_kwargs: dict[str, str] = {}
if settings.aws_access_key_id and settings.aws_secret_access_key:
    session_kwargs["aws_access_key_id"] = settings.aws_access_key_id
    session_kwargs["aws_secret_access_key"] = settings.aws_secret_access_key
    if settings.aws_session_token:
        session_kwargs["aws_session_token"] = settings.aws_session_token

session = boto3.Session(region_name=settings.aws_region, **session_kwargs)
dynamodb_resource = session.resource("dynamodb", config=boto_config)

dynamodb_table = dynamodb_resource.Table(settings.dynamodb_table_name)
