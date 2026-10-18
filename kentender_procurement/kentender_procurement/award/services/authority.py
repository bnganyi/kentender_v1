# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""GetAwardAuthorityStatus (AWD-CHG-001 v0.9 §5.11, §7, §7.2; AWD-AC-010,
AC-018, AC-029; AWD-OF-AC-004).

Two separate canonical facts per tender: the decision status (No decision
recorded / Award recorded / No award recorded / Unknown) — the latest
committed decision across every cycle, a return never counting — and the
notification status (Not issued / Issue in progress / Issued / Unknown),
which never returns to Not issued once anything was issued. Historical
decisions and batches stay listed after a successor cycle.

The answer comes from the durable Tender-level record (`tender_authority`),
registered when the Tender is published and before any Award case exists. It
is Unknown — never a negative synthesised from "no case found" — when that
record is missing, fails its integrity check, is not at the revision the caller
expected, does not account for the Award case, or disagrees with it.

The same record is Tenders' cancellation fence: its row lock serialises the
pre-notification cancellation against notice issue, and cancellation is refused
once issue has started or its state is unknown."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cint, cstr

from kentender_procurement.award.services import clock, records, state, tender_authority

EVL_RECORDED = "Award decision recorded"
EVL_NONE = "No award decision recorded"
UNAVAILABLE = "The award notification status could not be confirmed. Cancellation is unavailable until it is recovered."
ISSUED = "Award notices have been issued. The pre-notification cancellation route is unavailable."


def _case_for_tender(tender: str) -> str | None:
	return frappe.db.get_value(records.CASE, {"tender": tender}, "name")


def _source(tender: str) -> str:
	return f"{tender_authority.DOCTYPE} {tender}"


def _believe(tender: str, *, lock_rows: bool = False, expected_revision=None):
	"""(record, case, problem). `problem` is empty only when the record can be believed. With `lock_rows` the record and then the case are read with a
	locking read, in the documented lock order (Tender → record → case)."""
	row = tender_authority.lock(tender) if lock_rows else tender_authority.read(tender)
	if row is None:
		return None, None, "No Tender authority record"
	if not tender_authority.intact(row):
		return row, None, "The Tender authority record failed its integrity check"
	if expected_revision is not None and cint(expected_revision) != cint(row.record_version):
		return row, None, "The Tender authority record is not at the expected revision"
	name = _case_for_tender(tender)
	case = frappe.get_doc(records.CASE, name, for_update=True) if name and lock_rows else (frappe.get_doc(records.CASE, name) if name else None)
	if name and cstr(row.award_case) != name:
		return row, case, "The Tender authority record does not account for the Award case"
	if not name and row.award_case:
		return row, None, "The Award case the Tender authority record names is missing"
	if case is not None and cstr(case.notification_status) != cstr(row.notification_status):
		return row, case, "The Tender authority record disagrees with the Award case"
	return row, case, ""


def _unknown(tender: str, problem: str) -> dict[str, Any]:
	return {"decision_status": "Unknown", "notification_status": "Unknown", "decisions": [], "batches": [], "checked_at": clock.now(),
		"source": _source(tender) if problem != "No Tender authority record" else "No Tender authority record", "reason": problem, "case": ""}


def status(*, tender: str, expected_revision=None) -> dict[str, Any]:
	try:
		row, case, problem = _believe(tender, expected_revision=expected_revision)
		if problem:
			return _unknown(tender, problem)
		decisions = [{"decision": d.name, "cycle": d.cycle, "version": d.version, "outcome": d.outcome, "decided_at": d.decided_at}
			for d in state.decisions(case) if d.committed] if case else []
		batches = [{"batch": b.name, "decision": b.decision, "status": b.status, "issued_at": b.issued_at}
			for b in (frappe.get_doc(state.BATCH, n) for n in frappe.get_all(state.BATCH, filters={"award_case": case.name}, pluck="name", order_by="version asc"))] if case else []
		return {"decision_status": case.decision_status if case else "No decision recorded", "notification_status": row.notification_status, "decisions": decisions,
			"batches": batches, "record_version": cint(case.record_version) if case else None, "checked_at": clock.now(), "source": _source(tender),
			"source_revision": cint(row.record_version), "case": case.name if case else "", "cancellation_ref": cstr(row.cancellation_ref),
			"evidence": {**records.loads(row.evidence_json), "award_case": case.name if case else "", "verified_at": str(row.verified_at or "")}}
	except Exception:
		frappe.log_error(title="Award authority status failed")
		return _unknown(tender, "The Tender authority record could not be read")


def tender_status(*, tender: str) -> dict[str, Any] | None:
	"""`kt_award_authority_status` in Evaluation's vocabulary: its decision boundary. Unknown when the Tender-level record cannot be believed."""
	s = status(tender=tender)
	if s["decision_status"] == "Unknown":
		return {"status": "Unknown", "checked_at": s["checked_at"], "source": s["source"]}
	if not s["case"]:
		return {"status": EVL_NONE, "checked_at": s["checked_at"], "source": s["source"], "correction_instruction": ""}
	doc = frappe.get_doc(records.CASE, s["case"])
	instruction = ""
	pending = [d for d in state.decisions(doc) if d.outcome == "Request corrected evaluation"]
	c = state.cycle(doc)
	if pending and c and c.awaiting_report:
		instruction = pending[-1].name
	if s["decision_status"] in ("Award recorded", "No award recorded"):
		latest = s["decisions"][-1] if s["decisions"] else {}
		return {"status": EVL_RECORDED, "checked_at": s["checked_at"], "decided_at": latest.get("decided_at"), "source": f"Award {doc.name}",
			"correction_instruction": instruction}
	return {"status": EVL_NONE, "checked_at": s["checked_at"], "source": f"Award {doc.name}", "correction_instruction": instruction}


