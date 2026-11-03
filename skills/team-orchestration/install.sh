#!/usr/bin/env bash
# Symlink this skill folder, its agent presets and the shared statusline script
# into the Claude config dir ($CLAUDE_DIR, else $CLAUDE_CONFIG_DIR, else ~/.claude),
# so edits made in either place are tracked by git. Existing files are moved
# to <config dir>/backups/team-orchestration-<timestamp>/ first — outside skills/
# and agents/, so Claude Code doesn't load the backups as duplicates.
set -euo pipefail

REPO="$(cd "$(dirname "$0")" && pwd)"
CLAUDE_DIR="${CLAUDE_DIR:-${CLAUDE_CONFIG_DIR:-$HOME/.claude}}"
STAMP="$(date +%Y%m%d%H%M%S)"
BACKUP_DIR="$CLAUDE_DIR/backups/team-orchestration-$STAMP"
# The statusline is shared with opus-orchestration; one copy lives there.
STATUSLINE="$(cd "$REPO/.." && pwd)/opus-orchestration/statusline/statusline.sh"

link() {
  local src="$1" dst="$2"
  mkdir -p "$(dirname "$dst")"
  if [ -L "$dst" ] && [ "$(readlink "$dst")" = "$src" ]; then
    echo "ok       $dst"
    return
  fi
  if [ -e "$dst" ] || [ -L "$dst" ]; then
    mkdir -p "$BACKUP_DIR"
    mv "$dst" "$BACKUP_DIR/$(basename "$dst")"
    echo "backup   $dst -> $BACKUP_DIR/$(basename "$dst")"
  fi
  ln -s "$src" "$dst"
  echo "linked   $dst -> $src"
}

if [ -e "$CLAUDE_DIR/skills/opus-orchestration" ]; then
  echo "opus-orchestration zaten kurulu ($CLAUDE_DIR). İki orkestrasyon aynı klasöre kurulmaz; önce onu kaldır:" >&2
  echo "  rm \"$CLAUDE_DIR/skills/opus-orchestration\"" >&2
  exit 1
fi

link "$REPO" "$CLAUDE_DIR/skills/team-orchestration"
for a in team-haiku-worker team-sonnet-worker team-sonnet-worker-high \
         team-opus-worker team-opus-worker-high team-fable-worker; do
  link "$REPO/agents/$a.md" "$CLAUDE_DIR/agents/$a.md"
done
if [ -f "$STATUSLINE" ]; then
  link "$STATUSLINE" "$CLAUDE_DIR/statusline.sh"
  chmod +x "$STATUSLINE"
fi

# statusLine yoksa settings.json'a eklenir (yedekli); başka bir statusLine varsa dokunulmaz.
python3 - "$CLAUDE_DIR/settings.json" "$CLAUDE_DIR/statusline.sh" <<'PY'
import json, os, shutil, sys, time
p, cmd = sys.argv[1], sys.argv[2]
d = json.load(open(p, encoding="utf-8")) if os.path.exists(p) else {}
cur = (d.get("statusLine") or {}).get("command", "")
if cur and os.path.expanduser(cur) == cmd:
    print("ok       statusLine")
elif cur:
    print(f"statusLine başka bir komuta bağlı, dokunulmadı: {cur}\n  kota okuması için: \"statusLine\": {{\"type\": \"command\", \"command\": \"{cmd}\"}}")
else:
    if os.path.exists(p):
        shutil.copy(p, f"{p}.statusline-yedek-{time.strftime('%Y%m%d%H%M%S')}")
    d["statusLine"] = {"type": "command", "command": cmd}
    tmp = p + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(d, f, indent=2, ensure_ascii=False); f.write("\n")
    os.replace(tmp, p)
    print(f"statusLine eklendi: {p}")
PY

echo
echo "Bitti."
