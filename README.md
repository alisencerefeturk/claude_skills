# skills

Claude Code skill koleksiyonu. Her skill `skills/<ad>/` altında, giriş dosyası `SKILL.md`.

| Skill | Ne yapar |
|---|---|
| [ajan-olcum](skills/ajan-olcum/SKILL.md) | Ajan/model karşılaştırma ölçümü: kayıt, rapor, projelerden toplama, paylaşım |

## Kurulum

Bir ajana bu repo bağlantısını verip "kur" demek yeterli. Elle:

```bash
git clone <repo-url> ~/skills && ~/skills/install.sh
```

`install.sh` her `skills/*` klasörünü `~/.claude/skills/` altına bağlar. Güncellemek için `git pull`. Yeni skill eklemek için `skills/<ad>/SKILL.md` koymak yeter; `install.sh` yeniden çalıştırılır.

## Ajanlara not

Bu repoyu kurman istendiyse: klonla, `install.sh`'ı çalıştır, çıktıda bağlanan skill'leri kullanıcıya söyle. Kullanıcının verisi bu repoda değil `~/.ajan-olcum/data` altındadır; repoya veri koyma.
