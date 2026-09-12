# Copyright (c) 2026, KenTender and contributors
"""AUTH-ADR-001 v1.8 §8/§9 technical-read surface for STD Configuration.

Registered through the `kt_technical_reference_resolvers` and
`kt_technical_read_probes` hooks (see kentender_procurement/hooks.py).
Resolvers cover `STD Cfg Package` (identity) and `STD Cfg Version` (a
version — no route of its own, resolves to its parent Package's home page,
KT-STD-001 v1.5 §3A.6's child/version rule).

Every read in `std_configuration/api/std_configuration_api.py` is already
open to any authenticated caller (only the `save_*`/lifecycle commands call
`require_draft_capability`), so none of these probes depend on a technical
bypass being wired up — they exercise the same contract every reader uses.
`GetSTDPreview` is deliberately excluded from the probe list: the API
unconditionally raises `STD_NOT_YET_IMPLEMENTED` for it regardless of actor
or arguments (Phase 11 stub, see `_BLOCKED_ON_LATER_PHASE`), so it can never
satisfy the conformance test's "no exception" assertion.
"""

from __future__ import annotations

import frappe

from kentender_procurement.std_configuration.api import std_configuration_api as api

PACKAGE_PAGE = "std-cfg-package-home"


def _package_route(name: str) -> list[str]:
	return [PACKAGE_PAGE, name]


def _version_route(name: str) -> list[str]:
	package_id = frappe.db.get_value("STD Cfg Version", name, "package_id")
	return [PACKAGE_PAGE, package_id] if package_id else [PACKAGE_PAGE]


def reference_resolvers() -> list[dict]:
	return [
		{
			"doctype": "STD Cfg Package",
			"label": "STD Cfg Package",
			"reference_field": "package_code",
			"title_field": "official_title",
			"status_field": None,
			"route": _package_route,
		},
		{
			"doctype": "STD Cfg Version",
			"label": "STD Cfg Version",
			"reference_field": "version_id",
			"title_field": "version_id",
			"status_field": "status",
			"route": _version_route,
		},
	]


def _existing(doctype: str, filters: dict | None = None) -> str | None:
	rows = frappe.get_all(doctype, filters=filters or {}, limit=1, order_by="modified desc", pluck="name")
	return rows[0] if rows else None


def _package_kwargs() -> dict | None:
	name = _existing("STD Cfg Package")
	return {"package_id": name} if name else None


def _draft_kwargs() -> dict | None:
	name = _existing("STD Cfg Draft")
	return {"reference_doctype": "STD Cfg Draft", "reference_name": name} if name else None


def _area_kwargs() -> dict | None:
	name = _existing("STD Cfg Draft")
	return {"reference_doctype": "STD Cfg Draft", "reference_name": name, "area": "PCFG-02"} if name else None


def _review_task_kwargs() -> dict | None:
	name = _existing("STD Cfg Review Task")
	return {"review_task_id": name} if name else None


def _version_comparison_kwargs() -> dict | None:
	rows = frappe.get_all("STD Cfg Version", limit=2, order_by="modified desc", pluck="name")
	if not rows:
		return None
	version_a = rows[0]
	version_b = rows[1] if len(rows) > 1 else rows[0]
	return {"version_a": version_a, "version_b": version_b}


def _active_version_kwargs() -> dict | None:
	name = _existing("STD Cfg Package", {"current_active_version_id": ["is", "set"]})
	return {"package_id": name} if name else None


def _runtime_manifest_kwargs() -> dict | None:
	name = _existing("STD Cfg Version", {"status": "Active"})
	return {"std_version_id": name} if name else None


def _assistance_batch_kwargs() -> dict | None:
	name = _existing("STD Cfg Assistance Batch")
	return {"batch_id": name} if name else None


def read_probes() -> list[dict]:
	return [
		{"label": "std_configuration.list_std_packages", "call": api.list_std_packages, "kwargs": lambda: {}},
		{"label": "std_configuration.get_std_package_home", "call": api.get_std_package_home, "kwargs": _package_kwargs},
		{
			"label": "std_configuration.get_std_configuration_area",
			"call": api.get_std_configuration_area,
			"kwargs": _area_kwargs,
		},
		{"label": "std_configuration.get_std_coverage_report", "call": api.get_std_coverage_report, "kwargs": _draft_kwargs},
		{"label": "std_configuration.get_std_readiness_report", "call": api.get_std_readiness_report, "kwargs": _draft_kwargs},
		{
			"label": "std_configuration.get_std_review_workspace",
			"call": api.get_std_review_workspace,
			"kwargs": _review_task_kwargs,
		},
		{
			"label": "std_configuration.get_std_version_comparison",
			"call": api.get_std_version_comparison,
			"kwargs": _version_comparison_kwargs,
		},
		{
			"label": "std_configuration.get_active_std_version",
			"call": api.get_active_std_version,
			"kwargs": _active_version_kwargs,
		},
		{"label": "std_configuration.get_runtime_manifest", "call": api.get_runtime_manifest, "kwargs": _runtime_manifest_kwargs},
		{
			"label": "std_configuration.get_assistance_proposal",
			"call": api.get_assistance_proposal,
			"kwargs": _assistance_batch_kwargs,
		},
		{"label": "std_configuration.list_std_reviewers", "call": api.list_std_reviewers, "kwargs": lambda: {}},
	]
