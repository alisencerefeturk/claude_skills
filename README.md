# ajan-olcum

Modelleri (Claude, GPT/Codex, hangisi olursa) gerçek işte kıyaslamak için proje bağımsız ölçüm aracı. Tek veri klasörü, birçok proje: `data/*.csv`, her satırda `proje` sütunu. Standart ve puanlama: [STANDART.md](./STANDART.md).

Gereken: Python 3 (yalnız standart kütüphane).

## Kurulum

```bash
ln -s ~/ajan-olcum/bin/olcum /usr/local/bin/olcum   # ya da PATH'e ~/ajan-olcum/bin ekle
```

Proje adı sırayla: `--proje`, `$OLCUM_PROJE`, git deposu klasör adı (küçük harf, tireli). Veri yeri `$OLCUM_HOME/data` (varsayılan bu klasör).

## Günlük kullanım

**1. Ajanı sarıp çalıştır** (süre, token, maliyet, oturum kimliği, değişen satır/dosya otomatik yazılır):

```bash
olcum run --gorev TASK-042 --hat claude --model claude-sonnet-5-5 --effort medium \
  --risk R2 --boyut M --belirsizlik 1.5 --base main -- \
  claude -p "<spec>" --model claude-sonnet-5-5 --effort medium --output-format json
```

Ajanın çıktısı olduğu gibi geçer; sonda `run_id` yazılır. Claude için `--output-format json` şart (token ve maliyet oradan okunur). Codex için `codex exec` çıktısındaki `tokens used` satırı okunur.

**2. Review/E2E sonrası sonuçları işle** (hata puanı ve yoğunluklar hesaplanır):

```bash
olcum bitir <run_id> review_p1=1 ork_p1=0 p2=2 sonuc=kabul tur=2 not="tur 1 P1: ..."
```

**3. Review, araştırma, test kapısı** (elle ya da `run --rol review|arastirma`):

```bash
olcum add review gorev=TASK-042 tur=1 hat=codex model=gpt-6.1-sol dogrulanmis_p0p1=1 yanlis_alarm=0 bozma_denenen=4 bozma_kiran=4 karar=REVISE
olcum add kapi commit=abc123 sonuc=gecti kacan_hata=0
```

**4. Rapor**

```bash
olcum rapor                      # tüm projeler, markdown
olcum rapor --proje myapp        # tek proje
olcum rapor --html rapor.html
```

## Rapor ne gösterir

- Yürütücü: model × effort için hata yoğunluğu, süre yoğunluğu, ilk tur temizliği, ort. tur, maliyet. Satır sayısı 5'in altındaysa "yönlü" (karar için yetersiz).
- Model × risk: bir modelin hangi risk seviyesinde zayıfladığı.
- Reviewer: doğrulanmış/yanlış alarm/kaçırılan, yakalama oranı, bozma kontrolü.
- **Zorluk tahmini isabeti:** ZP aralığı → medyan satır/dosya/süre/tur. ZP büyürken bunlar büyümüyorsa puanlama gevşek demektir (öznel puanı objektif ölçülerle denetler).
- Veri sağlığı: boş süre, boş sonuç, token dolu satır oranı.

## Bilinen sınırlar

- Eski (geriye dönük) satırlarda sayaç sütunları boşsa hata yoğunluğu "bilinmiyor" sayılır, 0 sayılmaz.
- Codex çıktısında giriş/çıkış token ayrımı yok; toplam `not` sütununa `toplam_token=` olarak yazılır.
- Maliyet yalnız Claude `--output-format json` çıktısından gelir.
- Rapordaki model adı birleştirmesi (`ALIAS`) yalnız gösterimdedir; CSV ham kalır.

## Paylaşım ve toplama

Kalıp: projede `olcum/` klasörü = `olcum.json` + dört CSV. Komutlar:

```bash
olcum yayinla --repo . [--temiz]                 # projenin satırlarını olcum/ altına yaz (push sende)
olcum topla --github KULLANICI                    # olcum/olcum.json olan tüm repoları merkeze al
olcum topla --klasor gelen-paket --sahip ali      # başkasından gelen paketi al
olcum disa-aktar --hedef paket --sahip ben [--proje-gizle]   # anonim paket üret
olcum rapor --sahip ali                           # yalnız o kişinin verisi
```

`disa-aktar` serbest metni (`not`, `kacan_aciklama`, `oturum_id`, `test`) atar, görev/konu adlarını özetler. Yinelenen satırlar eklenmez.

## Skill

`skill/ajan-olcum/SKILL.md` herhangi bir Claude Code oturumuna ölçüm kalıbını öğretir. Kurulum: `ln -s ~/ajan-olcum/skill/ajan-olcum ~/.claude/skills/ajan-olcum`. Başkalarına: bu repoyu paylaş, aynı komutu çalıştırsınlar.
