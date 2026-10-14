"""Writes error_contract.md, next_step_register.md and command_map.md from CM v0.8 and the board dump.

Usage: from the repo root, node .../tools/extract_boards.mjs > /tmp/cm_boards.json; then from reconciliation/:
  python3 tools/build_contracts.py /tmp/cm_boards.json

Everything quoted comes from the spec with its line number. The mapping tables in this file
(CONTROL_RULES, SERVICE_ONLY) are the only authored content; the script fails if a board
control or a §7 command is left unmapped, and if a cited command name is not in §7.
"""
import collections
import json
import re
import sys

SPEC = "../KenTender_CM-CHG-001_Contract_Management_v0_8.md"
lines = open(SPEC).read().splitlines()
boards = json.load(open(sys.argv[1]))["boards"]
DATE = "14 October 2026"


def idx(prefix):
    return next(i for i, l in enumerate(lines) if l.startswith(prefix))


def table_rows(start_prefix, end_prefix):
    s, e = idx(start_prefix), idx(end_prefix)
    return [(i + 1, lines[i]) for i in range(s, e) if lines[i].startswith("|") and not lines[i].startswith("|---")]


# =============================================================================
# error_contract.md
# =============================================================================
err = [r for r in table_rows("## 8. Error contract", "## 9. UI architecture") if r[1].startswith("| CM_")]
assert len(err) == 17, len(err)
out = ["# CM-CHG-001 v0.8: error contract", "", "| Control | Value |", "|---|---|", "| Version | 0.8-errors.1 |", f"| Date | {DATE} |",
       "| Source | CM v0.8 §8, copied verbatim by `tools/build_contracts.py` (tracker CM8-002) |", "",
       f"**Count:** {len(err)} codes. `kentender_contracts/services/errors.py` must hold exactly these codes and messages, and `test_cm_errors` compares them with this file.", ""]
note = next(l for l in lines[idx("## 8. Error contract"):] if l.startswith("No internal tables"))
out += ["**Rule** (CM v0.8 §8, verbatim): \"" + note.strip() + "\"", "", "| Code | User-visible message | Fix / holder | Source line |", "|---|---|---|---|"]
for n, l in err:
    out.append(l.rstrip(" |") + f" | CM v0.8 line {n} |")
open("error_contract.md", "w").write("\n".join(out) + "\n")

# =============================================================================
# next_step_register.md  (§5.10)
# =============================================================================
ns = table_rows("### 5.10 Next steps and handoffs", "### 5.11 Contract rules")
ns = [r for r in ns if not r[1].startswith("| Event |")]
out = ["# CM-CHG-001 v0.8: next-step register", "", "| Control | Value |", "|---|---|", "| Version | 0.8-next-steps.1 |", f"| Date | {DATE} |",
       "| Source | CM v0.8 §5.10, copied verbatim by `tools/build_contracts.py` (tracker CM8-003); ordering from §6.3 |", "",
       f"**Count:** {len(ns)} rows. Each row creates one linked My Work item for each required current holder; a notification links to that item and is not a second approval (§5.10). "
       "A command subject, version and holder appear once (§6.3). **Named test** is the proposed test name in `tests/test_cm_next_steps.py` (new content for review); a row is `Planned` until that test passes.", "",
       "| # | Event | Next holder / work item | Sender's waiting-on item | Notification | Clears when | Named test (proposed) | Source line |", "|---|---|---|---|---|---|---|---|"]
for k, (n, l) in enumerate(ns, 1):
    cells = [c.strip() for c in l.strip().strip("|").split(" | ")]
    assert len(cells) == 5, (n, cells)
    slug = re.sub(r"[^a-z0-9]+", "_", cells[0].lower()).strip("_")[:60]
    out.append(f"| {k} | " + " | ".join(c.replace("|", "/") for c in cells) + f" | `test_cm_next_steps::test_{slug}` | CM v0.8 line {n} |")
out += ["", "## Ordering and deduplication (CM v0.8 §6.3)", "",
        "1. Protective, legal or security deadline at risk; 2. other verified overdue duty; 3. earliest verified upcoming due instant; 4. undated work by assignment instant and stable task id. A blocked duty stays visible with its exact fix owner and never hides actionable independent work. Waiting and scheduled rows sit below actionable work in the same order. Unknown dates read **Not established**; no invented urgency score.",
        "", "One logical item per command subject, version and required holder; retries and event replay never create a second item. Reassignment preserves the previous holder and time; an old task identity confers no command authority. The case shows one leading next-step block and a compact **Other work** region for the rest, excluding the leading task (board D40 is the reference presentation). Closed and Terminated records keep surviving items in My Work and All contracts."]
