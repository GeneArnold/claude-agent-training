"""
Lesson 1: Hello Agent — The Manual Loop

This is the fundamental pattern behind every Claude agent.
Three things happen in a loop:
  1. You send a message to Claude (with tool definitions)
  2. Claude either responds with text OR asks to call a tool
  3. If it asked for a tool, you run it and send the result back

That's it. That's the whole trick.
"""

import json

import anthropic
from dotenv import load_dotenv

load_dotenv()

client = anthropic.Anthropic()

# --- STEP 1: Define your tools ---
# Tools are just JSON schemas that tell Claude what functions it can call.
# Think of them as a menu: Claude reads the menu and decides what to order.

tools = [
    {
        "name": "add",
        "description": "Add two numbers together",
        "input_schema": {
            "type": "object",
            "properties": {
                "a": {"type": "number", "description": "First number"},
                "b": {"type": "number", "description": "Second number"},
            },
            "required": ["a", "b"],
        },
    },
    {
        "name": "multiply",
        "description": "Multiply two numbers together",
        "input_schema": {
            "type": "object",
            "properties": {
                "a": {"type": "number", "description": "First number"},
                "b": {"type": "number", "description": "Second number"},
            },
            "required": ["a", "b"],
        },
    },
]


# --- STEP 2: Implement the actual tool logic ---
# This is YOUR code. Claude never sees this — it only sees the results.


def run_tool(name: str, inputs: dict) -> str:
    if name == "add":
        result = inputs["a"] + inputs["b"]
        return str(result)
    elif name == "multiply":
        result = inputs["a"] * inputs["b"]
        return str(result)
    else:
        return f"Unknown tool: {name}"


# --- STEP 3: The agentic loop ---
# This is the core pattern. Send a message, check if Claude wants to
# call tools, execute them, send results back, repeat.


def run_agent(user_message: str):
    print(f"\n{'='*60}")
    print(f"User: {user_message}")
    print(f"{'='*60}\n")

    messages = [{"role": "user", "content": user_message}]
    turn = 0

    while True:
        turn += 1
        print(f"--- Turn {turn}: Sending to Claude ---")

        response = client.messages.create(
            model="claude-sonnet-4-6",  # using Sonnet to keep costs low for learning
            max_tokens=1024,
            tools=tools,
            messages=messages,
        )

        print(f"  Stop reason: {response.stop_reason}")

        # Claude is done talking — no more tool calls
        if response.stop_reason == "end_turn":
            for block in response.content:
                if block.type == "text":
                    print(f"\nClaude: {block.text}")
            break

        # Claude wants to call one or more tools
        if response.stop_reason == "tool_use":
            # Add Claude's response to the conversation
            messages.append({"role": "assistant", "content": response.content})

            # Find and execute each tool call
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    print(f"  Tool call: {block.name}({json.dumps(block.input)})")
                    result = run_tool(block.name, block.input)
                    print(f"  Result: {result}")

                    tool_results.append(
                        {
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": result,
                        }
                    )

            # Send results back as a user message
            messages.append({"role": "user", "content": tool_results})


# --- Try it! ---
if __name__ == "__main__":
    # Simple — one tool call
    run_agent("What is 7 + 15?")

    # Harder — Claude needs to chain multiple tool calls
    run_agent("What is (3 + 5) * 12?")

    # Interesting — Claude decides which tools to use
    run_agent(
        "I have 4 apples and someone gives me 6 more. Then I triple my collection. How many do I have?"
    )
