"""STD workbench: Template Version summary for detail tabs (STD-CURSOR-1007)."""

from __future__ import annotations

import frappe
from frappe import _

from kentender_procurement.std_engine.services.action_availability_service import (
	_perm_read,
	resolve_std_document,
)


def _locked_sections_for_version(version_code: str) -> list[dict]:
	return frappe.get_all(
		"STD Section Definition",
		filters={"version_code": version_code, "editability": "Locked"},
		fields=["section_title", "section_code"],
		limit=500,
	)


def _blob_for_section(row: dict) -> str:
	return f"{row.get('section_title') or ''} {row.get('section_code') or ''}".lower()


def _section_matches_itt(row: dict) -> bool:
	return "itt" in _blob_for_section(row)


def _section_matches_gcc(row: dict) -> bool:
	return "gcc" in _blob_for_section(row)


def build_std_template_version_workbench_summary(version_code: str, actor: str | None = None) -> dict[str, object]:
	"""Return workbench summary for a template version (read-only rule + locked section hints)."""
	user = (actor or "").strip() or frappe.session.user
	if user in (None, "", "Guest"):
		return {"ok": False, "error": "not_permitted", "message": str(_("Not permitted"))}

	code = (version_code or "").strip()
	if not code:
		return {"ok": False, "error": "invalid", "message": str(_("Version code is required."))}

	resolved = resolve_std_document("Template Version", code)
	if not resolved:
		return {
			"ok": False,
			"error": "not_found",
			"message": str(_("No document matches this version code.")),
			"version_code": code,
		}

	doctype, name, doc = resolved
	if doctype != "STD Template Version":
		return {"ok": False, "error": "invalid", "message": str(_("Not a template version."))}

	if not _perm_read(doctype, name, user):
		return {"ok": False, "error": "not_permitted", "message": str(_("Not permitted"))}

	status = str(doc.get("version_status") or "")
	try:
		immutable = int(doc.get("immutable_after_activation") or 0)
	except (TypeError, ValueError):
		immutable = 0
	read_only = status == "Active" and immutable == 1

	locked_rows = _locked_sections_for_version(code)
	locked_count = len(locked_rows)
	itt_locked = any(_section_matches_itt(r) for r in locked_rows)
	gcc_locked = any(_section_matches_gcc(r) for r in locked_rows)

	sample_titles: list[str] = []
	for r in locked_rows:
		t = str(r.get("section_title") or "").strip()
		if t and t not in sample_titles:
			sample_titles.append(t)
		if len(sample_titles) >= 8:
			break

	return {
		"ok": True,
		"version_code": code,
		"version_status": status,
		"read_only": read_only,
		"immutable_after_activation": immutable,
		"locked_section_count": locked_count,
		"itt_locked": itt_locked,
		"gcc_locked": gcc_locked,
		"sample_locked_titles": sample_titles,
	}
