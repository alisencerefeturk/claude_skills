#!/bin/sh
# Bu repodaki bütün skills/* klasörlerini ~/.claude/skills altına bağlar; araçlı skill'ler için komutu kurar.
set -e
REPO="$(cd "$(dirname "$0")" && pwd)"
mkdir -p "$HOME/.claude/skills" "$HOME/.local/bin"
for d in "$REPO"/skills/*/; do
  n="$(basename "$d")"
  ln -sfn "${d%/}" "$HOME/.claude/skills/$n"
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
