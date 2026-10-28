#!/usr/bin/env python3
"""Ajan ölçüm aracı: otomatik kayıt, hata girişi, rapor. Yalnız standart kütüphane.

Komutlar:
  run     bir ajan komutunu sarar; süre, token, maliyet, değişen satır/dosyayı kendisi yazar
  bitir   run satırına review/hata sonuçlarını işler, hata puanı ve yoğunlukları hesaplar
  add     review / arastirma / kapi için elle satır ekler (alan=değer)
  rapor   model × effort karşılaştırması (markdown, --html ile dosya)
  liste   son kayıtlar

Veri klasörü: $OLCUM_HOME/data (varsayılan: bu dosyanın yanındaki data/).
"""
import argparse, csv, html, json, os, re, statistics, subprocess, sys, time, uuid
from collections import defaultdict
from datetime import datetime
from pathlib import Path

ROOT = Path(os.environ.get("OLCUM_HOME", Path(__file__).resolve().parent))
DATA = ROOT / "data"

COLS = {
    "yurutme": ["tarih", "proje", "run_id", "gorev", "hat", "model", "effort", "risk", "boyut", "belirsizlik", "zp",
                "sure_dk", "tur", "token_giris", "token_cikis", "token_cache", "maliyet_usd", "oturum_id",
                "review_p1", "review_p0", "ork_p1", "ork_p0", "kacan_p1", "kacan_p0", "p2", "hp",
                "hata_yogunlugu", "sure_yogunlugu", "ilk_tur_temiz", "kapsam_ihlali", "satir", "dosya", "test",
                "sonuc", "kaynak", "not"],
    "review": ["tarih", "proje", "run_id", "gorev", "tur", "hat", "model", "effort", "yurutucu_model", "risk", "zp",
               "sure_dk", "token_giris", "token_cikis", "token_cache", "maliyet_usd", "oturum_id",
               "dogrulanmis_p0p1", "yanlis_alarm", "kacirilan", "yakalama_orani", "bozma_denenen", "bozma_kiran",
               "karar", "kaynak", "not"],
    "arastirma": ["tarih", "proje", "run_id", "konu", "hat", "model", "effort", "sure_dk", "token_giris",
                  "token_cikis", "token_cache", "maliyet_usd", "oturum_id", "kaynak_sayisi", "yanlis_iddia",
                  "karara_donusen", "kaynak", "not"],
    "kapi": ["tarih", "proje", "saat", "commit", "kapsadigi_birlestirme", "gorevler", "sonuc", "unit", "migration",
             "e2e_gecen", "e2e_kalan", "kacan_hata", "kacan_aciklama", "kaynak_bulma_dk", "main_kirik_dk", "flaky",
             "kaynak", "not"],
}
RISK = {"R0": 1, "R1": 1.5, "R2": 2, "R3": 3}
BOYUT = {"S": 1, "M": 2, "L": 4}
MIN_N = 5

# Rapor yalnız gösterimde birleştirir; CSV'deki ham yazım değişmez.
ALIAS = [  # (içerir, kanonik ad)
    ("opus", "claude-opus-5-5"), ("sonnet", "claude-sonnet-5-5"), ("haiku", "claude-haiku-5-5"),
    ("gpt-6.1-sol", "gpt-6.1-sol"), ("gpt-6-sol", "gpt-6-sol"), ("sol", "gpt-6.1-sol"),
    ("luna", "gpt-6-luna"), ("astra", "gpt-6-astra"),
]
SAYAC = ("review_p1", "review_p0", "ork_p1", "ork_p0", "kacan_p1", "kacan_p0", "p2")


def kanonik(model):
    m = (model or "").lower()
    for k, v in ALIAS:
        if k in m:
            return v
    return model or "?"


def yogunluk(r):
    """Kayıtlı değer varsa onu; yoksa sayaçlardan. Sayaçların hepsi boşsa bilinmiyor (0 sayılmaz)."""
    v = num(r.get("hata_yogunlugu"))
    if v is not None:
        return v
    z = num(r.get("zp"))
    if not z or not any(str(r.get(k, "")).strip() for k in SAYAC):
        return None
    w = {"review_p1": 1, "review_p0": 2, "ork_p1": 2, "ork_p0": 4, "kacan_p1": 3, "kacan_p0": 6, "p2": 0.25}
    return sum((num(r.get(k), 0) or 0) * x for k, x in w.items()) / z


def sure_yog(r):
    v = num(r.get("sure_yogunlugu"))
    if v is not None:
        return v
    z, s = num(r.get("zp")), num(r.get("sure_dk"))
    return s / z if z and s is not None else None


