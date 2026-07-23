# vks-pather

**A vSphere 8 → 9.1 upgrade and interoperability explorer for environments running
vSphere Kubernetes Service (VKS).**

Planning a vSphere 9.1 upgrade is hard when Kubernetes workloads are involved: every
component — vCenter, ESX, NSX, the vSphere Supervisor, VKS, the workload-cluster
Kubernetes releases (TKrs) and their packages — has its own compatibility rows, upgrade
paths, ceilings and dead ends, spread across many pages of the Broadcom Product
Interoperability Matrix. This tool pulls one exported snapshot of that matrix into a
single interactive page so the whole journey can be reasoned about — and explained to
stakeholders — in one place.

Open **`index.html`** (the full planner, titled *VCF - VKS Update Planner*) or
**`stack-builder.html`** (the standalone *VCF - VKS Stack Builder*) in any browser. No
server, no build step, no dependencies, and no network access: a strict
Content-Security-Policy blocks all external requests, so nothing leaves the page.

## What's inside

- **Overview** — an editable current-state (set your own versions), the recommended
  9.1-ready hold state, the validated 9.1 end state, confirmed 9.x dead ends, and known
  matrix coverage gaps.
- **Stack Builder** — interactive "moving window" sliders: pin versions across the
  stack and every other layer narrows to its compatible window; combinations that
  would leave any layer without options are blocked before they can be selected.
  Also shipped as the standalone `stack-builder.html`.
- **Roadmap** — four sequenced deployment options (full path to 9.1 via 9.0.2, pre-9.1
  handoff, minimal-supported, max-8.x), with done / applies / past-target chips that
  react to the current-state you set.
- **Deployment plan** — a plain-language, per-step plan for the selected option:
  what each step does, its expected application impact, and a numbered reference for
  every claim — references that could not be verified are explicitly flagged. Exports
  to standalone HTML or RTF (opens natively in Google Docs / Word / Pages), generated
  entirely in the browser.
- **Packages** — what ships in each package-repository generation (Tanzu Standard →
  VKS Standard Packages → VKS Add-ons), the dependency deltas, and where the CNI
  actually lives (inside each TKr, not the package repo).
- **Path finder** — shortest supported upgrade path per component, with 9.x✓/✕ badges
  showing whether each hop keeps a compatible onward path to vSphere 9.
- **Compat checker** — pick any version per component and see every known pairwise
  status.
- **Matrix browser** — the raw grids.

The bundled `index.html` was built from a matrix export dated in `EXPORT_DATE.txt`.
The matrix changes as new releases ship — re-export before relying on it (below).

## Getting the data

This repository does not redistribute Broadcom's matrix export files. To build (or
refresh) the page, export the CSVs yourself — about ten minutes of clicking:

1. Visit [interopmatrix.broadcom.com/Interoperability](https://interopmatrix.broadcom.com/Interoperability)
   and [interopmatrix.broadcom.com/Upgrade](https://interopmatrix.broadcom.com/Upgrade).
2. For each product below, select it, export/download the CSV (keep the default matrix
   layout), and save it into the matching folder as `Interoperability.csv` /
   `Upgrade.csv` (create the folders on first use — two files per folder, 12 in total):

   | Product on the site | Folder in this repo |
   |---|---|
   | VMware ESX | `ESX/` |
   | VMware vCenter | `vCenter/` |
   | VMware NSX | `NSX/` |
   | vSphere Kubernetes Service | `Kuberenets Service/` |
   | VMware vSphere Supervisor | `vSphere Supervisor/` |
   | vSphere Kubernetes releases | `Workload K8/` |

   (Folder names — including the `Kuberenets` typo — are load-bearing:
   `rebuild_explorer.py` keys on them.)

3. Put the export date in `EXPORT_DATE.txt` (it is shown in the page header and
   data-source note), then rebuild — Python 3 standard library only:

   ```
   python3 rebuild_explorer.py
   ```

The build prints per-component version counts and warns about any conflicting cells in
the export. **A rebuild refreshes every cell, badge and path automatically — but not
the written analysis.** The roadmap and deployment-plan wording was authored against
the export date in `EXPORT_DATE.txt`; if a newer export makes the badges contradict the
words, re-derive the analysis before relying on it.

## Repo layout

```
index.html                  VCF - VKS Update Planner (prebuilt output — open this)
stack-builder.html          VCF - VKS Stack Builder (standalone moving-window tool)
explorer_template.html      planner shell (HTML/CSS/JS); data is injected at build time
stack_builder_template.html standalone shell; reuses the planner's Stack Builder blocks
rebuild_explorer.py         one-shot build: parses the 12 CSVs → writes both pages
EXPORT_DATE.txt             date of the matrix export the pages were built from
```

## Disclaimer

The compatibility and upgrade-path data ("Compatible / Incompatible / Not Supported")
is reproduced from the official [Broadcom Product Interoperability
Matrix](https://interopmatrix.broadcom.com/) and remains Broadcom's data; it is
included here, attributed and unmodified in meaning, for interoperability-planning and
educational purposes, and will be removed or amended promptly on request from Broadcom.
**All commentary — impact assessments, recommended sequences, hold states, "dead end"
designations and deployment plans — is the author's own analysis and interpretation,
not official Broadcom or VMware guidance.** Matrix data is a point-in-time snapshot;
verify against the current matrix and official documentation, and validate with
Broadcom Support, before making production changes. Provided as-is, without warranty.

This project is not affiliated with, endorsed by, or supported by Broadcom Inc.
VMware, vSphere, vCenter, ESX, NSX, vSphere Kubernetes Service and related marks are
trademarks of Broadcom Inc.

## License

[MIT](LICENSE) — applies to the tool (code, page, build script). The compatibility
data embedded in the built page originates from Broadcom's Product Interoperability
Matrix and is not covered by the MIT license.
