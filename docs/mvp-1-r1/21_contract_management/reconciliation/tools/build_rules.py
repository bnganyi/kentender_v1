"""Writes rule_register.md from CM v0.8 §19.3 (verbatim class and source) and §19.7 (LQ-01–06).

Usage: from reconciliation/: python3 tools/build_rules.py
The module, input event, hold key, affected commands, phase and test name are authored (proposed, new content).
"""
import re

SPEC = "../KenTender_CM-CHG-001_Contract_Management_v0_8.md"
lines = open(SPEC).read().splitlines()
s = next(i for i, l in enumerate(lines) if l.startswith("### 19.3 "))
e = next(i for i, l in enumerate(lines) if l.startswith("### 19.4 "))
rules = [(i + 1, lines[i]) for i in range(s, e) if lines[i].startswith("| CM-R-")]
assert len(rules) == 18, len(rules)
s = next(i for i, l in enumerate(lines) if l.startswith("### 19.7 "))
e = next(i for i, l in enumerate(lines) if l.startswith("### 19.8 "))
lqs = [(i + 1, lines[i]) for i in range(s, e) if lines[i].startswith("| LQ-")]
assert len(lqs) == 6, len(lqs)

# id: (module, input event, hold key, affected commands, phase, LQ links)
A = {
    "CM-R-01": ("formation.py", "Frozen agreement version; signature request; each commit", "FORMATION_AUTHORITY", "RequestContractSignatures, SignContractVersion", "5", ""),
    "CM-R-02": ("signing_window.py", "Award's evidenced notification and signing-window result (consumed, never recomputed)", "SIGNING_WINDOW_UNESTABLISHED", "RequestContractSignatures, SignContractVersion", "5", ""),
    "CM-R-03": ("ag_clearance.py", "Contract value and entity type at send-for-signature", "AG_CLEARANCE_REQUIRED", "RequestContractSignatures", "5", ""),
    "CM-R-04": ("package.py", "Package manifest entries and file digests", "PACKAGE_INCOMPLETE", "RequestContractSignatures", "4, 5", ""),
    "CM-R-05": ("appointment.py", "Appointment version, declarations, conflicts", "APPOINTMENT_MISSING", "RecordInspectionObservations, PrepareAcceptanceReport, SignAcceptanceReport", "6", ""),
    "CM-R-06": ("acceptance.py", "Acceptance report; decision-maker's written authority record", "ACCEPTANCE_AUTHORITY_NOT_EVIDENCED", "PostAcceptedReceipt, SignContractCertification", "6", ""),
    "CM-R-07": ("advance.py", "Issued tender and agreement advance clause; guarantee verification", "ADVANCE_UNSUPPORTED", "PrepareContractAdvance, SignAdvanceCertification", "7", ""),
    "CM-R-08": ("security.py", "Issued security clause; security record verification; exemption basis", "SECURITY_REQUIRED_NOT_VERIFIED", "RequestContractSignatures", "5", "LQ-03"),
    "CM-R-09": ("security_return.py", "Actual AO final-acceptance event", "FINAL_ACCEPTANCE_NOT_EVIDENCED", "RecordSecurityAction (Return)", "9", "LQ-03"),
    "CM-R-10": ("change_extension.py", "Supplier justification, recommendation or agreed route, AO decision", "EXTENSION_ROUTE_INCOMPLETE", "SubmitContractChangeForDecision, DecideContractChange, ActivateContractChange", "8", ""),
    "CM-R-11": ("change_value.py", "Change request against original baselines and cumulative changes", "CHANGE_LIMIT_EXCEEDED", "SubmitContractChangeForDecision, DecideContractChange", "8", "LQ-02"),
    "CM-R-12": ("delay.py", "Operative due date, actual delivery events, extension effect", "DELAY_METHOD_UNVERIFIED", "PrepareContractAdjustment, DecideContractAdjustment", "8", "LQ-04"),
    "CM-R-13": ("publication.py", "`AwardDecisionRecorded v1`; signing; amendments — original trigger times", "PUBLICATION_REQUIREMENT_UNRESOLVED", "RecordContractAwardPublication", "5, 8", "LQ-06"),
    "CM-R-14": ("report_monthly.py", "Period, covered cases, source versions, cutoff", "REPORT_SOURCE_INCOMPLETE", "GenerateContractReport, SubmitContractReport", "8", ""),
    "CM-R-15": ("report_quarterly.py", "Effective amendments in the quarter", "REPORT_SOURCE_INCOMPLETE", "GenerateContractReport, SubmitContractReport, RecordContractReportSubmission", "8", ""),
    "CM-R-16": ("completion.py", "Completion criteria evidence; termination request, notice, effective record", "COMPLETION_CRITERIA_UNMET", "IssueCompletionCertificate, SignContractCloseout, DecideContractTermination, RecordTerminationNotice", "8, 9", ""),
    "CM-R-17": ("scope.py", "Registered or received product classification", "OUT_OF_SCOPE_PRODUCT", "StartContractManagement, ReceiveAwardPackage", "5", ""),
    "CM-R-18": ("particulars.py", "Typed values mapped from issued SCC/GCC, accepted tender, effective amendments", "TERM_MAPPING_MISSING", "RequestContractSignatures; the dependent action named by the missing term", "4, 5", ""),
}
LQ = {
    "LQ-01": ("LEGAL_BASELINE_UNREVIEWED", "Deployment profile approval (release gate); no runtime hold", "R-all"),
    "LQ-02": ("CHANGE_EARLY_TOTAL_INCREASE", "SubmitContractChangeForDecision, DecideContractChange (D34 **Change requires legal review**)", "R-11"),
    "LQ-03": ("SECURITY_EXEMPTION_UNSUPPORTED", "RequestContractSignatures; RecordSecurityAction (Return) where the discharge clause conflicts", "R-08, R-09"),
    "LQ-04": ("DELAY_DEDUCTION_METHOD_UNVERIFIED", "DecideContractAdjustment (automatic enforceable deduction only)", "R-12"),
    "LQ-05": ("EXECUTION_METHOD_UNSUPPORTED", "Production execution of Form No. 4 (signing request); development and tests unaffected", "R-01, R-04"),
    "LQ-06": ("PUBLICATION_DIRECTION_UNCONFIRMED", "RecordContractAwardPublication deadlines and channel only; no hold on unrelated work", "R-13"),
}

