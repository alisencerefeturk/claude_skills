---
name: proje-kur
description: "Yeni ya da mevcut bir projeye ajan çalışma düzeni kurar ve oturum sonunda devir notu yazar. Kur modu: AGENTS.md (bütün ajanlar için tek kural kaynağı), CLAUDE.md (@AGENTS.md + Claude'a özel satırlar), docs/DEVIR.md ('▶ BURADAN DEVAM ET') + docs/DEVIR-gunluk.md, docs/KARARLAR.md; profile göre (hafif / standart / tam) SPEC, araştırma klasörü, TASK şablonu, review klasörü; commit-msg kancası, git init ve orkestrasyon 'Yürütme düzeni' bölümü. Mevcut projede hiçbir dosyanın üstüne yazmadan eksikleri önerir. Devir modu: 'devir yaz', 'devir teslim', 'oturumu kapat', 'nerede kaldığımızı yaz' denince DEVIR.md'yi günceller. Tetikleyiciler: 'yeni proje', 'proje kur', 'projeyi başlat', 'proje-kur', 'AGENTS.md / CLAUDE.md oluştur', 'bu projeye düzen kur', 'devir yaz'."
---

# proje-kur

Kullanıcının projelerinde kendiliğinden oluşmuş ajan çalışma düzenini (Satın Alma, pano, arc_website, sunucu-bakim, deck-app) tek ve tekrarlanabilir bir kuruluma çevirir.

