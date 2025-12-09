import json
import chainlit as cl


async def create_tool_step(tool_name: str, tool_input: dict):
    step = cl.Step(name=tool_name, type="tool")
    step.input = json.dumps(tool_input, indent=2, ensure_ascii=False) if isinstance(tool_input, dict) else str(tool_input)
    step.output = "⏳ Running..."
    step.language = "json"
    await step.send()
    return step


async def update_tool_step(step, tool_output):
    if step and tool_output:
        step.output = format_tool_output(tool_output)
        await step.update()


@cl.step(type="tool")
async def display_tool_call(tool_name: str, tool_input: dict, tool_output: str):
    step = cl.context.current_step
    step.name = tool_name
    step.input = json.dumps(tool_input, indent=2, ensure_ascii=False) if isinstance(tool_input, dict) else str(tool_input)
    step.output = tool_output
    step.language = "json"
    return tool_output


@cl.step(type="run", name="Agent Steps")
async def display_agent_steps(input_text: str, tool_calls: list):
    step = cl.context.current_step
    content_parts = [f"📝 **Input:**\n> {input_text}"]

    if tool_calls:
        content_parts.append("\n🔧 **Tools Used:**")
        for tool in tool_calls:
            tool_name = tool.get("name", "Unknown")
            tool_input = tool.get("input", {})
            tool_output = tool.get("output")

            input_str = json.dumps(tool_input, indent=2, ensure_ascii=False) if isinstance(tool_input, dict) else str(tool_input)
            content_parts.append(f"\n**{tool_name}**")
            content_parts.append(f"```json\n{input_str}\n```")
            if tool_output:
                content_parts.append(f"➡️ Output: `{format_tool_output(tool_output)}`")

    step.output = "\n".join(content_parts)
    return step.output


def format_tool_output(output) -> str:
    if not output:
        return "⏳ Running..."
    if isinstance(output, (list, dict)):
        s = json.dumps(output, indent=2, ensure_ascii=False)
        return s[:500] + "\n..." if len(s) > 500 else s
    return str(output)


def extract_tool_calls(data: dict) -> list:
    tools = []
    for block in data.get("content_blocks", []):
        if block.get("title") == "Agent Steps":
            for content in block.get("contents", []):
                if content.get("type") == "tool_use":
                    tools.append({
                        "name": content.get("name", ""),
                        "input": content.get("tool_input", {}),
                        "output": content.get("output")
                    })
    return tools


def extract_agent_steps(data: dict) -> dict:
    result = {
        "input_text": "",
        "tools": []
    }

    for block in data.get("content_blocks", []):
        if block.get("title") == "Agent Steps":
            for content in block.get("contents", []):
                if content.get("type") == "text":
                    header = content.get("header", {})
                    if header.get("title") == "Input":
                        result["input_text"] = content.get("text", "")
                elif content.get("type") == "tool_use":
                    result["tools"].append({
                        "name": content.get("name", ""),
                        "input": content.get("tool_input", {}),
                        "output": content.get("output")
                    })
    return result
