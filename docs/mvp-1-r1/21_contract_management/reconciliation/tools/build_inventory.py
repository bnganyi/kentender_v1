"""Builds artboard_inventory.md from extract_boards.mjs output and the CM v0.8 headings.

Usage: from the repo root, dump the boards, then build from reconciliation/:
  node docs/mvp-1-r1/21_contract_management/reconciliation/tools/extract_boards.mjs > /tmp/cm_boards.json
  cd docs/mvp-1-r1/21_contract_management/reconciliation && python3 tools/build_inventory.py /tmp/cm_boards.json
"""
import collections
import json
import re
import sys

SPEC = "../KenTender_CM-CHG-001_Contract_Management_v0_8.md"
boards = json.load(open(sys.argv[1]))["boards"]
spec = open(SPEC).read().splitlines()

# --- spec section of each design (the "#### Dnn — ..." headings) -------------
section = ""
heading = {}
for n, line in enumerate(spec, 1):
    m = re.match(r"^### (\d+\.\d+[A-Z]?) ", line)
    if m:
        section = m.group(1)
    m = re.match(r"^#### (D[0-9A-Za-z-]+) — ", line)
    if m:
        heading[m.group(1)] = (section, n)
# D-ERR and D-DENIED are rows of the §10.3 shared-pages table.
for n, line in enumerate(spec, 1):
    for code in ("D-ERR", "D-DENIED"):
        if line.startswith(f"| {code} |"):
            heading[code] = ("10.3", n)

# --- slice (plan phase) ------------------------------------------------------
# Plan "Phases": the ordinary thread (4) takes the main board of each task family
# it walks; every other board belongs to the package that owns its variant.
THREAD = {"D01", "D02", "D03", "D23", "D24", "D04", "D05", "D19", "D06", "D07", "D18", "D08",
          "D33", "D09", "D09-F", "D17", "D22", "D11", "D10", "D40"}
PHASE_OF_DESIGN = {
    "D-ERR": 3, "D-DENIED": 3,
    "D01": 5, "D01-S": 5, "D02": 5, "D03": 5, "D12": 5, "D21": 5, "D25": 5, "D26": 5,
    "D23": 6, "D24": 6, "D04": 6, "D05": 6, "D19": 6, "D06": 6, "D07": 6, "D31": 6,
    "D18": 7, "D08": 7, "D08-L": 7, "D33": 7, "D09": 7, "D17": 7, "D28": 7, "D29": 7,
    "D13": 8, "D14": 8, "D15": 8, "D16": 8, "D20": 8, "D27": 8, "D34": 8, "D35": 8, "D36": 8, "D37": 8, "D10": 8, "D40": 8,
    "D11": 9, "D22": 9, "D32": 9, "D38": 9, "D39": 9,
}
SLICE_NAME = {3: "3 Foundations", 4: "4 Ordinary thread", 5: "5 Formation", 6: "6 Delivery and acceptance",
              7: "7 Invoices and Finance", 8: "8 Changes, warranty, security, reports", 9: "9 Close-out"}
# Dialogs belong with the command they commit.
DIALOG_PHASE = {"D23 · Appoint": 4, "D04 · Units": 4, "D05 · Record": 4, "D05 · All": 4}


def kind(b):
    if b["dialog"]:
        return "Dialog"
    return "Main" if b["id"] == b["design"] else "State"


def phase(b):
    if b["id"] in DIALOG_PHASE:
        return DIALOG_PHASE[b["id"]]
    if kind(b) == "Main" and b["id"] in THREAD:
        return 4
    if b["id"] == "D09-F":
        return 4
    return PHASE_OF_DESIGN[b["design"]]


surface = {b["group"] for b in boards}
rows = []
for b in boards:
    sec = heading.get(b["design"]) or heading.get(b["id"])
    spec_ref = f"§{sec[0]} {b['design']}" + ("" if b["id"] == b["design"] else f" ({b['variant']})") if sec else "NOT FOUND"
    actor = " · ".join(x for x in (b["who"], b["at"]) if x)
    rows.append((b, kind(b), phase(b), spec_ref, actor))

kinds = collections.Counter(r[1] for r in rows)
phases = collections.Counter(r[2] for r in rows)
designs = len({b["design"] for b in boards})
missing = [r[0]["id"] for r in rows if r[3] == "NOT FOUND"]
assert not missing, missing
assert len({b["id"] for b in boards}) == len(boards)

out = [
    "# CM-CHG-001 v0.8 — artboard inventory",
    "",
    "| Control | Value |",
    "|---|---|",
    "| Version | 0.8-inventory.1 |",
    "| Date | 14 October 2026 |",
    "| Source | `../design/CM Artboards.dc.html` + `cm-data-1…4.js`, run by `tools/extract_boards.mjs` through `cmKit` (`tests/ui/fidelity/board.js`), then `tools/build_inventory.py` (tracker CM8-001) |",
    "",
    f"**Counts:** {len(boards)} boards in {designs} designs: {kinds['Main']} main, {kinds['State']} state variants, {kinds['Dialog']} dialog boards. The design page states the same total in its own header (`{designs} designs · {len(boards)} artboards`). "
    "**This replaces the earlier count of 122**, which came from a text search that missed boards whose ids contain a dot-separated label (for example `D17 · Posted`) and the dialog boards; it is superseded.",
    "",
    "Every board is in exactly one slice (plan Phases 3–9) and in exactly one §9.0 surface (the design page's own review group). Slice 4 holds the main board of each task family the ordinary thread walks, plus D09-F and four dialogs the thread needs; every other board belongs to the package that owns its variant. A board number is a state of a shared surface, never a destination (plan D15).",
    "",
    "Board literals (`CM-MOH-2027-…` references, dates, serials, amounts) are fixture data. The runtime shows actual generated references and events. **Compare** is `Yes` for every board until a rare-branch board is recorded in `departures/contracts.js` as not compared, with a reason.",
    "",
    "## Counts by slice",
    "",
    "| Slice | Boards |",
    "|---|---|",
]
for p in sorted(phases):
    out.append(f"| {SLICE_NAME[p]} | {phases[p]} |")
out += ["", "## Counts by surface", "", "| Surface (§9.0) | Boards |", "|---|---|"]
for g, c in sorted(collections.Counter(b["group"] for b in boards).items()):
    out.append(f"| {g} | {c} |")
out += ["", "## Boards", "",
        "| # | Board | State | Design | Kind | Surface | Actor / instant | Subject | Case reference | Spec | Slice | Compare |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|"]
for b, k, p, spec_ref, actor in rows:
    out.append("| {n} | {id} | {vl} | {d} | {k} | {g} | {actor} | {subj} | {ref} | {spec} | {slice} | Yes |".format(
        n=b["order"], id=b["id"], vl=(b["variant"] or b["name"]).replace("|", "/"), d=b["design"], k=k, g=b["group"],
        actor=actor.replace("|", "/") or "—", subj=(b["subject"] or "—").replace("|", "/"), ref=b["ref"] or "—", spec=spec_ref, slice=SLICE_NAME[p]))
open("artboard_inventory.md", "w").write("\n".join(out) + "\n")
print(len(boards), dict(kinds), {SLICE_NAME[p]: c for p, c in sorted(phases.items())}, designs)
