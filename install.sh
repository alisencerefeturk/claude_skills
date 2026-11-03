#!/bin/sh
# Skill'leri kurar: her skill kendi kurulumunu yapar (skills/<ad>/install.sh).
# Argümansız: orkestrasyon dışındaki bütün skill'ler. Adla: ./install.sh ajan-olcum opus-orchestration
# İki orkestrasyon skill'i (opus-/team-orchestration) aynı Claude klasörüne kurulmaz; ad verilerek kurulur.
# Hedef: $CLAUDE_DIR, yoksa $CLAUDE_CONFIG_DIR, yoksa ~/.claude.
set -e
REPO="$(cd "$(dirname "$0")" && pwd)"
CLAUDE_DIR="${CLAUDE_DIR:-${CLAUDE_CONFIG_DIR:-$HOME/.claude}}"
export CLAUDE_DIR
for n in "$@"; do
  [ -d "$REPO/skills/$n" ] || { echo "böyle bir skill yok: $n" >&2; exit 1; }
done
if [ $# -eq 0 ]; then
  for d in "$REPO"/skills/*/; do
    n="$(basename "$d")"
    case "$n" in *-orchestration) ;; *) set -- "$@" "$n" ;; esac
  done
  ORK_NOTU=1
fi
for n in "$@"; do
  echo "== $n"
  if [ -x "$REPO/skills/$n/install.sh" ]; then
    "$REPO/skills/$n/install.sh"
  else
    mkdir -p "$CLAUDE_DIR/skills"
    ln -sfn "$REPO/skills/$n" "$CLAUDE_DIR/skills/$n"
    echo "skill bağlandı: $n"
  fi
done
if [ -n "${ORK_NOTU:-}" ]; then
  echo
  echo "Orkestrasyon kurulmadı. Birini seç: ./install.sh opus-orchestration (kişisel Claude Pro + ChatGPT Plus)"
  echo "ya da ./install.sh team-orchestration (şirket Claude Team, GPT yok)."
fi
echo "Skill'ler yeni açılan oturumda yüklenir."
