"""Writes fixture_chronology.md from EVL v0.4 §11.1 and §11.2 (verbatim rows) plus
this plan's fixture assignments.  Usage (from reconciliation/): python3 tools/build_chronology.py"""
lines = open("../KenTender_EVL-CHG-001_Bid_Evaluation_v0_4.md").read().splitlines()


def table(heading):
    i = next(n for n, l in enumerate(lines) if l.startswith(heading))
    rows, seen = [], False
    for n in range(i + 1, len(lines)):
        if lines[n].startswith("|"):
            seen = True
            rows.append((n + 1, lines[n]))
        elif seen:
            break
    return rows


ordinary = table("### 11.1 Ordinary scenario")
branches = table("### 11.2 Independent branches")
# One fixture entity per branch (plan D17): the ordinary canonical Tender or a test-year world.
FIXTURE = {
    "Source unavailable; before receipt": ("TND-MOH-2101-E01", "Opening completed; intake forced to fail (simulation switch)"),
    "Final no-bids outcome / existing preparation": ("TND-MOH-2101-E02", "Preparation with appointments; BOP no-bids completion"),
    "Opening incomplete": ("TND-MOH-2101-E03", "Preparation; opening in progress, no completion"),
    "Rule absent / defective": ("TND-MOH-2101-E04", "Rules file without the storage-capacity entry"),
    "Memory 8 GB in original alternative bid": ("TND-MOH-2101-E05", "Bid package with memory 8"),
    "Missing member during discussion": ("TND-MOH-2101-E06", "Reviewing, session active, one member leaves"),
    "Late conflict before delivery": ("TND-MOH-2101-E07", "Reviewing; Peter declares a conflict; Samuel replaces"),
    "Clarification notice failure": ("TND-MOH-2101-E08", "Clarification authorised; notice transport forced to fail"),
    "Late / absent / changed reply": ("TND-MOH-2101-E09", "Clarification sent; reply after deadline, none, or a changed offer (one world each)"),
    "Verification branch": ("TND-MOH-2101-E10", "Comparison complete; verification plan recorded"),
    "Tie / shortfall / no agreement": ("TND-MOH-2101-E11", "Two equal responsive bids (tie); funding below total (shortfall); recorded dissent (no agreement)"),
    "Report delivery failure": ("TND-MOH-2101-E12", "Signing; delivery forced to fail on the last proof"),
    "Stale report / uncertain signature": ("TND-MOH-2101-E13", "Signing; report superseded, or signing outcome Indeterminate"),
    "Return before downstream decision": ("TND-MOH-2101-E14", "Report sent; downstream status No award decision recorded"),
    "Correction after downstream decision": ("TND-MOH-2101-E15", "Report sent; simulation award-decision event recorded"),
    "Opening supplement": ("TND-MOH-2101-E16", "Reviewing, and separately Report sent; BOP completed-record correction"),
    "Suspended / cancelled": ("TND-MOH-2101-E17", "Simulation suspension / cancellation owner events at Preparing, Reviewing, Signing, after delivery"),
    "Deadline overdue / validity expired": ("TND-MOH-2101-E18", "Simulation dated rule (overdue); clock past the validity end (expired)"),
    "Publication replay / intake before appointment": ("TND-MOH-2101-E19", "Publication replayed; opening completes before appointment"),
    "Replacement clarification": ("TND-MOH-2101-E20", "Clarification sent; replacement authorised, original withdrawn"),
    "Generic evidence conclusion": ("TND-MOH-2101-E21", "Reviewing, concern open, full roster in session"),
    "Supplier / auditor / dual-role actor": ("TND-MOH-2101-E22", "Report sent; supplier, auditor and a secretary who is also a member"),
}
out = [
    "# EVL-CHG-001 v0.4: fixture chronology",
    "",
    "| Control | Value |",
    "|---|---|",
    "| Version | 0.4-chronology.1 |",
    "| Date | 30 September 2026 |",
    "| Source | EVL v0.4 §11.1 and §11.2, copied verbatim by `tools/build_chronology.py`; fixture columns are this plan's assignments |",
    "",
    "**Ordinary path.** The canonical `bid_evaluation` stage (plan D18) tells this story on the canonical Tender TND-MOH-2027-002 (the boards draw TND-MOH-2027-033, C21) through the real commands, at these instants, with the site clock set. Its source is the completed canonical opening `BOC-MOH-2027-002` (12 Jun 2027, 11:10:30 EAT) and the Afya bid, once the Bid Submission seed carries the §9.1 facts (C22).",
    "",
    "## Ordinary scenario (EVL v0.4 §11.1)",
    "",
    ordinary[0][1].rstrip(" |") + " | Source line |",
    "|---|---|---|---|---|---|",
]
for n, l in ordinary[2:]:
    out.append(l.rstrip(" |") + f" | EVL v0.4 line {n} |")
out += [
    "",
    "## Independent branches (EVL v0.4 §11.2)",
    "",
    "Each branch is its own fixture entity in a test year ≥ 2100 (plan D17), built from the stated entry point. It never modifies the canonical Tender. Browser specs build their world through the real commands; the reset state is the world's own purge.",
    "",
    branches[0][1].rstrip(" |") + " | Source line | Fixture entity | Entry state built |",
    "|---|---|---|---|---|---|---|",
]
for n, l in branches[2:]:
    key = l.split("|")[1].strip().split(";")[0].strip()
    fx = next((v for k, v in FIXTURE.items() if key.startswith(k) or k.startswith(key)), ("—", "—"))
    out.append(l.rstrip(" |") + f" | EVL v0.4 line {n} | {fx[0]} | {fx[1]} |")
open("fixture_chronology.md", "w").write("\n".join(out) + "\n")
missing = [l for n, l in branches[2:] if "| — |" in out[-1]]
print(len(ordinary) - 2, len(branches) - 2)
