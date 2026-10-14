"""Writes fixture_chronology.md from CM v0.8 §10.1B (verbatim) and the board dump.

Usage: from reconciliation/: python3 tools/build_chronology.py /tmp/cm_boards.json
"""
import collections
import datetime
import json
import re
import sys

SPEC = "../KenTender_CM-CHG-001_Contract_Management_v0_8.md"
lines = open(SPEC).read().splitlines()
boards = json.load(open(sys.argv[1]))["boards"]

s = next(i for i, l in enumerate(lines) if l.startswith("### 10.1B"))
e = next(i for i, l in enumerate(lines) if l.startswith("### 10.2 "))
table = [(i + 1, lines[i]) for i in range(s, e) if lines[i].startswith("|") and not lines[i].startswith("|---") and not lines[i].startswith("| Scenario")]
paras = [(i + 1, lines[i]) for i in range(s, e) if lines[i] and not lines[i].startswith("|") and not lines[i].startswith("#")]
assert len(table) == 15, len(table)

ENTRY = {
    "CM-MOH-2027-001": "Synthetic Award package `CM-DEMO-AWD-01` delivered through the receiver hook → `ReceiveAwardPackage` → the ordinary commands in order (plan Phase 4).",
    "CM-MOH-2027-EXT-001": "`RegisterExistingContract` → `ConfirmOpeningPosition` → `StartContractManagement` (no package, no signature).",
    "CM-MOH-2027-EXTENSION-001": "Package `EXTENSION-TERMS-01` → signed and Active 2 Jul 10:30 → `RequestContractChange` 18 Jul → review → `DecideContractChange` 19 Jul → amendment signatures → `ActivateContractChange`.",
    "CM-MOH-2027-SEC-RETURN-001": "Package with performance security `TEST-G-RETURN-001` verified 3 Jul → signed → delivery and acceptance → `SignFinalContractAcceptance` → `RecordSecurityAction` (Return).",
    "CM-MOH-2027-SEC-VERIFY-001": "Package with security `TEST-G-001` received → `VerifyContractSecurity` or `RejectContractSecurity` (no discharge).",
    "CM-MOH-2027-WAR-OPEN-001": "Completed delivery → warranty claim on `CM-WAR-OPEN-004` 10 Jul 2028 → remedy pending 21 and 28 Jul.",
    "CM-MOH-2027-WAR-001": "Completed and paid delivery → warranty claim on `CM-WAR-004` → `RecordAcceptanceCorrection` return and replacement → `VerifyContractRemedy`; resolved 15 Jul.",
    "CM-MOH-2027-TERM-001": "Eight units accepted 20 Jul and paid 600,000 + 200,000 → `DecideContractTermination` → `RecordTerminationNotice` 10 Aug → `PrepareTerminationSettlement` → `CompleteTerminationSettlement`.",
    "CM-MOH-2027-SVC-001": "Ten laptops plus training service → `PrepareAcceptanceReport` for the service subject (no stock or asset).",
    "CM-MOH-2027-QTY-001": "Active contract → `RequestContractChange` quantity 10 → 11 (and a 12-unit refusal) with synthetic source and funding evidence.",
    "CM-MOH-2027-DELAY-001": "Ten goods accepted 25 Jul after a 20 Jul due date → `PrepareContractAdjustment` → `DecideContractAdjustment`.",
    "CM-MOH-2027-SEC-001": "Verified instruments `TEST-SG` → `RequestSecurityClaim` → `DecideSecurityClaim` → `RecordSecurityClaimOutcome`.",
    "CM-MOH-2027-CLOSE-001": "Closed 28 Jul 2028 → `PrepareContractClosureCorrection` → `ReopenContractCloseout`.",
    "CM-MOH-2027-CLAIM-001": "Early liability recognised by Finance for invoice v1 → corrected claim v2 at 10:00 → native credit before certification.",
}

def parse(at):
    m = re.match(r"^(\d{1,2}) (\w{3}) (\d{4}), (\d{2}):(\d{2}) EAT$", at)
    if not m:
        return None
    return datetime.datetime.strptime(f"{m.group(1)} {m.group(2)} {m.group(3)} {m.group(4)}:{m.group(5)}", "%d %b %Y %H:%M")

