import os
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import boto3
from openai import OpenAI
from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels
from dotenv import load_dotenv

load_dotenv(dotenv_path=Path(__file__).resolve().parents[1] / ".env")

AWS_REGION = os.getenv("AWS_REGION", "ap-southeast-1")
MESSAGES_TABLE = os.getenv("DYNAMODB_MESSAGES_TABLE", "Messages")
QDRANT_URL = os.getenv("QDRANT_URL", "")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY", "")
QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "chat_embeddings")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_EMBEDDING_MODEL = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")


def iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def create_clients() -> tuple[object, object, object]:
    dynamodb = boto3.resource("dynamodb", region_name=AWS_REGION)
    openai_client = OpenAI(api_key=OPENAI_API_KEY)
    qdrant_client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
    return dynamodb, openai_client, qdrant_client


def ensure_collection(qdrant_client: QdrantClient, vector_size: int) -> None:
    existing = [collection.name for collection in qdrant_client.get_collections().collections]
    if QDRANT_COLLECTION in existing:
        return

    qdrant_client.create_collection(
        collection_name=QDRANT_COLLECTION,
        vectors_config=qmodels.VectorParams(size=vector_size, distance=qmodels.Distance.COSINE),
    )


def embed_text(openai_client: OpenAI, text: str) -> list[float]:
    response = openai_client.embeddings.create(model=OPENAI_EMBEDDING_MODEL, input=text)
    return response.data[0].embedding


def main() -> None:
    if not QDRANT_URL or not QDRANT_API_KEY or not OPENAI_API_KEY:
        raise RuntimeError("Missing QDRANT_URL, QDRANT_API_KEY, or OPENAI_API_KEY")

    dynamodb, openai_client, qdrant_client = create_clients()
    messages_table = dynamodb.Table(MESSAGES_TABLE)

    group_id = str(uuid4())
    user_id = str(uuid4())
    now = iso_now()

    sample_messages = [
        "Chúng ta cần hoàn thành xác thực websocket trước thứ Sáu.",
        "Hãy thêm tính năng tóm tắt cho các cuộc trò chuyện dài.",
        "Tìm kiếm nên trả về các tin nhắn liên quan trong cùng nhóm.",
        "Tính năng ghi âm phải chuyển giọng nói thành văn bản.",
        "Bản demo sẽ hiển thị đăng nhập, chat nhóm và trợ lý AI.",
    ]

    first_embedding = embed_text(openai_client, sample_messages[0])
    ensure_collection(qdrant_client, len(first_embedding))

    points = []
    for index, text in enumerate(sample_messages, start=1):
        message_sk = f"MSG#{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')}-{index}"
        message_id = str(uuid4())
        embedding = first_embedding if index == 1 else embed_text(openai_client, text)

        item = {
            "PK": f"GROUP#{group_id}",
            "SK": message_sk,
            "messageId": message_id,
            "sender": user_id,
            "content": text,
            "created_at": now,
        }
        messages_table.put_item(Item=item)

        points.append(
            qmodels.PointStruct(
                id=message_id,
                vector=embedding,
                payload={
                    "group_id": group_id,
                    "message_sk": message_sk,
                    "messageId": message_id,
                    "sender": user_id,
                    "content": text,
                    "created_at": now,
                },
            )
        )

    qdrant_client.upsert(collection_name=QDRANT_COLLECTION, points=points)

    print("Qdrant seed complete")
    print({"group_id": group_id, "points": len(points), "collection": QDRANT_COLLECTION})


if __name__ == "__main__":
    main()
