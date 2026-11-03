"""Oturum uzama ölçümü: Claude Code transcript'lerinden tur başına uzama sinyalleri. Yalnız standart kütüphane.

Veri kaynağı ~/.claude/projects/<proje>/<oturum>.jsonl (ve <oturum>/subagents/agent-*.jsonl). Modelden hiçbir şey
istenmez; kayıtlar sonradan okunur. olcum.py `oturum` alt komutu bu modülü çağırır.

Satır = ana oturumun bir turu (kullanıcı istemi, işçi bildirimi ya da alt ajan dönüşüyle başlayan) ya da bir alt ajanın
bütün koşusu. Aynı `istek_no` bir kullanıcı isteğine bağlı bütün turları ve alt ajanları birleştirir.
"""
import fcntl, hashlib, json, os, re, subprocess, sys, time
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from pathlib import Path

KOLON = ["tarih", "proje", "run_id", "saat", "oturum_id", "oturum_kodu", "istek_no", "tur_no", "tetik", "ajan_tipi", "model",
         "effort", "sure_sn", "api_cagri", "arac", "arac_dagilim", "tekrar", "ayni_dosya_max", "hata", "hata_seri",
         "bekleme", "zaman_asimi", "devam", "defter", "uygulama_arac", "ref_okuma", "ajan", "codex", "skill_tur", "skill_oturum",
         "token_giris", "token_cache_okuma", "token_cache_yazma", "token_cikis", "baglam_max", "sikistirma",
         "kesinti", "istem_uzunluk", "istem_ozet", "kaynak", "not"]

# Skill'lerin istediği kayıt işleri: devir/checkpoint/karar dosyaları, kota dosyası, olcum kaydı.
DEFTER = re.compile(r"DEVIR|orchestration-checkpoint|KARARLAR|CYCLE_LOG|STATUS(-gunluk)?\.md|rate-limit-status"
                    r"|\bolcum (run|add|bitir)")
BEKLE_ARAC = {"TaskOutput", "BashOutput", "Monitor", "ScheduleWakeup"}
BEKLE_BASH = re.compile(r"\bsleep\s+\d|\buntil\b|\bpgrep\b|\bps\b.*(codex|claude)")
ASIM_SN = 590  # Bash aracının üst sınırı 600 sn; buna dayanan komut arka plana atılır ya da kesilir
ASIM_METIN = ("backgrounded command", "Command timed out")
SKILL_DIZIN = re.compile(r"Base directory for this skill:\s*\S*/skills/([\w:.-]+)")
KOMUT = re.compile(r"<command-name>/?([\w:.-]+)</command-name>")
ATLA = ('{"type":"api-request', '{"type":"file-history', '{"type":"custom-title', '{"type":"last-prompt',
        '{"type":"agent-name', '{"type":"atis', '{"type":"bridge', '{"type":"mode"', '{"type":"artifact')
TAZE_SN = 900  # bu kadar yeni değişmiş dosyanın son turu henüz bitmemiş olabilir: atlanır


def projeler_dizini():
    return Path(os.environ.get("CLAUDE_CONFIG_DIR", Path.home() / ".claude")) / "projects"


def zaman(s):
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00")).astimezone()
    except Exception:
        return None


def metin(content):
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "\n".join(b.get("text", "") for b in content if isinstance(b, dict) and b.get("type") == "text")
    return ""


_proje_onbellek = {}


def proje_bul(cwd, slug):
    """Worktree'ler ana deponun adını alır (git common dir); git yoksa klasör adı."""
    if cwd in _proje_onbellek:
        return _proje_onbellek[cwd]
    ad = slug(Path(cwd).name) if cwd else "?"
    if cwd and Path(cwd).is_dir():
        try:
            c = subprocess.run(["git", "rev-parse", "--path-format=absolute", "--git-common-dir"], cwd=cwd,
                               capture_output=True, text=True, timeout=5).stdout.strip()
            if c:
                ad = slug(Path(c).parent.name if c.endswith(".git") else Path(c).name)
        except Exception:
            pass
    if "-worktrees-" in ad:  # klasör silinmiş worktree: ".worktrees/task-1" → ana proje
        ad = ad.split("-worktrees-")[0]
    _proje_onbellek[cwd] = ad
    return ad