out = ["# CM-CHG-001 v0.8: fixture chronology", "", "| Control | Value |", "|---|---|", "| Version | 0.8-chronology.1 |", "| Date | 14 October 2026 |",
       "| Source | CM v0.8 §10.1B (verbatim) and the board dump, built by `tools/build_chronology.py` (tracker CM8-005) |", "",
       "The board literals are fixture data (plan D17). The ordinary ten-laptop story and every isolated identity use a separate synthetic source (`CM-DEMO-AWD-01`, `CM-DEMO-TERMS-01`) and **never overwrite the canonical chain** (Award's TND-MOH-2027-002 package, KES 46,400,000, delivered 2 Jul 2027 09:00 EAT; CM v0.8 §13). Each isolated branch has its own source and operation identities and inherits nothing from another branch.", "",
       "## Scenario table (CM v0.8 §10.1B, verbatim)", "", "| Scenario | Resolved contract | Task families / fact boundary | Boards in the design | Entry point (proposed) | Spec line |", "|---|---|---|---|---|---|"]
byref = collections.defaultdict(list)
for b in boards:
    byref[b["ref"]].append(b["id"])
for n, l in table:
    cells = [c.strip() for c in l.strip().strip("|").split(" | ")]
    ref = cells[1].strip()
    key = re.findall(r"CM-MOH-2027-[A-Z0-9-]+", ref)
    ids = []
    for k in key:
        ids += byref.get(k, [])
    entry = ENTRY.get(key[0], "**Identity not named by the spec.** The boards carry the base reference in their header; the spec says explicit variant identities replace it. Proposed seed identities are new content for the owner (see Findings).") if key else "**Identity not named by the spec** (see Findings)."
    out.append(f"| {cells[0]} | {cells[1]} | {cells[2]} | {', '.join(ids) if ids else '— (see Findings)'} | {entry} | CM v0.8 line {n} |")

out += ["", "## Source chronology paragraphs (CM v0.8 §10.1B, verbatim)", ""]
for n, p in paras:
    out += [f"> **Line {n}.** " + p, ""]

base = [b for b in boards if b["ref"] == "CM-MOH-2027-001" and b["design"] not in ("D26", "D28", "D29")]
timed = [(parse(b["at"]), b) for b in base if parse(b["at"])]
timed.sort(key=lambda t: (t[0], t[1]["order"]))
out += ["## Ordinary path as drawn (boards whose header is CM-MOH-2027-001, sorted by their instant)", "",
        f"{len(timed)} boards carry a parseable instant; boards of the isolated D26, D28 and D29 branches are listed separately below. Display instants are EAT.", "",
        "| Instant | Board | Design | State | Actor |", "|---|---|---|---|---|"]
for t, b in timed:
    out.append(f"| {b['at']} | {b['id']} | {b['design']} | {(b['variant'] or b['name']).replace('|','/')} | {b['who']} |")

un = [b for b in base if not parse(b["at"])]
out += ["", "## Base-reference boards without a parseable instant", "", "| Board | Stated | Reason |", "|---|---|---|"]
for b in un:
    out.append(f"| {b['id']} | {b['at'] or '(empty)'} | The board states no single instant; the instant is read from the task card. |")

iso = [b for b in boards if b["design"] in ("D26", "D28", "D29")]
out += ["", "## Isolated D26, D28 and D29 boards", "", "| Board | Subject | Header reference | Instant |", "|---|---|---|---|"]
for b in iso:
    out.append(f"| {b['id']} | {b['subject']} | {b['ref']} | {b['at'] or '—'} |")

out += ["", "## Findings", "",
        "1. **D26, D28 and D29 have no identity.** CM v0.8 §10.1B names them \"explicitly isolated subject identities\" and the D28 / D29 briefs say \"Explicit variant contract identities replace this normal fixture\", but no identity is given and every board header shows `CM-MOH-2027-001`. The seeds need three identities. **Proposed (new content, for the owner):** `CM-MOH-2027-PART-001` (D28, payments TEST-PE-PART-01/02), `CM-MOH-2027-ADV-001` (D29, ADV-01 / TEST-AG-01) and `CM-MOH-2027-OUTSIDE-001` (D26). Logged as a follow-up.",
        f"2. **Boards of the base contract:** {len(base)} of {len(boards)} boards carry `CM-MOH-2027-001` outside D26, D28 and D29. Boards for every other §10.1B identity are listed in the scenario table.",
        "3. **Dates are 2027 unless a brief says 2028** (CM v0.8 §10.1B). The ordinary branch's final acceptance, completion certificate and closure are 28 Jul 2028; warranty ends 20 Jul 2028 for the first eight units and 27 Jul 2028 for the two replacements.",
        "4. **Test clock.** The canonical Award delivery to Contract Management is at 2 Jul 2027 09:00 EAT on the trusted test clock; every CM seed drives the same clock and never uses the real date."]
open("fixture_chronology.md", "w").write("\n".join(out) + "\n")
print(len(table), len(paras), len(timed), len(un), len(iso))
