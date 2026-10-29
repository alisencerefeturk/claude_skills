#!/usr/bin/env python3
import json
import os
import sys
import time

data = json.load(sys.stdin)

model = data.get("model", {}).get("display_name", "?")
ctx = data.get("context_window") or {}
ctx_pct = ctx.get("used_percentage")
rl = data.get("rate_limits") or {}
five_h = rl.get("five_hour") or {}
seven_d = rl.get("seven_day") or {}

snapshot = {
    "written_at": time.time(),
    "model": model,
    "context_used_percentage": ctx_pct,
    "rate_limits": {
        "five_hour": {
            "used_percentage": five_h.get("used_percentage"),
            "resets_at": five_h.get("resets_at"),
        },
        "seven_day": {
            "used_percentage": seven_d.get("used_percentage"),
            "resets_at": seven_d.get("resets_at"),
        },
    },
}

snapshot_path = os.path.join(os.environ.get("CLAUDE_CONFIG_DIR") or os.path.expanduser("~/.claude"), "rate-limit-status.json")
try:
    tmp_path = snapshot_path + ".tmp"
    with open(tmp_path, "w") as f:
        json.dump(snapshot, f)
    os.replace(tmp_path, snapshot_path)
except OSError:
    pass

RESET = "\033[0m"
DIM = "\033[2m"
GREEN = "\033[2;32m"
YELLOW = "\033[2;33m"
RED = "\033[2;31m"

PET_COLOR = "\033[38;5;180m"
LEVELS = ["low", "medium", "high", "xhigh", "max"]

def pet_for_effort(level):
    n = LEVELS.index(level) + 1 if level in LEVELS else 0
    meter = "▰" * n + DIM + "▱" * (5 - n) + RESET
    label = level or "—"
    return f"{PET_COLOR}ᓚᘏᗢ{RESET}  {PET_COLOR}{meter}  {DIM}{label}{RESET}"

def bar_color(pct):
    if pct > 80:
        return RED
    if pct > 70:
        return YELLOW
    return GREEN

def render_bar(pct, width=10):
    filled = int(round((pct / 100.0) * width))
    filled = max(0, min(width, filled))
    color = bar_color(pct)
    bar = color + ("█" * filled) + RESET + DIM + ("░" * (width - filled)) + RESET
    return bar

effort_level = (data.get("effort") or {}).get("level")
pet = pet_for_effort(effort_level)

parts = [f"[{model}]"]
if ctx_pct is not None:
    parts.append(f"ctx {int(ctx_pct)}%")

five_pct = five_h.get("used_percentage")
if five_pct is not None:
    parts.append(f"5h {render_bar(five_pct)} {int(five_pct)}%")

line = " | ".join(parts)

seven_pct = seven_d.get("used_percentage")
if seven_pct is not None:
    seven_part = f"7d {render_bar(seven_pct)} {int(seven_pct)}%"
    line = line + "  " + seven_part

print(line)
print(pet)
