# Chainlit App

Chainlit frontend for Langflow with Keycloak SSO support.

## Features

- 🔐 Keycloak SSO / Password authentication
- 💾 PostgreSQL data persistence
- 🔧 Tool calling display from Langflow Agent
- 🎨 Claude avatar & theme

## Setup

### Install with uv

```bash
uv pip install -e .
```

### Development

```bash
uv pip install -e ".[dev]"
```

## Configuration

Create a `.env` file:

```env
# Langflow
LANGFLOW_API_URL=http://localhost:7860
FLOW_ID=your-flow-id
CHAT_INPUT_ID=ChatInput-xxxxx

# Database
DATABASE_URL=postgresql+asyncpg://langflow:langflow@localhost:5432/chainlit

# Keycloak (optional)
OAUTH_KEYCLOAK_CLIENT_ID=chainlit-client
OAUTH_KEYCLOAK_CLIENT_SECRET=your-secret
OAUTH_KEYCLOAK_REALM_URL=http://localhost:8080/realms/langflow
```

## Run

```bash
cd src/chainlit_app && chainlit run main.py -h
```

Or with the script:

```bash
chainlit-app
```

## Project Structure

```
src/chainlit_app/
├── __init__.py       # Package exports
├── main.py           # Entry point, Chainlit handlers
├── config.py         # Configuration from .env
├── auth.py           # Authentication (Keycloak/Password)
├── data_layer.py     # PostgreSQL data layer
├── langflow.py       # Langflow streaming API client
└── tools.py          # Tool display utilities
```
