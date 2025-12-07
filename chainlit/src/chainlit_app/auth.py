from typing import Dict, Optional
import chainlit as cl
from chainlit_app.config import KEYCLOAK_ENABLED


def setup_auth():
    """Setup authentication based on configuration."""
    if KEYCLOAK_ENABLED:
        @cl.oauth_callback
        def oauth_callback(provider_id: str, token: str, raw_user_data: Dict[str, str], default_user: cl.User) -> Optional[cl.User]:
            return default_user
    else:
        @cl.password_auth_callback
        def auth_callback(username: str, password: str):
            if password == "admin123":
                return cl.User(identifier=username, metadata={"role": "user", "provider": "credentials"})
            return None
