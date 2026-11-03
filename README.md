# skills

Claude Code skill koleksiyonu. Her skill `skills/<ad>/` altında, giriş dosyası `SKILL.md`.

| Skill | Ne yapar |
|---|---|
| [ajan-olcum](skills/ajan-olcum/SKILL.md) | Ajan/model karşılaştırma ölçümü: kayıt, rapor, projelerden toplama, paylaşım |
| [opus-orchestration](skills/opus-orchestration/README.md) | Claude Pro + ChatGPT Plus için yönetici/işçi dağıtım politikası, ajan preset'leri, kota statusline'ı |
| [team-orchestration](skills/team-orchestration/README.md) | Şirket Claude Team koltuğu için tek hesaplı yönetici/işçi politikası (GPT yok), `team-*` ajan preset'leri |
| [proje-kur](skills/proje-kur/SKILL.md) | Yeni ya da mevcut projeye ajan düzeni kurar (AGENTS, CLAUDE, devir notu, kararlar; hafif / standart / tam profil); oturum sonunda devir notu yazar |

## Kurulum

Her skill kendi kurulumunu yapar: `skills/<ad>/install.sh`. Bir ajana bu repo bağlantısını verip "kur" (ya da "ajan-olcum'u kur") demek yeterli; ajan aşağıdaki "Ajanlara not"a göre kurar. Elle:

```bash
git clone https://github.com/alisencerefeturk/claude_skills.git ~/skills
~/skills/install.sh                       # orkestrasyon dışındaki bütün skill'ler
~/skills/install.sh opus-orchestration    # ya da team-orchestration; ikisi birden kurulmaz
```

| Skill | `install.sh` ne yapar |
|---|---|
| ajan-olcum | Skill'i bağlar, `olcum` komutunu `~/.local/bin`'e kurar, oturum uzama kancasını `settings.json`'a ekler (yedekli) ve son 7 günü tarar. `--kancasiz` ile kanca atlanır |
| proje-kur | Skill'i bağlar. Repo sahibi değilsen `~/.claude/proje-kur-varsayilanlar.md` açar (kendi commit kimliğin; sahibinin kimliği ve sunucusu kullanılmaz) |
| opus-orchestration | Skill'i, 5 işçi preset'ini ve statusline'ı bağlar; `statusLine` tanımlı değilse ekler (kota okuması buna bağlı). team-orchestration kuruluysa durur |
| team-orchestration | Aynısı, `team-*` preset'leriyle. opus-orchestration kuruluysa durur |

Hepsi `CLAUDE_CONFIG_DIR`'e uyar, tekrar çalıştırmak güvenlidir, var olan dosyayı yedekleyip değiştirir. Güncellemek için `git -C ~/skills pull`; yeni dosya eklenen bir güncellemeden sonra o skill'in `install.sh`'ı yeniden çalıştırılır.

## Uzama ölçümü (arkadaşlarla bir haftalık veri)

`ajan-olcum` kurulunca ölçüm kendiliğinden başlar: her tur bitince oturum kaydı arka planda taranır, modele yük binmez. Bir hafta sonra `olcum oturum rapor --gun 7` kendi özetini gösterir. Paylaşmak için `olcum disa-aktar --hedef paket --sahip <adın>`: istem metni, oturum kimliği ve serbest notlar atılır, görev adları özetlenir (`--proje-gizle` proje adlarını da gizler). Klasörü zipleyip gönder; alan `olcum topla --klasor paket` ve `olcum oturum rapor` ile birleştirir. Kancayı kaldırmak: `olcum kanca kaldir`.

## Ajanlara not

Kullanıcı bu repoyu verip "kur" dediyse kullanıcıyı uğraştırmadan şunu yap:

1. `~/skills` yoksa klonla, varsa `git -C ~/skills pull --ff-only`. Erişim hatası alırsan repo private'tır: kullanıcıya sahibinden GitHub erişimi istemesini söyle.
2. Kullanıcı skill adı verdiyse yalnız onları kur. Vermediyse `~/skills/install.sh` (orkestrasyon dışındakiler) çalıştır ve tek soru sor: orkestrasyon kişisel Claude Pro + ChatGPT Plus için `opus-orchestration` mı, şirket Claude Team için `team-orchestration` mı, yoksa hiçbiri mi? Cevaba göre `~/skills/install.sh <ad>`. İkisini birden kurma.
3. Kurulumdan sonra kullanıcıya en çok beş satırla söyle: kurulan skill'ler, `settings.json`'da ne değişti ve yedeğin yolu, PATH uyarısı çıktıysa düzeltme satırı, `opus-orchestration` kurulduysa Codex CLI'ın (`npm i -g @openai/codex && codex login`) kurulu olup olmadığı, skill'lerin yeni oturumda yükleneceği.
4. Kullanıcının verisi bu repoda değil `~/.ajan-olcum/data` altındadır; repoya veri koyma, commit ya da push etme.
