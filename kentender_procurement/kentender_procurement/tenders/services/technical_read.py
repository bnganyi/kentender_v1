# Copyright (c) 2026, KenTender and contributors
"""KT-STD-001 v1.6 §3A.6 / AUTH-ADR-001 v1.8 §8 technical-read surface for
Tenders, registered through the `kt_technical_reference_resolvers` and
`kt_technical_read_probes` hooks. Routes are under the one `tenders` Page
(§9): a Tender resolves to its business reference."""

from __future__ import annotations

import frappe

from kentender_procurement.tenders import api

PAGE = "tenders"


def _tender_route(name: str) -> list[str]:
	reference = frappe.db.get_value("Tender", name, "tender_reference") or name
	return [PAGE, reference]


def _publication_route(name: str) -> list[str]:
	tender = frappe.db.get_value("Tender Publication", name, "tender")
	return _tender_route(tender) + ["publication"] if tender else [PAGE]


def _addendum_route(name: str) -> list[str]:
	tender = frappe.db.get_value("Tender Addendum", name, "tender")
	return _tender_route(tender) + ["addenda", name] if tender else [PAGE]


def reference_resolvers() -> list[dict]:
	return [
		{"doctype": "Tender", "label": "Tender", "reference_field": "tender_reference", "title_field": "requirement_title", "status_field": "overall_status", "route": _tender_route},
		{"doctype": "Tender Publication", "label": "Tender Publication", "reference_field": "tender", "title_field": "rule_snapshot_id", "status_field": "publication_status", "route": _publication_route},
		{"doctype": "Tender Addendum", "label": "Tender Addendum", "reference_field": "addendum_reference", "title_field": "affected_reference", "status_field": "status", "route": _addendum_route},
	]


def _first_where(doctype: str, filters: dict | None, probe_kwarg: str, probe_call) -> str | None:
	for row in frappe.get_all(doctype, filters=filters or {}, order_by="modified desc", limit=20, pluck="name"):
		try:
			probe_call(**{probe_kwarg: row})
		except frappe.DoesNotExistError:
			continue
		return row
	return None


def _tender_kwargs() -> dict | None:
	name = _first_where("Tender", None, "tender", api.get_tender)
	return {"tender": name} if name else None


def _handoff_kwargs() -> dict | None:
	row = frappe.get_all("Authorised Requisition Handoff", fields=["name"], limit=1, order_by="modified desc")
	return {"handoff": row[0].name} if row else None


def read_probes() -> list[dict]:
	return [
		{"label": "tenders.get_tenders_workspace", "call": api.get_tenders_workspace, "kwargs": lambda: {}},
		{"label": "tenders.get_tender_start", "call": api.get_tender_start, "kwargs": _handoff_kwargs},
		{"label": "tenders.get_tender", "call": api.get_tender, "kwargs": _tender_kwargs},
		{"label": "tenders.get_tender_review", "call": api.get_tender_review, "kwargs": _tender_kwargs},
		{"label": "tenders.get_tender_history", "call": api.get_tender_history, "kwargs": _tender_kwargs},
		{"label": "tenders.get_tender_publication", "call": api.get_tender_publication, "kwargs": _tender_kwargs},
	]