def path(rol):
    return DATA / f"{rol}.csv"


def read(rol):
    p = path(rol)
    if not p.exists():
        return []
    with p.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def write(rol, rows):
    DATA.mkdir(parents=True, exist_ok=True)
    tmp = path(rol).with_suffix(".tmp")
    with tmp.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLS[rol], extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in COLS[rol]})
    tmp.replace(path(rol))


def num(v, default=None):
    try:
        return float(str(v).replace(",", "."))
    except (ValueError, TypeError):
        return default


def fmt(x, nd=2):
    return "" if x is None else (str(int(x)) if float(x).is_integer() else f"{x:.{nd}f}")


def slug(s):
    import unicodedata
    s = s.replace("ı", "i").replace("İ", "i")
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")


def proje_adi(arg):
    """--proje, sonra $OLCUM_PROJE, sonra git deposu klasör adı (küçük harf, tireli)."""
    if arg:
        return arg
    if os.environ.get("OLCUM_PROJE"):
        return os.environ["OLCUM_PROJE"]
    try:
        top = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True, check=True).stdout.strip()
        return slug(Path(top).name)
    except Exception:
        return slug(Path.cwd().name)


def zp(risk, boyut, bel):
    r, b, u = RISK.get(risk), BOYUT.get(boyut), num(bel)
    return None if None in (r, b, u) else r * b * u


# ---------- çıktıdan token / maliyet ayıklama ----------

def parse_usage(hat, out, err):
    """Claude -p --output-format json ve codex exec çıktısından ölçüleri okur; bulunamazsa boş bırakır."""
    u = {}
    if hat.startswith("claude"):
        obj = None
        for chunk in (out.strip(), out.strip().splitlines()[-1] if out.strip() else ""):
            try:
                obj = json.loads(chunk)
                break
            except Exception:
                continue
        if isinstance(obj, list):
            obj = next((o for o in reversed(obj) if isinstance(o, dict) and o.get("type") == "result"), None)
        if isinstance(obj, dict):
            us = obj.get("usage") or {}
            u["token_giris"] = us.get("input_tokens")
            u["token_cikis"] = us.get("output_tokens")
            u["token_cache"] = (us.get("cache_read_input_tokens") or 0) + (us.get("cache_creation_input_tokens") or 0)
            u["maliyet_usd"] = obj.get("total_cost_usd")
            u["oturum_id"] = obj.get("session_id")
            u["tur"] = obj.get("num_turns")
    else:  # codex
        text = err + "\n" + out
        m = re.search(r"tokens used\s*[:\n]\s*([\d.,]+)", text, re.I)
        if m:
            u["token_giris"] = ""
            u["token_cikis"] = ""
            u["token_cache"] = ""
            u["toplam_token"] = int(re.sub(r"[.,]", "", m.group(1)))
        m = re.search(r"session id:\s*([0-9a-f-]{8,})", text, re.I)
        if m:
            u["oturum_id"] = m.group(1)
    return {k: v for k, v in u.items() if v not in (None, "")}


def git_olcu(base, cwd):
    """base..HEAD ve çalışma ağacı: değişen satır ve dosya (lock/üretilmiş dosyalar hariç)."""
    skip = ("package-lock.json", "drizzle/meta/", "pnpm-lock.yaml", "yarn.lock")
    try:
        out = subprocess.run(["git", "diff", "--numstat", base], capture_output=True, text=True, cwd=cwd, check=True).stdout
    except Exception:
        return {}
    satir = dosya = 0
    for ln in out.splitlines():
        a, d, f = (ln.split("\t") + ["", "", ""])[:3]
        if any(s in f for s in skip) or not a.isdigit() or not d.isdigit():
            continue
        satir += int(a) + int(d)
        dosya += 1
    return {"satir": satir, "dosya": dosya}


# ---------- komutlar ----------

