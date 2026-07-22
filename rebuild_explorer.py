#!/usr/bin/env python3
"""
Rebuild index.html from fresh Broadcom interop-matrix CSV exports.

USAGE
  python3 rebuild_explorer.py [folder]     # folder defaults to this script's directory

EXPECTED LAYOUT (same as the original exports)
  <folder>/ESX/Interoperability.csv            <folder>/ESX/Upgrade.csv
  <folder>/vCenter/Interoperability.csv        <folder>/vCenter/Upgrade.csv
  <folder>/NSX/Interoperability.csv            <folder>/NSX/Upgrade.csv
  <folder>/Kuberenets Service/...              (VKS)
  <folder>/vSphere Supervisor/...
  <folder>/Workload K8/...                     (TKr)
  <folder>/explorer_template.html              (the app shell — do not edit by hand)

OUTPUT
  <folder>/index.html  (overwritten)

HOW TO GET FRESH CSVs
  Interoperability: https://interopmatrix.broadcom.com/Interoperability
  Upgrade paths:    https://interopmatrix.broadcom.com/Upgrade
  For each of the six components, select the product, export/download the CSV,
  and save it over the existing file with the SAME name and folder. Keep the
  default export format (matrix layout with a 'Product Interoperability Matrix'
  header row); the parser reads any set of product rows/columns.

WHAT UPDATES AUTOMATICALLY vs WHAT DOES NOT
  Automatic: every Compatible/Incompatible/Not Supported cell, the Path finder,
  the 9.x door badges, the Compat checker, the Matrix browser, and the
  done/applies/past-target chips on the Roadmap.
  NOT automatic: the curated Roadmap/Deployment-plan wording (e.g. "vCenter
  8.0U3h is the last patch with both 9.x doors"). If the badges start
  contradicting the words after an update, the analysis needs re-running —
  that is the signal to revisit the plan, not to trust the old text.

No dependencies beyond the Python 3 standard library.
"""
import csv, json, re, sys
from pathlib import Path

ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parent
COMPONENTS = {"ESX": "ESX", "vCenter": "vCenter", "NSX": "NSX",
              "Kuberenets Service": "VKS", "vSphere Supervisor": "Supervisor",
              "Workload K8": "WorkloadK8s"}

def read_matrix(path):
    with open(path, encoding="utf-8-sig") as f:
        rd = list(csv.reader(f))
    hi = next((i for i, r in enumerate(rd)
               if len(r) > 2 and r[0].strip() == "" and any(c.strip() for c in r[1:])), None)
    if hi is None:
        sys.exit(f"ERROR: no matrix header row found in {path} — was this exported from interopmatrix.broadcom.com?")
    cols = [c.strip() for c in rd[hi][1:]]
    rows = []
    for r in rd[hi + 1:]:
        if not r or not r[0].strip():
            continue
        cells = [c.strip() for c in r[1:]] + [""] * len(cols)
        rows.append((r[0].strip(), cells[:len(cols)]))
    return cols, rows

# ---------- 1. parse ----------
interop, upgrade, versions = [], [], {}
for folder, comp in COMPONENTS.items():
    ip, up_ = ROOT / folder / "Interoperability.csv", ROOT / folder / "Upgrade.csv"
    for p in (ip, up_):
        if not p.exists():
            sys.exit(f"ERROR: missing {p}")
    cols, rows = read_matrix(ip)
    versions[comp] = cols
    for other, cells in rows:
        for col, st in zip(cols, cells):
            if st:
                interop.append((comp, col, other, st))
    ucols, urows = read_matrix(up_)
    for frm, cells in urows:
        for to, st in zip(ucols, cells):
            if st:
                upgrade.append((comp, frm, to, st))

# ---------- 2. cross-component pairs ----------
FAMS = [("vCenter", re.compile(r"^VMware vCenter (?!Converter)(?=[v\d8])")),
        ("ESX", re.compile(r"^VMware ESX (?!on Arm)(?=[v\d8])")),
        ("NSX", re.compile(r"^VMware NSX (?=\d)")),
        ("Supervisor", re.compile(r"^VMware vSphere Supervisor (?=v?\d)")),
        ("VKS", re.compile(r"^vSphere Kubernetes Service (?=\d)")),
        ("WorkloadK8s", re.compile(r"^vSphere Kubernetes releases (?=\d)")),
        ("Addons", re.compile(r"^VKS Add-ons (?=v?\d)"))]
def classify(p):
    for f, rx in FAMS:
        if rx.match(p):
            return f
