from typing import Any

import botocore.exceptions
from boto3.dynamodb.conditions import Key
from fastapi import APIRouter, Depends, HTTPException, Query

from app.clients.dynamodb_client import dynamodb_table
from app.core.security import verify_api_key

router = APIRouter(prefix="/v1/db", tags=["database"], dependencies=[Depends(verify_api_key)])


@router.get("/items")
async def query_items(
    pk: str = Query(..., description="Partition Key"),
    sk_prefix: str | None = Query(None, description="Optional Sort Key prefix"),
) -> dict[str, Any]:
    try:
        if sk_prefix:
            response = dynamodb_table.query(
                KeyConditionExpression=Key("PK").eq(pk) & Key("SK").begins_with(sk_prefix)
            )
        else:
            response = dynamodb_table.query(KeyConditionExpression=Key("PK").eq(pk))
        return {"items": response.get("Items", [])}
    except botocore.exceptions.ClientError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/item")
async def get_item(
    pk: str = Query(..., description="Partition Key"),
    sk: str = Query(..., description="Sort Key"),
) -> dict[str, Any]:
    try:
        response = dynamodb_table.get_item(Key={"PK": pk, "SK": sk})
        item = response.get("Item")
        if not item:
            raise HTTPException(status_code=404, detail="Item not found")
        return {"item": item}
    except botocore.exceptions.ClientError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/item")
async def put_item(item: dict[str, Any]) -> dict[str, Any]:
    if "PK" not in item or "SK" not in item:
        raise HTTPException(status_code=400, detail="Item must contain at least 'PK' and 'SK'")
    try:
        dynamodb_table.put_item(Item=item)
        return {"status": "success", "message": "Item put successfully", "item": item}
    except botocore.exceptions.ClientError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/item")
async def delete_item(
    pk: str = Query(..., description="Partition Key"),
    sk: str = Query(..., description="Sort Key"),
) -> dict[str, Any]:
    try:
        dynamodb_table.delete_item(Key={"PK": pk, "SK": sk})
        return {"status": "success", "message": "Item deleted successfully"}
    except botocore.exceptions.ClientError as e:
        raise HTTPException(status_code=500, detail=str(e))