def cmd_run(a):
    rol = a.rol
    run_id = datetime.now().strftime("%y%m%d-%H%M%S-") + uuid.uuid4().hex[:4]
    cmd = a.komut[1:] if a.komut and a.komut[0] == "--" else a.komut
    if not cmd:
        sys.exit("komut yok: olcum run ... -- <komut>")
    t0 = time.time()
    p = subprocess.run(cmd, capture_output=True, text=True, stdin=subprocess.DEVNULL)
    dk = round((time.time() - t0) / 60, 1)
    sys.stdout.write(p.stdout)
    sys.stderr.write(p.stderr)
    row = {"tarih": datetime.now().strftime("%Y-%m-%d"), "proje": proje_adi(a.proje), "run_id": run_id,
           "gorev": a.gorev, "hat": a.hat, "model": a.model, "effort": a.effort, "risk": a.risk, "boyut": a.boyut,
           "belirsizlik": a.belirsizlik, "sure_dk": dk, "kaynak": "canli",
           "zp": fmt(zp(a.risk, a.boyut, a.belirsizlik))}
    row.update(parse_usage(a.hat, p.stdout, p.stderr))
    if a.base:
        row.update(git_olcu(a.base, a.cwd or "."))
    if p.returncode != 0:
        row["not"] = f"komut çıkış kodu {p.returncode}"
    if rol == "yurutme":
        row["tur"] = row.get("tur") or 1
    note = row.pop("toplam_token", None)
    if note:
        row["not"] = (row.get("not", "") + f" toplam_token={note}").strip()
    rows = read(rol)
    rows.append(row)
    write(rol, rows)
    print(f"\n[olcum] kaydedildi: {rol} run_id={run_id} süre={dk} dk", file=sys.stderr)
    print(run_id)
    return p.returncode


def hesapla(r):
    w = {"review_p1": 1, "review_p0": 2, "ork_p1": 2, "ork_p0": 4, "kacan_p1": 3, "kacan_p0": 6, "p2": 0.25}
    hp = sum((num(r.get(k), 0) or 0) * v for k, v in w.items())
    r["hp"] = fmt(hp)
    z = num(r.get("zp"))
    if z:
        r["hata_yogunlugu"] = fmt(hp / z)
        s = num(r.get("sure_dk"))
        if s is not None:
            r["sure_yogunlugu"] = fmt(s / z, 1)
    p01 = sum((num(r.get(k), 0) or 0) for k in ("review_p1", "review_p0"))
    if not r.get("ilk_tur_temiz"):
        r["ilk_tur_temiz"] = "evet" if p01 == 0 else "hayır"


def cmd_bitir(a):
    rol = a.rol
    rows = read(rol)
    hedef = [r for r in rows if r.get("run_id") == a.run_id]
    if not hedef:
        sys.exit(f"run_id bulunamadı: {a.run_id}")
    r = hedef[0]
    for kv in a.alan:
        k, _, v = kv.partition("=")
        if k not in COLS[rol]:
            sys.exit(f"bilinmeyen alan: {k}")
        r[k] = v
    if rol == "yurutme":
        hesapla(r)
    if rol == "review":
        d, k = num(r.get("dogrulanmis_p0p1"), 0), num(r.get("kacirilan"))
        if k is not None and d + k > 0:
            r["yakalama_orani"] = fmt(d / (d + k))
    write(rol, rows)
    print(f"güncellendi: {a.run_id}", {k: r.get(k) for k in ("hp", "hata_yogunlugu", "sure_yogunlugu", "ilk_tur_temiz", "sonuc") if rol == "yurutme"})


def cmd_add(a):
    rol = a.rol
    row = {"tarih": datetime.now().strftime("%Y-%m-%d"), "proje": proje_adi(a.proje), "kaynak": "canli",
           "run_id": datetime.now().strftime("%y%m%d-%H%M%S-") + uuid.uuid4().hex[:4]}
    for kv in a.alan:
        k, _, v = kv.partition("=")
        if k not in COLS[rol]:
            sys.exit(f"bilinmeyen alan: {k}. Geçerli: {', '.join(COLS[rol])}")
        row[k] = v
    if rol == "yurutme":
        row.setdefault("zp", fmt(zp(row.get("risk"), row.get("boyut"), row.get("belirsizlik"))))
        hesapla(row)
    rows = read(rol)
    rows.append(row)
    write(rol, rows)
    print(row["run_id"])


def cmd_liste(a):
    rows = read(a.rol)[-a.n:]
    for r in rows:
        print(" | ".join(str(r.get(k, "")) for k in COLS[a.rol][:12]))


# ---------- rapor ----------

def med(xs):
    xs = [x for x in xs if x is not None]
    return statistics.median(xs) if xs else None


def avg(xs):
    xs = [x for x in xs if x is not None]
    return sum(xs) / len(xs) if xs else None


def tablo(basliklar, satirlar):
    out = ["| " + " | ".join(basliklar) + " |", "|" + "|".join("---" for _ in basliklar) + "|"]
    out += ["| " + " | ".join(str(c) for c in s) + " |" for s in satirlar]
    return "\n".join(out)