def girdiler(yol):
    with open(yol, encoding="utf-8", errors="replace") as f:
        for ln in f:
            if ln.startswith(ATLA):
                continue
            try:
                yield json.loads(ln)
            except ValueError:
                continue


class Tur:
    def __init__(self, bas, tetik, istek_no, tur_no, istem="", uuid=""):
        self.bas, self.son, self.uuid = bas, bas, uuid
        self.tetik, self.istek_no, self.tur_no, self.istem = tetik, istek_no, tur_no, istem
        self.kullanim = {}          # requestId → usage (son blok)
        self.cagrilar = []          # (ad, girdi_json)
        self.sonuclar = []          # is_error sırası
        self.okunan = Counter()
        self.skill = set()
        self.model = Counter()
        self.effort = ""
        self.sikistirma = self.kesinti = 0
        self.tool_ids = []
        self.cagri_zamani = {}      # tool_use_id → zaman
        self.zaman_asimi = self.devam = 0
        self.bosta_sn = 0           # alt ajanın yönetici mesajı beklediği süre (aktif süreden düşülür)

    def ekle_asistan(self, o):
        m = o.get("message") or {}
        if o.get("attributionSkill"):
            self.skill.add(o["attributionSkill"])
        ts = zaman(o.get("timestamp", ""))
        rid = o.get("requestId") or m.get("id") or o.get("uuid")
        if m.get("usage"):
            self.kullanim[rid] = m["usage"]
        if m.get("model") and not m["model"].startswith("<"):
            self.model[m["model"]] += 1
        self.effort = o.get("effort") or self.effort
        for b in m.get("content") or []:
            if not isinstance(b, dict) or b.get("type") != "tool_use":
                continue
            ad, gir = b.get("name", "?"), b.get("input") or {}
            self.cagrilar.append((ad, json.dumps(gir, sort_keys=True, ensure_ascii=False)))
            self.tool_ids.append(b.get("id"))
            if ad == "Bash":  # yalnız Bash: diğer araçlarda uzun süre kullanıcı onayı/cevabı beklemektir
                self.cagri_zamani[b.get("id")] = ts
            if ad == "Read" and gir.get("file_path"):
                self.okunan[gir["file_path"]] += 1
            if ad == "Skill" and (gir.get("skill") or gir.get("name")):
                self.skill.add(gir.get("skill") or gir.get("name"))

    def ekle_kullanici(self, o):
        c = (o.get("message") or {}).get("content")
        t = metin(c)
        self.skill.update(SKILL_DIZIN.findall(t))
        self.skill.update(k for k in KOMUT.findall(t))
        if "[Request interrupted by user" in t:
            self.kesinti = 1
        if isinstance(c, list):
            for b in c:
                if isinstance(b, dict) and b.get("type") == "tool_result":
                    self.sonuclar.append(bool(b.get("is_error")))
                    t0, ts = self.cagri_zamani.get(b.get("tool_use_id")), zaman(o.get("timestamp", ""))
                    icerik = b.get("content") if isinstance(b.get("content"), str) else metin(b.get("content"))
                    if t0 and ts and ((ts - t0).total_seconds() >= ASIM_SN or any(x in icerik for x in ASIM_METIN)):
                        self.zaman_asimi += 1

    def satir(self, skill_oturum):
        ad_say = Counter(a for a, _ in self.cagrilar)
        tekrar = sum(n - 1 for n in Counter(self.cagrilar).values() if n > 1)
        seri = enuzun = 0
        for e in self.sonuclar:
            seri = seri + 1 if e else 0
            enuzun = max(enuzun, seri)
        bekleme = sum(1 for a, g in self.cagrilar if a in BEKLE_ARAC or (a == "Bash" and BEKLE_BASH.search(g)))
        uyg = sum(1 for a, _ in self.cagrilar if a.startswith("mcp__ccd_") or a == "ToolSearch")
        defter = sum(1 for a, g in self.cagrilar if DEFTER.search(g))
        ref = sum(1 for a, g in self.cagrilar if a in ("Read", "Bash") and "/skills/" in g and "/reference/" in g)
        u = self.kullanim.values()
        g = sum(x.get("input_tokens") or 0 for x in u)
        cr = sum(x.get("cache_read_input_tokens") or 0 for x in u)
        cw = sum(x.get("cache_creation_input_tokens") or 0 for x in u)
        baglam = max(((x.get("input_tokens") or 0) + (x.get("cache_read_input_tokens") or 0) +
                      (x.get("cache_creation_input_tokens") or 0) for x in u), default=0)
        return {
            "tarih": self.bas.strftime("%Y-%m-%d"), "saat": self.bas.strftime("%H:%M"),
            "istek_no": self.istek_no, "tur_no": self.tur_no, "tetik": self.tetik,
            "model": self.model.most_common(1)[0][0] if self.model else "", "effort": self.effort,
            "sure_sn": int((self.son - self.bas).total_seconds() - self.bosta_sn), "api_cagri": len(self.kullanim),
            "arac": len(self.cagrilar), "arac_dagilim": ";".join(f"{a}={n}" for a, n in ad_say.most_common(6)),
            "tekrar": tekrar, "ayni_dosya_max": max(self.okunan.values(), default=0), "hata": sum(self.sonuclar),
            "hata_seri": enuzun, "bekleme": bekleme, "zaman_asimi": self.zaman_asimi, "devam": self.devam, "defter": defter, "uygulama_arac": uyg, "ref_okuma": ref,
            "ajan": ad_say.get("Agent", 0) + ad_say.get("Task", 0),
            "codex": sum(1 for a, g in self.cagrilar if a == "Bash" and "codex exec" in g),
            "skill_tur": ";".join(sorted(self.skill)), "skill_oturum": ";".join(sorted(skill_oturum)),
            "token_giris": g, "token_cache_okuma": cr, "token_cache_yazma": cw,
            "token_cikis": sum(x.get("output_tokens") or 0 for x in u), "baglam_max": baglam,
            "sikistirma": self.sikistirma, "kesinti": self.kesinti, "istem_uzunluk": len(self.istem),
            "istem_ozet": " ".join(self.istem.split())[:80],
        }


