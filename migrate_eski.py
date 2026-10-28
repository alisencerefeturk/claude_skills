#!/usr/bin/env python3
"""Tek seferlik: eski proje içi CSV'leri ortak veri klasörüne proje sütunuyla taşır.
Kullanım: migrate_eski.py <eski olcum klasörü> <proje adı>
Mevcut satırlar korunur; aynı (proje, tarih, ilk anahtar alanlar) satırı iki kez eklenmez."""
import csv, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import olcum

src, proje = Path(sys.argv[1]), sys.argv[2]
for rol in olcum.COLS:
    f = src / f"{rol}.csv"
    if not f.exists():
        continue
    with f.open(newline="", encoding="utf-8") as fh:
        eski = list(csv.DictReader(fh))
    mevcut = olcum.read(rol)
    var = {tuple(r.get(k, "") for k in olcum.COLS[rol][:5]) for r in mevcut if r.get("proje") == proje}
    eklenen = 0
    for r in eski:
        r["proje"] = proje
        r.setdefault("run_id", "")
        key = tuple(r.get(k, "") for k in olcum.COLS[rol][:5])
        if key in var:
            continue
        mevcut.append(r)
        eklenen += 1
    olcum.write(rol, mevcut)
    print(f"{rol}: {eklenen} satır eklendi (toplam {len(mevcut)})")
