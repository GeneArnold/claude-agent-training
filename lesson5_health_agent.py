"""
Lesson 5: A Real Agent — Machine Health Analysis

This is the payoff from Lessons 1-4. Instead of toy math tools,
we build something you'd actually use: an agent that runs a full
health analysis on your machine.

Each health check category is a tool. Claude decides which to run,
reads the results, and writes a prioritized report. Same pattern
as Lesson 2 (Tool Runner + @beta_tool), but solving a real problem.

Run it:
  source .venv/bin/activate
  python lesson5_health_agent.py

The agent will:
  1. Run checks across all categories (disk, memory, security, etc.)
  2. Analyze the results
  3. Print a prioritized health report
"""

import subprocess

import anthropic
from anthropic import beta_tool
from dotenv import load_dotenv

load_dotenv()

client = anthropic.Anthropic()


def run_commands(commands: list[str]) -> str:
    """Run a list of bash commands and return combined output."""
    results = []
    for cmd in commands:
        try:
            out = subprocess.run(
                cmd, shell=True, capture_output=True, text=True, timeout=30
            )
            output = out.stdout.strip()
            if out.stderr.strip():
                output += f"\nSTDERR: {out.stderr.strip()}"
            if output:
                results.append(f"$ {cmd}\n{output}")
        except subprocess.TimeoutExpired:
            results.append(f"$ {cmd}\n[TIMED OUT]")
        except Exception as e:
            results.append(f"$ {cmd}\n[ERROR: {e}]")
    return "\n\n".join(results)


# --- HEALTH CHECK TOOLS ---


@beta_tool
def check_system_info() -> str:
    """Get system identity: hostname, OS, kernel, uptime, CPU, RAM, hardware model."""
    return run_commands(
        [
            "hostnamectl 2>/dev/null || echo 'hostnamectl not available'",
            "uname -a",
            "lscpu | head -15",
            "free -h | head -3",
            "uptime",
        ]
    )


@beta_tool
def check_disk_usage() -> str:
    """Check disk usage, filesystem health, inode usage, and find large files over 500MB."""
    return run_commands(
        [
            "df -h",
            "df -i | grep -v tmpfs",
            "lsblk -f",
            "du -sh /home /var /tmp /opt 2>/dev/null",
            "find / -type f -size +500M -exec ls -lh {} \\; 2>/dev/null | head -20",
        ]
    )


@beta_tool
def check_memory_swap() -> str:
    """Check memory usage, swap status, and memory pressure."""
    return run_commands(
        [
            "free -h",
            "swapon --show 2>/dev/null || echo 'No swap configured'",
            "vmstat 1 3",
        ]
    )


@beta_tool
def check_cpu_load() -> str:
    """Check CPU load averages and top processes consuming CPU."""
    return run_commands(
        [
            "cat /proc/loadavg",
            "uptime",
            "ps aux --sort=-%cpu | head -12",
        ]
    )


@beta_tool
def check_network() -> str:
    """Check network interfaces, IP addresses, listening ports, and connectivity."""
    return run_commands(
        [
            "ip addr show | grep -E 'inet |state '",
            "ip route show",
            "ss -tuln | head -30",
            "ping -c 2 -W 3 8.8.8.8 2>&1",
            "resolvectl status 2>/dev/null | head -15 || cat /etc/resolv.conf",
        ]
    )


@beta_tool
def check_updates() -> str:
    """Check for pending package updates, security patches, and held packages."""
    return run_commands(
        [
            "apt list --upgradable 2>/dev/null | head -30",
            "apt list --upgradable 2>/dev/null | wc -l",
            "apt-mark showhold 2>/dev/null",
            "cat /var/run/reboot-required 2>/dev/null || echo 'No reboot required'",
            "ls /var/run/reboot-required.pkgs 2>/dev/null && cat /var/run/reboot-required.pkgs || echo 'No packages requiring reboot'",
        ]
    )


@beta_tool
def check_system_errors() -> str:
    """Check system logs for errors, warnings, and failed services in the last 24 hours."""
    return run_commands(
        [
            "journalctl --since '24 hours ago' -p err --no-pager -q 2>/dev/null | tail -30",
            "systemctl --failed 2>/dev/null",
            "dmesg | grep -i -E 'error|fail|warn' | tail -20",
        ]
    )


