"""STD workbench: Template Version forms catalogue (STD-CURSOR-1010)."""

from __future__ import annotations

from collections import defaultdict

import frappe
from frappe import _

from kentender_procurement.std_engine.services.action_availability_service import (
	_perm_read,
	resolve_std_document,
)


def _to_int(value) -> int:
	try:
		return int(value or 0)
	except (TypeError, ValueError):
		return 0


def _to_bool(value) -> bool:
	return bool(_to_int(value))


def _category_for_section(section_number: str, section_title: str) -> tuple[str, str]:
	num = (section_number or "").strip().upper()
	title = (section_title or "").strip().lower()
	if num.startswith("X") or "contract" in title:
		return ("contract_forms", str(_("Contract Forms")))
	if num.startswith("IV") or "form" in title:
		return ("section_iv_forms", str(_("Section IV Forms")))
	return ("other_forms", str(_("Other Forms")))


def build_std_template_version_forms_catalogue(version_code: str, actor: str | None = None) -> dict[str, object]:
	"""Return forms with category metadata, detail payload, and model impact preview."""
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
	immutable = _to_int(doc.get("immutable_after_activation"))
	read_only = status == "Active" and immutable == 1
	draft_editable = status in {"Draft", "Structure In Progress"} and not read_only

	sections = frappe.get_all(
		"STD Section Definition",
		filters={"version_code": code},
		fields=["section_code", "section_number", "section_title"],
	)
	section_by_code = {str(s.get("section_code") or ""): s for s in sections if s.get("section_code")}

	raw = frappe.get_all(
		"STD Form Definition",
		filters={"version_code": code},
		fields=[
			"form_code",
			"title",
			"form_type",
			"section_code",
			"completed_by",
			"is_required",
			"supplier_submission_requirement",
			"contract_carry_forward",
			"drives_dsm",
			"drives_dem",
			"drives_dcm",
			"source_document_code",
			"source_page_start",
			"source_page_end",
		],
		order_by="section_code asc, title asc, form_code asc",
	)

	cat_forms: dict[str, list[dict[str, object]]] = defaultdict(list)
	cat_labels: dict[str, str] = {}
	all_forms: list[dict[str, object]] = []
	dsm_required_supplier_codes: list[str] = []
	for row in raw:
		section_code = str(row.get("section_code") or "")
		smeta = section_by_code.get(section_code, {})
		section_number = str(smeta.get("section_number") or "")
		section_title = str(smeta.get("section_title") or "")
		cat_id, cat_label = _category_for_section(section_number, section_title)
		cat_labels[cat_id] = cat_label
		form_code = str(row.get("form_code") or "")
		is_required = _to_bool(row.get("is_required"))
		supplier_submission_requirement = _to_bool(row.get("supplier_submission_requirement"))
		item = {
			"form_code": form_code,
			"title": row.get("title"),
			"form_type": row.get("form_type"),
			"section_code": section_code or None,
			"section_number": section_number or None,
			"section_title": section_title or None,
			"category_id": cat_id,
			"completed_by": row.get("completed_by"),
			"is_required": is_required,
			"supplier_submission_requirement": supplier_submission_requirement,
			"contract_carry_forward": _to_bool(row.get("contract_carry_forward")),
			"source_document_code": row.get("source_document_code"),
			"source_page_start": row.get("source_page_start"),
			"source_page_end": row.get("source_page_end"),
			"impact": {
				"drives_dsm": _to_bool(row.get("drives_dsm")),
				"drives_dem": _to_bool(row.get("drives_dem")),
				"drives_dcm": _to_bool(row.get("drives_dcm")),
			},
		}
		if supplier_submission_requirement and is_required and item["impact"]["drives_dsm"]:
			dsm_required_supplier_codes.append(form_code)
		cat_forms[cat_id].append(item)
		all_forms.append(item)

	category_order = ("section_iv_forms", "contract_forms", "other_forms")
	categories = []
	for cid in category_order:
		forms = cat_forms.get(cid, [])
		if not forms:
			continue
		categories.append(
			{
				"id": cid,
				"label": cat_labels.get(cid, cid),
				"count": len(forms),
			}
		)

	model_preview = {
		"read_only": True,
		"dsm_required_supplier_form_codes": dsm_required_supplier_codes,
		"dsm_form_count": sum(1 for row in all_forms if (row.get("impact") or {}).get("drives_dsm")),
		"dem_form_count": sum(1 for row in all_forms if (row.get("impact") or {}).get("drives_dem")),
		"dcm_form_count": sum(1 for row in all_forms if (row.get("impact") or {}).get("drives_dcm")),
	}

	return {
		"ok": True,
		"version_code": code,
		"read_only": read_only,
		"draft_editable": draft_editable,
		"categories": categories,
		"forms": all_forms,
		"model_preview": model_preview,
	}
