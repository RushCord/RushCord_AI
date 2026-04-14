from qdrant_client import QdrantClient

from app.core.config import get_settings

settings = get_settings()

qdrant_client = QdrantClient(url=settings.qdrant_url, api_key=settings.qdrant_api_key, timeout=settings.request_timeout_seconds)
