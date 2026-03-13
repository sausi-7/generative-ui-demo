import json
from pathlib import Path

import anthropic
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from tools import TOOLS
from system import SYSTEM_PROMPT

app = FastAPI()
client = anthropic.AsyncAnthropic()

GUIDELINES_DIR = Path(__file__).parent / "guidelines"


# ── Guidelines loader ──────────────────────────────────────────────────────

def get_guidelines(modules: list[str]) -> str:
    """Load core guidelines plus requested module files."""
    parts = []
    core = GUIDELINES_DIR / "core.md"
    if core.exists():
        parts.append(core.read_text())
    for module in modules:
        path = GUIDELINES_DIR / f"{module}.md"
        if path.exists():
            parts.append(path.read_text())
    return "\n\n---\n\n".join(parts)


# ── Partial JSON parser ────────────────────────────────────────────────────

def extract_widget_code(partial_json: str) -> str | None:
    """
    Extract the widget_code value from a partially-streamed JSON string.

    Claude streams tool arguments token by token, so the JSON is often
    invalid mid-stream. We first try a full parse, then fall back to
    manually walking the string from the "widget_code" key forward.
    """
    # Fast path: valid JSON
    try:
        data = json.loads(partial_json)
        return data.get("widget_code")
    except json.JSONDecodeError:
        pass

    # Find the key
    key = '"widget_code"'
    idx = partial_json.find(key)
    if idx == -1:
        return None

    # Find the colon after the key
    rest = partial_json[idx + len(key):]
    colon = rest.find(':')
    if colon == -1:
        return None

    rest = rest[colon + 1:].lstrip()
    if not rest.startswith('"'):
        return None

    # Walk the string value, handling JSON escape sequences
    content = rest[1:]  # skip opening quote
    result = []
    i = 0
    while i < len(content):
        c = content[i]
        if c == '\\' and i + 1 < len(content):
            n = content[i + 1]
            escapes = {'n': '\n', 't': '\t', 'r': '\r', '\\': '\\',
                       '"': '"', '/': '/', 'b': '\b', 'f': '\f'}
            result.append(escapes.get(n, n))
            i += 2
        elif c == '"':
            break  # end of string
        else:
            result.append(c)
            i += 1

    return ''.join(result) if result else None


# ── SSE helper ─────────────────────────────────────────────────────────────

def sse(data: dict) -> str:
    return f"data: {json.dumps(data)}\n\n"


# ── Request schema ─────────────────────────────────────────────────────────

class Message(BaseModel):
    role: str
    content: str


class ChatBody(BaseModel):
    messages: list[Message]


# ── Main SSE endpoint ──────────────────────────────────────────────────────

@app.post("/chat")
async def chat(body: ChatBody):
    async def generate():
        # Build messages list — tool use turns are added here during the loop
        messages = [{"role": m.role, "content": m.content} for m in body.messages]

        while True:
            # Per-turn state
            active_tool_calls: dict[int, dict] = {}
            current_text = ""

            try:
                async with client.messages.stream(
                    model="claude-opus-4-6",
                    max_tokens=8096,
                    system=SYSTEM_PROMPT,
                    tools=TOOLS,
                    messages=messages,
                ) as stream:

                    async for event in stream:

                        # ── New content block starting ──────────────────
                        if event.type == "content_block_start":
                            block = event.content_block
                            if block.type == "tool_use":
                                active_tool_calls[event.index] = {
                                    "id": block.id,
                                    "name": block.name,
                                    "partial_json": "",
                                }

                        # ── Content delta ───────────────────────────────
                        elif event.type == "content_block_delta":
                            delta = event.delta

                            if delta.type == "text_delta":
                                current_text += delta.text
                                yield sse({"type": "text", "text": delta.text})

                            elif delta.type == "input_json_delta":
                                tc = active_tool_calls.get(event.index)
                                if tc:
                                    tc["partial_json"] += delta.partial_json

                                    # Live-stream show_widget HTML as it arrives
                                    if tc["name"] == "show_widget":
                                        html = extract_widget_code(tc["partial_json"])
                                        if html and len(html) > 15:
                                            yield sse({"type": "widget_delta", "html": html})

                    final_msg = await stream.get_final_message()

            except Exception as e:
                yield sse({"type": "error", "text": str(e)})
                return

            # ── Build assistant content for conversation history ────────
            assistant_content = []
            if current_text:
                assistant_content.append({"type": "text", "text": current_text})
            for block in final_msg.content:
                if block.type == "tool_use":
                    assistant_content.append({
                        "type": "tool_use",
                        "id": block.id,
                        "name": block.name,
                        "input": block.input,
                    })

            # ── End of conversation ─────────────────────────────────────
            if final_msg.stop_reason != "tool_use":
                yield sse({"type": "done"})
                break

            # ── Process tool calls and loop ─────────────────────────────
            messages.append({"role": "assistant", "content": assistant_content})
            tool_results = []

            for block in final_msg.content:
                if block.type != "tool_use":
                    continue

                if block.name == "load_guidelines":
                    modules = block.input.get("modules", [])
                    content = get_guidelines(modules)
                    yield sse({"type": "status", "text": f"Loading {', '.join(modules)} guidelines..."})
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": content,
                    })

                elif block.name == "show_widget":
                    html = block.input.get("widget_code", "")
                    title = block.input.get("title", "widget").replace("_", " ")
                    yield sse({"type": "widget_final", "html": html, "title": title})
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": f"Widget '{title}' rendered successfully.",
                    })

            messages.append({"role": "user", "content": tool_results})
            # Loop → Claude sees tool results and continues

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


# Serve static/index.html — must be mounted last
app.mount("/", StaticFiles(directory=str(Path(__file__).parent / "static"), html=True), name="static")
