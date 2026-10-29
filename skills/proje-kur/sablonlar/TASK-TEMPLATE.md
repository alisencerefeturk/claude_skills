# TASK-### — Başlık

- Durum: ready | in_progress | review | blocked | done
- Risk: R0 | R1 | R2 | R3
- Boyut / zaman bütçesi: S (≤ yarım gün) | M (1–2 gün) | L (3–5 gün)
- Karar türü: iki yönlü | tek yönlü (hangi kararlar)
- Yürütücü: hat + model + effort
- Reviewer: yok (R0/R1'de AI review zorunlu değil) | yürütücünün diğer ailesi (R2/R3)
- Review dosyası:
- Bağlı karar: `docs/KARARLAR.md` satırı ya da araştırma raporu

## Amaç

## Kapsam içi

## Kapsam dışı

## Kabul kriterleri

3–7 madde. Her biri bir testle ya da demo adımıyla doğrulanabilir olmalı.

## Doğrulama demosu

Kod yazılmadan önce orkestratör yazar; yürütücü değiştiremez. Amaç geçmek değil, kırmaktır.

- Mutlu yol:
- Geçersiz girdi:
- Sınır değer:
- Türkçe karakter (İ/ı/ş/ğ):
- Boş/eksik alan:
- Mükerrer kayıt:
- Yetkisiz erişim (oturumsuz, yanlış rol):
- İş kuralı ihlali:
- Reviewer bozma kontrolü (R2/R3): kritik kural geçici olarak bozulur, testin kırıldığı görülür, geri alınır.

## Para, yetki ya da veri dönüşümü işiyse

- Para: ondalık tip (`numeric`), para birimi ayrı alanda; kayan noktalı sayıyla hesap yapılmaz; yuvarlama kuralı yazılı.
- Durum geçişleri: izinli geçişler tek yerde tanımlı; güncelleme koşullu ve atomik (beklenen eski durum şartıyla).
- Demoya şunlar eklenir: "iki kişi aynı anda onaylar", "eski sekmeden işlem".
- Denetim kaydı: kim, ne zaman, gerekçe. Sır ve ham istek gövdesi loglanmaz.

## Değişmesi beklenen dosyalar

## Test komutları

## Güvenlik ve veri notları

## Sonuç

Commit, test çıktısı, bilinen sınırlar.

## Retro (üç satır)

- Ne yeniden yapıldı:
- Hangi varsayım yanlış çıktı:
- Hangi kural ya da karar güncellenecek:
