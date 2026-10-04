"""Builds artboard_inventory.md from extract_boards.js output.

Usage: node tools/extract_boards.js > /tmp/boards.json && python3 tools/build_inventory.py /tmp/boards.json
"""
import json
import sys

boards = json.load(open(sys.argv[1]))

COMPONENT = {
    "D01 Work workspace": "EvaluationWorkspace",
    "D02 Committee and declaration": "CommitteeSetup",
    "D03 Evaluation record": "EvaluationRecord",
    "D04 Requirement review": "RequirementReview",
    "D05 Committee discussion": "CommitteeDiscussion",
    "D06 Clarification": "ClarificationDesk",
    "D07 Report and signing": "EvaluationReport",
    "D08 Issues, verification and correction": "EvaluationRecord",
    "Pause and cancellation": "EvaluationRecord",
    "Shared page states": "EvaluationShell",
}
SLICE = {
    "D01 Work workspace": "11.1", "Shared page states": "11.1",
    "D02 Committee and declaration": "11.2",
    "D03 Evaluation record": "11.3", "D04 Requirement review": "11.3",
    "D05 Committee discussion": "11.4", "D06 Clarification": "11.5",
    "D07 Report and signing": "11.6", "D08 Issues, verification and correction": "11.7",
    "Pause and cancellation": "11.8",
}
# Boards whose pictured interaction depends on a provider or owner fact that does not exist on
# this bench; the simulation stand-in is used and the dependency is named (plan D6, D8, D9, D16).
CONDITIONAL = {
    "D07-SIGN": "Personal proof through the TRUST-ADR-001 test double (plan D16, FU-EVL-11).",
    "D07-EXPIRED-SIGN": "Personal proof through the TRUST-ADR-001 test double (plan D16, FU-EVL-11).",
    "D08-DD-SIGN": "Participant proofs through the TRUST-ADR-001 test double (plan D16, FU-EVL-11).",
    "S-UNCONFIRMED": "An Indeterminate proof is forced through the signing-outcome switch (plan D16).",
    "D03-FUNDING": "Funding read over get_funding_lineage; no published Budget evaluation contract (plan D9, FU-EVL-06).",
    "D07-FUNDING": "Funding read over get_funding_lineage; no published Budget evaluation contract (plan D9, FU-EVL-06).",
    "D08-PAUSED": "Suspension is a simulation-only owner event until Tenders can issue one (plan D8, FU-EVL-02).",
    "P-PREP": "Suspension is a simulation-only owner event until Tenders can issue one (plan D8, FU-EVL-02).",
    "P-SIGN": "Suspension is a simulation-only owner event until Tenders can issue one (plan D8, FU-EVL-02).",
    "D08-CANCELLED": "Post-close cancellation is a simulation-only owner event under TPR v0.13 (plan D8, FU-EVL-02).",
    "C-SIGN": "Post-close cancellation is a simulation-only owner event under TPR v0.13 (plan D8, FU-EVL-02).",
    "D08-CORRECTION": "The recorded award decision is a simulation-only owner event; no Award owner exists (plan D8, FU-EVL-15).",
    "D08-CORRECTION-HOP": "The recorded award decision is a simulation-only owner event; no Award owner exists (plan D8, FU-EVL-15).",
    "D07-DECISION-UNKNOWN": "An unavailable downstream status is forced through a simulation switch (plan D8, D16).",
    "D07-DECISION-UNKNOWN-CHAIR": "An unavailable downstream status is forced through a simulation switch (plan D8, D16).",
}
# Boards without their own spec variant ID: the spec prose each one depicts (plan C15).
PROSE = {
    "D01-APPOINT-HOP": "§9.13 D01-APPOINT: \"Charles's separate view has Assign evaluation secretary …\"",
    "D02-INTAKE-FIRST-HOP": "§9.13 D02-INTAKE-FIRST: \"Charles's separate view offers Assign secretary\"",
    "D05-DISAGREE": "§9.6 D05-MEMBER: \"Disagreement dialog: required Your disagreement …\"",
    "D05-ABSENT-CHAIR": "§9.6 D05-ABSENT: \"Chair variant offers End discussion\"",
    "D05-ABSENT-MEMBER": "§9.6 D05-ABSENT: \"Ruth's view offers Join discussion\"",
    "D05-CONCLUSION-Q": "§9.13 D05-CONCLUSION: \"A qualified variant selects Needs review …\"",
    "D05-RECORD-MEMBER": "§9.12 D05-RECORD: \"Grace/member variant has View report only\"",
    "D05-RECORD-AUDITOR": "§9.12 D05-RECORD: \"Auditor variant uses Not involved …\"",
    "D06-LATE-RECEIVED": "§9.7 D06-LATE: \"Receipt variant shows Received late …\"",
    "D06-WITHDRAW-DLG": "§9.11 D06-WITHDRAW: \"dialog title Withdraw this clarification? …\"",
    "D06-FINAL-CLOSED-NR": "§9.11 D06-FINAL-CLOSED: \"The independent no-reply branch preserves Your unsent draft …\"",
    "D07-REVISE-DLG": "§9.11 D07-REVISE: \"dialog reason Correct the service-address page reference\"",
    "D07-OVERDUE-SEC": "§9.11 D07-OVERDUE: \"secretary variant retains Send for signing\"",
    "D07-DECISION-UNKNOWN-CHAIR": "§9.13 D07-DECISION-UNKNOWN: \"Grace's view also offers Send correction notice\"",
    "D07-PREVIEW": "§9.12 report-preview content",
    "D08-VERIFY-NEG": "§9.13 D08-VERIFY-OUTCOME: \"Negative variant …\"",
    "D08-SUPPLEMENT-HOP": "§9.13 D08-SUPPLEMENT-SENT: Charles's task \"Review opening update for TND-MOH-2027-033\"",
    "D08-CORRECTION-HOP": "§9.13 D08-SUPPLEMENT-SENT: \"A simultaneous correction notice creates a separate Review report correction … task\"",
}


