"""Writes error_contract.md and handoff_register.md verbatim from the EVL v0.4 spec.

Usage (from reconciliation/): python3 tools/build_contracts.py
"""
import re

SPEC = "../KenTender_EVL-CHG-001_Bid_Evaluation_v0_4.md"
lines = open(SPEC).read().splitlines()


def table_after(heading):
    start = next(i for i, l in enumerate(lines) if l.startswith(heading))
    rows, seen = [], False
    for i in range(start + 1, len(lines)):
        l = lines[i]
        if l.startswith("|"):
            seen = True
            rows.append((i + 1, l))
        elif seen:
            break
    return rows


# --- error contract ---------------------------------------------------------
err = table_after("## 8. Errors and recovery")
body = [r for r in err if r[1].startswith("| `EVL_")]
nonblock_line = next(i for i, l in enumerate(lines) if l.startswith("Nonblocking conditions"))
out = [
    "# EVL-CHG-001 v0.4: error contract",
    "",
    "| Control | Value |",
    "|---|---|",
    "| Version | 0.4-errors.1 |",
    "| Date | 30 September 2026 |",
    "| Source | EVL v0.4 §8, copied verbatim by `tools/build_contracts.py` |",
    "",
    f"**Counts:** {len(body)} blocking codes and 2 nonblocking conditions. `bid_evaluation/services/errors.py` must hold exactly these codes and messages, and `test_evl_errors` compares them with this file.",
    "",
    "**Rules** (EVL v0.4 §8 opening paragraph, verbatim): \"" + next(l for l in lines if l.startswith("These are the canonical")).strip() + "\"",
    "",
    "## Blocking codes",
    "",
    "| Code | Message | Recovery | Source line |",
    "|---|---|---|---|",
]
for n, l in body:
    out.append(l.rstrip(" |") + f" | EVL v0.4 line {n} |")
out += [
    "",
    "## Nonblocking conditions",
    "",
    f"EVL v0.4 line {nonblock_line + 1}, verbatim:",
    "",
    "> " + lines[nonblock_line],
    "",
    "| Code | Message |",
    "|---|---|",
]
for code, msg in re.findall(r"`(EVL_[A-Z_]+)` — \*\*(.+?)\*\*", lines[nonblock_line]):
    out.append(f"| `{code}` | {msg} |")
out += [
    "",
    "## Proceedings mapping",
    "",
    "Proceedings errors reached inside an Evaluation command are shown with Evaluation copy (plan D3 `from_prc`):",
    "",
    "| PRC code (PRC v0.9 §8) | Evaluation code shown |",
    "|---|---|",
    "| `PRC_VERSION_CONFLICT` | `EVL_VERSION_CONFLICT` |",
    "| `PRC_TARGET_CHANGED` | `EVL_TARGET_CHANGED` |",
    "| `PRC_PROOF_UNVERIFIED` | `EVL_SIGNATURE_UNCONFIRMED` |",
    "| `PRC_EVIDENCE_INCOMPLETE` (roster presence missing) | `EVL_MEMBERS_ABSENT` |",
    "| `PRC_EVIDENCE_INCOMPLETE` (other) | `EVL_REPORT_INCOMPLETE` |",
    "| `PRC_START_BLOCKED` | `EVL_MEMBERS_ABSENT` when the roster is incomplete, else `EVL_VERSION_CONFLICT` |",
    "| `PRC_MEMBER_REQUIRED` | `EVL_DECLARATION_REQUIRED` for an undeclared member; otherwise the read is Not found |",
    "| `PRC_OWNER_UNAVAILABLE`, `PRC_ALREADY_FINALIZED` | Not reachable from an Evaluation command: Evaluation checks its own state first. If one occurs it is returned as `EVL_VERSION_CONFLICT` and audited. |",
    "",
    "Evaluation guards its own state before calling Proceedings, so the PRC wording (\"opening record\") never reaches an Evaluation screen. The Evaluation profile gets its own PRC wording (plan D4).",
]
open("error_contract.md", "w").write("\n".join(out) + "\n")

# --- hand-off register ------------------------------------------------------
ho = table_after("| Event | Next holder |")
ho = [r for r in table_after("### 7.3 Hand-off register") if not r[1].startswith("|---")]
header, rows = ho[0], ho[1:]
TESTS = [
    "test_evl_preparation::test_publication_creates_ao_task_once",
    "test_evl_preparation::test_publication_creates_secretary_task_once",
    "test_evl_committee::test_appointment_creates_declaration_tasks",
    "test_evl_committee::test_conflict_and_unavailability_route_to_ao",
    "test_evl_intake::test_review_tasks_once_member_eligible",
    "test_evl_findings::test_needs_review_creates_one_chair_item",
    "test_evl_clarification::test_authorised_creates_send_task",
    "test_evl_clarification::test_sent_creates_supplier_reply_request",
    "test_evl_clarification::test_reply_or_deadline_creates_outcome_task",
    "test_evl_diligence::test_plan_creates_participant_and_lead_tasks",
    "test_evl_diligence::test_frozen_report_creates_participant_sign_tasks",
    "test_evl_diligence::test_all_proofs_create_chair_outcome_task",
    "test_evl_signing::test_freeze_creates_member_sign_tasks",
    "test_evl_signing::test_concern_creates_chair_and_secretary_task",
    "test_evl_signing::test_final_proof_delivers_one_hop_task",
    "test_evl_correction::test_return_creates_correction_task",
    "test_evl_correction::test_supplement_before_delivery_shared_chair_item",
    "test_evl_correction::test_supplement_after_delivery_separate_items",
    "test_evl_correction::test_correction_notice_task_keyed_by_source_event",
    "test_evl_intake::test_source_issue_task_clears_on_reconciliation",
]
assert len(rows) == len(TESTS), (len(rows), len(TESTS))
out = [
    "# EVL-CHG-001 v0.4: hand-off register",
    "",
    "| Control | Value |",
    "|---|---|",
    "| Version | 0.4-handoff.1 |",
    "| Date | 30 September 2026 |",
    "| Source | EVL v0.4 §7.3, copied verbatim by `tools/build_contracts.py`; the last two columns are this plan's assignments |",
    "",
    "**Rules** (EVL v0.4 §7.3, verbatim):",
    "",
]
sec = lines.index("### 7.3 Hand-off register")
for l in lines[sec + 1: header[0] - 1]:
    if l.strip():
        out.append("> " + l)
        out.append(">")
out += [
    "",
    f"**Counts:** {len(rows)} rows. Internal rows become My Work items from `bid_evaluation/services/my_work_provider.py` (plan D11). The supplier row is shown in the Bid Submission bid overview and sent as a courtesy email, never a Desk task (plan D11, D14). The support row is a core Support Issue item (plan D12).",
    "",
    header[1].rstrip(" |") + " | Source line | Named test (planned) |",
    "|---|---|---|---|---|---|---|---|",
]
for (n, l), t in zip(rows, TESTS):
    out.append(l.rstrip(" |") + f" | EVL v0.4 line {n} | `{t}` |")
open("handoff_register.md", "w").write("\n".join(out) + "\n")
print(len(body), len(rows))
