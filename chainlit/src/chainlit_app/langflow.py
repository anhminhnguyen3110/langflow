import httpx
import json
import uuid
import asyncio
from typing import AsyncGenerator, Callable, Optional
from chainlit_app.config import BASE_API_URL, FLOW_ID, CHAT_INPUT_ID, FILE_INPUT_ID


class RateLimitError(Exception):
    def __init__(self, retry_after: int = 60):
        self.retry_after = retry_after
        super().__init__(f"Rate limited. Retry after {retry_after} seconds.")


async def upload_file_to_langflow(file_content: bytes, filename: str) -> str:
    api_url = f"{BASE_API_URL}/api/v2/files"
    async with httpx.AsyncClient(timeout=60.0) as client:
        files = {"file": (filename, file_content)}
        response = await client.post(api_url, files=files)
        response.raise_for_status()
        return response.json()["path"]


async def run_flow_stream(
    message: str,
    session_id: str = None,
    sender_name: str = "User",
    file_path: Optional[str] = None,
    on_token: Optional[Callable[[str], None]] = None,
    max_retries: int = 3,
    retry_delay: float = 2.0
) -> AsyncGenerator[dict, None]:
    api_url = f"{BASE_API_URL}/api/v1/run/{FLOW_ID}?stream=true"
    if not session_id:
        session_id = str(uuid.uuid4())

    tweaks = {
        CHAT_INPUT_ID: {
            "sender": "User",
            "sender_name": sender_name,
            "session_id": session_id
        }
    }

    if file_path:
        tweaks[FILE_INPUT_ID] = {
            "path": [file_path]
        }

    payload = {
        "output_type": "chat",
        "input_type": "chat",
        "input_value": message,
        "session_id": session_id,
        "tweaks": tweaks
    }

    headers = {
        "Content-Type": "application/json",
        "Accept": "text/event-stream"
    }

    for attempt in range(max_retries + 1):
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                async with client.stream("POST", api_url, json=payload, headers=headers) as response:
                    if response.status_code == 429:
                        retry_after = int(response.headers.get("Retry-After", retry_delay * (2 ** attempt)))
                        if attempt < max_retries:
                            await asyncio.sleep(retry_after)
                            continue
                        else:
                            raise RateLimitError(retry_after)

                    response.raise_for_status()

                    buffer = ""
                    async for chunk in response.aiter_text():
                        buffer += chunk

                        while "\n" in buffer:
                            line_end = buffer.index("\n")
                            line = buffer[:line_end].strip()
                            buffer = buffer[line_end + 1:]

                            if not line:
                                continue

                            try:
                                event_obj = json.loads(line)
                                event_type = event_obj.get("event")
                                event_data = event_obj.get("data")

                                if event_type and event_data is not None:
                                    if event_type == "token" and on_token:
                                        token = event_data.get("chunk", "")
                                        if token:
                                            await on_token(token)

                                    yield {"event": event_type, "data": event_data}
                            except json.JSONDecodeError:
                                continue

                    return

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                retry_after = int(e.response.headers.get("Retry-After", retry_delay * (2 ** attempt)))
                if attempt < max_retries:
                    await asyncio.sleep(retry_after)
                    continue
                else:
                    raise RateLimitError(retry_after)
            raise


async def run_flow(message: str, session_id: str = None, sender_name: str = "User") -> dict:
    api_url = f"{BASE_API_URL}/api/v1/run/{FLOW_ID}"
    if not session_id:
        session_id = str(uuid.uuid4())

    payload = {
        "output_type": "chat",
        "input_type": "chat",
        "input_value": message,
        "session_id": session_id,
        "tweaks": {
            CHAT_INPUT_ID: {
                "sender": "User",
                "sender_name": sender_name,
                "session_id": session_id
            }
        }
    }

    headers = {"Content-Type": "application/json"}

    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(api_url, json=payload, headers=headers)
        response.raise_for_status()
        return response.json()
