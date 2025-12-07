import chainlit as cl
from chainlit_app import data_layer, auth
from chainlit_app.langflow import run_flow_stream
from chainlit_app.tools import create_tool_step, display_agent_steps, format_tool_output, extract_tool_calls, extract_agent_steps, update_tool_step
from chainlit.types import Feedback

# Initialize auth and data layer
auth.setup_auth()
_ = data_layer  # Ensure data_layer module is loaded


STARTERS = [
    cl.Starter(label="App Ideation", message="Help me brainstorm ideas for a new application", icon="/public/avatars/claude.png"),
    cl.Starter(label="How do authentication work?", message="Explain how authentication works in web applications", icon="/public/avatars/claude.png"),
    cl.Starter(label="Chainlit hello world", message="Show me how to create a hello world app with Chainlit", icon="/public/avatars/claude.png"),
]


@cl.set_starters
async def set_starters():
    return STARTERS


@cl.on_chat_start
async def on_chat_start():
    cl.user_session.set("session_id", None)


@cl.on_message
async def on_message(message: cl.Message):
    """Handle incoming messages - display tool calls first, then response."""
    user_input = message.content
    session_id = cl.user_session.get("session_id")
    
    new_session_id = None
    displayed_tools = {}
    final_response = ""
    
    try:
        async for event in run_flow_stream(user_input, session_id):
            event_type = event.get("event", "")
            data = event.get("data", {})
            
            if event_type == "add_message":
                agent_data = extract_agent_steps(data)
                
                for tool in agent_data["tools"]:
                    tool_name = tool["name"]
                    if not tool_name:
                        continue
                    
                    if tool_name not in displayed_tools:
                        step = await create_tool_step(tool_name, tool["input"])
                        displayed_tools[tool_name] = step
            
            elif event_type == "token":
                chunk = data.get("chunk", "")
                if chunk:
                    final_response += chunk
            
            elif event_type == "end":
                result = data.get("result", {})
                new_session_id = result.get("session_id")
                
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
        
        if final_response:
            await cl.Message(content=final_response, author="claude").send()
                    
    except Exception as e:
        await cl.Message(content=f"❌ Error: {str(e)}", author="claude").send()
    
    if new_session_id:
        cl.user_session.set("session_id", new_session_id)


@cl.on_stop
async def on_stop():
    await cl.Message(content="⏹️ Đã dừng xử lý.").send()


@cl.on_feedback
async def on_feedback(feedback: Feedback):
    return True


def run():
    """Entry point for the application."""
    import subprocess
    subprocess.run(["chainlit", "run", __file__, "-h"])


if __name__ == "__main__":
    run()
