# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Reading an Award case's current cycle and its exact versions (AWD-CHG-001
v0.4 §4, §5.9). The case shows its current cycle's stage; a completed cycle
is never changed; source reports, opinions and decisions are kept as numbered
versions, never replaced."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cint

from kentender_procurement.award.services import records

CYCLE = "Award Decision Cycle"
REPORT = "Award Source Report"
OPINION = "Award Professional Opinion"
DECISION = "Award Decision"
BATCH = "Award Notice Batch"
NOTICE = "Award Notice"
RESPONSE = "Award Supplier Response"
ISSUE = "Award Issue"
CORRESPONDENCE = "Award Correspondence"
CLOCK = "Award Clock"
PACKAGE = "Award Contracting Package"
EVENT = "Award Decision Event"
COMMITTED = ("Award", "No award")


def cycle(doc, number: int | None = None):
	n = cint(number if number is not None else doc.current_cycle) or 1
	name = frappe.db.get_value(CYCLE, {"award_case": doc.name, "number": n}, "name")
	return frappe.get_doc(CYCLE, name) if name else None


def cycles(doc) -> list:
	return [frappe.get_doc(CYCLE, n) for n in frappe.get_all(CYCLE, filters={"award_case": doc.name}, pluck="name", order_by="number asc")]


def report(name: str | None):
	return frappe.get_doc(REPORT, name) if name and frappe.db.exists(REPORT, name) else None


def snapshot(rep) -> dict[str, Any]:
	return records.loads(rep.snapshot_json, {}) if rep else {}


def current_report(doc):
	c = cycle(doc)
	return report(c.source_report if c else doc.current_report)


def opinions(doc, number: int | None = None) -> list:
	n = cint(number if number is not None else doc.current_cycle) or 1
	return [frappe.get_doc(OPINION, x) for x in frappe.get_all(OPINION, filters={"award_case": doc.name, "cycle": n}, pluck="name", order_by="version asc")]


def working_opinion(doc):
	"""The opinion HOP is working on (a draft or signing attempt), if any."""
	rows = [o for o in opinions(doc) if o.state in ("Draft", "Signing", "Out of date")]
	return rows[-1] if rows else None


def signed_opinion(doc, number: int | None = None):
	rows = [o for o in opinions(doc, number) if o.state == "Signed"]
	return rows[-1] if rows else None


def decisions(doc, number: int | None = None) -> list:
	filters = {"award_case": doc.name}
	if number is not None:
		filters["cycle"] = cint(number)
	return [frappe.get_doc(DECISION, x) for x in frappe.get_all(DECISION, filters=filters, pluck="name", order_by="creation asc")]


def committed_decision(doc, number: int | None = None):
	"""The latest committed Award/No award decision of a cycle (or of the case)."""
	rows = [d for d in decisions(doc, number) if d.committed]
	return rows[-1] if rows else None


def latest_committed(doc):
	rows = [d for d in decisions(doc) if d.committed]
	return rows[-1] if rows else None


def current_batch(doc):
	return frappe.get_doc(BATCH, doc.current_batch) if doc.current_batch and frappe.db.exists(BATCH, doc.current_batch) else None


def notices(batch) -> list:
	if not batch:
		return []
	return [frappe.get_doc(NOTICE, n) for n in frappe.get_all(NOTICE, filters={"batch": batch.name}, pluck="name", order_by="notice_number asc")]


def successful_notice(batch):
	return next((n for n in notices(batch) if n.result == "Successful"), None)


def operative_response(notice):
	if not notice:
		return None
	name = frappe.db.get_value(RESPONSE, {"notice": notice.name, "operative": 1}, "name")
	return frappe.get_doc(RESPONSE, name) if name else None


def responses(notice) -> list:
	if not notice:
		return []
	return [frappe.get_doc(RESPONSE, n) for n in frappe.get_all(RESPONSE, filters={"notice": notice.name}, pluck="name", order_by="received_at asc")]


def set_stage(doc, stage: str, **extra) -> None:
	c = cycle(doc)
	if c and c.stage != stage:
		records.update(c, stage=stage)
	records.bump(doc, stage=stage, **extra)


def reload(doc):
	return frappe.get_doc(records.CASE, doc.name)
