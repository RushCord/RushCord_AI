import os
import sys
from pathlib import Path

import httpx

BASE_URL = os.getenv("FASTAPI_BASE_URL", "http://127.0.0.1:8000/v1")
API_KEY = os.getenv("SERVICE_API_KEY", "replace-with-your-internal-api-key")
AUDIO_PATH = os.getenv("SMOKE_TEST_AUDIO_PATH", "")


def headers() -> dict[str, str]:
    return {"X-API-Key": API_KEY}


def pretty(title: str, data: object) -> None:
    print(f"\n=== {title} ===")
    print(data)


def main() -> None:
    client = httpx.Client(timeout=30.0)

    health = client.get(BASE_URL.replace("/v1", "/health"))
    pretty("health", health.json())

    chat = client.post(
        f"{BASE_URL}/chat",
        headers=headers(),
        json={
            "messages": [
                {"role": "system", "content": "Bạn là trợ lý hữu ích cho ứng dụng chat."},
                {"role": "user", "content": "Cho tôi một mẹo demo cho đồ án đại học."},
            ]
        },
    )
    pretty("chat", chat.json())

    summary = client.post(
        f"{BASE_URL}/summarize",
        headers=headers(),
        json={
            "messages": [
                {"role": "user", "content": "Chúng tôi có đăng nhập, chat, tìm kiếm và speech-to-text."},
                {"role": "assistant", "content": "Tốt, hãy giữ luồng demo thật ngắn gọn."},
            ]
        },
    )
    pretty("summarize", summary.json())

    embedding = client.post(
        f"{BASE_URL}/embedding",
        headers=headers(),
        json={"text": "tìm kiếm ngữ nghĩa cho tin nhắn trong dự án"},
    )
    pretty("embedding", embedding.json())

    search = client.post(
        f"{BASE_URL}/search",
        headers=headers(),
        json={"query": "xác thực websocket", "top_k": 5},
    )
    pretty("search", search.json())

    if AUDIO_PATH:
        audio_file = Path(AUDIO_PATH)
        if audio_file.exists():
            with audio_file.open("rb") as handle:
                files = {"file": (audio_file.name, handle, "audio/wav")}
                stt = client.post(f"{BASE_URL}/speech-to-text", headers={"X-API-Key": API_KEY}, files=files)
            pretty("speech-to-text", stt.json())
        else:
            print(f"\nSkipped speech-to-text: {AUDIO_PATH} not found")

    client.close()


if __name__ == "__main__":
    try:
        main()
    except httpx.HTTPStatusError as exc:
        print(exc.response.text)
        sys.exit(1)
    except Exception as exc:
        print(str(exc))
        sys.exit(1)