def cell(v):
    return str(v).replace("|", "\\|").replace("\n", " ")


rows = []
for b in boards:
    group = b["group"]
    slice_ = "12" if b["size"] == "390x844" else SLICE[group]
    component = "SupplierClarification" if slice_ == "12" else COMPONENT[group]
    status = "Conditional" if b["id"] in CONDITIONAL else "Covered"
    note = CONDITIONAL.get(b["id"], "")
    prose = PROSE.get(b["id"], "")
    rows.append((b, slice_, component, status, note, prose))

counts = {}
for r in rows:
    counts[r[1]] = counts.get(r[1], 0) + 1
cond = sum(1 for r in rows if r[3] == "Conditional")

out = []
out.append("# EVL-CHG-001 v0.4: artboard inventory\n")
out.append("| Control | Value |\n|---|---|")
out.append("| Version | 0.4-inventory.1 |")
out.append("| Date | 30 September 2026 |")
out.append("| Source | `../design/Bid Evaluation Artboards.dc.html`; registry `window.EVL.boards`, built by `../design/evl/evl-kit.js` and `boards-1.js` … `boards-5.js` |")
out.append("| Method | `tools/extract_boards.js` runs the kit and board files in node and prints the sorted registry; `tools/build_inventory.py` writes this file. Actor, instant, state, spec reference, archetype, size and note are copied from the registry. Component, slice and status are this plan's assignments. |")
out.append("")
out.append(f"**Counts:** {len(rows)} registry entries, all drawn boards; no note-only entries. "
           f"{len(rows) - cond} Covered, {cond} Conditional. "
           f"{sum(1 for r in rows if r[0]['dialog'])} draw a dialog. "
           f"{sum(1 for r in rows if r[0]['size'] == '1440x1024')} at 1440×1024, "
           f"{sum(1 for r in rows if r[0]['size'] == '390x844')} at 390×844, "
           f"{sum(1 for r in rows if r[0]['size'] == '1024x768')} at 1024×768.")
out.append("")
out.append("**Slices:** " + ", ".join(f"{k} = {counts[k]}" for k in sorted(counts, key=lambda s: [int(x) for x in s.split('.')])) + f". Total {len(rows)}; each board is in exactly one slice.")
out.append("")
out.append("**Statuses:**")
out.append("- **Covered:** built class-for-class from the board.")
out.append("- **Conditional:** built, but part of the pictured interaction depends on a provider or owner fact that does not exist on this bench; the simulation stand-in is used and the dependency is named.")
out.append("- **Replaced:** none.")
out.append("")
out.append("**Components** are Evaluation-owned Vue roots (plan D13):")
out.append("- `EvaluationWorkspace` is the Desk Page `/app/bid-evaluation`.")
out.append("- `EvaluationShell` holds the shared page states around every record screen.")
out.append("- `CommitteeSetup`, `EvaluationRecord`, `RequirementReview`, `CommitteeDiscussion`, `ClarificationDesk` and `EvaluationReport` are mounted under `/app/tenders/{tender}/evaluation…`.")
out.append("- `SupplierClarification` is mounted in the Bid Submission portal at `/tenders/{ref}/bid/evaluation-clarifications/{request}` (plan D14).")
out.append("")
out.append("**Cancellation after delivery** (EVL v0.4 §9.13 line 546) has no board. Its runtime view is built from the rules and is recorded as Conditional in the fidelity departures file (C15, FU-EVL-16).")
out.append("")
out.append("| Board id | Label | Actor | Pictured instant | State | Spec reference | Archetype | Size | Dialog | Component#variant | Slice | Status | Depicts (boards without a spec ID) | Condition | Registry note |")
out.append("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
for b, slice_, component, status, note, prose in rows:
    out.append("| " + " | ".join(cell(x) for x in [
        b["id"], b["name"], b["actor"], b["at"], b["state"], b["spec"], b["arch"], b["size"],
        "Yes" if b["dialog"] else "", f"{component}#{b['id']}", slice_, status, prose, note, b["note"],
    ]) + " |")
open("artboard_inventory.md", "w").write("\n".join(out) + "\n")
print(len(rows), counts, cond)
