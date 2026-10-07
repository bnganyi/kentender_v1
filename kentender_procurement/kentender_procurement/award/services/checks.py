# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Read-only checks (AWD-CHG-001 v0.4 §5.1): source completeness, current
tender status, validity, funding, the recommendation's consistency with the
published award method, outstanding corrections and supplier identity, plus
the verified operating profile (§15).

An established restriction and an unavailable check are different facts:
the first opens a business issue with its owner, the second a technical one;
neither permits an unsupported positive decision. Checks never repeat
Evaluation's own automatic checks (§16) — they read its signed result."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

import frappe
from frappe.utils import cstr, get_datetime

from kentender_procurement.award.services import clock, issues, people, profile, simulation, sources, state
from kentender_procurement.services import sequence

TIE = "No single recommendation — equal evaluated totals"
SOURCE_INCOMPLETE = "Incomplete source"
STATUS_UNAVAILABLE = "Status unavailable"
RULES_UNVERIFIED = "Rules unverified"
VALIDITY_EXPIRED = "Validity expired"
FUNDING = "Funding restriction"


def source_problem(snap: dict[str, Any]) -> str:
	sig = snap.get("signatures") or {}
	if not snap.get("digest_verified", True):
		return "The report could not be verified against its signed version."
	if not sig.get("required") or int(sig.get("signed") or 0) < int(sig.get("required") or 0):
		return "A required committee signature is missing."
	if any(not a.get("available") for a in snap.get("annexes") or []):
		return "One required annex is unavailable."
	return ""


def validity(doc) -> dict[str, Any]:
	"""{end, expired, known, rule}: an unreadable validity is unknown, not expired."""
	try:
		v = sources.for_case(doc).validity(doc.tender)
	except sources.SourceUnavailable:
		return {"known": False, "expired": False, "end": None, "rule": None}
	end = get_datetime(v.get("validity_end")) if v.get("validity_end") else None
	return {"known": end is not None, "end": end, "expired": bool(end and clock.now() >= end), "rule": v.get("rule")}


def tender_status(doc) -> dict[str, Any]:
	try:
		facts = sources.for_case(doc).tender_facts(doc.tender)
	except sources.SourceUnavailable:
		return {"known": False, "cancelled": False}
	return {"known": facts is not None, "cancelled": bool((facts or {}).get("cancelled")), "status": cstr((facts or {}).get("status"))}


def recommendation(doc) -> dict[str, Any]:
	"""Whether the signed report supports a positive award under the published
	method: exactly one lowest evaluated responsive tender (§5.3)."""
	snap = state.snapshot(state.current_report(doc))
	rec = snap.get("recommended")
	if snap.get("outcome") == TIE:
		return {"supported": False, "reason": "The published tender has no tie-break rule.", "tie": True}
	if not rec or snap.get("outcome") != "Recommendation":
		return {"supported": False, "reason": cstr(snap.get("reason")) or "The signed report has no current recommendation.", "tie": False}
	ranked = [r for r in snap.get("comparison") or [] if str(r.get("position")) == "1"]
	if len(ranked) != 1 or ranked[0].get("bid") != rec.get("bid"):
		return {"supported": False, "reason": "The recommendation does not match the lowest evaluated responsive tender.", "tie": False}
	if not rec.get("organisation"):
		return {"supported": False, "reason": "The recommended supplier could not be identified.", "tie": False}
	return {"supported": True, "reason": "", "tie": False, "recommended": rec}


def funding(doc) -> dict[str, Any]:
	"""The funding position read from Budget now (AWD-IF-07), against the
	recommended supplier's evaluated amount. `known` is False when Budget
	cannot answer: that is an unavailable check, never "not restricted" (§5.1).
	The figure frozen in the signed report is history, not today's position."""
	rep = state.current_report(doc)
	rec = (state.snapshot(rep).get("recommended") or {}) if rep else {}
	needed = Decimal(cstr(rec.get("evaluated_total") or 0))
	try:
		read = sources.for_case(doc).funding(doc.tender)
	except (sources.SourceUnavailable, AttributeError) as exc:
		read = {"known": False, "reason": cstr(exc)}
	if not read or not read.get("known"):
		return {"known": False, "restricted": False, "detail": {}, "reason": cstr((read or {}).get("reason")) or "Budget did not answer."}
	available = Decimal(cstr(read.get("available") or 0))
	short = max(needed - available, Decimal("0"))
	detail = {"available": str(available), "needed": str(needed), "shortfall": str(short), "reservations": read.get("reservations") or [], "as_at": str(clock.now()),
		"qualification": "Funding needs resolution before award." if short > 0 else ""}
	return {"known": True, "restricted": short > 0, "detail": detail, "reason": ""}