| Mod | Ne zaman | Bölüm |
|---|---|---|
| **kur** | Boş ya da yeni klasör | [Kur](#kur) |
| **uyarla** | İçinde kod ya da ajan dosyası olan proje | [Uyarla](#uyarla) |
| **devir** | "devir yaz", "devir teslim", "oturumu kapat" | [Devir yaz](#devir-yaz) |

Bu skill'in dosyaları:

- `reference/varsayilanlar.md`: kullanıcıya özgü sabitler (commit kimliği, GitHub, sunucu). Her kur/uyarla işinden önce oku.
- `reference/ilkeler.md`: her kuralın neden var olduğu ve kanıtı. Uyarlamada karar verirken ya da kullanıcı "neden" diye sorunca oku.
- `sablonlar/`: üretilecek dosyaların şablonları.

## Kur

### 1. Bak

- Saati al: `TZ=Europe/Istanbul date '+%Y-%m-%d %H:%M'`. Saat tahmin edilmez.
- `reference/varsayilanlar.md`'yi oku.
- Klasörü incele: `ls -A`, `git status -sb 2>&1`, `ls "${CLAUDE_CONFIG_DIR:-$HOME/.claude}/skills"`. Klasörde AGENTS.md, CLAUDE.md, README, kod ya da `docs/` varsa **uyarla** moduna geç.

### 2. Sor (tek görüşme)

İstekte proje adı ve bir-iki cümlelik amaç yoksa önce bunları düz metinle sor. Kalanları `AskUserQuestion` ile sor. Önerilen seçenek ilk sırada olsun, her seçenek tek düz cümleyle anlatılsın.

**Tur 1**

1. **Profil.** Öneriyi amaçtan çıkar:
   | Profil | Ne için | Dosyalar |
   |---|---|---|
   | hafif | Tek kişilik, kısa ömürlü iş: betik, araç, bakım, deneme | AGENTS, CLAUDE, DEVIR + günlük, KARARLAR, .gitignore |
   | standart | Süren bir uygulama ya da site | + `docs/SPEC.md`, `docs/arastirma/` |
   | tam | Çok modüllü iş; para, yetki ya da kişisel veri; birden çok yürütücü ve review | + `tasks/TASK-TEMPLATE.md`, `reviews/`, görev akışı ve döngü bölümleri |
2. **Orkestrasyon.** Kurulu orkestrasyon skill'i (`opus-orchestration` ya da `team-orchestration`; ikisi aynı Claude klasöründe olmaz) ya da yok.
3. **Commit imzası.** Seçenekler:
   - AI eki yok, kancayla zorlanır (önerilen).
   - Serbest.
   - Zorunlu (ör. ortak depoda asistanın `Co-Authored-By` satırı isteniyorsa).
4. **Yayın.** Yok / kullanıcının VDS'i (`varsayilanlar.md`) / başka bir yer (adresi sor).

**Tur 2** (yalnız gerekenler)

5. **Git ve GitHub.** Seçenekler:
   - Yerel ilk commit + GitHub'da private depo + push.
   - Yalnız yerel ilk commit.
   - Commit atma.

   GitHub'da depo açmak ve push etmek dış sisteme yazmaktır; yalnız bu cevapla yapılır.
6. **Ölçüm.** Yalnız orkestrasyon seçildiyse ve `ajan-olcum` kuruluysa (§1'deki skills listesinde varsa) sorulur: her dağıtım `olcum run --proje <ad>` ile kaydedilsin mi? Önerilen: evet.
7. **Orkestrasyonun kendi soruları.** Seçilen skill'in `reference/project-setup.md` dosyasını oku. İmza ve ölçüm zaten soruldu; kalanları burada sor:
   - opus-orchestration: yürütücü hattı.
   - team-orchestration: koltuk tipi.
   - İkisinde de: risk seviyeleri.

   Hafif profilde risk sorulmaz, varsayılan R0–R3 yazılır.
8. **Sunucu hesabı.** Yalnız yayın VDS ise sorulur: ajan yönetici takma adını mı kullanacak, projeye ayrı hesap mı açılacak (`varsayilanlar.md`)?

### 3. Yaz

Şablon → hedef:

| Şablon (`sablonlar/`) | Hedef | Ne zaman |
|---|---|---|
| `AGENTS.md` | `AGENTS.md` | her zaman |
| `CLAUDE.md` | `CLAUDE.md` | her zaman |
| `DEVIR.md` | `docs/DEVIR.md` | her zaman |
| `DEVIR-gunluk.md` | `docs/DEVIR-gunluk.md` | her zaman |
| `KARARLAR.md` | `docs/KARARLAR.md` | her zaman |
| `gitignore` | `.gitignore` (varsa yalnız eksik satırları ekle) | her zaman |
| `SPEC.md` | `docs/SPEC.md` | standart, tam |
| `arastirma-README.md` | `docs/arastirma/README.md` | standart, tam |
| `TASK-TEMPLATE.md` | `tasks/TASK-TEMPLATE.md` | tam |
| `reviews-README.md` | `reviews/README.md` | tam |
| `commit-msg` | `.githooks/commit-msg` (`chmod +x`) | imza "AI eki yok" ise, her profilde |

**Blok işaretleri.** Şablonlarda işaretler kendi satırlarındadır: `<!-- standart+ -->`, `<!-- tam -->`, `<!-- sunucu -->`, `<!-- orkestrasyon -->`, `<!-- imza-yok -->` ve kapanışları `<!-- /… -->`. `standart+` bloğu standart ve tam profilde geçerlidir.

- Seçimde olan bloğun yalnız işaret satırlarını sil.
- Seçimde olmayan bloğu içeriğiyle birlikte sil.
- Dosyada işaret satırı kalmaz.

**Alanlar.** `{{…}}` alanlarının hepsi doldurulur. Kullanıcının söylemediği bir gerekçe ya da bilgi uydurulmaz; yerine "—" yazılır.

| Alan | Değer (örnek) |
|---|---|
| `{{PROJE_ADI}}` | Kullanıcının verdiği ad ("Stok Takip") |
| `{{AMAC}}` | Bir-iki cümle: ne, kimin için, nerede çalışacak |
| `{{KLASOR_SATIRLARI}}` | Klasör tablosunun satırları; boş projede aşağıdaki tek satır |
| `{{TARIH}}` / `{{SAAT}}` | §1'deki `date` çıktısının iki parçası (`2026-10-29` / `11:41`) |
| `{{HAFTA_SONU}}` | Tarih + 7 gün: `date -j -v+7d '+%Y-%m-%d'` (macOS) ya da `date -d '+7 days' '+%Y-%m-%d'` (Linux) |
| `{{KIM}}` | Model, hesap, makine ("Claude Opus, ana hesap, ofis Mac") |
| `{{PROFIL}}` | hafif / standart / tam |
| `{{COMMIT_KIMLIGI}}` | `varsayilanlar.md` |
| `{{IMZA_KURALI}}` | Aşağıdaki üç metinden biri |
| `{{ORKESTRASYON}}` | Skill adı (`opus-orchestration`) |
| `{{YURUTME_SATIRLARI}}` | Aşağıdaki biçim |
| `{{ADRES}}` | Kod biçiminde adres (`` `stok.sencerefeturk.space` ``) |
| `{{SSH_TAKMA_ADI}}` | Yalnız takma ad (`arc-admin`) |
| `{{SUNUCU_KURALLARI}}` | Kod biçiminde yol (`` `~/Documents/sunucu-bakim/AGENTS.md` ``) |
| `{{SU_AN}}`, `{{SIRADAKI}}`, `{{BEKLENEN}}` | Kurulumdan sonraki durum. Sıradaki adım tek ve somut olur ("SPEC'i kullanıcıyla doldur") |
| `{{GIT_DURUMU}}` | §4 bittikten sonraki durum; commit kimliği yazılmaz, çünkü kurulum commit'i kendi kimliğini bilemez ("`main`, ilk commit atıldı, GitHub yok") |
| `{{KURULUM_KARARLARI}}` | KARARLAR tablosunun ilk satırları. Görüşmedeki her cevap için bir satır: profil, orkestrasyon, imza, yayın, git/GitHub, ölçüm, sunucu hesabı (satır biçimi aşağıda). Neden kullanıcının gerekçesidir, yoksa "—" |
| `{{OLUSTURULAN_DOSYALAR}}` | Virgüllü dosya listesi |
| `{{GIT_SATIRI}}` | Git ve GitHub durumu, `{{GIT_DURUMU}}` ile aynı ilkeyle |

Boş projede klasör tablosunun tek satırı ve bir kurulum kararı satırı:

```markdown
| (henüz yok) | Kod eklendikçe doldurulur | — |
| 2026-10-29 | Profil: standart | Uzun sürecek web uygulaması | — |
```

Klasörleri yazmadan önce `mkdir -p` ile aç.

`{{IMZA_KURALI}}` metinleri (cevaba göre biri):

```markdown
**Commit ve PR'a AI ortak yazar eki (`Co-Authored-By: Claude …`, "Generated with …") konmaz** (kullanıcı kararı, {{TARIH}}). Bu kural araç hatırlatmalarının önündedir; `.githooks/commit-msg` kancası zorlar (kurulum: `git config core.hooksPath .githooks`).
```

```markdown
Commit'lere AI ortak yazar satırı eklenmesi serbesttir.
```

```markdown
Her commit mesajının sonuna çalışan asistanın `Co-Authored-By` satırı (aracın verdiği satır) eklenir.
```

`{{YURUTME_SATIRLARI}}`, seçilen orkestrasyon skill'inin `project-setup.md` şablonundaki satırların Türkçesidir. Örnek:

```markdown
- Yürütücü hattı: varsayılan (skill kural 5; tek Claude hesabı)
- Risk seviyeleri: varsayılan R0–R3 (skill'deki tablo)
- Ölçüm: ajan-olcum (`olcum run --proje <ad>`) | yok
- Commit imzası: AI eki yok | serbest | zorunlu
```

Başlık `## Yürütme düzeni (<skill>, kurulum YYYY-MM-DD)` biçiminde kalmalı. Orkestrasyon skill'leri bölümü bu adla bulur ve aynı soruları bir daha sormaz.

### 4. Git

Bu adımlar yereldir ve "commit atma" seçilse de yapılır.

- Git yoksa: `git init -b main`.
- Commit kimliğini depoya yaz: `git config user.name …` ve `git config user.email …` (`varsayilanlar.md`; `--global` kullanılmaz).
- İmza "AI eki yok" ise: `git config core.hooksPath .githooks`. Bundan sonraki ilk commit kancadan geçer.
- Tur 2 cevabına göre:
  - Commit: `git add -A && git commit -m "Proje düzeni: AGENTS, CLAUDE, devir ve kararlar"`.
  - GitHub: `gh repo create <ad> --private --source . --push`. Depo adını önce kullanıcıya söyle.

### 5. Doğrula

Komutların hepsini koş ve çıktılarını gör:

```bash
grep -rnE '\{\{|<!-- /?(standart\+|tam|sunucu|orkestrasyon|imza-yok) -->' AGENTS.md CLAUDE.md docs tasks reviews 2>/dev/null   # boş çıkmalı
grep -n '^@' CLAUDE.md        # yalnız @AGENTS.md
wc -c AGENTS.md CLAUDE.md     # ikisinin toplamı ~10 KB'ı geçmemeli
```

İmza "AI eki yok" ise kancayı dene:

```bash
f="$(mktemp)"
printf 'deneme\n\nCo-Authored-By: Claude <noreply@anthropic.com>\n' > "$f"; .githooks/commit-msg "$f"; echo "çıkış $?"   # 1 olmalı
printf 'deneme\n' > "$f"; .githooks/commit-msg "$f"; echo "çıkış $?"                                              # 0 olmalı
rm -f "$f"
```

Göreli bağlantıların gösterdiği dosyalar var olmalı:

```bash
for f in AGENTS.md CLAUDE.md docs/*.md; do [ -f "$f" ] || continue; d="$(dirname "$f")"
  grep -oE '\]\([^)#]+' "$f" | sed 's/^](//' | grep -v '^https\?:' | while read -r p; do
    [ -e "$d/$p" ] || echo "kırık bağlantı: $f → $p"; done; done   # boş çıkmalı
```

### 6. Bildir

En çok beş satır yaz:

- Profil.
- Oluşturulan dosyalar.
- Git ve GitHub durumu.
- "Kurallar oturum başında yüklenir; çalışmaya yeni oturumla başla."
- İlk adım önerisi (standart ve tam profilde: SPEC'i birlikte doldurmak).

## Uyarla

Mevcut projede **hiçbir dosyanın üstüne yazılmaz; hiçbir dosya taşınmaz, silinmez ya da yeniden adlandırılmaz.** Önce plan yapılır, onay alınır, sonra uygulanır.

1. Kur §1'deki bakışa ek olarak şunları oku:
   - AGENTS.md, CLAUDE.md ve bunların içe aktardıkları.
   - README.
   - `docs/` altındaki başlıklar (`grep -n '^#'`).
   - `git log --oneline -10`.
2. Var olan karşılıkları eşle. Aynı işi gören bir dosya varsa yenisi açılmaz; şablondaki yol, eşlenen dosyanın yoluyla değiştirilir.
   | İş | Bilinen karşılıklar | Karşılık varsa |
   |---|---|---|
   | Devir: şu an (güncel durum + sıradaki adım; oturum başında ilk okunan) | `DEVIR.md`, `STATUS.md` "BURADAN DEVAM ET", CYCLE_LOG'daki en yeni "SONRAKİ OTURUM İÇİN", `.orchestration-checkpoint.md` | `docs/DEVIR.md` açılmaz; devir modu o dosyaya yazar |
   | Devir: geçmiş | `DEVIR-gunluk.md`, `STATUS-gunluk.md`, `raporlar/` altındaki tarihli raporlar, döngü arşivi | `docs/DEVIR-gunluk.md` açılmaz; geçmiş oraya yazılır |
   | Kararlar | `KARARLAR*.md`, `OPEN_DECISIONS.md`, `docs/adr/` | `docs/KARARLAR.md` açılmaz |
   | Kapsam | `SPEC.md`, `MVP_SCOPE.md`, README'deki kapsam bölümü | `docs/SPEC.md` açılmaz |
   | Kurallar | `AGENTS.md`, `WORKING_AGREEMENT.md`, `CLAUDE.md` | Aşağıdaki 4. adıma göre bölüm eklenir |

   Yapılacaklar listesi (ör. AGENTS.md'de "Açık işler") tek başına "şu an" karşılığı sayılmaz, çünkü güncel durumu ve sıradaki adımı yazmaz. Eşleme belirsizse planda iki seçeneği göster, kullanıcı seçsin.
3. Başlangıç yükünü ölç: CLAUDE.md ile `@` ile içe aktarılan her dosyanın `wc -c` toplamı. Toplam ~20 KB'ı geçiyorsa hangi içe aktarmanın bağlantıya dönebileceğini öner (`reference/ilkeler.md` §1).
4. Eklenecekleri çıkar. Metinler Kur §3'teki kurallarla (blok işaretleri, alanlar) şablondan üretilir; yollar 2. adımdaki eşlemeye göre değişir.
   - Eşlenmemiş dosyalar (Kur §3 tablosu, seçilen profile göre) yeni dosya olarak açılır.
   - Kurallar dosyasına şablon AGENTS.md'nin, mevcut dosyada konusu hiç geçmeyen bölümleri sona eklenir. Konusu geçen bölüm atlanır.
   - **Oturum başı** ve **Devir** bölümlerinin konusu mevcut dosyada yoksa bu iki bölüm her zaman eklenir: yeni ajanın devir dosyasını bulması bunlara bağlıdır.
   - Mevcut kuralla çelişen bir şablon kuralı eklenmez; çelişki planda kullanıcıya sorulur.
   - Var olan bir dosyanın kendi metnine dokunulmaz.
   - Kur §2 sorularından yalnız cevabı dosyalarda olmayanları sor.
5. Planı sohbette göster:
   - Her dosya için tek satır: yeni / bölüm eklenecek / dokunulmayacak.
   - Eklenecek bölümlerin **tam metni**. Uzunsa geçici bir dosyaya yaz ve yolunu ver.
   - Git yoksa ilk commit'e girecek dosyaların listesi (`.gitignore` yazıldıktan sonraki `git status --short`). `.env`, anahtar ya da yedek gibi görünen dosya varsa ayrıca uyar.
6. Onay gelince uygula:
   - Klasörleri `mkdir -p` ile aç.
   - `.gitignore` commit'ten önce yazılır.
   - Kur §4 Git adımları uygulanır. Commit mesajı eklenenleri söyler (ör. "Ajan düzeni: oturum başı, devir, kararlar").
7. Kur §5 doğrulamasını koş. Yalnız var olan yollar denetlenir; kanca testi yalnız kanca kurulduysa yapılır.
8. KARARLAR'a kurulum kararlarının yanında eşleme kararları da yazılır (ör. "Devir: şu an `docs/STATUS.md`, geçmiş `raporlar/`").

## Devir yaz

Projede `docs/DEVIR.md` yoksa ve AGENTS.md başka bir devir dosyası adlandırıyorsa (`STATUS.md`, CYCLE_LOG …) o dosyanın kendi biçimine uy. Hiçbiri yoksa "uyarla" ile DEVIR.md kurmayı öner.

1. **Topla:**
   - Saat: `TZ=Europe/Istanbul date '+%Y-%m-%d %H:%M'`.
   - Git: `git status -sb`, `git log --oneline -15`, `git worktree list`.
   - Çalışan işçiler: çalışma klasörü bu proje (ya da onun altı) olan `claude -p` / `codex exec` süreçleri:
     ```bash
     for p in $(pgrep -f 'claude -p|codex exec'); do
       lsof -a -d cwd -p "$p" -Fn 2>/dev/null | grep -q "^n$PWD" && ps -o pid=,etime=,command= -p "$p"; done
     ```
   - Bu oturumda yapılanlar, alınan kararlar ve kullanıcının geri bildirimleri.
2. **Günlüğe taşı.** `docs/DEVIR-gunluk.md`'nin en üstüne (açıklama paragrafının altına) tek girdi yaz. Girdiye iki şey girer: bu oturumun ayrıntısı ve eski "▶ BURADAN DEVAM ET"ten artık geçerli olmayıp günlükte henüz bulunmayan bilgi. Günlükte zaten olan bilgi tekrar yazılmaz. Başlık `## YYYY-MM-DD HH:MM — <konu>`. İçerik:
   - Ne yapıldı (dosyalar, commit kimlikleri).
   - Kim yaptı (model, hesap).
   - Kararlar.
   - Doğrulama (koşulan komut ve sonucu).
   - Açık kalanlar.
3. **Şu anı yeniden yaz.** "▶ BURADAN DEVAM ET" en çok ~25 satır olur:
   - Şu an.
   - Git.
   - Tek ve somut sıradaki adım.
   - Çalışan işçiler (kim, model/hesap, spec dosyası, çıktının yeri).
   - Kullanıcıdan beklenen.
   - Dikkat.

   "Son güncelleme" satırını yenile. Eski durum buraya yığılmaz.
4. **Diğer bölümleri güncelle:**
   - "Sıradaki işler": biten iş silinir; 1. madde "Sıradaki adım"la aynı kalır.
   - Onaylanan yeni tercih → "Kullanıcı tercihleri".
   - Yeni karar → KARARLAR tablosu.
   - Cevap bekleyen soru → KARARLAR "Açık sorular".
   - Yaşanan tuzak → AGENTS.md "Bilinen tuzaklar"a tek satır. Bu kural değil olgudur; eklediğini kullanıcıya söyle.
5. **Uydurma.** Doğrulamadığın şeyi "doğrulanmadı" diye yaz. Sır yazma.
6. **Commit.** AGENTS.md'de ayakta duran bir onay varsa (ör. "devir commit + push serbest") ona uy. Yoksa yalnız belge değişikliğini commit etmeyi öner ve push'u sor.
7. **Bildir.** Kullanıcıya en çok üç cümle yaz: nerede kaldık, sıradaki adım, bekleyen karar.

## Sınırlar

- GitHub'da depo açmak, push etmek ve sunucuya yazmak yalnız kullanıcının bu oturumdaki açık cevabıyla yapılır.
- Kullanıcının genel `~/.claude/CLAUDE.md`'sine ve hafıza dosyalarına dokunulmaz. Tek istisna, team-orchestration'ın koltuk tipini oraya yazmayı kendisinin önermesidir.
- Proje kuralı bu skill ile çelişirse proje kuralı geçerlidir; çelişkiyi kullanıcıya söyle.
