from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from app.core.security import verify_api_key
from app.models.schemas import (
    ChatRequest,
    ChatResponse,
    EmbeddingRequest,
    EmbeddingResponse,
    SearchRequest,
    SearchResponse,
    SpeechToTextResponse,
    SummarizeRequest,
    SummarizeResponse,
)
from app.services.openai_service import chat_reply, create_embedding, summarize_messages, transcribe_audio
from app.services.search_service import semantic_search

router = APIRouter(prefix="/v1", tags=["ai"], dependencies=[Depends(verify_api_key)])


@router.post("/summarize", response_model=SummarizeResponse)
async def summarize_endpoint(payload: SummarizeRequest) -> SummarizeResponse:
    if not payload.messages:
        raise HTTPException(status_code=400, detail="messages must not be empty")
    summary = await summarize_messages(payload.messages)
    return SummarizeResponse(summary=summary)


@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(payload: ChatRequest) -> ChatResponse:
    if not payload.messages:
        raise HTTPException(status_code=400, detail="messages must not be empty")
    reply = await chat_reply(payload.messages)
    return ChatResponse(reply=reply)


@router.post("/embedding", response_model=EmbeddingResponse)
async def embedding_endpoint(payload: EmbeddingRequest) -> EmbeddingResponse:
    vector = await create_embedding(payload.text)
    return EmbeddingResponse(vector=vector, dimension=len(vector))


@router.post("/search", response_model=SearchResponse)
async def search_endpoint(payload: SearchRequest) -> SearchResponse:
    results = await semantic_search(query=payload.query, top_k=payload.top_k)
    return SearchResponse(results=results)


@router.post("/speech-to-text", response_model=SpeechToTextResponse)
async def speech_to_text_endpoint(file: UploadFile = File(...)) -> SpeechToTextResponse:
    if not file.filename:
        raise HTTPException(status_code=400, detail="file name is required")
    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="audio file is empty")

    text = await transcribe_audio(file.filename, data, file.content_type)
    return SpeechToTextResponse(text=text)
