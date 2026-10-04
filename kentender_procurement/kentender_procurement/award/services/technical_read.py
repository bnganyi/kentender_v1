# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Technical record search for Award (KT-STD-001 §3A.6; AWD-CHG-001 v0.4 §6
"Technical operators see safe operation identifiers, service outcomes and
recovery controls"). Only the award case is searchable, and it opens the
technical view of `/app/award/{award_id}` — operations and outcomes, never
the report, opinion, decision, notices, supplier or price."""

from __future__ import annotations


def _route(name: str) -> list[str]:
	return ["award", name]


def reference_resolvers() -> list[dict]:
	return [{"doctype": "Award Case", "label": "Award", "reference_field": "award_id", "title_field": "tender_reference", "status_field": "stage", "route": _route}]


def read_probes() -> list[dict]:
	import frappe

	from kentender_procurement.award import api

	def _award() -> dict | None:
		name = frappe.db.get_value("Award Case", {}, "name", order_by="modified desc")
		return {"award": name} if name else None

	return [
		{"label": "award.get_workspace", "call": api.get_workspace, "kwargs": lambda: {}},
		{"label": "award.get_award", "call": api.get_award, "kwargs": _award},
	]