open("next_step_register.md", "w").write("\n".join(out) + "\n")

# =============================================================================
# command_map.md
# =============================================================================
s7a, s7b = idx("## 7. Service and command contracts"), idx("## 8. Error contract")
VERBS = "Receive|Record|Register|Revise|Confirm|Start|Save|Request|Sign|Prepare|Post|Submit|Correct|Return|Approve|Resolve|Respond|Decide|Activate|Get|Recommend|Appoint|Declare|Verify|Reject|Generate|Issue|Complete|Reopen|Send|Reply"
COMMANDS = []
for l in lines[s7a:s7b]:
    for m in re.finditer(r"\b((?:%s)[A-Z][A-Za-z0-9]+)\b" % VERBS, l):
        if m.group(1) not in COMMANDS:
            COMMANDS.append(m.group(1))
assert len(COMMANDS) == 83, len(COMMANDS)
sec7 = "\n".join(lines[s7a:s7b])


def src_line(text):
    return next(i + 1 for i, l in enumerate(lines) if text in l)


# --- control -> command rules -------------------------------------------------
# (labels, designs or None for any, kind, commands, source line, status)
# status: Named = the spec row names this control; Inferred = the spec names the command
# but not this control on this board; Gap = the spec names no command for this control.
L = src_line
R = []


def rule(labels, designs, kind, commands, line, status="Named"):
    R.append((labels if isinstance(labels, list) else [labels], designs, kind, commands if isinstance(commands, list) else [commands], line, status))


l_appt = L("| Recommend inspectors / Appoint inspectors")
l_sec = L("| Save security / Verify security / Reject security")
l_out = L("| Save signature evidence / Confirm signature evidence")
l_chg = L("| Request extension / Submit change for decision / Sign amendment")
l_src = L("| Record source evidence =>") if any("| Record source evidence =>" in x for x in lines) else L("| Record source evidence | `RecordLegalSourceEvidence`")
l_adv = L("| Sign advance certification")
l_use = L("| Use references")
l_fin = L("| Sign final acceptance |")
l_pay = L("| Prepare payment |")
l_dlg = L("| Appoint / Verify / Reject / Save evidence / Confirm decision / Return in a named dialog")
l_reg = L("| Register existing contract / Save and review")
l_msg = L("| Send message / Send reply / Send notice")
l_dec = L("| Approve extension / Decline extension")
l_ter = L("| Approve termination / Decline termination")
l_rep = L("| Submit report / Record source evidence")
l_ret = L("| Record return / Sign technical certificate")
l_app = L("| Approve payment / Confirm payment")
l_inv = L("| Submit invoice / Submit correction")
l_srch = L("| Search contracts / All statuses")
l_open = L("| Open contract / Back / section navigation")
l_vw = L("| View award / agreement / evidence")
l_sig = L("| Send for signature / Sign contract")
l_enter = L("| Enter unit references / Record delivery")
l_obs = L("| Record observations / Save observations")
l_rpt = L("| Prepare report for signing / Sign report")
l_corr = L("| Request correction / Send request")
l_cert = L("| Sign certification |")
l_nat = L("| View payment record / View settlement")
l_fd = L("| Save draft / Submit invoice for approval")
l_fa = L("| Approve accounting invoice / Return invoice")
l_iss = L("| Open replacement issue / View issue")
l_co = L("| Sign close-out / Return for correction")
l_rt = L("| Retry / View update status")
l_cl = L("| Disclosures / Cancel")
l_d34 = L("| Request change / Approve change / Decline / Sign amendment (D34)")
l_d35 = L("| Record return (D35)")
l_rem = L("| Verify remedy / Request correction / Close claim")
l_adj = L("| Submit adjustment for decision / Approve adjustment")
l_clm = L("| Request claim / Approve claim")
l_rpl = L("| Verify replacement / Reject replacement")
l_reo = L("| Reopen contract / Keep closed with surviving work")
l_d38 = L("| Submit correction / Save draft (D38-P)")
l_cmp = L("| Complete settlement / Confirm completion")
l_oth = L("| Other work / Open / View affected records")
l_dl = next(i + 1 for i, x in enumerate(lines) if "can download the same frozen package" in x)

