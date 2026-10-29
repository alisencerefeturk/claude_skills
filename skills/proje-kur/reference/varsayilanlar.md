# Kullanıcı varsayılanları

Skill bunları sormadan kullanır. Bir şey değişirse bu dosya güncellenir. Dosya skills reposundadır; kurulu skill buna bağlantı olduğu için değişiklik hemen geçerli olur.

## Kimlik ve dil

- Kullanıcıyla Türkçe konuşulur. Kod tanımlayıcıları ve yorumlar İngilizce, kullanıcıya görünen metin Türkçe ve kısa.
- Saat dilimi: Europe/Istanbul.
- Commit kimliği: `alisencerefeturk <161599497+alisencerefeturk@users.noreply.github.com>`.
- GitHub: hesap `alisencerefeturk`; yeni depo private, dal `main`.

## Önerilen seçenekler

- Commit imzası: AI eki yok. Kullanıcının çoğu projesinde kural budur. Başkasının deposunda ya da ortak depoda o deponun kuralı sorulur (ör. deck-app'te ortak yazar satırı zorunlu).
- Orkestrasyon:
  - Kişisel makinede `opus-orchestration`, şirket Team hesabında `team-orchestration`.
  - İkisi aynı Claude klasörüne kurulmaz; kurulu olan önerilir.
  - Hiçbiri kurulu değilse "yok" önerilir ve skills reposunun kurulumu hatırlatılır.
- Ölçüm: `ajan-olcum` kuruluysa öneri "evet". Proje adı küçük harf ve tireyle yazılır (ör. `pano`, `arc-website`).

## Sunucu ("kullanıcının VDS'i" seçilirse)

- Genel sunucu kuralları ve bakım raporları: `~/Documents/sunucu-bakim/AGENTS.md`, `~/Documents/sunucu-bakim/raporlar/`.
- Alt alan adları `*.sencerefeturk.space` biçimindedir. DNS Cloudflare'de ve kullanıcıdadır; ajan DNS değiştirmez.
- Ajan sunucuya şu hesaplardan biriyle bağlanır; hangisi olacağı proje başında sorulur:
  - Yönetici takma adı `arc-admin` (sudo'lu).
  - Projeye açılmış ayrı hesap (ör. satınalma'nın `satinalma-vds-claude`'u).

  Kullanıcının kişisel hesabı (`arc-server`) kullanılmaz.
- Sunucuda başka projeler de çalışır. Ajan yalnız kendi projesine dokunur ve her sunucu değişikliğini `~/Documents/sunucu-bakim/raporlar/YYYY-MM-DD-konu.md` dosyasına yazar.
