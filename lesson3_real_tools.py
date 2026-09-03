"""
Lesson 3: Real Tools — An Agent That Does Things

Lessons 1-2 used toy math tools. This one gives Claude real abilities:
  - Read files from disk
  - Write files to disk
  - List directory contents
  - Get the current date and time

Now Claude can actually interact with your system. And instead of
hardcoded test questions, this one gives you an interactive chat loop
so you can talk to the agent yourself.

Try things like:
  "What files are in this directory?"
  "Read lesson1_manual_loop.py and summarize what it does"
  "Create a file called notes.txt with a summary of what I've learned"
  "What time is it?"
"""

import os
from datetime import datetime

import anthropic
from anthropic import beta_tool
from dotenv import load_dotenv

load_dotenv()

client = anthropic.Anthropic()

# The working directory the agent can access (this project folder)
WORK_DIR = os.path.dirname(os.path.abspath(__file__))


# --- Tools ---


@beta_tool
def get_current_time() -> str:
    """Get the current date and time."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


@beta_tool
def list_files(directory: str = ".") -> str:
    """List files and folders in a directory.

    Args:
        directory: Relative path to list. Defaults to the project root.
    """
    target = os.path.join(WORK_DIR, directory)
    if not os.path.isdir(target):
        return f"Not a directory: {directory}"

    entries = []
    for name in sorted(os.listdir(target)):
        full = os.path.join(target, name)
        if os.path.isdir(full):
            entries.append(f"  [dir]  {name}/")
        else:
            size = os.path.getsize(full)
            entries.append(f"  [file] {name} ({size} bytes)")

    return "\n".join(entries) if entries else "(empty directory)"


@beta_tool
def read_file(path: str) -> str:
    """Read the contents of a file.

    Args:
        path: Relative path to the file.
    """
    target = os.path.join(WORK_DIR, path)
    if not os.path.isfile(target):
        return f"File not found: {path}"
    with open(target, "r") as f:
        content = f.read()
    # Truncate very large files so we don't blow up the context
    if len(content) > 5000:
        return content[:5000] + f"\n\n... (truncated, {len(content)} chars total)"
    return content


@beta_tool
def write_file(path: str, content: str) -> str:
    """Write content to a file. Creates the file if it doesn't exist.

    Args:
        path: Relative path for the file.
        content: The text content to write.
    """
    target = os.path.join(WORK_DIR, path)
    os.makedirs(os.path.dirname(target) or ".", exist_ok=True)
    with open(target, "w") as f:
        f.write(content)
    return f"Wrote {len(content)} chars to {path}"


ALL_TOOLS = [get_current_time, list_files, read_file, write_file]


# --- Agent ---


def run_agent(user_message: str, history: list) -> str:
    """Run the agent with conversation history for multi-turn chat."""

    history.append({"role": "user", "content": user_message})

    runner = client.beta.messages.tool_runner(
        model="claude-sonnet-4-6",
        max_tokens=4096,
        system=(
            "You are a helpful file assistant. You can read, write, and list files "
            "in the user's project directory. Keep responses concise. "
            "When reading code, give a brief summary unless asked for details. "
            "If the user sends a single ambiguous word that doesn't form a clear "
            "question, ask them to clarify rather than guessing what they meant."
        ),
        tools=ALL_TOOLS,
        messages=history,
    )

    final_text = ""
    for message in runner:
        # Print tool calls as they happen
        for block in message.content:
            if block.type == "tool_use":
                print(f"  [tool] {block.name}({block.input})")

        if message.stop_reason == "end_turn":
            for block in message.content:
                if block.type == "text":
                    final_text += block.text

    # Add the assistant's reply to history for multi-turn
    history.append({"role": "assistant", "content": final_text})

    return final_text


# --- Interactive chat ---


def main():
    print("=" * 60)
    print("  Lesson 3: File Assistant Agent")
    print("  Type your questions. 'quit' to exit.")
    print("=" * 60)

    history = []

    while True:
        try:
            user_input = input("\nYou: ").strip()
        except (EOFError, KeyboardInterrupt):
            break

        if not user_input:
            continue
        if user_input.lower() in ("quit", "exit", "q", "quite", "qui", "bye"):
            break

        response = run_agent(user_input, history)
        print(f"\nClaude: {response}")

    print("\nGoodbye!")


if __name__ == "__main__":
    main()
