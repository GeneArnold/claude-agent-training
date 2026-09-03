# Claude Agents — Project Overview

## What This Is

A hands-on learning project for understanding how the **Anthropic Claude Agent SDK** works. The goal is to build real intuition for how Claude agents operate under the hood — not just call APIs, but understand the mechanics: the agentic loop, tool use, streaming, and how to debug all of it.

This is part of a broader path toward **Anthropic certification**.

## Who This Is For

Gene Arnold — Sales Engineer at Aquant.ai, with deep prior experience building AI agents on the OpenAI side (a full 7-module AI Agent Engineering Course covering agent loops, memory/RAG, tools, multi-agent systems, evaluation, and visual recognition). The Anthropic SDK is new; the agent concepts are not.

## The Lessons

Each lesson file builds on the previous one, progressing from raw API mechanics to a working streaming agent UI.

### Lesson 1: The Manual Loop (`lesson1_manual_loop.py`)
The fundamental agentic pattern, written by hand:
1. Send a message to Claude with tool definitions (JSON schemas)
2. Claude responds with text OR requests a tool call
3. If it requested a tool, execute it locally and send the result back
4. Repeat until Claude says it's done (`stop_reason == "end_turn"`)

Uses simple `add` and `multiply` math tools. The point isn't the tools — it's seeing the loop that drives every agent.

### Lesson 2: Tool Runner (`lesson2_tool_runner.py`)
Same tools, but now the SDK handles the loop. Key differences:
- Tools defined as decorated Python functions (`@beta_tool`) instead of raw JSON schemas
- `client.beta.messages.tool_runner()` replaces the manual while-loop
- The SDK reads type hints and docstrings to auto-generate the tool schema

### Lesson 2 Debug (`lesson2_debug.py`)
Same as Lesson 2, designed for stepping through with a debugger to inspect what Claude asked for and what came back. Use the VS Code debug configuration ("Lesson 2 — Debug Version") to set breakpoints visually and step through with the full debugging UI.

### Lesson 3: Real Tools (`lesson3_real_tools.py`)
Gives Claude actual system capabilities:
- Read files from disk
- Write files to disk
- List directory contents
- Get current date/time

Includes an interactive chat loop (terminal-based) so you can talk to the agent live. This is where the agent starts feeling like a real tool, not a demo.

### Lesson 4: Streaming UI (`lesson4_streaming_ui.py`)
A web frontend (FastAPI + SSE) that shows the agent working in real-time:
- Tokens stream to the browser as Claude generates them
- Tool calls and results are displayed inline
- Dark themed chat UI

Uses the manual loop pattern (not tool_runner) because streaming requires direct control over the message flow. Run with `python lesson4_streaming_ui.py` and open `http://localhost:8888`.

## Tooling Stack

### Development & Debugging
- **VS Code** — Primary editor and debugger. Used for stepping through lesson code with breakpoints, variable inspection, and the debug console. Settled on VS Code after evaluating simpler alternatives (Thonny, pudb) — they introduced more friction than they solved.
- **Python venv** — Standard virtual environment at `.venv/`. All dependencies (anthropic, python-dotenv, fastapi, uvicorn) installed there.
- **VS Code launch.json** — Debug configurations for all lesson files (`.vscode/launch.json`). Set breakpoints visually, hit F5, and step through any lesson.

### Observability & Tracing
- **Glassbox** — A custom-built OTEL (OpenTelemetry) based agent trace visualization tool with a co-pilot. Built previously as part of the OpenAI agent work. Glassbox handles the **agentic observability layer** — tracing agent behavior, LLM calls, tool invocations, and execution flow at the agent/system level. Think of it as "what is my agent doing and why."
- **VS Code Debugger** — Handles the **Python execution layer** — "what is my Python code doing line by line." These are complementary: Glassbox shows you the agent's decisions, VS Code shows you the code mechanics.

### APIs & Models
- **Anthropic Python SDK** (`anthropic` package)
- **Claude Sonnet 4.6** — Used across all lessons to keep costs low during learning
- **API key** via `.env` file (loaded with `python-dotenv`)

## Key Concepts Covered

| Concept | Where | What You Learn |
|---|---|---|
| Agentic loop | Lesson 1 | The send → check → execute → repeat pattern |
| Tool schemas | Lesson 1 | How to define tools as JSON for Claude |
| `@beta_tool` decorator | Lesson 2 | Let the SDK build schemas from type hints |
| Tool Runner | Lesson 2 | SDK-managed agentic loop |
| Debugging agents | Lesson 2 Debug | Using breakpoints to inspect agent state |
| Real system tools | Lesson 3 | File I/O, directory listing, timestamps |
| Multi-turn conversation | Lesson 3 | Maintaining message history across turns |
| Streaming | Lesson 4 | Token-by-token output via SSE |
| Web UI for agents | Lesson 4 | FastAPI + browser frontend for agent interaction |
| Real-world agent | Lesson 5 | Packaging a real task as an automated agent |
| subprocess tools | Lesson 5 | Tools that run actual system commands |
| Agent orchestration | Lesson 5 | Claude decides which tools to call and when |
| Structured reporting | Lesson 5 | Synthesizing raw data into actionable output |

### Lesson 5: Machine Health Agent (`lesson5_health_agent.py`)
The first real agent — not a demo. Uses the Tool Runner (`@beta_tool`) to build a machine health analyzer:
- 12 health check tools (disk, memory, CPU, network, security, Docker, thermal, etc.)
- Each tool runs real bash commands via `subprocess` and returns results
- Claude orchestrates which tools to call and in what order
- Synthesizes all results into a prioritized health report (Critical/Warning/Info/Recommendations)
- Runs headless — no human input needed after launch

This bridges the gap between "asking Claude to do something" and "packaging an agent as a product."

## Lesson Roadmap

| Lesson | Topic | Status |
|---|---|---|
| 1 | Manual agentic loop | Done |
| 2 | Tool Runner (`@beta_tool`) | Done |
| 2 Debug | Debugging with breakpoints | Done |
| 3 | Real tools (file I/O, interactive chat) | Done |
| 4 | Streaming UI (FastAPI + SSE) | Done |
| 5 | Machine Health Agent (real-world Tool Runner) | Done |
| 6 | Server-side tools (web search, code execution) | Planned |
| 7 | Structured outputs (typed JSON responses) | Planned |
| 8 | Extended thinking & effort levels | Planned |
| 9 | Prompt caching & cost optimization | Planned |
| 10 | Managed Agents — custom tools & vaults | Planned |
| 11 | Managed Agents — multi-agent coordination | Planned |
| 12 | Claude Agent SDK (Claude Code as a library) | Planned |

## What's Next

The lesson progression is building toward understanding how production agents are built with the Anthropic SDK — tool composition, error handling, multi-agent coordination, and how all of this connects to the certification path. The OpenAI agent course covered these concepts on that side; this project maps them to the Anthropic ecosystem.

## Debugging Philosophy

The project explored whether to build a custom simple Python debugger (something a child could use — load a file, step through, see variables, nothing else). After evaluating Thonny (broken Zenity dialogs on Ubuntu, snap sandboxing issues), pudb (terminal-only, learning curve), and the CodeHS web debugger (browser-based, not local), the conclusion was:

- **VS Code's debugger is the right tool** for this project — set breakpoints by clicking, hit F5, watch variables. Ignore everything else VS Code does.
- **Glassbox is the right tool** for agent-level tracing — it shows what the agent decided, not what the Python did.
- If a simpler debugger is ever built, the approach would be: a thin UI layer on top of Python's `bdb` module (the base class that `pdb` is built on), not a from-scratch implementation.
