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

link "$REPO" "$CLAUDE_DIR/skills/team-orchestration"
for a in team-haiku-worker team-sonnet-worker team-sonnet-worker-high \
         team-opus-worker team-opus-worker-high team-fable-worker; do
  link "$REPO/agents/$a.md" "$CLAUDE_DIR/agents/$a.md"
done
if [ -f "$STATUSLINE" ]; then
  link "$STATUSLINE" "$CLAUDE_DIR/statusline.sh"
  chmod +x "$STATUSLINE"
fi

if [ -e "$CLAUDE_DIR/skills/opus-orchestration" ]; then
  cat <<EOF

Warning: opus-orchestration is also installed in $CLAUDE_DIR.
Both policies would load on sub-agent work. On the Team account remove it:
  rm "$CLAUDE_DIR/skills/opus-orchestration"
EOF
fi

cat <<EOF

Done. Optional status line (shows model, context and effort; Team seats
usually get no quota bars) in $CLAUDE_DIR/settings.json:

  "statusLine": { "type": "command", "command": "$CLAUDE_DIR/statusline.sh" }
EOF
