#!/usr/bin/env bash
# proje-kur kurulumu: skill bağlantısı ve (repo sahibi değilsen) kişisel varsayılanlar dosyası.
# reference/varsayilanlar.md repo sahibinin sabitleridir (commit kimliği, sunucu). Başka bir makinede
# bunlar kullanılmasın diye <config>/proje-kur-varsayilanlar.md açılır; skill önce onu okur.
# Tekrar çalıştırmak güvenlidir; var olan kişisel dosyaya dokunulmaz.
set -euo pipefail

REPO="$(cd "$(dirname "$0")" && pwd)"
CLAUDE_DIR="${CLAUDE_DIR:-${CLAUDE_CONFIG_DIR:-$HOME/.claude}}"
SAHIP="alisencerefeturk"
KISISEL="$CLAUDE_DIR/proje-kur-varsayilanlar.md"

mkdir -p "$CLAUDE_DIR/skills"
ln -sfn "$REPO" "$CLAUDE_DIR/skills/proje-kur"
echo "skill bağlandı: $CLAUDE_DIR/skills/proje-kur"

login="$(gh api user -q .login 2>/dev/null || true)"
if [ "$login" = "$SAHIP" ]; then
  echo "repo sahibi: reference/varsayilanlar.md kullanılır"
elif [ -f "$KISISEL" ]; then
  echo "kişisel varsayılanlar zaten var: $KISISEL"
else
  ad="$(git config --global user.name 2>/dev/null || true)"
  eposta="$(git config --global user.email 2>/dev/null || true)"
  if [ -n "$ad" ] && [ -n "$eposta" ]; then kimlik="\`$ad <$eposta>\`"
  elif [ -n "$login" ]; then kimlik="\`$login\` (e-posta proje kurulurken sorulur)"
  else kimlik="ilk projede sorulur ve buraya yazılır"; fi
  cat > "$KISISEL" <<EOF
# Kullanıcı varsayılanları (bu makine)

proje-kur skill'i bunları sormadan kullanır; değişince bu dosya güncellenir. Skill reposundaki
\`reference/varsayilanlar.md\` repo sahibinindir, bu makinede kullanılmaz.

## Kimlik ve dil

- Kullanıcıyla Türkçe konuşulur. Kod tanımlayıcıları ve yorumlar İngilizce, kullanıcıya görünen metin Türkçe ve kısa.
- Saat dilimi: Europe/Istanbul.
- Commit kimliği: $kimlik.
- GitHub: hesap ${login:-"(gh girişi yok; GitHub'a yazmadan önce sorulur)"}; yeni depo private, dal \`main\`.

## Önerilen seçenekler

- Commit imzası: AI eki yok. Başkasının deposunda ya da ortak depoda o deponun kuralı sorulur.
- Orkestrasyon: kurulu olan skill önerilir; hiçbiri kurulu değilse "yok".
- Ölçüm: \`ajan-olcum\` kuruluysa öneri "evet". Proje adı küçük harf ve tireyle yazılır.

## Sunucu

- Tanımlı sunucu yok. Kullanıcı yayın yeri verirse adres, bağlanılacak hesap ve kurallar buraya eklenir.
EOF
  echo "kişisel varsayılanlar açıldı: $KISISEL (commit kimliği: $kimlik)"
fi
