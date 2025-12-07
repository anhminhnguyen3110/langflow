FROM langflowai/langflow:latest

RUN mkdir -p /app/flows
RUN mkdir -p /app/langflow-config-dir
RUN mkdir -p /app/components
WORKDIR /app

COPY flows /app/flows
COPY langflow-config-dir /app/langflow-config-dir
COPY docker.env /app/.env

COPY components /app/components

COPY pyproject.toml /app/

ENV PYTHONPATH=/app
ENV LANGFLOW_LOAD_FLOWS_PATH=/app/flows
ENV LANGFLOW_CONFIG_DIR=/app/langflow-config-dir
ENV LANGFLOW_COMPONENTS_PATH=/app/components
ENV LANGFLOW_LOG_ENV=container

EXPOSE 7860
CMD ["langflow", "run", "--env-file", "/app/.env", "--host", "0.0.0.0", "--port", "7860"]