rule("Register existing contract", None, "Navigation", "(route /app/contracts/register)", l_reg)
rule(["Open contract", "Open", "Back to contracts"], None, "Read", "GetContractWorkspace", l_open)
rule("Clear search", None, "Read", "(list query)", l_srch)
rule("Send for signature", None, "Command", "RequestContractSignatures", l_sig)
rule("Sign contract", None, "Command", "SignContractVersion", l_sig)
rule("Download agreement 1", None, "Read", "GetContractHistory", l_dl)
rule(["Report a problem", "Report a new issue", "Report difference"], None, "Command", "RecordContractIssue", l_msg)
rule("Save signature evidence", None, "Command", "RecordOutsideContractSignature", l_out)
rule("Confirm signature evidence", None, "Command", "ConfirmOutsideSignatureEvidence", l_out)
rule(["Record source evidence", "Save evidence"], None, "Command", "RecordLegalSourceEvidence", l_rep)
rule(["Appoint inspectors", "Appoint"], None, "Command", "AppointContractInspectors", l_appt)
rule(["Recommend inspectors", "Revise appointment recommendation"], None, "Command", "RecommendContractInspectors", l_appt)
rule("Save declaration", None, "Command", "DeclareContractInterest", l_appt)
rule(["Return", "Return for correction"], ["D23"], "Command", "ReturnContractAppointment", l_appt)
rule("Record delivery", None, "Command", "RecordContractArrival", l_enter)
rule(["Enter unit references", "Use references"], None, "Local", "(local arrival draft; RecordContractArrival commits)", l_use)
rule("Record observations", None, "Navigation", "(opens the observation editor; RecordInspectionObservations saves)", l_obs)
rule("Save observations", None, "Command", "RecordInspectionObservations", l_obs)
rule("Sign technical certificate", None, "Command", "SignTechnicalCertificate", l_ret)
rule(["Request correction", "Send request"], ["D07", "D19", "D35"], "Command", "RequestAcceptanceCorrection", l_corr)
rule(["Request correction", "Send request"], ["D08"], "Command", "RequestInvoiceCorrection", l_corr)
rule("Prepare report for signing", None, "Command", "PrepareAcceptanceReport", l_rpt)
rule("Sign report", None, "Command", "SignAcceptanceReport", l_rpt)
rule("Submit invoice", None, "Command", "SubmitContractInvoice", l_inv)
rule("Submit correction", ["D18"], "Command", "CorrectContractInvoice", l_inv)
rule("Submit correction", ["D38"], "Command", "PrepareContractClosureCorrection", l_d38)
rule("Sign certification", None, "Command", "SignContractCertification", l_cert)
rule("Save draft", ["D33", "D09", "D28"], "Command", "SaveNativeFinanceDraft", l_fd)
rule("Save draft", ["D38"], "Command", "PrepareContractClosureCorrection", l_d38)
rule(["Submit invoice for approval", "Submit payment for approval"], None, "Command", "SubmitNativeFinanceForApproval", l_fd)
rule(["Approve accounting invoice", "Approve payment"], None, "Command", "ApproveNativeFinanceRecord", l_fa)
rule(["Return invoice for correction", "Return payment for correction", "Return invoice", "Return payment"], None, "Command", "ReturnNativeFinanceForCorrection", l_fa)
rule("Review latest version", None, "Read", "GetContractWorkspace", L("| CM_CHANGED"), "Inferred")
rule("Prepare payment", None, "Navigation", "(opens the KenTender payment editor)", l_pay)
rule("Confirm payment", None, "Command", "RecordFinanceSettlement", l_app)
rule("Sign advance certification", None, "Command", "SignAdvanceCertification", l_adv)
rule(["Send message", "Send notice"], None, "Command", "SendContractCorrespondence", l_msg)
rule("Send reply", None, "Command", "ReplyContractCorrespondence", l_msg)
rule(["Verify security", "Verify", "Verify replacement"], None, "Command", "VerifyContractSecurity", l_sec)
rule(["Reject security", "Reject", "Reject replacement"], None, "Command", "RejectContractSecurity", l_sec)
rule("Save security", None, "Command", "RecordContractSecurity", l_sec)
rule("Record return", ["D16"], "Command", "RecordSecurityAction", l_ret)
rule("Record return", ["D35"], "Command", "RecordAcceptanceCorrection", l_d35)
rule("Request extension", None, "Command", "RequestContractChange", l_chg)
rule("Request change", None, "Command", "RequestContractChange", l_d34)
rule("Submit change for decision", None, "Command", "SubmitContractChangeForDecision", l_chg)
rule("Sign amendment", None, "Command", "SignContractVersion", l_chg)
rule(["Approve extension", "Approve change", "Decline", "Confirm decision"], ["D14", "D34"], "Command", "DecideContractChange", l_dec)
rule(["Return for correction"], ["D14", "D27", "D34"], "Command", "ReturnContractChange", l_dec)
rule(["Decline", "Confirm decision"], ["D20"], "Command", "DecideContractTermination", l_ter)
rule("Approve termination", None, "Command", "DecideContractTermination", l_ter)
rule("Return for correction", ["D20"], "Command", "ReturnContractTermination", l_ter)
rule(["Approve adjustment", "Decline", "Confirm decision", "Return for correction"], ["D36"], "Command", "DecideContractAdjustment", l_adj)
rule("Submit adjustment for decision", None, "Command", "PrepareContractAdjustment", l_adj)
rule("Request claim", None, "Command", "RequestSecurityClaim", l_clm)
rule(["Approve claim", "Decline", "Return for correction"], ["D37"], "Command", "DecideSecurityClaim", l_clm)
rule(["Record claim outcome", "Save outcome"], None, "Command", "RecordSecurityClaimOutcome", l_clm)
rule("Verify remedy", None, "Command", "VerifyContractRemedy", l_rem)
rule("Submit settlement for completion", None, "Command", "PrepareTerminationSettlement", l_d38)
rule(["Complete settlement", "Confirm completion"], None, "Command", "CompleteTerminationSettlement", l_cmp)
rule("Return for correction", ["D39"], "Command", "ReturnContractTermination", l_co, "Gap")
rule(["Return", "Return for correction"], ["D32"], "Command", "ReturnContractCloseout", l_co, "Gap")
rule("Sign final acceptance", None, "Command", "SignFinalContractAcceptance", l_fin)
rule("Sign and issue certificate", None, "Command", "IssueCompletionCertificate", l_ret)
rule("Sign close-out", None, "Command", "SignContractCloseout", l_co)
rule(["Return", "Return for correction"], ["D11"], "Command", "ReturnContractCloseout", l_co)
rule(["Reopen contract", "Confirm reopening"], None, "Command", "ReopenContractCloseout", l_reo)
rule("Keep closed with surviving work", None, "Command", "ConfirmContractClosure", l_reo)
rule("Return for correction", ["D38"], "Command", "ReturnContractCloseout", l_reo)
rule("Save and review", None, "Command", ["RegisterExistingContract", "ReviseContractIntake"], l_reg)
rule("Confirm opening position", None, "Command", "ConfirmOpeningPosition", l_reg)
rule("Start management", None, "Command", "StartContractManagement", l_reg)
rule("Submit report", None, "Command", "SubmitContractReport", l_rep)
rule(["Retry", "View update status"], None, "Read", "(operation-status projection)", l_rt)
rule("Cancel", None, "Local", "(closes the local dialog or edit; commits nothing)", l_cl)
rule("Close", None, "Local", "(closes the local dialog)", l_cl, "Inferred")
rule(["View payment record", "View settlement", "View accounting invoice"], None, "Read", "(native record projection)", l_nat)
rule(["View issue", "View claim", "Open replacement issue"], None, "Read", "GetContractWorkspace", l_iss)
rule("View affected records", None, "Read", "GetContractWorkspace", l_oth)
rule(["View award", "View agreement", "View agreement 1", "View report", "View history", "View evidence"], None, "Read", "GetContractHistory", l_vw)

