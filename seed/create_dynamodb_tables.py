import os
from pathlib import Path

import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv


load_dotenv(dotenv_path=Path(__file__).resolve().parents[1] / ".env")

AWS_REGION = os.getenv("AWS_REGION", "ap-southeast-1")
USERS_TABLE = os.getenv("DYNAMODB_USERS_TABLE", "Users")
GROUPS_TABLE = os.getenv("DYNAMODB_GROUPS_TABLE", "Groups")
MESSAGES_TABLE = os.getenv("DYNAMODB_MESSAGES_TABLE", "Messages")


def table_exists(client: object, table_name: str) -> bool:
    try:
        client.describe_table(TableName=table_name)
        return True
    except ClientError as exc:
        error_code = exc.response.get("Error", {}).get("Code", "")
        if error_code == "ResourceNotFoundException":
            return False
        raise


def describe_table(client: object, table_name: str) -> dict | None:
    try:
        return client.describe_table(TableName=table_name)["Table"]
    except ClientError as exc:
        error_code = exc.response.get("Error", {}).get("Code", "")
        if error_code == "ResourceNotFoundException":
            return None
        raise


def recreate_table(client: object, table_name: str) -> None:
    if table_exists(client, table_name):
        print(f"Table schema mismatch detected. Deleting table: {table_name}")
        client.delete_table(TableName=table_name)
        client.get_waiter("table_not_exists").wait(TableName=table_name)


def create_users_table(client: object) -> None:
    table = describe_table(client, USERS_TABLE)
    if table:
        key_schema = table.get("KeySchema", [])
        expected_key_schema = [{"AttributeName": "PK", "KeyType": "HASH"}]
        if key_schema == expected_key_schema:
            print(f"Table already exists: {USERS_TABLE}")
            return
        recreate_table(client, USERS_TABLE)

    client.create_table(
        TableName=USERS_TABLE,
        KeySchema=[
            {"AttributeName": "PK", "KeyType": "HASH"},
        ],
        AttributeDefinitions=[
            {"AttributeName": "PK", "AttributeType": "S"},
            {"AttributeName": "username", "AttributeType": "S"},
        ],
        BillingMode="PAY_PER_REQUEST",
        GlobalSecondaryIndexes=[
            {
                "IndexName": "username-index",
                "KeySchema": [
                    {"AttributeName": "username", "KeyType": "HASH"},
                ],
                "Projection": {"ProjectionType": "ALL"},
            }
        ],
    )
    client.get_waiter("table_exists").wait(TableName=USERS_TABLE)
    print(f"Created table: {USERS_TABLE}")


def create_groups_table(client: object) -> None:
    table = describe_table(client, GROUPS_TABLE)
    if table:
        key_schema = table.get("KeySchema", [])
        expected_key_schema = [
            {"AttributeName": "PK", "KeyType": "HASH"},
            {"AttributeName": "SK", "KeyType": "RANGE"},
        ]
        if key_schema == expected_key_schema:
            print(f"Table already exists: {GROUPS_TABLE}")
            return
        recreate_table(client, GROUPS_TABLE)

    client.create_table(
        TableName=GROUPS_TABLE,
        KeySchema=[
            {"AttributeName": "PK", "KeyType": "HASH"},
            {"AttributeName": "SK", "KeyType": "RANGE"},
        ],
        AttributeDefinitions=[
            {"AttributeName": "PK", "AttributeType": "S"},
            {"AttributeName": "SK", "AttributeType": "S"},
        ],
        BillingMode="PAY_PER_REQUEST",
    )
    client.get_waiter("table_exists").wait(TableName=GROUPS_TABLE)
    print(f"Created table: {GROUPS_TABLE}")


def create_messages_table(client: object) -> None:
    table = describe_table(client, MESSAGES_TABLE)
    if table:
        key_schema = table.get("KeySchema", [])
        expected_key_schema = [
            {"AttributeName": "PK", "KeyType": "HASH"},
            {"AttributeName": "SK", "KeyType": "RANGE"},
        ]
        if key_schema == expected_key_schema:
            print(f"Table already exists: {MESSAGES_TABLE}")
            return
        recreate_table(client, MESSAGES_TABLE)

    client.create_table(
        TableName=MESSAGES_TABLE,
        KeySchema=[
            {"AttributeName": "PK", "KeyType": "HASH"},
            {"AttributeName": "SK", "KeyType": "RANGE"},
        ],
        AttributeDefinitions=[
            {"AttributeName": "PK", "AttributeType": "S"},
            {"AttributeName": "SK", "AttributeType": "S"},
        ],
        BillingMode="PAY_PER_REQUEST",
    )
    client.get_waiter("table_exists").wait(TableName=MESSAGES_TABLE)
    print(f"Created table: {MESSAGES_TABLE}")


def main() -> None:
    dynamodb = boto3.client("dynamodb", region_name=AWS_REGION)

    print(f"Using region: {AWS_REGION}")
    create_users_table(dynamodb)
    create_groups_table(dynamodb)
    create_messages_table(dynamodb)

    print("All DynamoDB tables are ready.")


if __name__ == "__main__":
    main()