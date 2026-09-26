# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""STD Templates API (STD-TPL-IMP-001 v1.0 §6, §11).

Thin, explicit endpoints over the owner services. An unknown or unauthorised
release is returned as `{"outcome": "NOT_FOUND"}` data, never a Frappe
modal (AGENTS §6.10); a caller with no STD Templates access receives
`{"outcome": "FORBIDDEN"}` for the page. There is deliberately no endpoint
that installs, edits, activates, approves, supersedes, withdraws, repairs or
uploads a release, and none that resolves a concern (release-owner commands
are deployment-only, owner ruling R5).
"""

from __future__ import annotations

import json
from typing import Any

import frappe

from kentender_procurement.std_templates.compiler.errors import STDTemplateError
from kentender_procurement.std_templates.services import access, concerns, documents, lifecycle, read

NOT_FOUND = {"outcome": "NOT_FOUND", "heading": "STD Template not found", "text": "This STD Template is unavailable or you do not have permission to view it."}


def _parse_json(value, default):
	if value is None:
		return default
	if isinstance(value, str):
		return json.loads(value) if value.strip() else default
	return value


def _masked(fn, **arguments) -> dict[str, Any]:
	try:
		return fn(**arguments)
	except STDTemplateError as exc:
		if exc.code == "STD_RELEASE_NOT_FOUND":
			return dict(NOT_FOUND)
		return {"outcome": "ERROR", "code": exc.code, "message": exc.message}


@frappe.whitelist()
def get_std_templates_access() -> dict[str, Any]:
	state = access.resolve()
	if not state["allowed"]:
		return {"outcome": "FORBIDDEN", "heading": "You do not have access to STD Templates", "text": access.FORBIDDEN_MESSAGE}
	return {"outcome": "OK", "technical": state["technical"]}


@frappe.whitelist()
def get_std_templates(search: str = "", status: str = "") -> dict[str, Any]:
	if not access.can_read():
		return {"outcome": "FORBIDDEN", "heading": "You do not have access to STD Templates", "text": access.FORBIDDEN_MESSAGE}
	return _masked(read.list_installed_releases, search=search, status=status)


@frappe.whitelist()
def get_std_template(release_id: str) -> dict[str, Any]:
	return _masked(read.get_installed_release, release_id=release_id)


@frappe.whitelist()
def get_std_template_coverage(release_id: str, search: str = "", treatment: str = "", page: int = 1, page_length: int = 25) -> dict[str, Any]:
	return _masked(read.list_release_coverage, release_id=release_id, search=search, treatment=treatment, page=int(page or 1), page_length=int(page_length or 25))


@frappe.whitelist()
def get_std_template_changes(release_id: str, category: str = "", page: int = 1, page_length: int = 25) -> dict[str, Any]:
	return _masked(read.get_release_change_report, release_id=release_id, category=category, page=int(page or 1), page_length=int(page_length or 25))


@frappe.whitelist()
def get_std_template_affected_tenders(release_id: str) -> dict[str, Any]:
	return _masked(lifecycle.list_tenders_affected, release_id=release_id)


@frappe.whitelist(methods=["POST"])
def report_std_template_concern(release_id: str, concern_values=None) -> dict[str, Any]:
	values = _parse_json(concern_values, {})
	return _masked(concerns.create_concern, release_id=release_id, values=values)


def _send(filename: str, content: bytes, kind: str) -> None:
	frappe.local.response.filename = filename
	frappe.local.response.filecontent = content
	frappe.local.response.type = kind


@frappe.whitelist()
def preview_std_template_document(release_id: str, output_id: str) -> None:
	try:
		filename, content = documents.preview(release_id, output_id)
	except STDTemplateError:
		raise frappe.DoesNotExistError("STD Template not found")
	_send(filename, content, "pdf")


@frappe.whitelist()
def download_std_template_review_pack(release_id: str) -> None:
	try:
		filename, content = documents.review_pack(release_id)
	except STDTemplateError:
		raise frappe.DoesNotExistError("STD Template not found")
	_send(filename, content, "download")
