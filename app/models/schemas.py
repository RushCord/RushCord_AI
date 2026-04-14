from typing import Any

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: str = Field(description="system | user | assistant")
    content: str


class SummarizeRequest(BaseModel):
    messages: list[ChatMessage]


class SummarizeResponse(BaseModel):
    summary: str


class ChatRequest(BaseModel):
    messages: list[ChatMessage]


class ChatResponse(BaseModel):
    reply: str


class EmbeddingRequest(BaseModel):
    text: str = Field(min_length=1)


class EmbeddingResponse(BaseModel):
    vector: list[float]
    dimension: int


class SearchRequest(BaseModel):
    query: str = Field(min_length=1)
    top_k: int = Field(default=5, ge=1, le=20)


class SearchResultItem(BaseModel):
    score: float
    group_id: str
    message_sk: str
    message: dict[str, Any] | None = None


class SearchResponse(BaseModel):
    results: list[SearchResultItem]


class SpeechToTextResponse(BaseModel):
    text: str
