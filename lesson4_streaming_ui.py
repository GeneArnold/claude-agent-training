"""
Lesson 4: Streaming Frontend — Watch the Agent Think

This puts a web UI on our agent. When Claude calls a tool or types a
response, you see it happen in real-time via Server-Sent Events (SSE).

Run it:
  source .venv/bin/activate
  python lesson4_streaming_ui.py

Then open http://localhost:8888 in your browser.

New concepts:
  - Streaming: tokens arrive one at a time instead of all at once
  - SSE (Server-Sent Events): the browser listens for a stream of events
  - The agent loop now runs on the server and pushes updates to the browser
"""

import json
import os
from datetime import datetime

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, StreamingResponse

load_dotenv()

import anthropic

client = anthropic.Anthropic()
app = FastAPI()

WORK_DIR = os.path.dirname(os.path.abspath(__file__))


# --- Tools (same ones from Lesson 3) ---

TOOLS = [
    {
        "name": "get_current_time",
        "description": "Get the current date and time.",
        "input_schema": {
            "type": "object",
            "properties": {},
        },
    },
    {
        "name": "list_files",
        "description": "List files and folders in a directory.",
        "input_schema": {
            "type": "object",
            "properties": {
                "directory": {
                    "type": "string",
                    "description": "Relative path to list. Defaults to project root.",
                },
            },
        },
    },
    {
        "name": "read_file",
        "description": "Read the contents of a file.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Relative path to the file.",
                },
            },
            "required": ["path"],
        },
    },
]


def run_tool(name: str, inputs: dict) -> str:
    if name == "get_current_time":
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    elif name == "list_files":
        directory = inputs.get("directory", ".")
        target = os.path.join(WORK_DIR, directory)
        if not os.path.isdir(target):
            return f"Not a directory: {directory}"
        entries = []
        for n in sorted(os.listdir(target)):
            full = os.path.join(target, n)
            if n.startswith("."):
                continue
            if os.path.isdir(full):
                entries.append(f"  [dir]  {n}/")
            else:
                entries.append(f"  [file] {n} ({os.path.getsize(full)} bytes)")
        return "\n".join(entries) if entries else "(empty)"
    elif name == "read_file":
        target = os.path.join(WORK_DIR, inputs["path"])
        if not os.path.isfile(target):
            return f"File not found: {inputs['path']}"
        with open(target) as f:
            content = f.read()
        if len(content) > 5000:
            return content[:5000] + f"\n...(truncated, {len(content)} chars total)"
        return content
    return f"Unknown tool: {name}"


# --- Streaming agent endpoint ---


def sse_event(event_type: str, data: dict) -> str:
    """Format a Server-Sent Event."""
    return f"event: {event_type}\ndata: {json.dumps(data)}\n\n"


def agent_stream(user_message: str):
    """Generator that runs the agent loop and yields SSE events."""

    messages = [{"role": "user", "content": user_message}]

    yield sse_event("status", {"text": "Thinking..."})

    while True:
        # Stream the response so tokens arrive one at a time
        with client.messages.stream(
            model="claude-sonnet-4-6",
            max_tokens=4096,
            system=(
                "You are a helpful file assistant. You can read and list files "
                "in the user's project directory. Keep responses concise."
            ),
            tools=TOOLS,
            messages=messages,
        ) as stream:
            # Stream text tokens to the browser as they arrive
            for event in stream:
                if event.type == "content_block_delta":
                    if event.delta.type == "text_delta":
                        yield sse_event("token", {"text": event.delta.text})

            response = stream.get_final_message()

        # Done — no more tool calls
        if response.stop_reason == "end_turn":
            yield sse_event("done", {})
            break

        # Tool calls — execute and continue
        if response.stop_reason == "tool_use":
            messages.append({"role": "assistant", "content": response.content})

            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    yield sse_event(
                        "tool_call",
                        {
                            "name": block.name,
                            "input": block.input,
                        },
                    )

                    result = run_tool(block.name, block.input)

                    yield sse_event(
                        "tool_result",
                        {
                            "name": block.name,
                            "result": result[:500],
                        },
                    )

                    tool_results.append(
                        {
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": result,
                        }
                    )

            messages.append({"role": "user", "content": tool_results})
            yield sse_event("status", {"text": "Thinking..."})


@app.get("/chat")
async def chat(message: str):
    return StreamingResponse(
        agent_stream(message),
        media_type="text/event-stream",
    )


# --- Frontend ---

HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Claude Agent</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }

  body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
    background: #111;
    color: #e0e0e0;
    height: 100vh;
    display: flex;
    flex-direction: column;
  }

  header {
    padding: 1rem 1.5rem;
    border-bottom: 1px solid #2a2a2a;
    font-size: 0.8rem;
    color: #888;
    letter-spacing: 0.05em;
    text-transform: uppercase;
  }

  #chat {
    flex: 1;
    overflow-y: auto;
    padding: 1.5rem;
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }

  .msg {
    max-width: 720px;
    line-height: 1.6;
    font-size: 0.95rem;
  }

  .msg.user {
    color: #a0c4ff;
    font-weight: 500;
  }

  .msg.assistant {
    color: #e0e0e0;
  }

  .msg.tool {
    font-family: 'SF Mono', 'Fira Code', monospace;
    font-size: 0.8rem;
    color: #888;
    background: #1a1a1a;
    border-left: 3px solid #444;
    padding: 0.5rem 0.75rem;
    border-radius: 0 4px 4px 0;
    white-space: pre-wrap;
    overflow-x: auto;
  }

  .msg.tool .tool-name {
    color: #c084fc;
    font-weight: 600;
  }

  .msg.tool .tool-result {
    color: #6ee7b7;
    margin-top: 0.25rem;
  }

  .status {
    color: #666;
    font-size: 0.8rem;
    font-style: italic;
  }

  #input-area {
    padding: 1rem 1.5rem;
    border-top: 1px solid #2a2a2a;
    display: flex;
    gap: 0.75rem;
  }

  #input {
    flex: 1;
    background: #1a1a1a;
    border: 1px solid #333;
    border-radius: 6px;
    padding: 0.75rem 1rem;
    color: #e0e0e0;
    font-size: 0.95rem;
    font-family: inherit;
    outline: none;
  }

  #input:focus { border-color: #555; }

  #send {
    background: #2563eb;
    border: none;
    border-radius: 6px;
    padding: 0.75rem 1.5rem;
    color: white;
    font-size: 0.9rem;
    font-weight: 500;
    cursor: pointer;
    font-family: inherit;
  }

  #send:hover { background: #1d4ed8; }
  #send:disabled { opacity: 0.4; cursor: default; }
</style>
</head>
<body>

<header>Lesson 4 &mdash; Streaming Agent UI</header>

<div id="chat"></div>

<div id="input-area">
  <input id="input" placeholder="Ask something... try 'what files are here?'" autofocus>
  <button id="send" onclick="send()">Send</button>
</div>

<script>
const chat = document.getElementById('chat');
const input = document.getElementById('input');
const sendBtn = document.getElementById('send');

input.addEventListener('keydown', e => { if (e.key === 'Enter') send(); });

function addMsg(cls, html) {
  const div = document.createElement('div');
  div.className = 'msg ' + cls;
  div.innerHTML = html;
  chat.appendChild(div);
  chat.scrollTop = chat.scrollHeight;
  return div;
}

function send() {
  const text = input.value.trim();
  if (!text) return;

  input.value = '';
  sendBtn.disabled = true;
  addMsg('user', text);

  const responseDiv = addMsg('assistant', '');
  const source = new EventSource('/chat?message=' + encodeURIComponent(text));

  source.addEventListener('status', e => {
    const data = JSON.parse(e.data);
    const s = document.createElement('div');
    s.className = 'status';
    s.textContent = data.text;
    chat.appendChild(s);
    chat.scrollTop = chat.scrollHeight;
  });

  source.addEventListener('token', e => {
    const data = JSON.parse(e.data);
    responseDiv.textContent += data.text;
    chat.scrollTop = chat.scrollHeight;
  });

  source.addEventListener('tool_call', e => {
    const data = JSON.parse(e.data);
    const args = JSON.stringify(data.input);
    addMsg('tool', '<span class="tool-name">' + data.name + '</span>(' + args + ')');
  });

  source.addEventListener('tool_result', e => {
    const data = JSON.parse(e.data);
    const last = chat.querySelector('.msg.tool:last-of-type');
    if (last) {
      const r = document.createElement('div');
      r.className = 'tool-result';
      r.textContent = '→ ' + data.result;
      last.appendChild(r);
      chat.scrollTop = chat.scrollHeight;
    }
  });

  source.addEventListener('done', () => {
    source.close();
    sendBtn.disabled = false;
    // Remove the "Thinking..." status messages
    chat.querySelectorAll('.status').forEach(s => s.remove());
    input.focus();
  });

  source.onerror = () => {
    source.close();
    sendBtn.disabled = false;
    if (!responseDiv.textContent) {
      responseDiv.textContent = '(connection error — is the server running?)';
    }
  };
}
</script>
</body>
</html>"""


@app.get("/", response_class=HTMLResponse)
async def index():
    return HTML


if __name__ == "__main__":
    import uvicorn

    print("\n  Open http://localhost:8888 in your browser\n")
    uvicorn.run(app, host="0.0.0.0", port=8888)