AWARD_OWNER = "Award service owner"
AWARD_AND_LEGAL = "Award and legal process owner"


def _blocker(reason: str, message: str, holder: str, *, case: str = "") -> dict[str, Any]:
	return {"reason": reason, "message": message, "holder": holder, "route": {"area": "Award", "case": case}}


def cancellation_fence(*, tender: str) -> dict[str, Any]:
	"""`kt_tender_cancellation_fence` — the structured pre-notification fence Tenders asks before it cancels (AWD-CHG-001 v0.9 §5.11, §7.2).

	Takes the Tender's record lock, then its case's (Tender → record → case): issue and cancellation serialise on that one row even when no Award case
	exists, and the answer is read as last committed, never from the caller's older snapshot. Allowed only while the Tender-level notification status is
	Not issued and can be believed. Each blocker carries its reason, the holder who can resolve it and the route to it:

	- no record / a record that cannot be believed / Unknown → the Award service owner;
	- issue in progress → the Award service owner (an unresolved issue for them);
	- issued → the Award and legal process owner (cancellation is no longer available through this route).

	A cancellation already stamped on the record (a replay of the same decision) is not blocked."""
	row, case, problem = _believe(tender, lock_rows=True)
	checked_at = clock.now()
	name = case.name if case is not None else ""
	if row is None:
		return {"allowed": False, "blockers": [_blocker("no_authority_record", UNAVAILABLE, AWARD_OWNER)], "status": _unknown(tender, problem), "checked_at": checked_at}
	if problem:
		return {"allowed": False, "blockers": [_blocker("status_unknown", UNAVAILABLE, AWARD_OWNER, case=name)], "status": _unknown(tender, problem), "checked_at": checked_at}
	value = cstr(row.notification_status)
	blockers: list[dict[str, Any]] = []
	if value == tender_authority.UNKNOWN:
		blockers.append(_blocker("status_unknown", UNAVAILABLE, AWARD_OWNER, case=name))
	elif value == tender_authority.IN_PROGRESS:
		blockers.append(_blocker("issue_in_progress", ISSUED, AWARD_OWNER, case=name))
	elif value == tender_authority.ISSUED:
		blockers.append(_blocker("issued", ISSUED, AWARD_AND_LEGAL, case=name))
	return {"allowed": not blockers, "blockers": blockers, "checked_at": checked_at,
		"status": {"notification_status": value, "source": _source(tender), "source_revision": cint(row.record_version), "case": name,
			"cancellation_ref": cstr(row.cancellation_ref), "verified_at": str(row.verified_at or "")}}


def cancellation_guard(*, tender: str) -> str:
	"""`kt_tender_cancellation_guards`: the first blocker's words, or "" when cancellation is allowed. Refuses while any notice is issued, being issued or
	of unknown state (§5.4: in-progress or unknown is never "no notification"), and while the Tender-level status cannot be believed."""
	blockers = cancellation_fence(tender=tender)["blockers"]
	return cstr(blockers[0]["message"]) if blockers else ""


def downstream_disposition(*, tender: str) -> dict[str, Any]:
	"""`kt_tender_cancellation_downstream_disposition` (PLN-CHG-001 v1.32 §5.4.7, TPR-CHG-001 v0.21 §7.5): what Award itself holds that would
	make a cancelled Tender's allowance unsafe to restore, read at the moment of consequence. A locking read of the record and its case, so an issue of
	notices that another command is committing is waited for and seen, never answered from an older snapshot (the same reason as
	`cancellation_guard`). `known` is False when Award could not say — including when the Tender-level record cannot be believed; notices issued or in
	progress, or a contracting package prepared or delivered, each mean a downstream obligation may exist. The answer never says 'nothing' for a Tender it
	cannot read."""
	unknown = {"known": False, "case": "", "notification_status": "Unknown", "package_status": "", "package_delivered": False, "source": "Unavailable"}
	try:
		row, case, problem = _believe(tender, lock_rows=True)
		if problem:
			return {**unknown, "source": _source(tender) if row is not None else "No Tender authority record", "reason": problem}
		if case is None:
			return {"known": True, "case": "", "notification_status": cstr(row.notification_status), "package_status": "", "package_delivered": False, "source": _source(tender)}
		packages = frappe.get_all(state.PACKAGE, filters={"award_case": case.name}, fields=["status"], limit_page_length=0)
		statuses = sorted({cstr(p.status) for p in packages})
		return {
			"known": True, "case": case.name, "notification_status": cstr(row.notification_status), "decision_status": cstr(case.decision_status),
			"package_status": ", ".join(statuses), "package_delivered": "Delivered" in statuses, "source": case.name,
		}
	except Exception:
		frappe.log_error(title="Award downstream disposition failed")
		return unknown