CMD_SOURCES = {"lnk", "btn", "row"}


def resolve(design, label, sources):
    best = None
    for labels, designs, kind, commands, line, status in R:
        if label in labels and (designs is None or design in designs):
            if best is None or (designs is not None and best[1] is None):
                best = (labels, designs, kind, commands, line, status)
    if best:
        return best[2], best[3], best[4], best[5]
    if label.startswith("View ") or label.startswith("Download "):
        return "Read", ["GetContractHistory"], l_vw, "Inferred"
    if sources <= CMD_SOURCES:
        return "Read", ["GetContractHistory"], l_vw, "Inferred"
    return None


occ = collections.OrderedDict()


def add(b, label, src):
    label = label.lstrip("-").strip()
    if label:
        occ.setdefault((b["design"], label), {"boards": [], "src": set()})
        occ[(b["design"], label)]["boards"].append(b["id"])
        occ[(b["design"], label)]["src"].add(src)


for b in boards:
    if b["primary"]: add(b, b["primary"], "p")
    for x in b["secondary"]: add(b, x, "s")
    if b["headP"]: add(b, b["headP"], "head")
    if b["emptyAct"]: add(b, b["emptyAct"], "empty")
    if b["dialog"]:
        if b["dialog"]["primary"]: add(b, b["dialog"]["primary"], "dlg-p")
        for x in b["dialog"]["secondary"]: add(b, x, "dlg-s")
    for x in b["fixes"]: add(b, x, "fix")
    for x in b["buttons"]: add(b, x, "btn")
    for x in b["links"]: add(b, x, "lnk")
    for x in b["rowLinks"]: add(b, x, "row")

