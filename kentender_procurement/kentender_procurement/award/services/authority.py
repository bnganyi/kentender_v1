# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""GetAwardAuthorityStatus (AWD-CHG-001 v0.4 §5.4, §7 last paragraph;
AWD-AC-010, AC-018, AC-029).

Two separate canonical facts per tender: the decision status (No decision
recorded / Award recorded / No award recorded / Unknown) — the latest
committed decision across every cycle, a return never counting — and the
notification status (Not issued / Issue in progress / Issued / Unknown),
which never returns to Not issued once anything was issued. Historical
decisions and batches stay listed after a successor cycle. An unreadable
status is Unknown, never a fabricated negative.

The same status is Tenders' cancellation guard: the case row lock serialises
the pre-notification cancellation against notice issue, and cancellation is
refused once issue has started or its state is unknown."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cstr

from kentender_procurement.award.services import clock, records, state

EVL_RECORDED = "Award decision recorded"
EVL_NONE = "No award decision recorded"


def _case_for_tender(tender: str) -> str | None:
	return frappe.db.get_value(records.CASE, {"tender": tender}, "name")


def status(*, tender: str) -> dict[str, Any]:
	try:
		name = _case_for_tender(tender)
		if not name:
			return {"decision_status": "No decision recorded", "notification_status": "Not issued", "decisions": [], "batches": [], "checked_at": clock.now(),
				"source": "No Award case"}
		doc = frappe.get_doc(records.CASE, name)
		decisions = [{"decision": d.name, "cycle": d.cycle, "version": d.version, "outcome": d.outcome, "decided_at": d.decided_at}
			for d in state.decisions(doc) if d.committed]
		batches = [{"batch": b.name, "decision": b.decision, "status": b.status, "issued_at": b.issued_at}
			for b in (frappe.get_doc(state.BATCH, n) for n in frappe.get_all(state.BATCH, filters={"award_case": doc.name}, pluck="name", order_by="version asc"))]
		return {"decision_status": doc.decision_status, "notification_status": doc.notification_status, "decisions": decisions, "batches": batches,
			"record_version": doc.record_version, "checked_at": clock.now(), "source": doc.name}
	except Exception:
		frappe.log_error(title="Award authority status failed")
		return {"decision_status": "Unknown", "notification_status": "Unknown", "decisions": [], "batches": [], "checked_at": clock.now(), "source": "Unavailable"}


def tender_status(*, tender: str) -> dict[str, Any] | None:
	"""`kt_award_authority_status` in Evaluation's vocabulary. None when no
	Award case exists, so Tenders answers from its own durable record."""
	name = _case_for_tender(tender)
	if not name:
		return None
	s = status(tender=tender)
	if s["decision_status"] == "Unknown":
		return {"status": "Unknown", "checked_at": s["checked_at"]}
	doc = frappe.get_doc(records.CASE, name)
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


def cancellation_guard(*, tender: str) -> str:
	"""`kt_tender_cancellation_guards`: refuse while any notice is issued, being
	issued or of unknown state (§5.4: in-progress or unknown is never "no
	notification"). Takes the case lock so issue and cancellation serialise."""
	name = _case_for_tender(tender)
	if not name:
		return ""
	# A locking read: MariaDB runs at REPEATABLE READ and the caller (Tenders) already
	# holds a snapshot, so a plain read after the lock would answer "Not issued" for
	# notices another command issued and committed while this waited (AUD-XC-108).
	value = cstr(frappe.db.get_value(records.CASE, name, "notification_status", for_update=True))
	if value == "Not issued":
		return ""
	if value == "Unknown":
		return "The award notification status could not be confirmed. Cancellation is unavailable until it is recovered."
	return "Award notices have been issued. The pre-notification cancellation route is unavailable."