@beta_tool
def check_security() -> str:
    """Check firewall status, open ports, recent logins, and failed login attempts."""
    return run_commands(
        [
            "sudo ufw status 2>/dev/null || echo 'UFW not available'",
            "ss -tuln | grep LISTEN",
            "lastlog -t 7 2>/dev/null | grep -v 'Never'",
            "grep 'Failed password' /var/log/auth.log 2>/dev/null | tail -10 || echo 'No auth.log access'",
            "who",
        ]
    )


@beta_tool
def check_docker() -> str:
    """Check Docker status: running containers, images, disk usage. Returns 'not installed' if Docker is absent."""
    return run_commands(
        [
            "docker version --format '{{.Server.Version}}' 2>/dev/null || echo 'Docker not installed'",
            "docker ps -a --format 'table {{.Names}}\t{{.Status}}\t{{.Image}}' 2>/dev/null || echo 'N/A'",
            "docker system df 2>/dev/null || echo 'N/A'",
        ]
    )


@beta_tool
def check_thermal() -> str:
    """Check CPU and system temperatures, thermal throttling status."""
    return run_commands(
        [
            "sensors 2>/dev/null || echo 'lm-sensors not installed (install with: sudo apt install lm-sensors)'",
            "cat /sys/class/thermal/thermal_zone*/temp 2>/dev/null || echo 'No thermal zones found'",
            "cat /sys/class/thermal/thermal_zone*/type 2>/dev/null || echo ''",
        ]
    )


@beta_tool
def check_scheduled_tasks() -> str:
    """List all scheduled tasks: cron jobs, systemd timers, periodic maintenance."""
    return run_commands(
        [
            "crontab -l 2>/dev/null || echo 'No user crontab'",
            "sudo crontab -l 2>/dev/null || echo 'No root crontab or no sudo access'",
            "systemctl list-timers --no-pager 2>/dev/null | head -20",
            "ls /etc/cron.daily/ 2>/dev/null",
        ]
    )


@beta_tool
def check_boot_health() -> str:
    """Check boot configuration: EFI entries, GRUB config, kernel parameters."""
    return run_commands(
        [
            "sudo efibootmgr -v 2>/dev/null | head -15 || echo 'Not an EFI system or no access'",
            "cat /proc/cmdline",
            "ls -la /boot/vmlinuz-* 2>/dev/null | tail -5",
            "dmesg | grep -i -E 'efi|acpi' | head -10",
        ]
    )


ALL_TOOLS = [
    check_system_info,
    check_disk_usage,
    check_memory_swap,
    check_cpu_load,
    check_network,
    check_updates,
    check_system_errors,
    check_security,
    check_docker,
    check_thermal,
    check_scheduled_tasks,
    check_boot_health,
]


# --- THE AGENT ---


def run_health_agent():
    print("=" * 60)
    print("  Machine Health Agent")
    print("  Powered by Claude + Tool Runner")
    print("=" * 60)

    task = (
        "Run a complete health analysis on this machine. Call every available "
        "health check tool to gather data. After collecting all results, write "
        "a prioritized health report with these sections:\n\n"
        "1. CRITICAL — Issues that need immediate attention\n"
        "2. WARNING — Things to address soon\n"
        "3. INFO — Current status, no action needed\n"
        "4. RECOMMENDATIONS — Improvements and maintenance suggestions\n\n"
        "Be specific. Include actual numbers (disk %, memory usage, error counts). "
        "Don't repeat raw command output — interpret it."
    )

    print(f"\nTask: {task[:80]}...")
    print("\nRunning health checks...\n")

    runner = client.beta.messages.tool_runner(
        model="claude-sonnet-4-6",
        max_tokens=8192,
        system=(
            "You are a Linux system health analyst. You have tools to check "
            "every aspect of this machine. Run ALL of them to get a complete "
            "picture, then synthesize the results into a clear, actionable report. "
            "Focus on what matters — flag problems, skip noise."
        ),
        tools=ALL_TOOLS,
        messages=[{"role": "user", "content": task}],
    )

    for message in runner:
        for block in message.content:
            if block.type == "tool_use":
                print(f"  [{block.name}] running...")

        if message.stop_reason == "end_turn":
            print("\n" + "=" * 60)
            print("  HEALTH REPORT")
            print("=" * 60)
            for block in message.content:
                if block.type == "text":
                    print(f"\n{block.text}")


if __name__ == "__main__":
    run_health_agent()
