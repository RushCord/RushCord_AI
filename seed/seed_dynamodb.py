import os
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import boto3
from dotenv import load_dotenv

load_dotenv(dotenv_path=Path(__file__).resolve().parents[1] / ".env")

AWS_REGION = os.getenv("AWS_REGION", "ap-southeast-1")
USERS_TABLE = os.getenv("DYNAMODB_USERS_TABLE", "Users")
GROUPS_TABLE = os.getenv("DYNAMODB_GROUPS_TABLE", "Groups")
MESSAGES_TABLE = os.getenv("DYNAMODB_MESSAGES_TABLE", "Messages")


def iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def main() -> None:
    dynamodb = boto3.resource("dynamodb", region_name=AWS_REGION)
    users = dynamodb.Table(USERS_TABLE)
    groups = dynamodb.Table(GROUPS_TABLE)
    messages = dynamodb.Table(MESSAGES_TABLE)

    user_id = str(uuid4())
    group_id = str(uuid4())

    user_item = {
        "PK": f"USER#{user_id}",
        "username": "an",
        "email": "an@example.com",
        "name": "An",
        "created_at": iso_now(),
    }

    group_meta = {
        "PK": f"GROUP#{group_id}",
        "SK": "METADATA",
        "name": "Nhóm học AI",
        "description": "Phòng dự án AI của sinh viên",
        "owner": user_id,
    }

    group_member = {
        "PK": f"GROUP#{group_id}",
        "SK": f"USER#{user_id}",
        "joined_at": iso_now(),
    }

    msg_ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    message_item = {
        "PK": f"GROUP#{group_id}",
        "SK": f"MSG#{msg_ts}",
        "messageId": str(uuid4()),
        "sender": user_id,
        "content": "Chào mọi người, đây là tin nhắn mẫu đầu tiên để test hệ thống.",
        "created_at": iso_now(),
    }

    users.put_item(Item=user_item)
    groups.put_item(Item=group_meta)
    groups.put_item(Item=group_member)
    messages.put_item(Item=message_item)

    print("Seed complete")
    print({"user_id": user_id, "group_id": group_id, "message_sk": message_item["SK"]})


if __name__ == "__main__":
    main()
