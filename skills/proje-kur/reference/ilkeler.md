# İlkeler ve kanıtları

Her kural, kullanıcının projelerinde yaşanmış bir olaydan gelir. Uyarlamada bir kuralı esnetmeden önce buradaki nedene bak; neden geçerli değilse kuralı kullanıcıyla konuş.

1. **Başlangıç yükü küçük tutulur. CLAUDE.md yalnız AGENTS.md'yi içe aktarır.**
   - Kanıt: Satın Alma'da yeni oturumun ilk turu 45–58 bin token'dan 104 bin token'a çıktı. İçe aktarılan 89 KB'ın %63'ü `OPEN_DECISIONS.md` idi (02.10.2026 kural denetimi). Her alt ajan ve işçi oturumu da aynı yükü taşır.
   - Karar dosyası ~40 KB'ı geçerse ikiye bölünür: arşiv (tam metin, bağlantıyla) ve en çok 8 KB'lık özet (yalnız geçerli kararlar). Gerekirse yalnız özet içe aktarılır.
2. **Tek kural kaynağı AGENTS.md'dir.**
   - Codex AGENTS.md'yi, Claude CLAUDE.md'yi okur. Kural iki yerde yazılırsa birbiriyle çelişir.
   - Kanıt: Satın Alma'da yürütme kuralı aynı anda beş yerde çelişti: çalışma sözleşmesindeki tablo, aynı dosyada bir satır, skill ve iki hafıza notu.
   - CLAUDE.md'ye yalnız Claude'a özgü satırlar yazılır.
3. **Devirde tek bir "şu an" bölümü olur.**
   - Kanıt: Satın Alma'nın döngü kaydında 15'ten fazla "SONRAKİ OTURUM İÇİN" bölümü birikti; eskiyen notlar yeni oturuma yanlış "ilk iş" verdi. pano'nun tarihli bölümlü devir notu 200 satıra çıktı.
   - arc_website bu düzeni kullanıyor: STATUS.md'de tek bir "▶ BURADAN DEVAM ET" bölümü var, ayrıntılı geçmiş STATUS-gunluk.md'de.
4. **Kalıcı kural hafızada değil, repoda ve kancada durur.**
   - Kanıt: Satın Alma'da hafıza dizini elle kısaltılınca sabitlenmiş "Co-Authored-By ekleme" notu dizinden düştü; ek geri geldi; denetim gününde son 300 commit'in 179'unda görüldü.
   - Bu yüzden imza kuralı CLAUDE.md'nin en üstünde durur ve `.githooks/commit-msg` kancası onu zorlar.
5. **Commit imzası her projede sorulur.**
   - pano'da serbest, deck-app'te zorunlu (ortak depo), Satın Alma ve arc_website'ta yasak. Tek bir varsayılan her projeye uymaz.
6. **Kurallar oturum başında bir kez yüklenir.** Uzun oturumda diskteki kural değişir ama bağlamdaki eski metin kalır. Kural değişince dosya yeniden okunur; büyük değişiklikten sonra yeni oturum açılır.
7. **Açık soru varsayılmaz; karar sorusu somut örnekle sorulur.**
   - Kanıt: Satın Alma'da 29.09.2026'da "revizyon / kalan miktar" terimleriyle sorulan bir karar sorusuna kullanıcı "anlamadım" dedi.
   - Aynı soru sayılı bir hikâye olarak sorulunca hemen cevaplandı: 100 m sipariş, 60 m teslim, kalan 40 m'nin fiyatı 10'dan 12 USD'ye çıkıyor.
8. **Doğrulama özelliği kırmaya çalışır; "testler yeşil" kabul değildir.**
   - Kanıt: 01.10.2026'da review'dan geçmiş üç iş (PDF okunabilirliği, giriş uyarısı, kilit açma düğmesi) yalnız kullanıcının demosunda yakalandı.
9. **Saat `date` ile alınır; "dün/yarın" yazılmaz.** Devir notu başka bir gün, başka bir makinede okunur; göreli tarih o gün yanlış anlam taşır.
10. **Sunucuda ajan kendi hesabını kullanır ve yalnız kendi projesine dokunur.** VDS'de birden çok proje çalışır (Satın Alma, pano, arc siteleri). Kural pano'dan ve sunucu-bakim'den geldi.
11. **Uyarlamada hiçbir dosyanın üstüne yazılmaz.** Mevcut dosyalar kullanıcının birikmiş kararlarını taşır. Var olan bir karşılığın (STATUS.md, CYCLE_LOG) yanına ikinci bir devir dosyası açılırsa iki kaynak birbiriyle çelişir.
12. **Profil projeye göre seçilir.**
   - sunucu-bakim 40 satırlık bir AGENTS.md ile sorunsuz yürüyor; görev sözleşmesi ve review klasörü orada yalnız yük olurdu.
   - Satın Alma'da (para, yetki, kişisel veri) görev sözleşmesi, R0–R3 ve kırma demosu hataları erken yakaladı.
