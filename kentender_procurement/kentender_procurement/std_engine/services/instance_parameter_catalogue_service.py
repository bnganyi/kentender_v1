"""STD workbench: instance parameter catalogue with values (STD-CURSOR-1102)."""

from __future__ import annotations

import json
from typing import Any

import frappe
from frappe import _

from kentender_procurement.std_engine.services.action_availability_service import (
	_perm_read,
	resolve_std_document,
)
from kentender_procurement.std_engine.services.instance_workbench_service import build_std_instance_workbench_shell
from kentender_procurement.std_engine.services.template_version_parameters_service import (
	build_std_template_version_parameter_catalogue,
)


def _display_value(raw_json: str | None, data_type: str | None) -> str:
	if raw_json is None or str(raw_json).strip() == "":
		return ""
	try:
		val = json.loads(raw_json)
	except (TypeError, ValueError):
		return str(raw_json)
	if isinstance(val, (dict, list)):
		return frappe.as_json(val)[:500]
	return str(val)


def build_std_instance_parameter_catalogue(instance_code: str, actor: str | None = None) -> dict[str, Any]:
	"""Grouped parameters with instance values, impacts, read-only from publication lock."""
	user = (actor or "").strip() or frappe.session.user
	if user in (None, "", "Guest"):
		return {"ok": False, "error": "not_permitted", "message": str(_("Not permitted"))}

	code = (instance_code or "").strip()
	if not code:
		return {"ok": False, "error": "invalid", "message": str(_("Instance code is required."))}

	resolved = resolve_std_document("STD Instance", code)
	if not resolved:
		return {
			"ok": False,
			"error": "not_found",
			"message": str(_("No document matches this instance code.")),
			"instance_code": code,
		}

	doctype, name, inst_doc = resolved
	if doctype != "STD Instance":
		return {"ok": False, "error": "invalid", "message": str(_("Not an STD instance."))}

	if not _perm_read(doctype, name, user):
		return {"ok": False, "error": "not_permitted", "message": str(_("Not permitted"))}

	version_code = str(inst_doc.get("template_version_code") or "").strip()
	if not version_code:
		return {"ok": False, "error": "invalid", "message": str(_("Instance has no template version."))}

	base = build_std_template_version_parameter_catalogue(version_code, actor=user)
	if not base.get("ok"):
		return base

	shell = build_std_instance_workbench_shell(code, actor=user)
	read_only = bool(shell.get("read_only")) if shell.get("ok") else False
	addendum_guidance = str(shell.get("addendum_guidance") or "") if shell.get("ok") else ""

	values = {
		str(r.get("parameter_code") or ""): r
		for r in frappe.get_all(
			"STD Instance Parameter Value",
			filters={"instance_code": code},
			fields=["parameter_code", "value_json", "is_stale", "instance_parameter_value_code"],
			limit=2000,
		)
		if r.get("parameter_code")
	}

	# Tender security visibility: surface group/parameters containing "security" or explicit reference
	def _is_tender_security_row(p: dict[str, Any]) -> bool:
		blob = f"{p.get('label') or ''} {p.get('parameter_code') or ''} {p.get('parameter_group') or ''}".lower()
		return "security" in blob or "tender security" in blob

	groups_out: list[dict[str, Any]] = []
	for grp in base.get("groups") or []:
		params_enriched: list[dict[str, Any]] = []
		for p in grp.get("parameters") or []:
			p = dict(p)
			pc = str(p.get("parameter_code") or "")
			row = values.get(pc)
			p["current_value_display"] = _display_value(row.get("value_json") if row else None, str(p.get("data_type") or ""))
			p["value_is_stale"] = bool(int(row.get("is_stale") or 0)) if row else False
			p["instance_parameter_value_code"] = str(row.get("instance_parameter_value_code") or "") if row else ""
			p["tender_security_dependency"] = _is_tender_security_row(p)
			params_enriched.append(p)
		groups_out.append({"group_name": grp.get("group_name"), "parameters": params_enriched})

	return {
		"ok": True,
		"instance_code": code,
		"template_version_code": version_code,
		"read_only": read_only,
		"addendum_guidance": addendum_guidance,
		"groups": groups_out,
	}
