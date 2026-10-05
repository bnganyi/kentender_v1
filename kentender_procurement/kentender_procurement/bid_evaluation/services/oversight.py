# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Oversight and department reads of a delivered evaluation report
(OVS-CHG-001 v0.6 §§4, 4.1, 7, 13; plan D1, D2, D16, D17; tracker OVS6-02xx).

The Accounting Officer and the Head of Procurement Function see
administrative facts only until the report is delivered, and everything the
frozen delivered version holds afterwards, read-only. A Head of User
Department whose unit contributed to the Tender sees a department-level
summary after delivery and nothing of the bids at any time.

What a reader gets after delivery is built from the frozen Evaluation Report
Version, never from the live case (plan D1). A return or a correction in
progress therefore cannot leak unfinished findings, and an earlier delivered
version stays readable (plan D2). The delivery point is "a Delivered
delivery row exists for the version", not the case state."""

from __future__ import annotations

import json
from typing import Any

import frappe
from frappe.utils import cstr

from kentender_procurement.bid_evaluation.services import next_steps, people, report

DELIVERY = "Evaluation Report Delivery"
VERSION = "Evaluation Report Version"


def deliveries(case_name: str) -> list[dict[str, Any]]:
	"""Every delivered report version of the case, newest delivery first."""
	return frappe.get_all(DELIVERY, filters={"evaluation_case": case_name, "status": "Delivered"}, fields=["name", "report_version", "recipient_user", "delivered_at",
		"review_state", "returned_by", "return_comment", "returned_at"], order_by="delivered_at desc, creation desc")


def delivered_names(case_name: str) -> list[str]:
	return [d.report_version for d in deliveries(case_name)]


def department_scope(doc, user: str) -> bool:
	"""A Head of User Department whose scope (with descendants) covers a unit that
	contributed to this Tender (OVS v0.6 §4.1; the Tender's own reader rule)."""
	from kentender_procurement.tenders.services import tender_authorization as authz

	return authz.is_department_head_of(frappe.get_doc("Tender", doc.tender), user)


def content(version_name: str) -> dict[str, Any]:
	"""The frozen content of one report version."""
	return json.loads(frappe.db.get_value(VERSION, version_name, "content_json") or "{}")


def _row(version_name: str) -> dict[str, Any]:
	return frappe.db.get_value(VERSION, version_name, ["name", "version_number", "state", "content_digest", "outcome", "frozen_at", "supersession_kind",
		"supersession_reason"], as_dict=True) or {}


def correction(doc, rows: list[dict[str, Any]]) -> dict[str, Any] | None:
	"""The state of a return for correction: the delivered version stays
	readable and a corrected report is being prepared (OVS v0.6 §7)."""
	if not rows or doc.state == "Report sent" or rows[0].review_state != "Returned":
		return None
	return {"returned": True, "headline": "A corrected report is being prepared.", "reason": cstr(rows[0].return_comment),
		"returned_by_name": people.full_name(rows[0].returned_by) if rows[0].returned_by else "", "returned_at": next_steps.when(rows[0].returned_at)}


def versions(case_name: str) -> list[dict[str, Any]]:
	"""The delivered versions as a reader may list them (newest first)."""
	out = []
	for d in deliveries(case_name):
		v = _row(d.report_version)
		if v:
			out.append({"report": v.name, "version_number": v.version_number, "state": v.state, "delivered": next_steps.when(d.delivered_at),
				"review_state": d.review_state, "outcome": cstr(v.outcome)})
	return out


def delivered_report(doc, *, version_name: str = "") -> dict[str, Any]:
	"""The decision and the report, for an Accounting Officer or Head of
	Procurement Function after delivery: the frozen summary, recommendation
	and comparison of the chosen delivered version (default: the latest),
	with the versions available and any return in progress."""
	rows = deliveries(doc.name)
	names = [d.report_version for d in rows]
	chosen = version_name if version_name in names else (names[0] if names else "")
	if not chosen:
		return {}
	frozen = content(chosen)
	delivery = next(d for d in rows if d.report_version == chosen)
	row = _row(chosen)
	return {
		"report": chosen, "version_number": row.get("version_number"), "report_state": row.get("state"), "digest": row.get("content_digest"),
		"delivered": next_steps.when(delivery.delivered_at), "recipient_name": people.full_name(delivery.recipient_user) if delivery.recipient_user else "",
		"review_state": delivery.review_state, "summary": frozen.get("summary") or {}, "recommendation": frozen.get("recommendation") or {},
		"comparison": frozen.get("financial_comparison") or {}, "tender_and_committee": frozen.get("tender_and_committee") or {},
		"versions": versions(doc.name), "correction": correction(doc, rows),
	}


def department_summary(doc) -> dict[str, Any]:
	"""A department-level summary of the delivered outcome: no bids, no
	findings, no committee notes and no report text beyond the recommendation
	and its recorded reason (OVS v0.6 §4.1, owner decision 4 Oct 2026)."""
	rows = deliveries(doc.name)
	if not rows:
		return {}
	frozen = content(rows[0].report_version)
	summary, rec = frozen.get("summary") or {}, frozen.get("recommendation") or {}
	outcome = cstr(rec.get("outcome"))
	recommended = rec.get("recommended") or {}
	return {
		"version_number": _row(rows[0].report_version).get("version_number"), "delivered": next_steps.when(rows[0].delivered_at), "outcome": outcome,
		"recommended_bidder": cstr(recommended.get("bidder")) if outcome == "Recommendation" else "",
		"evaluated_total": cstr(summary.get("evaluated_total")) if outcome == "Recommendation" else "",
		"reason": cstr(rec.get("reason")), "qualifications": rec.get("qualifications") or [], "not_an_award": cstr(rec.get("not_an_award")),
		"validity_expired": outcome == report.EXPIRED, "correction": correction(doc, rows),
		"notices": frappe.db.count("Evaluation Correction Notice", {"evaluation_case": doc.name}),
	}


def committee_for_department(committee: dict[str, Any]) -> dict[str, Any]:
	"""The assigned committee as administrative facts: names, departments and
	capacities, without any member's declaration."""
	return {"members": [{k: m[k] for k in ("user", "name", "department", "capacity")} for m in committee.get("members") or []],
		"appointment_reference": committee.get("appointment_reference"), "secretary": committee.get("secretary")}
