# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""KT-STD-001 §3A.6 / AUTH-ADR-001 v1.8 §8 technical-read surface for STD
Templates, registered through the `kt_technical_reference_resolvers` and
`kt_technical_read_probes` hooks. Every route is under the one
`std-templates` Page (STD-TPL-001 v0.10 §11); a release resolves to its
detail, a concern to the detail of the release it concerns."""

from __future__ import annotations

import frappe

from kentender_procurement.std_templates import api

PAGE = "std-templates"


def _release_route(name: str) -> list[str]:
	return [PAGE, name]


def _concern_route(name: str) -> list[str]:
	release = frappe.db.get_value("STD Template Concern", name, "release_id")
	return [PAGE, release] if release else [PAGE]


def reference_resolvers() -> list[dict]:
	return [
		{"doctype": "Installed STD Release", "label": "Installed STD Release", "reference_field": "release_id", "title_field": "display_name", "status_field": "lifecycle_status", "route": _release_route},
		{"doctype": "STD Template Concern", "label": "STD Template Concern", "reference_field": "concern_id", "title_field": "summary", "status_field": "status", "route": _concern_route},
	]


def _release_kwargs() -> dict | None:
	name = frappe.db.get_value("Installed STD Release", {}, "name", order_by="installed_at desc")
	return {"release_id": name} if name else None


def read_probes() -> list[dict]:
	return [
		{"label": "std_templates.get_std_templates_access", "call": api.get_std_templates_access, "kwargs": lambda: {}},
		{"label": "std_templates.get_std_templates", "call": api.get_std_templates, "kwargs": lambda: {}},
		{"label": "std_templates.get_std_template", "call": api.get_std_template, "kwargs": _release_kwargs},
		{"label": "std_templates.get_std_template_coverage", "call": api.get_std_template_coverage, "kwargs": _release_kwargs},
		{"label": "std_templates.get_std_template_changes", "call": api.get_std_template_changes, "kwargs": _release_kwargs},
		{"label": "std_templates.get_std_template_affected_tenders", "call": api.get_std_template_affected_tenders, "kwargs": _release_kwargs},
	]