def oturum_turlari(yol):
    """Ana transcript'i turlara böler. (turlar, cwd, oturum_id, tool_use_id → (istek_no, tur_no))."""
    turlar, cwd, sid, eslem = [], "", "", {}
    cur = None
    sayac = 0
    for o in girdiler(yol):
        typ = o.get("type")
        if typ not in ("user", "assistant", "system", "attachment") or o.get("isSidechain"):
            continue
        cwd = cwd or o.get("cwd", "")
        sid = sid or o.get("sessionId", "")
        ts = zaman(o.get("timestamp", ""))
        tp = o.get("turnPosition")
        bas = False
        if typ == "user" and not o.get("toolUseResult") and not o.get("isCompactSummary"):
            if tp:
                bas = True
            elif not o.get("isMeta") and metin((o.get("message") or {}).get("content")).strip() \
                    and "<command-" not in metin((o.get("message") or {}).get("content"))[:40]:
                bas = True  # eski sürüm: turnPosition yok
        if bas and ts:
            sayac += 1
            istek = (tp or {}).get("promptIndex")
            tetik = o.get("turnOrigin") or "human"
            if istek is None:
                istek = (turlar[-1].istek_no + (tetik == "human")) if turlar else 1
            istem = metin((o.get("message") or {}).get("content")) if tetik == "human" else ""
            cur = Tur(ts, tetik, istek, (tp or {}).get("turnIndex") or sayac, istem, o.get("uuid", ""))
            turlar.append(cur)
        if cur is None:
            continue
        if ts and ts > cur.son:
            cur.son = ts
        if typ == "assistant":
            k = len(cur.tool_ids)
            cur.ekle_asistan(o)
            for tid in cur.tool_ids[k:]:
                eslem[tid] = (cur.istek_no, cur.tur_no)
        elif typ == "user":
            if o.get("isCompactSummary"):
                cur.sikistirma = 1
            cur.ekle_kullanici(o)
        elif typ == "system" and o.get("subtype") == "compact_boundary":
            cur.sikistirma = 1
    return turlar, cwd, sid, eslem


