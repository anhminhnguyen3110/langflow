import httpx
import json
import uuid
from typing import AsyncGenerator
from chainlit_app.config import BASE_API_URL, FLOW_ID, CHAT_INPUT_ID


async def run_flow_stream(message: str, session_id: str = None) -> AsyncGenerator[dict, None]:
    """Call Langflow streaming API and yield parsed JSON events."""
    api_url = f"{BASE_API_URL}/api/v1/run/{FLOW_ID}?stream=true"
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
                "sender_name": "User",
                "session_id": session_id
            }
        }
    }
    
    async with httpx.AsyncClient(timeout=120.0) as client:
        async with client.stream("POST", api_url, json=payload, headers={"Content-Type": "application/json"}) as response:
            buffer = ""
            async for chunk in response.aiter_text():
                buffer += chunk
                while buffer:
                    buffer = buffer.lstrip()
                    if not buffer or not buffer.startswith("{"):
                        if buffer:
                            idx = buffer.find('{')
                            buffer = buffer[idx:] if idx > 0 else ""
                        break
                    
                    depth, in_str, esc, end = 0, False, False, -1
                    for i, c in enumerate(buffer):
                        if esc:
                            esc = False
                            continue
                        if c == '\\' and in_str:
                            esc = True
                            continue
                        if c == '"' and not esc:
                            in_str = not in_str
                        elif not in_str:
                            if c == '{':
                                depth += 1
                            elif c == '}':
                                depth -= 1
                                if depth == 0:
                                    end = i + 1
                                    break
                    
                    if end > 0:
                        try:
                            yield json.loads(buffer[:end])
                        except json.JSONDecodeError:
                            pass
                        buffer = buffer[end:]
                    else:
                        break
