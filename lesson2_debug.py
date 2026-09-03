"""
Lesson 2 (Debug Version) — Step through the agent with pdb

Run this in your terminal:
  source .venv/bin/activate
  python lesson2_debug.py

When it hits a breakpoint, you'll get a (Pdb) prompt. Try these commands:
  n         → next line (step over)
  s         → step into a function
  p <var>   → print a variable  (e.g.  p a  or  p message.stop_reason)
  pp <var>  → pretty-print      (e.g.  pp message.content)
  c         → continue to the next breakpoint
  q         → quit

The breakpoints are inside the tool functions and in the message loop,
so you can inspect what Claude asked for and what came back.
"""

import anthropic
from anthropic import beta_tool
from dotenv import load_dotenv

load_dotenv()

client = anthropic.Anthropic()


@beta_tool
def add(a: float, b: float) -> str:
    """Add two numbers together.

    Args:
        a: First number.
        b: Second number.
    """
    result = a + b
    print(f"  [tool] add({a}, {b}) = {result}")
    return str(result)


@beta_tool
def multiply(a: float, b: float) -> str:
    """Multiply two numbers together.

    Args:
        a: First number.
        b: Second number.
    """
    result = a * b
    print(f"  [tool] multiply({a}, {b}) = {result}")
    return str(result)


def run_agent(user_message: str):
    print(f"\n{'='*60}")
    print(f"User: {user_message}")
    print(f"{'='*60}\n")

    runner = client.beta.messages.tool_runner(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        tools=[add, multiply],
        messages=[{"role": "user", "content": user_message}],
    )

    for message in runner:
        if message.stop_reason == "end_turn":
            for block in message.content:
                if block.type == "text":
                    print(f"\nClaude: {block.text}")


if __name__ == "__main__":
    # Just one question so the debugging session stays focused
    run_agent("What is (3 + 5) * 12?")
