"""Chainlit App - Frontend for Langflow with Keycloak SSO."""
from chainlit_app.config import BASE_API_URL, FLOW_ID, CHAT_INPUT_ID, DATABASE_URL, KEYCLOAK_ENABLED

__version__ = "0.1.0"
__all__ = ["BASE_API_URL", "FLOW_ID", "CHAT_INPUT_ID", "DATABASE_URL", "KEYCLOAK_ENABLED"]
