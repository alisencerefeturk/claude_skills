#!/usr/bin/env bash
# ajan-olcum kurulumu: skill bağlantısı, `olcum` komutu, oturum uzama kancası ve son 7 günün taranması.
# Tekrar çalıştırmak güvenlidir. Kancasız kurmak için: ./install.sh --kancasiz
# Hedef: $CLAUDE_DIR, yoksa $CLAUDE_CONFIG_DIR, yoksa ~/.claude.
set -euo pipefail

REPO="$(cd "$(dirname "$0")" && pwd)"
CLAUDE_DIR="${CLAUDE_DIR:-${CLAUDE_CONFIG_DIR:-$HOME/.claude}}"
export CLAUDE_DIR
KANCA=1
[ "${1:-}" = "--kancasiz" ] && KANCA=0

command -v python3 >/dev/null || { echo "python3 gerekli, bulunamadı" >&2; exit 1; }

mkdir -p "$CLAUDE_DIR/skills" "$HOME/.local/bin"
ln -sfn "$REPO" "$CLAUDE_DIR/skills/ajan-olcum"
echo "skill bağlandı: $CLAUDE_DIR/skills/ajan-olcum"

printf '#!/bin/sh\nexec python3 "%s/olcum.py" "$@"\n' "$REPO" > "$HOME/.local/bin/olcum"
chmod +x "$HOME/.local/bin/olcum"
echo "komut kuruldu: ~/.local/bin/olcum"
case ":$PATH:" in
  *":$HOME/.local/bin:"*) ;;
  *) echo "uyarı: ~/.local/bin PATH'te değil; kabuk ayarına ekle: export PATH=\"\$HOME/.local/bin:\$PATH\"" ;;
esac

if [ "$KANCA" = 1 ]; then
  python3 "$REPO/olcum.py" kanca kur
  python3 "$REPO/olcum.py" oturum tara --gun 7
fi

echo
echo "Bitti. Bir hafta sonra: olcum oturum rapor --gun 7 · paylaşmak için: olcum disa-aktar --hedef paket --sahip <ad>"
[ "$KANCA" = 1 ] && echo "Kancayı kaldırmak için: olcum kanca kaldir"
exit 0
