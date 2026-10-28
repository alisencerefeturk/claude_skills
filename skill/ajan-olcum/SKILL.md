---
name: ajan-olcum
description: Model/ajan karşılaştırma ölçümü (süre, token, maliyet, hata, zorluk puanı). Kullan: bir ajan/alt ajan/codex/claude -p dağıtırken kayıt tutmak, iş bitince hata sonuçlarını işlemek, model karşılaştırma raporu çıkarmak, GitHub'daki projelerin olcum/ klasörlerini toplamak, ölçüm verisini paylaşmak ya da başkasının verisini içeri almak. "ölçüm", "kıyas", "hangi model daha iyi", "olcum klasörlerini topla" gibi isteklerde tetiklenir.
---

# ajan-olcum

Aracın kendisi `olcum` komutu (`~/ajan-olcum/olcum.py`; kurulu değilse repo'yu klonla, README.md'ye bak). Standart ve sütunlar: `STANDART.md`. Veri merkezi: `$OLCUM_HOME/data` (varsayılan aracın yanındaki `data/`). Yalnız Python 3 gerekir.

## Kalıp (herkes aynı biçimi kullanır)

Bir projenin paylaşılabilir ölçümü `olcum/` klasörüdür: `olcum.json` (`{"arac":"ajan-olcum","format":1,"proje":...,"sahip":...}`) + `yurutme.csv`, `review.csv`, `arastirma.csv`, `kapi.csv`. GitHub'da toplama bu `olcum/olcum.json` dosyasını arar. `format` uyuşmayan paket atlanır.

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

## 6. Başkasıyla paylaş

```bash
olcum disa-aktar --hedef paket --sahip <adın> [--proje P] [--proje-gizle]
```

Anonim paket üretir (serbest metin atılır, görev adları özetlenir; `--proje-gizle` proje adlarını da). Kullanıcı klasörü zipleyip gönderir. Alıcı: `olcum topla --klasor paket`. Gönderme ve yayınlama kullanıcının kararıdır; paketi kendin gönderme/push etme.

## Dikkat

- Ham veri serbest metinde proje/iş sırrı içerebilir; paylaşım öncesi `disa-aktar` kullan, ham CSV'yi paylaşma.
- Gelen satırlara `sahip` yazılır; kendi satırlarında boştur. Başkasının verisini kendi kararına karıştırırken `--sahip` ile ayır.
- Eksik/şüpheli ölçüm uydurma; bilinmeyeni boş bırak.
