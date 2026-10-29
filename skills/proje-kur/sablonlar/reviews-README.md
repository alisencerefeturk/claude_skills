# Review kayıtları

- Dosya adı: `TASK-###-<claude|codex>-review.md`; ikinci tur için sonuna `-tur2` eklenir.
- Reviewer yalnız kendi dosyasını yazar. Yazarın sohbetini görmez; yalnız görev sözleşmesi, `git diff` ve test çıktısı verilir. Review'dan sonra orkestratör `git status` ile yalnız bu dosyanın değiştiğini doğrular.
- Başlık: incelenen dal, HEAD, diff komutu, tarih, reviewer (aile, model, effort), yürütücü.
- Bölümler:
  - **Bulgular:** P0/P1 kanıtlı (kırılan test, tekrar üretme adımı ya da `dosya:satır` + girdi → yanlış çıktı); P2/P3 iyileştirme.
  - **Bozma kontrolü** (R2/R3): hangi kural bozuldu, hangi test kırıldı.
  - **Koşulan kapılar** ve sonuçları.
  - **Karar:** ACCEPT | REVISE | NEEDS-FACT (karar repo dışındaki bir bilgiye bağlıysa; eksik bilgi tam yazılır).
- Review en fazla iki tur sürer; anlaşmazlık sürerse kullanıcıya karar notuyla gider.