def funding_stop(doc) -> str:
	""""" when funding is confirmed sufficient now; else why a positive step
	must not proceed: "unknown" (Budget unavailable) or "restricted"."""
	f = funding(doc)
	return "unknown" if not f["known"] else "restricted" if f["restricted"] else ""


def sync(doc) -> dict[str, Any]:
	"""Recompute the automatic conditions and open or clear their issues. Only
	a condition the system itself detected is cleared by the system."""
	out: dict[str, Any] = {}
	rep = state.current_report(doc)
	snap = state.snapshot(rep)
	problem = source_problem(snap) if rep else ""
	if problem:
		issues.open_issue(doc, source_event=f"source:{rep.name}", issue_type="Source correction", subtype=SOURCE_INCOMPLETE,
			title="The evaluation report is incomplete. The Head of Procurement has been notified.", reason=problem, source=f"Evaluation report {rep.version_number}",
			detail={"owner": "Evaluation chair"})
	out["source_problem"] = problem
	st = tender_status(doc)
	if not st["known"]:
		i = issues.open_issue(doc, source_event=f"status-unavailable:{doc.name}:{clock.now().date()}", issue_type="Service failure", subtype=STATUS_UNAVAILABLE,
			title="The current tender status could not be confirmed. The system will check again when service is restored.", owner_role=people.TECHNICAL_OPERATOR,
			owner_user=_technical(), reason="The tender status service did not answer.")
		_support_issue(doc, "CheckTenderStatus", f"status:{doc.name}", "Restore tender status checks", i.reason)
	else:
		if issues.resolve_automatic(doc, subtype=STATUS_UNAVAILABLE, note="The tender status could be read again."):
			_support_resolved(f"status:{doc.name}")
	out["status"] = st
	if profile.revised_treatment_verified():
		issues.resolve_automatic(doc, subtype="Revised notice treatment", note="The verified profile now settles the revised-notice treatment.")
	if not profile.verified():
		issues.open_issue(doc, source_event=f"rules-unverified:{doc.name}", issue_type="Rules and notice audience", subtype=RULES_UNVERIFIED,
			title="The applicable rules have not been confirmed. The award cannot proceed yet.", reason="No verified legal operating profile is installed.",
			detail={"owner": "Legal-rule owner"})
	else:
		issues.resolve_automatic(doc, subtype=RULES_UNVERIFIED, note="A verified operating profile is installed.")
	v = validity(doc)
	if v["expired"] and not doc.cancelled:
		issues.open_issue(doc, source_event=f"validity-expired:{doc.name}:{v['end']}", issue_type="Validity", subtype=VALIDITY_EXPIRED,
			title="Tender validity has expired. No award can proceed.", reason=f"Tender validity ended {clock.when(v['end'])}.", effective_at=v["end"])
	out["validity"] = v
	fund = funding(doc)
	if rep and fund["known"]:
		if fund["restricted"]:
			if not issues.open_issues(doc, subtype=FUNDING):
				number = sequence.next_count(issues.ISSUE, {"award_case": doc.name, "subtype": FUNDING})
				issues.open_issue(doc, source_event=f"funding:{rep.name}:{number}", issue_type="Funding", subtype=FUNDING, title="Funding needs resolution before award.",
					reason="The funding Budget now holds for this tender is less than the evaluated amount.", detail={"owner": "Budget", "funding": fund["detail"]})
		else:
			issues.resolve_automatic(doc, subtype=FUNDING, note="Budget now confirms the funding.")
	out["funding"] = fund
	return out


def _technical() -> str:
	return cstr(profile.current().get("technical_operator")) or next(iter(people.technical_operators()), "")


def _support_issue(doc, operation: str, correlation: str, subject: str, detail: str) -> None:
	from kentender_core.services import support_issues

	support_issues.open_issue(module="Award", operation=operation, operation_correlation=correlation, subject=subject, reference_doctype="Award Case",
		reference_name=doc.name, safe_detail=cstr(detail), fixture_namespace=doc.fixture_namespace)


def _support_resolved(correlation: str) -> None:
	from kentender_core.services import support_issues

	support_issues.resolve_on_success(module="Award", operation_correlation=correlation, note="The operation succeeded.")


def open_support_issue(doc, operation: str, correlation: str, subject: str, detail: str) -> None:
	_support_issue(doc, operation, correlation, subject, detail)


def support_resolved(correlation: str) -> None:
	_support_resolved(correlation)


def simulated() -> bool:
	return simulation.enabled()