def alt_ajan_satiri(yol):
    meta_p = yol.with_suffix(".meta.json")
    meta = {}
    if meta_p.exists():
        try:
            meta = json.loads(meta_p.read_text(encoding="utf-8"))
        except ValueError:
            pass
    if meta and meta.get("finished") is False:
        return None, meta
    t = None
    for o in girdiler(yol):
        if o.get("type") not in ("user", "assistant", "system"):
            continue
        ts = zaman(o.get("timestamp", ""))
        if not ts:
            continue
        if t is None:
            t = Tur(ts, "alt-ajan", None, None)
        elif o["type"] == "user" and (o.get("origin") or {}).get("kind") == "coordinator":
            t.devam += 1  # yönetici aynı işçiye yeni mesaj gönderdi (yeni tur ya da düzeltme)
            t.bosta_sn += max(0, (ts - t.son).total_seconds())
        t.son = max(t.son, ts)
        if o["type"] == "assistant":
            t.ekle_asistan(o)
        elif o["type"] == "user":
            t.ekle_kullanici(o)
    return t, meta


# ---------- kayıt ----------

def veri_yolu(data):
    return data / "oturum.csv"


def ekle(data, satirlar):
    """Kilitli ekleme: paralel kancalar satır kaybettirmez; run_id'si olan satır tekrar yazılmaz."""
    import csv
    data.mkdir(parents=True, exist_ok=True)
    p = veri_yolu(data)
    with open(data / ".oturum.lock", "w") as kilit:
        fcntl.flock(kilit, fcntl.LOCK_EX)
        var = set()
        yeni_dosya = not p.exists()
        if not yeni_dosya:
            with p.open(newline="", encoding="utf-8") as f:
                var = {r.get("run_id") for r in csv.DictReader(f)}
        yeni = [s for s in satirlar if s["run_id"] not in var]
        if yeni:
            with p.open("a", newline="", encoding="utf-8") as f:
                w = csv.DictWriter(f, fieldnames=KOLON_SAHIPLI, extrasaction="ignore")
                if yeni_dosya:
                    w.writeheader()
                for s in yeni:
                    w.writerow({k: s.get(k, "") for k in KOLON_SAHIPLI})
    return len(yeni)


KOLON_SAHIPLI = KOLON[:2] + ["sahip"] + KOLON[2:]


def tara_dosya(yol, slug, tamam=False, kaynak="geriye-donuk", gun=None):
    yol = Path(yol)
    turlar, cwd, sid, eslem = oturum_turlari(yol)
    if not sid:
        return []
    proje = proje_bul(cwd, slug)
    taze = (time.time() - yol.stat().st_mtime) < TAZE_SN
    if turlar and taze and not tamam:
        turlar = turlar[:-1]  # son tur sürüyor olabilir
    sinir = (datetime.now().astimezone() - timedelta(days=gun)) if gun else None
    out, birikim = [], set()
    kod = hashlib.sha256(sid.encode()).hexdigest()[:10]  # anonim pakette oturum_id atılır; gruplama bununla
    for t in turlar:
        birikim |= t.skill
        if sinir and t.bas < sinir:
            continue
        s = t.satir(birikim)
        s.update(proje=proje, oturum_id=sid, oturum_kodu=kod, run_id=f"t:{t.uuid}" if t.uuid else f"{sid}:{t.tur_no}", kaynak=kaynak)
        out.append(s)
    alt = yol.with_suffix("") / "subagents"
    if alt.is_dir():
        for ap in sorted(alt.glob("agent-*.jsonl")):
            t, meta = alt_ajan_satiri(ap)
            if t is None or (sinir and t.bas < sinir):
                continue
            ist, tur = eslem.get(meta.get("toolUseId"), (None, None))
            t.istek_no, t.tur_no = ist, tur
            s = t.satir(birikim)
            s.update(proje=proje, oturum_id=sid, oturum_kodu=kod, run_id=f"{sid}:a:{ap.stem[6:]}", kaynak=kaynak,
                     ajan_tipi=meta.get("agentType", ""), skill_oturum=";".join(sorted(birikim)))
            out.append(s)
    return out