unmapped, rows = [], []
for (design, label), v in occ.items():
    res = resolve(design, label, v["src"])
    if res is None:
        unmapped.append((design, label, v["boards"][:3]))
        continue
    kind, cmds, line, status = res
    for c in cmds:
        if c.startswith("("):
            continue
        assert c in COMMANDS, f"{c} is not a §7 command"
    rows.append((design, label, sorted(set(v["boards"])), kind, cmds, line, status))
assert not unmapped, unmapped

used = {c for r in rows for c in r[4] if not c.startswith("(")}
SERVICE_ONLY = {
    "ReceiveAwardPackage": "Event / adapter: arrives from Award's receiver hook; no board control (CM-IF-01).",
    "ReceiveAwardUpdate": "Event / adapter: immutable Award update; no board control.",
    "ReceiveAwardPublicationEvent": "Event / adapter: `AwardDecisionRecorded v1`; no board control.",
    "RecordContractAwardPublication": "Command with no board in the design: HOP records actual publication evidence for a publication obligation (§5.2, §5.15). **Design gap — logged.**",
    "SaveContractParticulars": "Command with no board of its own: the D02 particulars fields save through it (§7 pairs it with RequestContractSignatures). Control label not drawn separately.",
    "RecordCustodyReturn": "Command with no board in the design: returns of unaccepted units to the supplier (§5.4). **Design gap — logged.** D35 draws only the accepted-unit return.",
    "RecordWarrantyClaim": "Command with no board of its own: the D16-W / D16-P warranty claim controls (**Send notice**, **Record return**) record claims; **Design gap — confirm which control.**",
    "PostAcceptedReceipt": "Service-only: worker posting from an effective acceptance decision (§7 'Service-only'); no board control.",
    "ReceiveFinanceResult": "Service / event: trusted native document event; no board control.",
    "RecordFinanceSettlement": None,
    "CorrectFinanceSettlement": "Command with no board in the design: correcting an evidenced settlement (§5.18 'Payment reversed or settlement correction'). **Design gap — logged.** D28-V shows only the reversal read.",
    "ResolveContractIssue": "Service-only: called by VerifyContractRemedy when all evidence is complete, and by an authorised disposition (§5.20); no board control of its own.",
    "RespondToContractIssue": "Command with no board of its own: supplier and holder replies to an issue (D13 **Send reply** uses ReplyContractCorrespondence). **Design gap — confirm which control.**",
    "ActivateContractChange": "Service-only: runs after required amendment signatures and effectiveness (§11.1 D34 row); no board control.",
    "PrepareContractCloseout": "Service-only: generates the close-out review (§5.9); the board D11 shows its output.",
    "GetContractWorkspace": None, "GetContractHistory": None,
    "GenerateContractReport": "Service / scheduler: period report generation (§5.15); no board control. D15 submits the generated report.",
    "RecordContractReportSubmission": "Command with no board of its own: records an actual external submission reference (§5.15). D15 draws **Submit report**; **Design gap — confirm control for external evidence.**",
    "RequestContractFundingUpdate": "Service-only: durable funding intent (§7); no board control.",
    "ReceiveContractFundingResult": "Service-only: owner's idempotent funding result; no board control.",
    "PrepareContractAdvance": "Service-only: produces the entitlement D29 **Sign advance certification** signs (§11 advance row).",
    "RecordTerminationNotice": "Command with no board in the design: actual notice dispatch and effectiveness evidence (§5.7). **Design gap — logged.** D20-T shows the recorded result.",
    "RecordContractChangeReview": "Command with no board in the design: reviewer recommendation record (§7 final paragraph). D27-R shows the result. **Design gap — logged.**",
    "SignContractChangeReview": "Command with no board in the design: reviewer personal signature on a review (§7 final paragraph). **Design gap — logged.**",
    "RecordOutsideContractSignature": None, "ConfirmOutsideSignatureEvidence": None,
    "RequestAcceptanceCorrection": None, "RequestInvoiceCorrection": None,
}
gaps_cmd = [c for c in COMMANDS if c not in used and SERVICE_ONLY.get(c) is None and c not in {"GetContractWorkspace", "GetContractHistory"}]
assert not gaps_cmd, f"commands with neither a control nor a stated reason: {gaps_cmd}"

