# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Technical record search for Bid Opening and Proceedings (KT-STD-001 §3A.6;
BOP-CHG-001 v0.10 §6 "Administrator/System Manager: non-content health and
incident support only"). Only status records are searchable: the opening
case, the proceeding, and Opening access support incidents. Bid facts, the
register and the opening record are never reachable here."""

from __future__ import annotations


def _form(doctype: str) -> str:
	return "/app/" + doctype.lower().replace(" ", "-") + "/{name}"


def reference_resolvers() -> list[dict]:
	return [
		{"doctype": "Bid Opening Case", "label": "Bid opening", "reference_field": "opening_id", "title_field": "tender_reference", "status_field": "state",
			"route": _form("Bid Opening Case")},
		{"doctype": "Opening Access Incident", "label": "Opening access incident", "reference_field": "incident_id", "title_field": "incident_type",
			"status_field": "status", "route": _form("Opening Access Incident")},
		{"doctype": "Proceeding", "label": "Proceeding", "reference_field": "proceeding_id", "title_field": "title", "status_field": "state", "route": _form("Proceeding")},
	]