def tara(data, slug, dosyalar=None, gun=7, tamam=False, kaynak="geriye-donuk", sessiz=False):
    if not dosyalar:
        kok = projeler_dizini()
        sinir = time.time() - gun * 86400 if gun else 0
        dosyalar = [p for p in kok.glob("*/*.jsonl") if p.stat().st_mtime >= sinir]
    toplam = 0
    for p in dosyalar:
        try:
            toplam += ekle(data, tara_dosya(p, slug, tamam=tamam, kaynak=kaynak, gun=gun))
        except Exception as e:  # bir bozuk transcript bütün taramayı durdurmasın
            if not sessiz:
                print(f"  atlandı {p}: {e}", file=sys.stderr)
    if not sessiz:
        print(f"{len(dosyalar)} transcript tarandı, {toplam} yeni satır → {veri_yolu(data)}")
    return toplam


def kanca(olcum_py):
    """Stop kancası: stdin'deki transcript yolunu arka planda tarar, hemen çıkar (oturumu bekletmez)."""
    if os.environ.get("OLCUM_KANCA") == "0":
        return 0
    try:
        girdi = json.load(sys.stdin)
        yol = girdi.get("transcript_path")
        if not yol:
            return 0
        log = Path(os.environ.get("OLCUM_HOME", Path.home() / ".ajan-olcum")) / "kanca.log"
        log.parent.mkdir(parents=True, exist_ok=True)
        with open(log, "a") as lf:
            subprocess.Popen([sys.executable, str(olcum_py), "oturum", "tara", "--dosya", yol, "--tamam",
                              "--kaynak", "canli", "--gun", "0", "--sessiz"],
                             stdin=subprocess.DEVNULL, stdout=lf, stderr=lf, start_new_session=True)
    except Exception:
        pass
    return 0


# ---------- kanca kurulumu ----------

def ayar_yolu():
    d = os.environ.get("CLAUDE_DIR") or os.environ.get("CLAUDE_CONFIG_DIR") or str(Path.home() / ".claude")
    return Path(d) / "settings.json"


def kanca_komutu(olcum_py):
    return f"python3 '{olcum_py}' oturum kanca"


