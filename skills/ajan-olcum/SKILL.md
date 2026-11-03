---
name: ajan-olcum
description: Model/ajan karşılaştırma ölçümü (süre, token, maliyet, hata, zorluk puanı). Kullan: bir ajan/alt ajan/codex/claude -p dağıtırken kayıt tutmak, iş bitince hata sonuçlarını işlemek, model karşılaştırma raporu çıkarmak, GitHub'daki projelerin olcum/ klasörlerini toplamak, ölçüm verisini paylaşmak ya da başkasının verisini içeri almak, oturumların/skill'lerin işi uzatıp uzatmadığını oturum kayıtlarından ölçmek. "ölçüm", "kıyas", "hangi model daha iyi", "olcum klasörlerini topla", "uzama", "döngüye giriyor mu", "oturum raporu" gibi isteklerde tetiklenir.
---

# ajan-olcum

Araç `olcum` komutu (bu klasördeki `olcum.py`). `olcum` yoksa skills reposunun kökündeki `install.sh` çalıştırılır (komutu `~/.local/bin/olcum` olarak kurar). Standart ve sütunlar: `STANDART.md` (bu klasörde). Veri: `~/.ajan-olcum/data` (`$OLCUM_HOME` ile değişir); repoya konmaz. Yalnız Python 3 gerekir.

## Kalıp (herkes aynı biçimi kullanır)

Bir projenin paylaşılabilir ölçümü `olcum/` klasörüdür: `olcum.json` (`{"arac":"ajan-olcum","format":1,"proje":...,"sahip":...}`) + `yurutme.csv`, `review.csv`, `arastirma.csv`, `kapi.csv`, `oturum.csv`. GitHub'da toplama bu `olcum/olcum.json` dosyasını arar. `format` uyuşmayan paket atlanır.

## 1. Ajan dağıtırken kaydet

```bash
olcum run --gorev TASK-042 --hat claude --model claude-sonnet-5-5 --effort medium \
  --risk R2 --boyut M --belirsizlik 1.5 --base main -- \
  claude -p "<spec>" --model claude-sonnet-5-5 --effort medium --output-format json
```

- ZP girdileri (risk R0–R3, boyut S/M/L, belirsizlik 1.0/1.5/2.0) **dağıtım anında** verilir, sonradan değişmez.
- Claude için `--output-format json` şart (token/maliyet oradan). Codex için `codex exec` çıktısındaki `tokens used` okunur.
- Sonunda yazılan `run_id`'yi sakla.

## 2. İş ve review bitince sonuç işle

```bash
olcum bitir <run_id> review_p1=1 review_p0=0 ork_p1=0 p2=2 sonuc=kabul tur=2 not="..."
```

Sayaç boş = bilinmiyor, 0 = hata yok. Hata yoksa 0 yaz. Review/araştırma/kapı: `olcum add review|arastirma|kapi alan=değer ...`.

## 3. Rapor

`olcum rapor [--proje P] [--sahip S|ben] [--html dosya]`. Rol başına 5 satırdan azı "yönlü"dür; model hakkında karar için yetmez. "Zorluk tahmini isabeti" tablosu ZP'nin işe yarayıp yarımadığını gösterir.

## 4. Projelerden topla (GitHub)

Kullanıcı "tüm projelerde olcum klasörü olanları topla" derse:

```bash
olcum topla --github <kullanıcı-ya-da-org>        # olcum/olcum.json olan her repo
olcum topla --repo owner/ad --repo owner/ad2      # belirli repolar
olcum topla --klasor ./gelen-paket --sahip ali    # başkasından gelen paket
olcum rapor
```

`gh` giriş yapmış olmalı (özel repolar o hesapla görünür). Kendi repoların varsayılan atlanır (merkez zaten içeriyor; `--kendi` ile zorla). Yinelenen satırlar eklenmez, tekrar koşmak güvenlidir.

## 5. Projenin ölçümünü repoya koy

```bash
olcum yayinla --repo . --proje <ad> [--temiz]
```

Yalnız `olcum/` klasörünü yazar. **Commit ve push'u kullanıcı ister.** Önce `gh repo view --json isPrivate` ile depo görünürlüğüne bak; herkese açıksa `--temiz` (serbest metin `not`, `kacan_aciklama`, `oturum_id`, `test` atılır, görev/konu adları özetlenir) kullan ya da kullanıcıya sor.

## 6. Oturum uzama ölçümü (transcript'ten, modele yük yok)

Skill'lerin işi uzatıp uzatmadığını Claude Code oturum kayıtlarından (`~/.claude/projects/**/*.jsonl`) ölçer. Ajan hiçbir şey kaydetmez; kayıtlar sonradan okunur.

```bash
olcum oturum tara --gun 7     # son 7 günün oturumlarını oturum.csv'ye ekler (tekrar koşmak güvenli)
olcum kanca kur               # isteğe bağlı: her tur bitince arka planda tarar (settings.json'a Stop kancası, yedekli)
olcum oturum rapor --gun 7    # skill bağlamına göre istek başına süre/API/token, uzama işaretleri, alt ajanlar
olcum kanca kaldir
```

- Satır: ana oturumun bir turu (kullanıcı istemi, işçi bildirimi, alt ajan dönüşü) ya da bir alt ajanın koşusu. Aynı `istek_no` bir kullanıcı isteğine bağlı her şeyi toplar.
- Uzama işaretleri: aynı çağrının tekrarı, art arda hata, `sleep`/`until` yoklaması, Bash'in 10 dk sınırına çarpma, işçiye ek tur (`devam`), devir/checkpoint/kota/olcum dosyalarına giden çağrı payı (`defter`), bağlam sıkıştırma.
- "Bağlam" o isteğe kadar oturumda yüklenen skill'lerdir. Görevler farklı olduğu için bağlamlar arası fark yönlüdür; skill'in etkisini kanıtlamaz.
- `istem_ozet` (istemin ilk 80 karakteri) yalnız yerelde kalır; `disa-aktar` ve `yayinla --temiz` onu ve `oturum_id`'yi atar. Paylaşılan raporda proje adlarını da gizlemek için `olcum oturum rapor --gizli`.
- Transcript'ler Claude Code'da varsayılan 30 gün tutulur; kanca kurulu değilse bu süre dolmadan `tara` koşulmalı.

## 7. Başkasıyla paylaş

```bash
olcum disa-aktar --hedef paket --sahip <adın> [--proje P] [--proje-gizle]
```

Anonim paket üretir; oturum ölçümü (`oturum.csv`) da içindedir (serbest metin atılır, görev adları özetlenir; `--proje-gizle` proje adlarını da). Kullanıcı klasörü zipleyip gönderir. Alıcı: `olcum topla --klasor paket`. Gönderme ve yayınlama kullanıcının kararıdır; paketi kendin gönderme/push etme.

## Dikkat

- Ham veri serbest metinde proje/iş sırrı içerebilir; paylaşım öncesi `disa-aktar` kullan, ham CSV'yi paylaşma.
- Gelen satırlara `sahip` yazılır; kendi satırlarında boştur. Başkasının verisini kendi kararına karıştırırken `--sahip` ile ayır.
- Eksik/şüpheli ölçüm uydurma; bilinmeyeni boş bırak.
