#!/bin/sh
# Bu repodaki skills/* klasörlerini Claude yapılandırma klasörüne bağlar; araçlı skill'ler için komutu kurar.
# Argümansız hepsini kurar; ad verilirse yalnız onları: ./install.sh team-orchestration ajan-olcum
# Hedef: $CLAUDE_DIR, yoksa $CLAUDE_CONFIG_DIR, yoksa ~/.claude.
set -e
REPO="$(cd "$(dirname "$0")" && pwd)"
CLAUDE_DIR="${CLAUDE_DIR:-${CLAUDE_CONFIG_DIR:-$HOME/.claude}}"
export CLAUDE_DIR
for n in "$@"; do
  [ -d "$REPO/skills/$n" ] || { echo "böyle bir skill yok: $n" >&2; exit 1; }
done
mkdir -p "$CLAUDE_DIR/skills" "$HOME/.local/bin"
# Only the owner pushes to this repo; collaborators get a read-only clone.
OWNER=alisencerefeturk
login="$(gh api user --jq .login 2>/dev/null || true)"
[ -n "$login" ] || login="$(git -C "$REPO" config user.name 2>/dev/null || true)"
if [ "$login" != "$OWNER" ]; then
  git -C "$REPO" config remote.origin.pushurl "DISABLED-read-only-clone"
  echo "salt okunur klon: push kapalı (yalnız $OWNER değiştirir)"
fi
for d in "$REPO"/skills/*/; do
  n="$(basename "$d")"
  if [ $# -gt 0 ]; then
    case " $* " in *" $n "*) ;; *) continue ;; esac
  fi
  ln -sfn "${d%/}" "$CLAUDE_DIR/skills/$n"
  echo "skill bağlandı: $n"
  if [ -f "$d/olcum.py" ]; then
    printf '#!/bin/sh\nexec python3 "%s/olcum.py" "$@"\n' "${d%/}" > "$HOME/.local/bin/olcum"
    chmod +x "$HOME/.local/bin/olcum"
    echo "komut kuruldu: olcum (PATH'te ~/.local/bin olmalı)"
  fi
  if [ -x "$d/install.sh" ]; then
    "$d/install.sh"
  fi
done