def rapor_md(proje=None):
    parts = [f"# Ajan ölçüm raporu — {datetime.now():%Y-%m-%d}", ""]
    flt = (lambda rows: [r for r in rows if r.get("proje") == proje]) if proje else (lambda rows: rows)

    y = flt(read("yurutme"))
    g = defaultdict(list)
    for r in y:
        g[(kanonik(r["model"]), r.get("effort", ""))].append(r)
    sat = []
    for (m, e), rs in sorted(g.items(), key=lambda kv: -len(kv[1])):
        n = len(rs)
        temiz = [r["ilk_tur_temiz"] for r in rs if r.get("ilk_tur_temiz")]
        sat.append([m, e or "—", n, fmt(avg([yogunluk(r) for r in rs])),
                    fmt(avg([sure_yog(r) for r in rs]), 1),
                    f"{100 * sum(t == 'evet' for t in temiz) / len(temiz):.0f}%" if temiz else "—",
                    fmt(avg([num(r.get("tur")) for r in rs]), 1),
                    fmt(sum(num(r.get("maliyet_usd"), 0) or 0 for r in rs)) or "—",
                    "yönlü (n<5)" if n < MIN_N else "yeterli"])
    parts += ["## Yürütücüler (düşük iyi: hata/süre yoğunluğu)", "",
              tablo(["model", "effort", "n", "hata yoğ.", "süre yoğ. (dk/ZP)", "ilk tur temiz", "ort. tur", "maliyet $", "güven"], sat), ""]

    # risk kırılımı (aynı model, farklı risk): modelin hangi işte zayıf olduğu
    gr = defaultdict(list)
    for r in y:
        gr[(kanonik(r["model"]), r.get("risk", ""))].append(r)
    sat = [[m, rk, len(rs), fmt(avg([yogunluk(r) for r in rs])),
            fmt(avg([sure_yog(r) for r in rs]), 1)]
           for (m, rk), rs in sorted(gr.items()) if rk]
    parts += ["## Model × risk", "", tablo(["model", "risk", "n", "hata yoğ.", "süre yoğ."], sat), ""]

    rv = flt(read("review"))
    g = defaultdict(list)
    for r in rv:
        g[(kanonik(r["model"]), r.get("effort", ""))].append(r)
    sat = []
    for (m, e), rs in sorted(g.items(), key=lambda kv: -len(kv[1])):
        n = len(rs)
        dv = sum(num(r.get("dogrulanmis_p0p1"), 0) or 0 for r in rs)
        ya = sum(num(r.get("yanlis_alarm"), 0) or 0 for r in rs)
        ka = sum(num(r.get("kacirilan"), 0) or 0 for r in rs)
        bd = sum(num(r.get("bozma_denenen"), 0) or 0 for r in rs)
        bk = sum(num(r.get("bozma_kiran"), 0) or 0 for r in rs)
        sat.append([m, e or "—", n, int(dv), int(ya), int(ka),
                    f"{100 * dv / (dv + ka):.0f}%" if dv + ka else "—",
                    f"{int(bk)}/{int(bd)}" if bd else "—", "yönlü (n<5)" if n < MIN_N else "yeterli"])
    parts += ["## Reviewer'lar", "",
              tablo(["model", "effort", "n", "doğrulanmış", "yanlış alarm", "kaçırılan", "yakalama", "bozma kıran/denenen", "güven"], sat), ""]

    # zorluk tahmini isabeti: ZP aralığına göre gerçek ölçüler
    kov = defaultdict(list)
    for r in y:
        z = num(r.get("zp"))
        if z:
            kov["≤3" if z <= 3 else "3–8" if z <= 8 else "8–15" if z <= 15 else ">15"].append(r)
    sat = [[k, len(kov[k]), fmt(med([num(r.get("satir")) for r in kov[k]]), 0) or "—",
            fmt(med([num(r.get("dosya")) for r in kov[k]]), 0) or "—",
            fmt(med([num(r.get("sure_dk")) for r in kov[k]]), 0) or "—",
            fmt(avg([num(r.get("tur")) for r in kov[k]]), 1) or "—"]
           for k in ("≤3", "3–8", "8–15", ">15") if k in kov]
    parts += ["## Zorluk tahmini isabeti (ZP aralığı → gerçekleşen)", "",
              "ZP büyüdükçe satır/dosya/süre/tur de büyümüyorsa puanlama gevşektir.", "",
              tablo(["ZP", "n", "medyan satır", "medyan dosya", "medyan dk", "ort. tur"], sat), ""]

    k = flt(read("kapi"))
    if k:
        kh = sum(num(r.get("kacan_hata"), 0) or 0 for r in k)
        parts += ["## Test kapısı", "", f"{len(k)} koşu, toplam kaçan hata {int(kh)}, "
                  f"kırık sonuç {sum(r.get('sonuc') == 'kirik' for r in k)}.", ""]

    eksik = [r for r in y if not r.get("sure_dk")]
    parts += ["## Veri sağlığı", "",
              f"- yürütme satırı: {len(y)}; süresi boş: {len(eksik)}; token/maliyet dolu: "
              f"{sum(bool(r.get('maliyet_usd') or r.get('token_cikis')) for r in y)}",
              f"- sonucu boş (bitir bekliyor): {sum(not r.get('sonuc') for r in y if r.get('kaynak') == 'canli')}"]
    return "\n".join(parts)


