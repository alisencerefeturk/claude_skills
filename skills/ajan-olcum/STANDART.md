# Ajan Ölçüm Standardı (proje bağımsız)

Amaç: modelleri ve effort seviyelerini gerçek işte karşılaştırmak. Zor ve uzun işi yapan ajan ile kolay işi yapan ajan eşit tutulmaz; bütün sayılar işin **zorluk puanına (ZP)** bölünerek karşılaştırılır. Kullanım için [SKILL.md](./SKILL.md).

Veri (`~/.ajan-olcum/data/`): `yurutme.csv` (uygulama), `review.csv`, `arastirma.csv`, `kapi.csv` (test kapısı). Her satırda `proje` sütunu vardır; aynı model farklı projelerde birleştirilip karşılaştırılabilir.

**Otomatik olanlar** (`olcum run`): tarih, proje, run_id, süre, token (giriş/çıkış/önbellek), maliyet, oturum kimliği, tur (Claude), değişen satır ve dosya. **Elle verilenler:** ZP girdileri (dağıtım anında) ve hata sayaçları (review/E2E sonrası, `olcum bitir`).

## 1. Zorluk puanı (ZP) — iş başlamadan verilir

Zorluk, sonuç görülmeden **dağıtım anında** puanlanır ve sonradan değiştirilmez. Sonradan değiştirmek, hata yapan ajanın işini "aslında zordu" diye kayırmak olur. Tahmin yanlış çıktıysa satırın `not` sütununa yazılır.

**ZP = Risk × Boyut × Belirsizlik**

| Etken | Değerler | Nereden gelir |
|---|---|---|
| **Risk** | R0 = 1 · R1 = 1,5 · R2 = 2 · R3 = 3 | Görev sözleşmesindeki risk seviyesi |
| **Boyut** | S = 1 · M = 2 · L = 4 | Sözleşmedeki zaman bütçesi (kural 15). İşin bir parçası dağıtılıyorsa o parçanın boyutu |
| **Belirsizlik** | 1,0 = spec her kararı yazıyor, iş uygulamaktan ibaret · 1,5 = yürütücü birkaç teknik kararı kendisi veriyor · 2,0 = keşif, tasarım veya kök neden araştırması gerekiyor | Orkestratörün spec'e bakarak verdiği değer |

Aralık 1 (R0, S, tam spec) ile 24 (R3, L, keşif) arasındadır. Örnekler: kapsamı net bir R1 küçük düzeltme 1,5; kısmen açık bir R2 orta iş 6; tam spec'li bir R3 büyük iş 12.

Düzeltme turları ayrı satır açmaz; aynı ajanın aynı işteki bütün turları tek satırda toplanır. İş başka ajana devredilirse yeni ajan için yeni satır açılır.

## 2. Hata puanı (HP) — hatanın nerede yakalandığına göre ağırlıklı

Aynı hata ne kadar geç yakalanırsa o kadar pahalıdır, bu yüzden ağırlığı artar. P0 her yerde P1'in iki katıdır.

| Nerede yakalandı | P1 | P0 |
|---|---|---|
| Review'da (sistem çalıştı ama hata yürütücünün) | 1 | 2 |
| Yürütücü "bitti" dedikten sonra orkestratör veya E2E'de | 2 | 4 |
| Kaçan: ürün sahibi demosunda, staging'de ya da commit'ten sonra | 3 | 6 |
| P2 (iyileştirme, test boşluğu) | 0,25 | — |

