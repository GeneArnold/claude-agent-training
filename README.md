# Claude Agent Training

A hands-on course for building AI agents with the Anthropic Claude SDK. Each lesson builds on the previous one, progressing from raw API mechanics to a real-world agent that performs machine health analysis.

This project exists because Anthropic has a certification exam (CCA-F) but no structured curriculum. These lessons fill that gap.

## The Lessons

| # | File | What You Build |
|---|---|---|
| 1 | `lesson1_manual_loop.py` | The agentic loop by hand — the pattern behind every AI agent |
| 2 | `lesson2_tool_runner.py` | Same agent, SDK handles the loop — `@beta_tool` + Tool Runner |
| 2d | `lesson2_debug.py` | Debug version with breakpoints for stepping through |
| 3 | `lesson3_real_tools.py` | Agent with real tools — file I/O, interactive chat |
| 4 | `lesson4_streaming_ui.py` | Web UI with real-time streaming (FastAPI + SSE) |
| 5 | `lesson5_health_agent.py` | **A real agent** — full machine health analysis with 12 tools, pushes a phone alert when something's wrong |

## Quick Start

```bash
git clone https://github.com/GeneArnold/claude-agent-training.git
cd claude-agent-training
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Create a `.env` file with your API key:

```
ANTHROPIC_API_KEY=your-key-here
```

For Lesson 5's phone notifications, also add a secret ntfy.sh topic (subscribe
to the same name in the [ntfy app](https://ntfy.sh/) or a browser tab):

```
NTFY_TOPIC=pick-something-unguessable
```

Run any lesson:

```bash
python lesson1_manual_loop.py
```

## What You'll Learn

**Lessons 1-2:** Every AI agent is a while loop. Send a message, check if Claude wants to call a tool, execute it, send the result back. That's it. Lesson 1 writes the loop by hand. Lesson 2 lets the SDK do it.

**Lesson 3:** Give Claude real tools (file read/write, directory listing) and an interactive chat loop. The agent starts feeling like a real assistant.

**Lesson 4:** Put a web UI on the agent. Tokens stream to the browser in real-time. Tool calls appear inline. You see the agent think.

**Lesson 5:** The payoff. A machine health agent that runs 12 system checks (disk, memory, CPU, network, security, Docker, thermal, updates, etc.) and synthesizes a prioritized report. Same pattern as Lesson 2, but solving a real problem. It also has a `send_notification` tool wired to [ntfy.sh](https://ntfy.sh/) — Claude pushes exactly one phone notification every run, always, with the title/priority reflecting what it found. That's a **dead man's switch**: if the agent only notified on problems, a clean machine and a check that crashed before it ever ran would both look like silence — indistinguishable from each other. Notifying every time means silence can only ever mean one thing: the check didn't run.

## Requirements

- Python 3.10+
- An Anthropic API key
- Linux (Lesson 5 uses Linux system commands)

## Background

Built by [Gene Arnold](https://www.linkedin.com/in/genearnold/) while learning the Anthropic SDK for the Claude Certified Architect (CCA-F) exam. Previously built a 7-module AI Agent Engineering Course on the OpenAI side. These lessons map those concepts to the Anthropic ecosystem.

See [PROJECT_OVERVIEW.md](PROJECT_OVERVIEW.md) for the full technical writeup.
