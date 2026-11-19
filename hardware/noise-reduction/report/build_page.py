#!/usr/bin/env python3
"""Assemble uavrt-noise-reduction.html from ../data, figures/noise_budget.json, the template and the script.
Usage (from this folder): python3 build_page.py"""
import csv, json, collections, os
H = os.path.dirname(os.path.abspath(__file__)); D = os.path.join(H, "..", "data")
rd = lambda f: list(csv.DictReader(open(os.path.join(D, f))))
cal = json.load(open(os.path.join(D, "bench_calibration.json")))
summ = {r["flight"]: r for r in rd("flight_summary.csv")}
tl = collections.defaultdict(list)
for r in rd("flight_timelines.csv"): tl[r["flight"]].append(round(float(r["floor_dBm_per_Hz"]), 1))
sp, spf = collections.defaultdict(list), {}
for r in rd("flight_spectra.csv"):
    sp[r["flight"] + "|" + r["segment"]].append(round(float(r["psd_dBm_per_Hz"]), 1))
    spf.setdefault(r["receiver"], {}).setdefault(r["flight"] + r["segment"], []).append(round(float(r["freq_offset_hz"])))
spf = {rx: next(iter(v.values())) for rx, v in spf.items()}
bs, bsf = collections.defaultdict(list), {}
for r in rd("bench_spectra.csv"):
    if r["run"] not in ("Mini_1", "HF"): continue
    f = float(r["freq_offset_hz"])
    if abs(f) > 1600: continue
    g = cal["k_hf"] if r["run"] == "HF" else cal["k_mini"]
    bs[r["run"] + "|" + r["segment"]].append(round(float(r["psd_db_units_per_hz"]) - g, 1))
    if r["segment"] == "load": bsf.setdefault(r["run"], []).append(round(f))
vna, vf = collections.defaultdict(lambda: {"il": [], "rl": []}), []
for r in rd("vna.csv"):
    vna[r["component"]]["il"].append(round(-float(r["s21_db"]), 3)); vna[r["component"]]["rl"].append(round(-float(r["s11_db"]), 2))
    if r["component"] == "thru": vf.append(int(r["freq_hz"]) / 1e6)
data = {"timelines": tl, "spectra": sp, "spectra_f": spf, "summary": summ, "bench": bs, "bench_f": bsf, "vna": vna, "vna_f": vf,
        "cal": {k: v for k, v in cal.items() if k != "runs"}, "budget": json.load(open(os.path.join(H, "figures", "noise_budget.json")))}
s = json.dumps(data, separators=(",", ":")); assert "</script" not in s
page = open(os.path.join(H, "page_template.html"), encoding="utf-8").read().replace("__DATA__", s).replace("__SCRIPT__", open(os.path.join(H, "page_script.js"), encoding="utf-8").read())

def ascii_only(html):
    """Escape every non-ASCII character so the page reads correctly whatever encoding a browser
    assumes (Safari opening a local file defaults to Windows-1252): \\uXXXX inside <script>
    blocks, &#xXXXX; everywhere else."""
    out, i = [], 0
    def js1(c):
        o = ord(c)
        if o < 128: return c
        if o < 0x10000: return "\\u%04x" % o
        o -= 0x10000
        return "\\u%04x\\u%04x" % (0xD800 + (o >> 10), 0xDC00 + (o & 0x3FF))
    def js(t): return "".join(js1(c) for c in t)
    def ent(t): return "".join(c if ord(c) < 128 else "&#x%x;" % ord(c) for c in t)
    while True:
        a = html.find("<script", i)
        if a < 0: out.append(ent(html[i:])); break
        b = html.find(">", a) + 1; c = html.find("</script>", b)
        out.append(ent(html[i:b])); out.append(js(html[b:c])); i = c
    return "".join(out)

frag = ascii_only(page)
assert all(ord(ch) < 128 for ch in frag)
# Fragment for publishing as a claude.ai artifact (the host adds <head> and the charset).
open(os.path.join(H, "uavrt-noise-reduction.artifact.html"), "w", encoding="ascii").write(frag)
# Standalone page for the archive: a full document that any browser opens from disk.
full = ('<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n</head>\n<body>\n'
        + frag + '\n</body>\n</html>\n')
open(os.path.join(H, "uavrt-noise-reduction.html"), "w", encoding="ascii").write(full)
print("wrote", len(full), "bytes (standalone) and", len(frag), "bytes (artifact fragment)")
