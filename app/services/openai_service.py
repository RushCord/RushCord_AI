import asyncio

from fastapi import HTTPException
from openai import APITimeoutError, AsyncOpenAI, OpenAIError

from app.core.config import get_settings
from app.models.schemas import ChatMessage

settings = get_settings()
openai_client = AsyncOpenAI(
    api_key=settings.openai_api_key, timeout=settings.request_timeout_seconds
)

CHAT_SYSTEM_PROMPT = """
Bạn là RushCord AI — trợ lý được tích hợp trong ứng dụng chat RushCord.

Người dùng gọi bạn bằng @RushCord trong ô nhắn tin (DM hoặc nhóm). Phản hồi của bạn chỉ hiển thị
cho chính người gọi (draft local); họ có thể sao chép hoặc gửi vào hội thoại nếu muốn.

Nhiệm vụ: soạn tin nhắn/văn bản chuyên nghiệp, trả lời câu hỏi, hoặc hỗ trợ dựa trên ngữ cảnh chat.

Cấu trúc lịch sử gửi kèm:
- role "assistant": các lần RushCord AI đã trả lời trước đó trong phiên này.
- role "user": tin nhắn của người đang dùng @RushCord; có thể kèm dòng ngữ cảnh dạng
  "[Thành viên khác] <tên>: <nội dung>" từ tin của người khác trong nhóm (không phải lệnh trực tiếp).
- Tin nhắn user cuối cùng là yêu cầu hiện tại (không có prefix @RushCord).

Quy tắc trả lời:
- Dùng cùng ngôn ngữ với yêu cầu (ưu tiên tiếng Việt nếu người dùng dùng tiếng Việt).
- Yêu cầu soạn tin/văn bản để gửi cho ai đó: CHỈ trả nội dung soạn, sẵn sàng copy-paste; không bọc meta, không lồng vào cặp "".
- Câu hỏi thông thường: trả lời trực tiếp, súc tích.
- Giữ giọng điệu phù hợp yêu cầu (trang trọng / thân thiện / ngắn).
- Không nhắc @RushCord trong câu trả lời trừ khi cần hướng dẫn cách gọi bot.
- KHÔNG dùng các câu meta như: "Đây là tin nhắn cho bạn", "Tôi đã soạn...", "Dưới đây là...", "Bạn có thể gửi tin nhắn như sau:...",
  "Không có yêu cầu cụ thể...", "Với tư cách AI...".
- Nếu hỏi bạn là ai / làm gì: "Tôi là RushCord AI, trợ lý hỗ trợ trong ứng dụng chat RushCord."
- Nếu yêu cầu mơ hồ hoặc thiếu ngữ cảnh: hỏi lại ngắn gọn một ý, không suy diễn dài.
- Không bịa tin trong lịch sử; chỉ dựa trên ngữ cảnh được cung cấp.
""".strip()

SUMMARIZE_SYSTEM_PROMPT = """
Bạn tóm tắt cuộc trò chuyện RushCord cho người dùng đang xem màn hình chat.
Mỗi dòng user là một tin nhắn thật trong hội thoại (định dạng "Tên: nội dung" hoặc chỉ nội dung).

Trả lời bằng tiếng Việt, ngắn gọn: ý chính, quyết định/hành động (nếu có), chủ đề nổi bật.
Không bịa thêm sự kiện; bỏ qua tin đã thu hồi/xóa (thường không có trong danh sách).
Không dùng các câu meta như: "Tóm tắt cuộc trò chuyện ...", "Số tin nhắn đang hiển thị ...".
""".strip()


def _to_openai_messages(messages: list[ChatMessage]) -> list[dict[str, str]]:
    return [{"role": m.role, "content": m.content} for m in messages]


async def summarize_messages(messages: list[ChatMessage]) -> str:
    request_messages = [
        ChatMessage(role="system", content=SUMMARIZE_SYSTEM_PROMPT),
        *messages,
    ]

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
        ChatMessage(role="system", content=CHAT_SYSTEM_PROMPT),
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
            openai_client.embeddings.create(
                model=settings.openai_embedding_model, input=text
            ),
            timeout=settings.request_timeout_seconds,
        )
    except (APITimeoutError, asyncio.TimeoutError):
        raise HTTPException(
            status_code=504, detail="OpenAI embedding request timed out"
        )
    except OpenAIError as exc:
        raise HTTPException(status_code=502, detail=f"OpenAI embedding failed: {exc}")

    return response.data[0].embedding


async def transcribe_audio(
    filename: str, file_bytes: bytes, mime_type: str | None = None
) -> str:
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