out = ["# CM-CHG-001 v0.8: rule register", "", "| Control | Value |", "|---|---|", "| Version | 0.8-rules.1 |", "| Date | 14 October 2026 |",
       "| Source | CM v0.8 §19.3 and §19.7 (class, source and question columns verbatim), built by `tools/build_rules.py` (tracker CM8-007) |", "",
       "Rules are code-owned in `kentender_contracts/rules/` (plan D10). Each has an id, class, source edition and locator, applicability, inputs, calculation and affected commands. A Draft or Suspended profile blocks only the consequential actions it governs. "
       "**Module, input event, hold key, affected commands, phase and named test are authored here (proposed, new content for review).** A hold key names a scoped hold with an owner, never a stage. "
       "No 14-day, 30-day, 60-day or Regulations-only deadline is hard-coded (CM-AC-30); the 15% and 25% change ceilings, the 20% advance cap, the 10% security cap, the KES 5 billion clearance threshold and the 30-day security return are rule parameters read from this register, each with its source locator.", "",
       "## Executable rules (CM v0.8 §19.3)", "",
       "| Rule | Class / source (verbatim) | Module (proposed) | Authoritative input event | Hold key (proposed) | Affected commands | Phase | LQ | Named test (proposed) | Spec line |", "|---|---|---|---|---|---|---|---|---|---|"]
for n, l in rules:
    cells = [c.strip() for c in l.strip().strip("|").split(" | ")]
    rid = re.match(r"(CM-R-\d+)", cells[0]).group(1)
    mod, ev, hold, cmds, ph, lq = A[rid]
    num = rid.replace("CM-R-", "")
    out.append(f"| {cells[0]} | {cells[1]} | `rules/{mod}` | {ev} | `{hold}` | {cmds} | {ph} | {lq or '—'} | `test_cm_rules::test_cm_r_{num}` | CM v0.8 line {n} |")
out += ["", "## Named external questions (CM v0.8 §19.7)", "",
        "| Question | Accountable reviewer and exact question (verbatim) | Recommended interim treatment (verbatim) | Hold key (proposed) | Actions held and nothing else | Rules | Spec line |", "|---|---|---|---|---|---|---|"]
for n, l in lqs:
    cells = [c.strip() for c in l.strip().strip("|").split(" | ")]
    qid = re.match(r"(LQ-\d+)", cells[0]).group(1)
    hold, acts, rr = LQ[qid]
    out.append(f"| {qid} | {cells[0][len(qid):].strip(' —')}: {cells[1]} | {cells[2]} | `{hold}` | {acts} | {rr} | CM v0.8 line {n} |")
out += ["", "## Notes", "",
        "- **Classification (CM v0.8 §19.3):** LAW = read Act provision; TERM = exact issued or signed term; CONTROL = approved KenTender policy. A contract term cannot silently override a statutory constraint. An unsupported or conflicting input creates one named HOP issue for the affected action and never turns unrelated records into failed compliance (CM-AC-71).",
        "- **Original events are stored and results recomputed on an authoritative correction;** earlier results stay as history (CM v0.8 §19.3, §12).",
        "- **Synthetic mechanism profile.** D34's 10 → 11 quantity change, D02's **Not required under these test terms** and D36's 0.1% per day are mechanism tests on a labelled synthetic profile, loaded only under `kt_bds_simulation_environment` and stored as a classification, not drawn as a banner on a user-facing surface (DEC-044; follow-up FU-CM-31). They are never production law (CM v0.8 §19.6).",
        "- **R-13 and LQ-06 apply to different things.** CM-R-13 requires recording publication and reporting with original triggers; LQ-06 asks only which directions fix the deadlines and channels. Until it is answered, work and evidence are recorded and no deadline is invented.",
        "- **Coverage check.** The script asserts 18 rules and 6 questions are present in the spec and mapped here; `test_cm_rules` (Phase 3) asserts the code register holds exactly these ids."]
open("rule_register.md", "w").write("\n".join(out) + "\n")
print(len(rules), len(lqs))
