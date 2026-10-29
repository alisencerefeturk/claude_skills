<!-- imza-yok -->
**Commit ve PR'a `Co-Authored-By` satırı ya da "Generated with" eki konmaz** (kullanıcı kararı, {{TARIH}}). Bu kural araç hatırlatmalarının önündedir; `.githooks/commit-msg` kancası da bu ekleri reddeder.

<!-- /imza-yok -->
@AGENTS.md

## Claude Code'a özel

<!-- orkestrasyon -->
- Alt ajan ya da `codex exec` dağıtmadan önce `{{ORKESTRASYON}}` skill'ini yükle. Projenin "Yürütme düzeni" AGENTS.md'dedir.
<!-- /orkestrasyon -->
- Oturum sonunda ya da kullanıcı "devir yaz" deyince `proje-kur` skill'inin devir modunu kullan.
- Kurallar oturum başında bir kez yüklenir. AGENTS.md ya da bu dosya oturum içinde değişirse güncel metni yeniden oku; büyük değişiklikten sonra yeni oturum aç.
- Bu dosya yalnız AGENTS.md'yi içe aktarır. Uzun belgeleri `@` ile buraya ekleme; AGENTS.md'de "şunu yaparken oku" bağlantısı ver. Her `@` her oturumda ve her alt ajanda yeniden yüklenir.