def md_to_html(md):
    out, tbl = ["<meta charset=utf-8><style>body{font:14px system-ui;max-width:1000px;margin:2rem auto;padding:0 1rem}"
                "table{border-collapse:collapse;margin:.5rem 0 1.5rem}td,th{border:1px solid #ccc;padding:4px 8px;text-align:left}"
                "th{background:#f3f4f6}</style>"], []
    for ln in md.splitlines():
        if ln.startswith("|"):
            if set(ln.replace("|", "").strip()) <= {"-"}:
                continue
            tbl.append([c.strip() for c in ln.strip("|").split("|")])
            continue
        if tbl:
            out.append("<table>" + "".join(
                "<tr>" + "".join(f"<{'th' if i == 0 else 'td'}>{html.escape(c)}</{'th' if i == 0 else 'td'}>" for c in row) + "</tr>"
                for i, row in enumerate(tbl)) + "</table>")
            tbl = []
        if ln.startswith("# "):
            out.append(f"<h1>{html.escape(ln[2:])}</h1>")
        elif ln.startswith("## "):
            out.append(f"<h2>{html.escape(ln[3:])}</h2>")
        elif ln.strip():
            out.append(f"<p>{html.escape(ln)}</p>")
    if tbl:
        out.append("<table>" + "".join("<tr>" + "".join(f"<td>{html.escape(c)}</td>" for c in row) + "</tr>" for row in tbl) + "</table>")
    return "\n".join(out)


def cmd_rapor(a):
    md = rapor_md(a.proje)
    if a.html:
        Path(a.html).write_text(md_to_html(md), encoding="utf-8")
        print(f"yazıldı: {a.html}")
    else:
        print(md)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest="cmd", required=True)

    r = sp.add_parser("run", help="ajan komutunu sar ve kaydet")
    r.add_argument("--rol", choices=["yurutme", "review", "arastirma"], default="yurutme")
    r.add_argument("--gorev", required=True)
    r.add_argument("--hat", required=True, help="claude / codex / orkestrator")
    r.add_argument("--model", required=True)
    r.add_argument("--effort", default="")
    r.add_argument("--risk", default="")
    r.add_argument("--boyut", default="")
    r.add_argument("--belirsizlik", default="")
    r.add_argument("--proje")
    r.add_argument("--base", help="git ref; verilirse değişen satır/dosya ölçülür")
    r.add_argument("--cwd")
    r.add_argument("komut", nargs=argparse.REMAINDER)
    r.set_defaults(f=cmd_run)

    b = sp.add_parser("bitir", help="run satırına sonuçları işle (alan=değer ...)")
    b.add_argument("run_id")
    b.add_argument("alan", nargs="*")
    b.add_argument("--rol", choices=["yurutme", "review", "arastirma"], default="yurutme")
    b.set_defaults(f=cmd_bitir)

    d = sp.add_parser("add", help="elle satır ekle (alan=değer ...)")
    d.add_argument("rol", choices=list(COLS))
    d.add_argument("alan", nargs="*")
    d.add_argument("--proje")
    d.set_defaults(f=cmd_add)

    l = sp.add_parser("liste")
    l.add_argument("rol", choices=list(COLS))
    l.add_argument("-n", type=int, default=10)
    l.set_defaults(f=cmd_liste)

    p = sp.add_parser("rapor")
    p.add_argument("--proje")
    p.add_argument("--html", help="HTML dosyası yolu")
    p.set_defaults(f=cmd_rapor)

    a = ap.parse_args()
    sys.exit(a.f(a) or 0)


if __name__ == "__main__":
    main()
