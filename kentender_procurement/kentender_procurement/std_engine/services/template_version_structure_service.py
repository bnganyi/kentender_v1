"""STD workbench: Template Version structure tree (STD-CURSOR-1008)."""

from __future__ import annotations

from collections import defaultdict

import frappe
from frappe import _

from kentender_procurement.std_engine.services.action_availability_service import (
	_perm_read,
	resolve_std_document,
)


def _section_blob(title: str, code: str) -> str:
	return f"{title or ''} {code or ''}".lower()


def _section_itt_hint(title: str, code: str) -> bool:
	return "itt" in _section_blob(title, code)


def _section_gcc_hint(title: str, code: str) -> bool:
	return "gcc" in _section_blob(title, code)


def _source_titles_for_codes(codes: set[str]) -> dict[str, str]:
	out: dict[str, str] = {}
	for code in codes:
		if not code:
			continue
		title = frappe.db.get_value("Source Document Registry", {"source_document_code": code}, "source_document_title")
		out[code] = str(title or code)
	return out


def build_std_template_version_structure_tree(version_code: str, actor: str | None = None) -> dict[str, object]:
	"""Return nested parts → sections → clauses for workbench Structure tab (read-only)."""
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

	doctype, name, _doc = resolved
	if doctype != "STD Template Version":
		return {"ok": False, "error": "invalid", "message": str(_("Not a template version."))}

	if not _perm_read(doctype, name, user):
		return {"ok": False, "error": "not_permitted", "message": str(_("Not permitted"))}

	parts_raw = frappe.get_all(
		"STD Part Definition",
		filters={"version_code": code},
		fields=[
			"part_code",
			"part_number",
			"part_title",
			"order_index",
			"is_supplier_facing",
			"is_contract_facing",
			"is_mandatory",
		],
		order_by="order_index asc, part_code asc",
	)

	sections_raw = frappe.get_all(
		"STD Section Definition",
		filters={"version_code": code},
		fields=[
			"section_code",
			"part_code",
			"section_number",
			"section_title",
			"section_classification",
			"editability",
			"order_index",
			"source_document_code",
			"source_page_start",
			"source_page_end",
		],
		order_by="order_index asc, section_code asc",
	)

	clauses_raw = frappe.get_all(
		"STD Clause Definition",
		filters={"version_code": code},
		fields=[
			"clause_code",
			"section_code",
			"clause_number",
			"clause_title",
			"editability",
			"order_index",
			"source_document_code",
			"source_page_start",
			"source_page_end",
			"drives_bundle",
			"drives_dsm",
			"drives_dom",
			"drives_dem",
			"drives_dcm",
			"drives_addendum",
		],
		order_by="order_index asc, clause_code asc",
	)

	src_codes: set[str] = set()
	for row in sections_raw:
		src_codes.add(str(row.get("source_document_code") or ""))
	for row in clauses_raw:
		src_codes.add(str(row.get("source_document_code") or ""))
	src_titles = _source_titles_for_codes(src_codes)

	clauses_by_section: dict[str, list[dict[str, object]]] = defaultdict(list)
	for crow in clauses_raw:
		sc = str(crow.get("section_code") or "")
		src_c = str(crow.get("source_document_code") or "")
		clauses_by_section[sc].append(
			{
				"clause_code": crow.get("clause_code"),
				"clause_number": crow.get("clause_number"),
				"clause_title": crow.get("clause_title"),
				"editability": crow.get("editability"),
				"order_index": crow.get("order_index"),
				"source_document_code": src_c or None,
				"source_document_title": src_titles.get(src_c, src_c) if src_c else None,
				"source_page_start": crow.get("source_page_start"),
				"source_page_end": crow.get("source_page_end"),
				"impact": {
					"drives_bundle": bool(int(crow.get("drives_bundle") or 0)),
					"drives_dsm": bool(int(crow.get("drives_dsm") or 0)),
					"drives_dom": bool(int(crow.get("drives_dom") or 0)),
					"drives_dem": bool(int(crow.get("drives_dem") or 0)),
					"drives_dcm": bool(int(crow.get("drives_dcm") or 0)),
					"drives_addendum": bool(int(crow.get("drives_addendum") or 0)),
				},
			}
		)

	sections_by_part: dict[str, list[dict[str, object]]] = defaultdict(list)
	for srow in sections_raw:
		pc = str(srow.get("part_code") or "")
		stitle = str(srow.get("section_title") or "")
		scode = str(srow.get("section_code") or "")
		src_c = str(srow.get("source_document_code") or "")
		edit = str(srow.get("editability") or "")
		itt_hint = _section_itt_hint(stitle, scode)
		gcc_hint = _section_gcc_hint(stitle, scode)
		sections_by_part[pc].append(
			{
				"section_code": srow.get("section_code"),
				"section_number": srow.get("section_number"),
				"section_title": srow.get("section_title"),
				"section_classification": srow.get("section_classification"),
				"editability": edit,
				"order_index": srow.get("order_index"),
				"source_document_code": src_c or None,
				"source_document_title": src_titles.get(src_c, src_c) if src_c else None,
				"source_page_start": srow.get("source_page_start"),
				"source_page_end": srow.get("source_page_end"),
				"itt_locked_hint": bool(edit == "Locked" and itt_hint),
				"gcc_locked_hint": bool(edit == "Locked" and gcc_hint),
				"clauses": clauses_by_section.get(scode, []),
			}
		)

	parts_out: list[dict[str, object]] = []
	for prow in parts_raw:
		pc = str(prow.get("part_code") or "")
		parts_out.append(
			{
				"part_code": prow.get("part_code"),
				"part_number": prow.get("part_number"),
				"part_title": prow.get("part_title"),
				"order_index": prow.get("order_index"),
				"is_supplier_facing": bool(int(prow.get("is_supplier_facing") or 0)),
				"is_contract_facing": bool(int(prow.get("is_contract_facing") or 0)),
				"is_mandatory": bool(int(prow.get("is_mandatory") or 0)),
				"sections": sections_by_part.get(pc, []),
			}
		)

	return {"ok": True, "version_code": code, "parts": parts_out}