out = ["# CM-CHG-001 v0.8: control → command map", "", "| Control | Value |", "|---|---|", "| Version | 0.8-command-map.1 |", f"| Date | {DATE} |",
       "| Source | board dump (`tools/extract_boards.mjs`), CM v0.8 §7 and §§11–11.1, built by `tools/build_contracts.py` (tracker CM8-004); CM-AC-44 |", "",
       f"Every visible control of the {len(boards)} boards maps to exactly one command or read of §7, or is local (cancel, close) or navigation. The script reads the controls from the design (primary and secondary actions, page and empty-state actions, dialog actions, next-step fixes, button and link blocks, row links) and fails if one is unmapped. "
       f"**{len(COMMANDS)} commands and reads** are named in §7. **Status:** *Named* = the §11 / §11.1 row names this control; *Inferred* = the spec names the command or read but not this control on this board (a View-style link opens an exact linked version read-only, §11 View row); *Gap* = the spec names no command for this control (see Gaps). "
       "The mapping column and its source line are the authored content of this file (new content for review).", "",
       "## Controls", "", "| Design | Control | Boards | Kind | Command or read | §11 source line | Status |", "|---|---|---|---|---|---|---|"]
for design, label, bs, kind, cmds, line, status in sorted(rows, key=lambda r: (r[0], r[1])):
    bl = ", ".join(bs) if len(bs) <= 3 else f"{bs[0]}, {bs[1]} … ({len(bs)} boards)"
    out.append(f"| {design} | {label} | {bl} | {kind} | {', '.join('`'+c+'`' if not c.startswith('(') else c for c in cmds)} | CM v0.8 line {line} | {status} |")

by_status = collections.Counter(r[6] for r in rows)
out += ["", f"**Totals:** {len(rows)} (design, control) pairs: {by_status['Named']} Named, {by_status['Inferred']} Inferred, {by_status['Gap']} Gap.", "",
        "## Commands and reads with no board control", "",
        "| Command or read | Why there is no control on a board |", "|---|---|"]
for c in COMMANDS:
    if c in used:
        continue
    if c in ("GetContractWorkspace", "GetContractHistory"):
        continue
    out.append(f"| `{c}` | {SERVICE_ONLY[c]} |")
cnt = collections.Counter()
for r in rows:
    for c in r[4]:
        if not c.startswith("("):
            cnt[c] += 1
out += ["", "## Commands with their controls", "", "| Command or read | Board controls that invoke it |", "|---|---|"]
for c in COMMANDS:
    if c in used:
        owners = sorted({f"{r[0]} {r[1]}" for r in rows if c in r[4]})
        out.append(f"| `{c}` | {len(owners)}: " + "; ".join(owners) + " |")
gaps = [r for r in rows if r[6] == "Gap"]
out += ["", "## Gaps found (logged as follow-ups)", "",
        "1. **No command for a Return from D32 (final acceptance) or D39 (termination settlement).** Both boards draw **Return for correction** (D32 also a **Return** dialog). §7 names ReturnContractChange, ReturnContractTermination and ReturnContractCloseout only. The map proposes ReturnContractCloseout for D32 and ReturnContractTermination for D39; the owner confirms or names a command.",
        "2. **Commands with no board.** " + ", ".join(f"`{c}`" for c in COMMANDS if c not in used and SERVICE_ONLY.get(c) and 'gap' in SERVICE_ONLY[c].lower()) + " have no control drawn on any board (see the table above). Each is a required §7 command; their surface is a decision for the owner and the designer, not something the build invents.",
        "3. **Boards carry no per-field control labels** (field edits save through the originating command). The map covers actions, not fields."]
open("command_map.md", "w").write("\n".join(out) + "\n")
print(len(err), len(ns), len(COMMANDS), len(rows), dict(by_status), len(used))
