from fastapi import HTTPException
from fastapi.concurrency import run_in_threadpool

from app.clients.dynamodb_client import dynamodb_table
from app.clients.qdrant_client import qdrant_client
from app.core.config import get_settings
from app.models.schemas import SearchResultItem
from app.services.openai_service import create_embedding

settings = get_settings()


def _fetch_message(group_id: str, message_sk: str) -> dict | None:
    key = {"PK": f"CONV#{group_id}", "SK": message_sk}
    result = dynamodb_table.get_item(Key=key)
    return result.get("Item")


async def semantic_search(query: str, top_k: int) -> list[SearchResultItem]:
    embedding = await create_embedding(query)

    try:
        points = await run_in_threadpool(
            lambda: qdrant_client.search(
                collection_name=settings.qdrant_collection,
                query_vector=embedding,
                limit=top_k,
                with_payload=True,
            )
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Qdrant search failed: {exc}")

    results: list[SearchResultItem] = []
    for point in points:
        payload = point.payload or {}
        group_id = str(payload.get("group_id", ""))
        message_sk = str(payload.get("message_sk", ""))

        message = None
        if group_id and message_sk:
            message = await run_in_threadpool(_fetch_message, group_id, message_sk)

        results.append(
            SearchResultItem(
                score=float(point.score),
                group_id=group_id,
                message_sk=message_sk,
                message=message,
            )
        )

    return results
