# skills

Claude Code skill koleksiyonu. Her skill `skills/<ad>/` altında, giriş dosyası `SKILL.md`.

| Skill | Ne yapar |
|---|---|
| [ajan-olcum](skills/ajan-olcum/SKILL.md) | Ajan/model karşılaştırma ölçümü: kayıt, rapor, projelerden toplama, paylaşım |
| [opus-orchestration](skills/opus-orchestration/README.md) | Claude Pro + ChatGPT Plus için yönetici/işçi dağıtım politikası, ajan preset'leri, kota statusline'ı |
| [team-orchestration](skills/team-orchestration/README.md) | Şirket Claude Team koltuğu için tek hesaplı yönetici/işçi politikası (GPT yok), `team-*` ajan preset'leri |
| [proje-kur](skills/proje-kur/SKILL.md) | Yeni ya da mevcut projeye ajan düzeni kurar (AGENTS, CLAUDE, devir notu, kararlar; hafif / standart / tam profil); oturum sonunda devir notu yazar |

## Kurulum

Bir ajana bu repo bağlantısını verip "kur" demek yeterli. Elle:

```bash
git clone <repo-url> ~/skills && ~/skills/install.sh
```

`install.sh` her `skills/*` klasörünü `~/.claude/skills/` altına (`CLAUDE_CONFIG_DIR` varsa oraya) bağlar; kendi `install.sh`'ı olan skill'lerde onu da çalıştırır (ajan preset'leri ve statusline). Ad verilirse yalnız onları kurar:

```bash
~/skills/install.sh team-orchestration ajan-olcum
```

İki orkestrasyon skill'i aynı Claude klasörüne kurulmaz, ikisi de alt ajan dağıtımında yüklenir: kişisel makinede `opus-orchestration`, şirket Team hesabında `team-orchestration`. Güncellemek için `git pull`. Yeni skill eklemek için `skills/<ad>/SKILL.md` koymak yeter; `install.sh` yeniden çalıştırılır.

## Ajanlara not

Bu repoyu kurman istendiyse: klonla, `install.sh`'ı çalıştır, çıktıda bağlanan skill'leri kullanıcıya söyle. Hangi orkestrasyon skill'inin kurulacağını (kişisel Pro + ChatGPT → `opus-orchestration`, şirket Team → `team-orchestration`) bilmiyorsan sor; ikisini birden kurma. Kullanıcının verisi bu repoda değil `~/.ajan-olcum/data` altındadır; repoya veri koyma.
