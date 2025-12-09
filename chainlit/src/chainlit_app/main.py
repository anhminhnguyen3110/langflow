import chainlit as cl
import logging
from chainlit.types import Feedback, ThreadDict
from chainlit_app import data_layer, auth
from chainlit_app.langflow import run_flow_stream, RateLimitError, upload_file_to_langflow
from chainlit_app.tools import create_tool_step, extract_agent_steps, update_tool_step

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MAX_FILE_SIZE_MB = 10
MAX_FILES = 1

auth.setup_auth()
_ = data_layer

COMMANDS = [
    {"id": "chat", "icon": "message-circle", "description": "Normal chat mode", "button": True},
    {"id": "search", "icon": "globe", "description": "Search the web", "button": True},
    {"id": "code", "icon": "code", "description": "Generate code", "button": True},
]

STARTERS = [
    cl.Starter(
        label="App Ideation",
        message="Help me brainstorm ideas for a new application",
        icon="/public/avatars/claude.png",
    ),
    cl.Starter(
        label="How authentication works",
        message="Explain how authentication works in web applications",
        icon="/public/avatars/claude.png",
    ),
    cl.Starter(
        label="Chainlit hello world",
        message="Show me how to create a hello world app with Chainlit",
        icon="/public/avatars/claude.png",
        command="code",
    ),
    cl.Starter(
        label="Search latest AI news",
        message="What are the latest developments in AI?",
        icon="/public/avatars/claude.png",
        command="search",
    ),
]


def get_user_identifier() -> str:
    user = cl.user_session.get("user")
    if user:
        return user.identifier
    return "User"


def get_langflow_session_id() -> str:
    thread_id = cl.context.session.thread_id
    return thread_id or cl.user_session.get("langflow_session_id")


@cl.set_starters
async def set_starters():
    return STARTERS


@cl.on_chat_start
async def on_chat_start():
    await cl.context.emitter.set_commands(COMMANDS)
    cl.user_session.set("langflow_session_id", cl.context.session.thread_id)


@cl.on_chat_resume
async def on_chat_resume(thread: ThreadDict):
    await cl.context.emitter.set_commands(COMMANDS)
    cl.user_session.set("langflow_session_id", thread["id"])


@cl.on_chat_end
async def on_chat_end():
    pass


@cl.on_message
async def on_message(message: cl.Message):
    user_input = message.content
    sender_name = get_user_identifier()
    session_id = get_langflow_session_id()
    command = message.command
    file_path = None

    if message.elements:
        logger.info(f"Message has {len(message.elements)} elements")
        for i, el in enumerate(message.elements):
            logger.info(f"Element {i}: type={type(el).__name__}, name={getattr(el, 'name', 'N/A')}, path={getattr(el, 'path', 'N/A')}, mime={getattr(el, 'mime', 'N/A')}")

        files = [el for el in message.elements if hasattr(el, 'path') and el.path]
        logger.info(f"Found {len(files)} files with path attribute")

        if len(files) > MAX_FILES:
            await cl.Message(
                content=f"⚠️ Only {MAX_FILES} file allowed at a time. Please upload only one file.",
                author="Assistant"
            ).send()
            return

        if files:
            file_element = files[0]
            try:
                import os
                file_size_mb = os.path.getsize(file_element.path) / (1024 * 1024)
                if file_size_mb > MAX_FILE_SIZE_MB:
                    await cl.Message(
                        content=f"⚠️ File too large ({file_size_mb:.2f}MB). Maximum size is {MAX_FILE_SIZE_MB}MB.",
                        author="Assistant"
                    ).send()
                    return

                with open(file_element.path, "rb") as f:
                    file_content = f.read()

                logger.info(f"Uploading file {file_element.name} ({len(file_content)} bytes) to Langflow")
                file_path = await upload_file_to_langflow(file_content, file_element.name)
                logger.info(f"File uploaded successfully, Langflow path: {file_path}")

            except Exception as e:
                await cl.Message(
                    content=f"❌ Error uploading file: {str(e)}",
                    author="Assistant"
                ).send()
                return

    if command:
        if command == "search":
            user_input = f"[Search Mode] {user_input}"
        elif command == "code":
            user_input = f"[Code Mode] {user_input}"

    displayed_tools = {}

    msg = cl.Message(content="", author="Assistant")
    await msg.send()

    try:
        async for event in run_flow_stream(user_input, session_id, sender_name, file_path=file_path):
            event_type = event.get("event", "")
            data = event.get("data", {})

            if event_type == "token":
                chunk = data.get("chunk", "")
                if chunk:
                    await msg.stream_token(chunk)

            elif event_type == "add_message":
                agent_data = extract_agent_steps(data)
                for tool in agent_data.get("tools", []):
                    tool_name = tool.get("name")
                    if not tool_name:
                        continue
                    if tool_name not in displayed_tools:
                        step = await create_tool_step(tool_name, tool.get("input", {}))
                        displayed_tools[tool_name] = step

            elif event_type == "end":
                result = data.get("result", {})
                outputs = result.get("outputs", [])
                for output in outputs:
                    for out in output.get("outputs", []):
                        msg_obj = out.get("results", {}).get("message", {})
                        final_tools = extract_agent_steps(msg_obj).get("tools", [])
                        for tool in final_tools:
                            tool_name = tool.get("name")
                            tool_output = tool.get("output")
                            if tool_name and tool_output and tool_name in displayed_tools:
                                await update_tool_step(displayed_tools[tool_name], tool_output)

        await msg.update()

    except RateLimitError as e:
        msg.content = f"⚠️ Rate limited by the API. Please wait {e.retry_after} seconds and try again."
        await msg.update()
    except Exception as e:
        msg.content = f"❌ Error: {str(e)}"
        await msg.update()


@cl.on_stop
async def on_stop():
    await cl.Message(content="⏹️ Stopped processing.").send()


@cl.on_feedback
async def on_feedback(feedback: Feedback):
    return True


def run():
    import subprocess
    subprocess.run(["chainlit", "run", __file__, "-h"])


if __name__ == "__main__":
    run()