Yalnız kanıtlı bulgular sayılır (kural: kanıtsız P0/P1 P2'ye düşer). Yürütücünün kendi bulup düzelttiği hata sayılmaz. Spec'teki bir eksikten doğan hata yürütücüye yazılmaz; `not` sütununa "spec eksiği" diye yazılır.

## 3. Karşılaştırma ölçüleri

| Ölçü | Hesap | İyi olan |
|---|---|---|
| **Hata yoğunluğu** | HP ÷ ZP | Düşük |
| **Süre yoğunluğu** | Yürütücünün bütün turlardaki toplam duvar saati (dk) ÷ ZP | Düşük |
| **İlk tur temizliği** | İlk review turunda P0/P1 yok mu (evet/hayır) | Evet |
| **Tur sayısı** | Kabul edilene kadar yürütücüye dönen tur | Düşük |
| **Kapsam ihlali** | Spec dışı dosya değişikliği veya demo senaryosunu zayıflatma sayısı | 0 |

**Ölçülen boyut** (iş bitince): değişen satır (eklenen + silinen; `package-lock.json`, `drizzle/meta/**` ve üretilmiş dosyalar hariç), dosya sayısı ve eklenen test sayısı. Bu ölçü ZP'yi değiştirmez; zorluk tahminlerinin ne kadar isabetli olduğunu görmeye yarar.

### Review yapan ajanlar

| Ölçü | Hesap |
|---|---|
| Doğrulanmış bulgu | Kanıtlı ve kabul edilen P0/P1 sayısı |
| Yanlış alarm | P0/P1 dediği ama kanıtsız çıkan ya da reddedilen bulgu |
| Kaçırılan | Review'dan sonra (orkestratör, E2E, demo) bulunan P0/P1 sayısı |
| **Yakalama oranı** | Doğrulanmış ÷ (doğrulanmış + kaçırılan) |
| Bozma kontrolü | Denenen bozma sayısı / testi gerçekten kıran sayısı (R2/R3) |

### Araştırma yapan ajanlar

Süre, kaynak sayısı, orkestratörün kontrolünde **yanlış çıkan iddia** sayısı ve karara dönüşen öneri sayısı tutulur. Araştırmada zorluk puanı yoktur; karşılaştırma yalnız benzer araştırmalar arasında yapılır.

## 4. Okuma kuralları

- Karşılaştırma yalnız **aynı rol** içinde yapılır: yürütücü yürütücüyle, reviewer reviewer'la.
- Bir model hakkında karar vermek için o rolde **en az 5 satır** gerekir. Daha azı "yönlü" sayılır, kural değiştirmez.
- Süre, Codex hatlarında `codex exec` başlangıç–bitiş zamanından; Claude alt ajanlarında dağıtım–bildirim zamanından alınır. Kota nedeniyle bekleme süresi düşülür ve `not`'a yazılır.
- Geriye dönük eklenen satırlar `kaynak` sütununda `geriye-donuk` diye işaretlenir; bilinmeyen alanlar boş bırakılır, tahmin edilmez.

## 5. Sütunlar

Ortak: `tarih`, `proje`, `run_id`, `kaynak` (canli/geriye-donuk), `not`. Otomatik: `sure_dk`, `token_giris`, `token_cikis`, `token_cache`, `maliyet_usd`, `oturum_id`.

**yurutme.csv:** `gorev`, `hat`, `model`, `effort`, `risk`, `boyut`, `belirsizlik`, `zp`, `tur`, `review_p1`, `review_p0`, `ork_p1`, `ork_p0`, `kacan_p1`, `kacan_p0`, `p2`, `hp`, `hata_yogunlugu`, `sure_yogunlugu`, `ilk_tur_temiz`, `kapsam_ihlali`, `satir`, `dosya`, `test`, `sonuc` (kabul/kismi/basarisiz/devredildi).

**review.csv:** `gorev`, `tur`, `hat`, `model`, `effort`, `yurutucu_model`, `risk`, `zp`, `dogrulanmis_p0p1`, `yanlis_alarm`, `kacirilan`, `yakalama_orani`, `bozma_denenen`, `bozma_kiran`, `karar` (ACCEPT/REVISE).

**arastirma.csv:** `konu`, `hat`, `model`, `effort`, `kaynak_sayisi`, `yanlis_iddia`, `karara_donusen`.

**kapi.csv:** `saat`, `commit`, `kapsadigi_birlestirme`, `gorevler`, `sonuc`, `unit`, `migration`, `e2e_gecen`, `e2e_kalan`, `kacan_hata`, `kacan_aciklama`, `kaynak_bulma_dk`, `main_kirik_dk`, `flaky`.

## 6. Veri kuralları

- Sayaç sütunları (`review_p1` … `p2`) **boşsa "bilinmiyor"**, 0 ise "hata yok" demektir. Hata yok ise 0 yazılır. Rapor boş sayaçlı satırı hata yoğunluğu ortalamasına katmaz.
- Model adı sürümüyle yazılır (`claude-sonnet-5-5`). Rapor takma adları birleştirir; CSV ham kalır.
- **Objektif zorluk sinyali:** `satir`, `dosya`, `tur`, `sure_dk` rapordaki "zorluk tahmini isabeti" tablosuyla ZP'ye karşı okunur. ZP büyürken bunlar büyümüyorsa puanlama (özellikle belirsizlik) gevşektir; sonraki işlerde ayarlanır, eski satırlar değişmez.
- Hata puanı yalnız kanıtlı bulgudan (kanıtsız P0/P1 → P2) ve yürütücünün kendi bulup düzeltmediği hatadan doğar.
