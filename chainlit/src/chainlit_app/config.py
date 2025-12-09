import os
from dotenv import load_dotenv

load_dotenv()

BASE_API_URL = os.getenv("LANGFLOW_API_URL", "http://localhost:7860")
FLOW_ID = os.getenv("FLOW_ID", "e52d19f0-15d4-4dc4-9b96-a56e00f8c7b6")
CHAT_INPUT_ID = os.getenv("CHAT_INPUT_ID", "ChatInput-tu2Z3")
FILE_INPUT_ID = os.getenv("FILE_INPUT_ID", "File-JFTKV")
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://langflow:langflow@localhost:5432/chainlit")
KEYCLOAK_ENABLED = bool(os.getenv("OAUTH_KEYCLOAK_CLIENT_ID"))