def short(v):
    for pre in ("VMware vCenter ", "VMware ESX ", "VMware NSX ", "VMware vSphere Supervisor ",
                "vSphere Kubernetes Service ", "vSphere Kubernetes releases ", "VKS Add-ons "):
        if v.startswith(pre):
            return v[len(pre):].strip()
    return v.strip()

pairs = {}
for comp, ver, other, st in interop:
    f = classify(other)
    if not f or f == comp:
        continue
    key = frozenset([(comp, short(ver)), (f, short(other))])
    prev = pairs.get(key)
    if prev and prev != st:
        print(f"WARNING conflicting cells for {sorted(key)}: {prev} vs {st} — keeping first")
        continue
    pairs[key] = st

# ---------- 3. catalogs (newest first) ----------
def vkey(v):
    s = re.sub(r"(\d)U(\d)", r"\1.\2.", v)
    return [(1, int(t), "") if t.isdigit() else (0, 0, t.lower())
            for t in re.findall(r"\d+|[A-Za-z]+", s)]
catalog = {}
for comp in list(COMPONENTS.values()):
    vs = list(dict.fromkeys(short(v) for v in versions[comp]))
    for c2, f, t, st in upgrade:
        if c2 == comp:
            for x in (short(f), short(t)):
                if x not in vs:
                    vs.append(x)
    vs.sort(key=vkey, reverse=True)
    catalog[comp] = vs
catalog["Addons"] = sorted({short(o) for _, _, o, _ in interop if classify(o) == "Addons"},
                           key=vkey, reverse=True)

comps = list(COMPONENTS.values()) + ["Addons"]
cidx = {c: i for i, c in enumerate(comps)}
vidx = {c: {v: i for i, v in enumerate(catalog[c])} for c in comps}
STATUSES = ["Compatible", "Incompatible", "Not Supported"]
sidx = {s: i for i, s in enumerate(STATUSES)}

pair_arr = []
for key, st in pairs.items():
    (ca, va), (cb, vb) = sorted(key)
    if st in sidx and va in vidx[ca] and vb in vidx[cb]:
        pair_arr.append([cidx[ca], vidx[ca][va], cidx[cb], vidx[cb][vb], sidx[st]])
edge_arr = [[cidx[c], vidx[c][short(f)], vidx[c][short(t)], sidx[st]]
            for c, f, t, st in upgrade if st in sidx]

data = {"components": comps, "catalog": catalog, "statuses": STATUSES,
        "pairs": pair_arr, "edges": edge_arr,
        "current": {"vCenter": "8.0U3", "ESX": "8.0U3", "NSX": "4.2.2.1",
                    "Supervisor": "v1.28.3+vmware.2-fips.1-vsc0.1.9",
                    "VKS": "3.1.1", "WorkloadK8s": "1.26.13", "Addons": "v2023.9.19"}}

# Export date shown in the page header/footer. Kept in a committed file (not CSV
# mtimes — git does not preserve those) so the page never claims a fresher export
# than it has. Update EXPORT_DATE.txt whenever the CSVs are re-exported.
asof_path = ROOT / "EXPORT_DATE.txt"
if asof_path.exists():
    asof = asof_path.read_text().strip()
    if asof:
        data["asof"] = asof
else:
    print("NOTE: EXPORT_DATE.txt missing — page will show the template's hardcoded export date")

# ---------- 4. merge into template ----------
tpl_path = ROOT / "explorer_template.html"
if not tpl_path.exists():
    sys.exit(f"ERROR: missing {tpl_path} — keep it next to this script")
tpl = tpl_path.read_text()
if "__DATA__" not in tpl:
    sys.exit("ERROR: template has no __DATA__ placeholder")
out = ROOT / "index.html"
# "</" -> "<\/" so no CSV cell can ever close the <script> block (same string in JSON).
payload = json.dumps(data, separators=(",", ":")).replace("</", "<\\/")
out.write_text(tpl.replace("__DATA__", "const DATA=" + payload + ";"))
print(f"OK  {out}")
print(f"    interop cells: {len(interop)}  upgrade cells: {len(upgrade)}  cross-pairs: {len(pair_arr)}")
for c in comps:
    print(f"    {c}: {len(catalog[c])} versions | newest: {catalog[c][0] if catalog[c] else '-'}")
print("REMINDER: cells/badges/paths are now current; the curated roadmap & deployment-plan text is not re-derived — if badges contradict the words, re-run the analysis.")
