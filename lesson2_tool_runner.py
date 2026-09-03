"""
Lesson 2: Tool Runner — Let the SDK Do the Loop

In Lesson 1 we wrote the loop ourselves:
  send message → check for tool calls → execute → send results → repeat

The Tool Runner does all of that for you. You just:
  1. Decorate your functions with @beta_tool
  2. Hand them to tool_runner()
  3. Iterate — each step is a complete turn

Compare this file to lesson1. Same tools, same results, way less plumbing.
"""

import anthropic
from anthropic import beta_tool
from dotenv import load_dotenv

load_dotenv()

client = anthropic.Anthropic()


# --- STEP 1: Define tools as decorated functions ---
# The decorator reads your function signature and docstring
# and builds the JSON schema automatically. No manual schema needed.


@beta_tool
def add(a: float, b: float) -> str:
    """Add two numbers together.

    Args:
        a: First number.
        b: Second number.
    """
    print(f"  [tool] add({a}, {b}) = {a + b}")
    return str(a + b)


@beta_tool
def multiply(a: float, b: float) -> str:
    """Multiply two numbers together.

    Args:
        a: First number.
        b: Second number.
    """
    print(f"  [tool] multiply({a}, {b}) = {a * b}")
    return str(a * b)


# --- STEP 2: Run the agent ---
# No while loop. No message assembly. No tool_result plumbing.
# The runner handles everything.


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

    # Each iteration yields a complete message from Claude.
    # The runner calls your tool functions behind the scenes.
    for message in runner:
        # When Claude is done, print the final text
        if message.stop_reason == "end_turn":
            for block in message.content:
                if block.type == "text":
                    print(f"\nClaude: {block.text}")


# --- Try it! ---
if __name__ == "__main__":
    run_agent("What is 7 + 15?")

    run_agent("What is (3 + 5) * 12?")

    run_agent(
        "I have 4 apples and someone gives me 6 more. "
        "Then I triple my collection. How many do I have?"
    )