def kanca_kur(olcum_py, kaldir=False):
    p = ayar_yolu()
    ayar = json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}
    hooks = ayar.setdefault("hooks", {})
    stop = hooks.setdefault("Stop", [])
    bizim = lambda h: "oturum kanca" in h.get("command", "") and "olcum" in h.get("command", "")
    var = any(bizim(h) for grup in stop for h in grup.get("hooks", []))
    if kaldir:
        if not var:
            print("kanca zaten yok")
            return
        for grup in stop:
            grup["hooks"] = [h for h in grup.get("hooks", []) if not bizim(h)]
        hooks["Stop"] = [g for g in stop if g.get("hooks")]
        if not hooks["Stop"]:
            del hooks["Stop"]
    else:
        if var:
            print(f"kanca zaten kurulu: {p}")
            return
        stop.append({"hooks": [{"type": "command", "command": kanca_komutu(olcum_py), "timeout": 10}]})
    if p.exists():
        yedek = p.with_name(f"settings.json.olcum-yedek-{datetime.now():%Y%m%d-%H%M%S}")
        yedek.write_text(p.read_text(encoding="utf-8"), encoding="utf-8")
        print(f"yedek: {yedek}")
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(".tmp")
    tmp.write_text(json.dumps(ayar, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    tmp.replace(p)
    print(("kanca kaldırıldı: " if kaldir else "kanca kuruldu (Stop): ") + str(p))
    if not kaldir:
        print("Yeni açılan oturumlarda geçerli. Her tur bitince transcript arka planda taranır; modele yük yok.")


# ---------- rapor ----------

def n(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return 0.0


def yuzdelik(xs, q):
    xs = sorted(x for x in xs if x is not None)
    if not xs:
        return None
    i = min(len(xs) - 1, max(0, round(q * (len(xs) - 1))))
    return xs[i]


def baglam_etiket(skill_oturum):
    s = set(filter(None, (skill_oturum or "").split(";")))
    ork = any(x.endswith("orchestration") for x in s)
    pk = "proje-kur" in s
    return "orkestrasyon+proje-kur" if ork and pk else "orkestrasyon" if ork else "proje-kur" if pk else "skill yok"


ISARET = {  # (ad, koşul): tur başına uzama sinyali
    "tekrar≥3": lambda r: n(r["tekrar"]) >= 3,
    "hata serisi≥3": lambda r: n(r["hata_seri"]) >= 3,
    "aynı dosya≥4 okuma": lambda r: n(r["ayni_dosya_max"]) >= 4,
    "bekleme/yoklama≥3": lambda r: n(r["bekleme"]) >= 3,
    "10 dk sınırına çarpma": lambda r: n(r.get("zaman_asimi")) >= 1,
    "işçiye ek tur (devam)": lambda r: n(r.get("devam")) >= 1,
    "defter payı≥%30": lambda r: n(r["arac"]) >= 10 and n(r["defter"]) / n(r["arac"]) >= 0.3,
    "api çağrısı>60": lambda r: n(r["api_cagri"]) > 60,
    "sıkıştırma": lambda r: n(r["sikistirma"]) > 0,
}


def toplam_token(r):
    return n(r["token_giris"]) + n(r["token_cache_okuma"]) + n(r["token_cache_yazma"]) + n(r["token_cikis"])


def rapor(rows, tablo, fmt, gun=None, gizli=False):
    if gun:
        sinir = (datetime.now() - timedelta(days=gun)).strftime("%Y-%m-%d")
        rows = [r for r in rows if r.get("tarih", "") >= sinir]
    ana = [r for r in rows if r.get("tetik") != "alt-ajan"]
    alt = [r for r in rows if r.get("tetik") == "alt-ajan"]
    out = [f"# Oturum uzama raporu — {datetime.now():%Y-%m-%d}" + (f" (son {gun} gün)" if gun else ""), ""]
    if not ana:
        return "\n".join(out + ["Veri yok. Önce: `olcum oturum tara --gun 7`"])

    # istek = (sahip, oturum, istek_no): kullanıcının bir isteği + ona bağlı bildirim turları + alt ajanlar
    istek = defaultdict(lambda: {"tur": [], "alt": []})
    for r in ana:
        istek[(r.get("sahip", ""), r.get("oturum_kodu") or r["oturum_id"], r["istek_no"])]["tur"].append(r)
    for r in alt:
        k = (r.get("sahip", ""), r.get("oturum_kodu") or r["oturum_id"], r["istek_no"])
        if k in istek:
            istek[k]["alt"].append(r)
    ozet = []
    for k, v in istek.items():
        ts = v["tur"]
        ilk = min(ts, key=lambda r: (r["tarih"], r["saat"]))
        ozet.append({
            "k": k, "tarih": ilk["tarih"], "saat": ilk["saat"], "proje": ilk["proje"],
            "baglam": baglam_etiket(max((r["skill_oturum"] for r in ts), key=len)),
            "tur": len(ts), "bildirim": sum(r["tetik"] != "human" for r in ts),
            "aktif_dk": sum(n(r["sure_sn"]) for r in ts) / 60,
            "api": sum(n(r["api_cagri"]) for r in ts), "arac": sum(n(r["arac"]) for r in ts),
            "defter": sum(n(r["defter"]) for r in ts), "uyg": sum(n(r["uygulama_arac"]) for r in ts),
            "isci": len(v["alt"]) + sum(n(r["codex"]) for r in ts),
            "token": sum(toplam_token(r) for r in ts + v["alt"]) / 1e6,
            "isaret": sorted({a for r in ts for a, f in ISARET.items() if f(r)}),
            "istem": next((r.get("istem_ozet", "") for r in ts if r["tetik"] == "human"), ""),
            "insan": any(r["tetik"] == "human" for r in ts),
        })
    ozet = [o for o in ozet if o["insan"]]

    out += [f"- İstek (kullanıcı istemi): {len(ozet)} · ana tur: {len(ana)} "
            f"(bildirim/dönüş turu: {sum(r['tetik'] != 'human' for r in ana)}) · alt ajan koşusu: {len(alt)}",
            f"- Sahipler: {', '.join(sorted({r.get('sahip') or 'ben' for r in rows}))}", ""]

    def satirlar(grup):
        s = []
        for ad, os_ in sorted(grup.items(), key=lambda kv: -len(kv[1])):
            arac = sum(o["arac"] for o in os_)
            s.append([ad, len(os_),
                      fmt(yuzdelik([o["aktif_dk"] for o in os_], .5), 1), fmt(yuzdelik([o["aktif_dk"] for o in os_], .9), 1),
                      fmt(yuzdelik([o["tur"] for o in os_], .5)), fmt(yuzdelik([o["api"] for o in os_], .5)),
                      fmt(yuzdelik([o["api"] for o in os_], .9)), fmt(yuzdelik([o["arac"] for o in os_], .5)),
                      fmt(yuzdelik([o["token"] for o in os_], .5), 2),
                      f"{100 * sum(o['defter'] for o in os_) / arac:.0f}%" if arac else "—",
                      f"{100 * sum(o['uyg'] for o in os_) / arac:.0f}%" if arac else "—",
                      f"{100 * sum(bool(o['isaret']) for o in os_) / len(os_):.0f}%"])
        return s

    bas = ["bağlam", "istek", "aktif dk p50", "aktif dk p90", "tur p50", "API p50", "API p90", "araç p50",
           "Mtoken p50", "defter payı", "uygulama aracı payı", "işaretli istek"]
    g = defaultdict(list)
    for o in ozet:
        g[o["baglam"]].append(o)
    out += ["## İstek başına maliyet, skill bağlamına göre", "",
            "Bağlam: o isteğe kadar oturumda yüklenen skill'ler. Görevler farklıdır; fark yönlüdür, kanıt değildir.", "",
            tablo(bas, satirlar(g)), ""]
    g = defaultdict(list)
    for o in ozet:
        g[o["proje"] if not gizli else "—"].append(o)
    if not gizli and len(g) > 1:
        out += ["## Projeye göre", "", tablo(["proje"] + bas[1:], satirlar(g)), ""]

    sat = []
    for ad, f in ISARET.items():
        hit = [r for r in ana if f(r)]
        bg = Counter(baglam_etiket(r["skill_oturum"]) for r in hit)
        sat.append([ad, len(hit), f"{100 * len(hit) / len(ana):.0f}%", ", ".join(f"{k}: {v}" for k, v in bg.most_common())])
    out += ["## Uzama işaretleri (ana turlar)", "",
            "tekrar = aynı araç aynı girdiyle tekrar çağrıldı; hata serisi = art arda başarısız araç sonucu; "
            "bekleme = sleep/yoklama; defter = devir/checkpoint/karar/kota/olcum dosyalarına dokunan çağrı.", "",
            tablo(["işaret", "tur", "pay", "bağlam dağılımı"], sat), ""]

    if alt:
        g = defaultdict(list)
        for r in alt:
            g[r.get("ajan_tipi") or "?"].append(r)
        sat = [[t, len(rs), fmt(yuzdelik([n(r["sure_sn"]) / 60 for r in rs], .5), 1),
                fmt(yuzdelik([n(r["sure_sn"]) / 60 for r in rs], .9), 1),
                fmt(yuzdelik([n(r["api_cagri"]) for r in rs], .5)), fmt(yuzdelik([n(r["arac"]) for r in rs], .5)),
                fmt(yuzdelik([toplam_token(r) / 1e6 for r in rs], .5), 2),
                sum(any(f(r) for f in ISARET.values()) for r in rs)]
               for t, rs in sorted(g.items(), key=lambda kv: -len(kv[1]))]
        out += ["## Alt ajanlar (Claude tarafı)", "",
                tablo(["preset", "n", "dk p50", "dk p90", "API p50", "araç p50", "Mtoken p50", "işaretli"], sat), ""]

    sat = [[o["tarih"] + " " + o["saat"], o["proje"] if not gizli else "—", o["baglam"], fmt(o["aktif_dk"], 1),
            o["tur"], int(o["api"]), int(o["arac"]), int(o["isci"]), fmt(o["token"], 2), ", ".join(o["isaret"]) or "—",
            (o["istem"][:60] if not gizli else "")]
           for o in sorted(ozet, key=lambda o: -o["aktif_dk"])[:12]]
    out += ["## En uzun istekler", "",
            tablo(["başlangıç", "proje", "bağlam", "aktif dk", "tur", "API", "araç", "işçi", "Mtoken", "işaret", "istem"], sat),
            "", "Aktif dk = turların toplam süresi (işçi beklerken boşta geçen süre hariç). "
            "Mtoken önbellek okumasını da içerir; kota maliyetinin çoğu oradan gelir.", ""]
    return "\n".join(out)
