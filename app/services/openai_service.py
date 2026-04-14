import asyncio

from fastapi import HTTPException
from openai import APITimeoutError, AsyncOpenAI, OpenAIError

from app.core.config import get_settings
from app.models.schemas import ChatMessage

settings = get_settings()
openai_client = AsyncOpenAI(api_key=settings.openai_api_key, timeout=settings.request_timeout_seconds)


def _to_openai_messages(messages: list[ChatMessage]) -> list[dict[str, str]]:
    return [{"role": m.role, "content": m.content} for m in messages]


async def summarize_messages(messages: list[ChatMessage]) -> str:
    prompt = "Hãy tóm tắt cuộc trò chuyện sau bằng tiếng Việt, ngắn gọn theo gạch đầu dòng."
    request_messages = [ChatMessage(role="system", content=prompt), *messages]

    try:
        response = await asyncio.wait_for(
            openai_client.chat.completions.create(
                model=settings.openai_summary_model,
                messages=_to_openai_messages(request_messages),
                temperature=0.2,
                max_tokens=220,
            ),
            timeout=settings.request_timeout_seconds,
        )
    except (APITimeoutError, asyncio.TimeoutError):
        raise HTTPException(status_code=504, detail="OpenAI summary request timed out")
    except OpenAIError as exc:
        raise HTTPException(status_code=502, detail=f"OpenAI summary failed: {exc}")

    return response.choices[0].message.content or ""


async def chat_reply(messages: list[ChatMessage]) -> str:
    request_messages = [
        ChatMessage(
            role="system",
            content=(
                "Bạn là trợ lý AI cho ứng dụng chat MeCord. "
                "Hãy trả lời hoàn toàn bằng tiếng Việt, ngắn gọn, rõ ràng và hữu ích. "
                "Nếu người dùng hỏi bạn là ai hoặc bạn làm gì, hãy trả lời: "
                "'Tôi là AI hỗ trợ cho ứng dụng MeCord.'"
            ),
        ),
        *messages,
    ]

    try:
        response = await asyncio.wait_for(
            openai_client.chat.completions.create(
                model=settings.openai_chat_model,
                messages=_to_openai_messages(request_messages),
                temperature=0.7,
                max_tokens=300,
            ),
            timeout=settings.request_timeout_seconds,
        )
    except (APITimeoutError, asyncio.TimeoutError):
        raise HTTPException(status_code=504, detail="OpenAI chat request timed out")
    except OpenAIError as exc:
        raise HTTPException(status_code=502, detail=f"OpenAI chat failed: {exc}")

    return response.choices[0].message.content or ""


async def create_embedding(text: str) -> list[float]:
    try:
        response = await asyncio.wait_for(
            openai_client.embeddings.create(model=settings.openai_embedding_model, input=text),
            timeout=settings.request_timeout_seconds,
        )
    except (APITimeoutError, asyncio.TimeoutError):
        raise HTTPException(status_code=504, detail="OpenAI embedding request timed out")
    except OpenAIError as exc:
        raise HTTPException(status_code=502, detail=f"OpenAI embedding failed: {exc}")

    return response.data[0].embedding


async def transcribe_audio(filename: str, file_bytes: bytes, mime_type: str | None = None) -> str:
    # OpenAI SDK accepts tuple(file_name, bytes, media_type).
    audio_file = (filename, file_bytes, mime_type or "application/octet-stream")

    try:
        response = await asyncio.wait_for(
            openai_client.audio.transcriptions.create(
                model=settings.openai_whisper_model,
                file=audio_file,
            ),
            timeout=max(settings.request_timeout_seconds, 45),
        )
    except (APITimeoutError, asyncio.TimeoutError):
        raise HTTPException(status_code=504, detail="Speech-to-text request timed out")
    except OpenAIError as exc:
        raise HTTPException(status_code=502, detail=f"Speech-to-text failed: {exc}")

    return response.text
