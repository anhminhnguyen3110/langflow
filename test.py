import requests
import os
import uuid

base_url = "http://localhost:7860"
flow_id = "d8d62885-b9c7-45b0-a199-a9525c62c3cf"
session_id = str(uuid.uuid4())
payload = {
    "output_type": "chat",
    "input_type": "chat",
    "input_value": "3+3 = ?",
    "session_id": session_id,
    "tweaks": {
        "ChatInput-tu2Z3": {
            "sender": "User",
            "sender_name": "Minh dep trai",
            "session_id": session_id
        }
    }
}

response = requests.post(
    f"{base_url}/api/v1/run/{flow_id}?stream=true",
    headers={"Content-Type": "application/json"},
    json=payload,
    stream=True
)

# In ra response để debug nếu có lỗi
if response.status_code != 200:
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
else:
    # Xử lý streaming response
    import json
    for i, line in enumerate(response.iter_lines()):
        if line:
            decoded_line = line.decode('utf-8')
            # SSE format: "data: {...}"
            if decoded_line.startswith('data: '):
                data = decoded_line[6:]  # Bỏ prefix "data: "
                try:
                    parsed = json.loads(data)
                    print(f"\n=== Chunk {i} ===")
                    print(json.dumps(parsed, indent=2, ensure_ascii=False))
                except json.JSONDecodeError:
                    print(f"\n=== Chunk {i} (raw) ===")
                    print(decoded_line)
            else:
                print(f"\n=== Chunk {i} (raw) ===")
                print(decoded_line)