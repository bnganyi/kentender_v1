# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Planning-to-tender B3/B4/B5/B7/B8/B9 — release package to **TM2 Tender** (hook + service).

Doc 2 sec. 16.1: ``release_procurement_package_to_tender(package_name) -> dict``.

Creates or returns a canonical ``TM2 Tender`` via :func:`create_tender_from_package`, then
merges planning ``configuration_json``, snapshot hashes, and audit comment (B7–B8).

Hook failures must not raise: ``deliver_procurement_package_release`` swallows
exceptions per handler; this hook logs ``ok: False`` outcomes instead.
"""

from __future__ import annotations

import json
from typing import Any

import frappe
from frappe import _

from kentender_procurement.tender_management.services.create_tender_from_package import (
	active_tm2_tender_name_for_package,
	create_tender_from_package,
)
from kentender_procurement.tender_management.services.planning_tender_handoff_audit import (
	append_handoff_audit_comment,
	build_handoff_snapshot_and_hashes,
)
from kentender_procurement.tender_management.services.planning_tender_handoff_configuration import (
	build_handoff_configuration_json,
	load_plan_for_handoff,
	procurement_category_code_from_template,
)
from kentender_procurement.tender_management.services.planning_tender_handoff_xmv import (
	format_xmv_critical_message,
	validate_package_for_release_xmv,
)
from kentender_procurement.tender_management.services.std_template_handoff_resolution import (
	resolve_std_template_for_handoff,
)
from kentender_procurement.tender_management.services.std_template_loader import TEMPLATE_CODE
from kentender_procurement.tender_management.security.authorization.integration import (
	enforce_sec_authorization,
)

_TM2_CATEGORY_FROM_PLANNING_CODE = {
	"GOODS": "Goods",
	"WORKS": "Works",
	"SERVICES": "Services",
	"CONSULTING": "Consultancy",
	"DISPOSAL": "Goods",
}


def _tm2_procurement_category_from_template(template_id: str | None) -> str:
	pc = procurement_category_code_from_template(template_id)
	return _TM2_CATEGORY_FROM_PLANNING_CODE.get(pc, "Goods")


def _map_package_method_to_tender(method: str | None) -> str:
	"""Map planning package method label to TM2 ``procurement_method`` select (display strings)."""
	if not method:
		return "Open Tender"
	m = (method or "").strip()
	if m in (
		"Open Tender",
		"Restricted Tender",
		"RFQ",
		"RFP",
		"Direct Procurement",
	):
		return m
	return "Open Tender"


def package_has_release_tender(package_name: str) -> bool:
	"""True if an active ``TM2 Tender`` is linked to this package (PT-HANDOFF-AC-009 / R07)."""
	return active_tm2_tender_name_for_package(package_name) is not None


def _apply_std_identity_to_tm2(t, std_template_name: str) -> None:
	row = frappe.db.get_value(
		"STD Template",
		std_template_name,
		["template_code", "package_version", "package_hash"],
		as_dict=True,
	)
	if row:
		t.template_code = row.get("template_code") or ""
		t.template_version = row.get("package_version") or ""
		t.package_hash = row.get("package_hash") or ""


def _delete_tm2_and_access_rules(tm2_name: str) -> None:
	for row in frappe.get_all(
		"TM2 Tender Access Rule",
		filters={"tm2_tender": tm2_name},
		pluck="name",
	):
		try:
			frappe.delete_doc("TM2 Tender Access Rule", row, force=True, ignore_permissions=True)
		except Exception:
			frappe.db.delete("TM2 Tender Access Rule", {"name": row})
	for row in frappe.get_all(
		"TM2 Tender Timeline",
		filters={"tm2_tender": tm2_name},
		pluck="name",
	):
		try:
			frappe.delete_doc("TM2 Tender Timeline", row, force=True, ignore_permissions=True)
		except Exception:
			frappe.db.delete("TM2 Tender Timeline", {"name": row})
	if frappe.db.exists("TM2 Tender", tm2_name):
		try:
			frappe.delete_doc("TM2 Tender", tm2_name, force=True, ignore_permissions=True)
		except Exception:
			frappe.db.delete("TM2 Tender", {"name": tm2_name})


def _created_response_from_tm2(tm2_name: str, std_template: str) -> dict[str, Any]:
	row = frappe.db.get_value(
		"TM2 Tender",
		tm2_name,
		["tender_code", "status", "std_template"],
		as_dict=True,
	)
	return {
		"ok": True,
		"existing": True,
		"tender": tm2_name,
		"tender_reference": (row or {}).get("tender_code") or "",
		"std_template": (row or {}).get("std_template") or std_template,
		"tender_status": (row or {}).get("status") or "",
		"tender_code": (row or {}).get("tender_code") or "",
		"tm2_tender": tm2_name,
	}


def release_procurement_package_to_tender(package_name: str) -> dict[str, Any]:
	"""Create or return a ``TM2 Tender`` for the given package (B3/B4/B5/B7).

	:param package_name: Internal name of ``Procurement Package`` (same as hook payload ``package``).
	:returns: Dict with ``ok`` bool; on success includes ``tender`` (TM2 name), ``tender_code``,
		``tm2_tender``, ``std_template``, ``existing``, ``tender_status``.
	"""
	if not (package_name or "").strip():
		return {"ok": False, "message": _("Package name is required.")}

	package_name = package_name.strip()

	if not frappe.db.exists("Procurement Package", package_name):
		return {"ok": False, "message": _("Procurement Package {0} was not found.").format(package_name)}

	enforce_sec_authorization(
		action_code="RELEASE_PACKAGE_TO_TENDER",
		actor=frappe.session.user,
		object_type="Procurement Package",
		object_code=package_name,
		context={"object_exists": True, "object_scope_kind": "package", "enforce_object_scope": True},
		fallback_message="Not authorized to release package to tender.",
	)

	if not frappe.has_permission("Procurement Package", "read", doc=package_name):
		return {"ok": False, "message": _("Not permitted to read Procurement Package.")}

	if not frappe.has_permission("TM2 Tender", "create"):
		return {"ok": False, "message": _("Not permitted to create TM2 Tender.")}

	pkg = frappe.get_doc("Procurement Package", package_name)

	std_res_existing = resolve_std_template_for_handoff(pkg)
	std_for_existing = std_res_existing.std_name or ""

	existing = active_tm2_tender_name_for_package(package_name)
	if existing:
		return _created_response_from_tm2(existing, std_for_existing)

	xmv = validate_package_for_release_xmv(pkg)
	if xmv.has_critical():
		return {
			"ok": False,
			"message": format_xmv_critical_message(xmv),
			"xmv_findings": xmv.all_findings_dicts(),
		}

	std_res = resolve_std_template_for_handoff(pkg)
	std_template = std_res.std_name
	if not std_template:
		return {
			"ok": False,
			"message": _(
				"No STD Template could be resolved (set Procurement Template.default_std_template, resolve mapping ambiguity, or satisfy Works POC fallback; see {0})."
			).format(TEMPLATE_CODE),
			"xmv_findings": xmv.all_findings_dicts(),
			"std_resolution_path": std_res.path,
		}

	plan = load_plan_for_handoff(pkg)
	pkg_status_before = (pkg.get("status") or "").strip()
	ref = (pkg.package_code or "").strip() or f"REL-{pkg.name[:12]}"
	package_business_code = (pkg.package_code or pkg.name or "").strip()

	created = create_tender_from_package(
		frappe.session.user,
		package_business_code,
		context={
			"preferred_std_template": std_template,
			"bypass_tnd2_create_from_package_availability": True,
		},
	)
	if not created.get("ok"):
		out: dict[str, Any] = {
			"ok": False,
			"message": str(created.get("message") or _("Unable to create TM2 tender from package.")),
		}
		if created.get("denial_code"):
			out["denial_code"] = created.get("denial_code")
		if created.get("availability") is not None:
			out["availability"] = created.get("availability")
		out["xmv_findings"] = xmv.all_findings_dicts()
		if std_res.path:
			out["std_resolution_path"] = std_res.path
		return out

	tm2_name = str(created.get("tm2_tender") or "").strip()
	if not tm2_name:
		return {
			"ok": False,
			"message": _("TM2 tender creation returned no document name."),
			"xmv_findings": xmv.all_findings_dicts(),
		}

	try:
		tm2 = frappe.get_doc("TM2 Tender", tm2_name)
		tm2.std_template = std_template
		_apply_std_identity_to_tm2(tm2, std_template)
		tm2.tender_reference = ref
		tm2.tender_scope = "NATIONAL"
		tm2.source_package_code = (pkg.package_code or "").strip() or None
		tm2.procurement_method = _map_package_method_to_tender(pkg.procurement_method)
		tm2.procurement_category = _tm2_procurement_category_from_template(pkg.template_id)
		ev = float(pkg.get("estimated_value") or 0)
		if ev > 0:
			tm2.estimated_value_internal = ev

		cfg_str = build_handoff_configuration_json(tm2, pkg, plan)
		tm2.configuration_json = cfg_str

		_snap, snap_json, snap_hash, cfg_hash, dcnt, bcnt = build_handoff_snapshot_and_hashes(
			pkg,
			plan,
			std_template,
			std_res.path,
			[f.as_dict() for f in xmv.critical],
			[w.as_dict() for w in xmv.warnings],
			cfg_str,
			pkg_status_before,
		)
		tm2.planning_handoff_snapshot_json = snap_json
		tm2.planning_handoff_snapshot_sha256 = snap_hash
		tm2.planning_handoff_configuration_sha256 = cfg_hash
		tm2.planning_handoff_source_demand_count = dcnt
		tm2.planning_handoff_source_budget_line_count = bcnt

		tm2.save(ignore_permissions=True)
	except Exception:
		_delete_tm2_and_access_rules(tm2_name)
		raise

	package_status_after = (
		frappe.db.get_value("Procurement Package", package_name, "status") or ""
	).strip()
	roles = list(frappe.get_roles(frappe.session.user))
	try:
		append_handoff_audit_comment(
			tm2.name,
			tender_doctype="TM2 Tender",
			actor=frappe.session.user,
			roles=roles,
			source_package=pkg.name,
			source_plan=plan.name if plan else None,
			package_status_before=pkg_status_before,
			package_status_after=package_status_after or None,
			target_tender=tm2.name,
			std_template=std_template,
			xmv_findings=[],
			xmv_warnings=[w.as_dict() for w in xmv.warnings],
			snapshot_hash=snap_hash,
			configuration_hash=cfg_hash,
		)
	except Exception as exc:
		frappe.log_error(
			title="Release-to-tender: handoff audit comment failed",
			message=json.dumps({"tender": tm2.name, "package": package_name, "error": str(exc)}),
		)
		_delete_tm2_and_access_rules(tm2.name)
		frappe.throw(
			_("Planning-to-tender handoff could not be completed: audit trail was not written."),
			title=_("Handoff audit failed"),
		)

	out: dict[str, Any] = {
		"ok": True,
		"existing": False,
		"tender": tm2.name,
		"tender_reference": tm2.tender_code,
		"tender_code": tm2.tender_code,
		"tm2_tender": tm2.name,
		"std_template": std_template,
		"tender_status": tm2.status,
	}
	if xmv.warnings:
		out["xmv_warnings"] = [w.as_dict() for w in xmv.warnings]
	return out


def hook_release_procurement_package_to_tender(payload: dict[str, Any] | None) -> None:
	"""Registered on ``release_procurement_package_to_tender`` hook; accepts ``build_release_payload`` shape."""
	if not isinstance(payload, dict):
		frappe.log_error(
			title="Release-to-tender: invalid payload (not a dict)",
			message=json.dumps({"payload_type": type(payload).__name__}),
		)
		return

	package = payload.get("package")
	if not package:
		frappe.log_error(
			title="Release-to-tender: missing package in payload",
			message=json.dumps({"payload_keys": list(payload.keys())}),
		)
		return

	out = release_procurement_package_to_tender(str(package))
	if not out.get("ok"):
		frappe.log_error(
			title="Release-to-tender: tender not created",
			message=json.dumps(
				{
					"package": package,
					"message": str(out.get("message", "")),
					"xmv_findings": out.get("xmv_findings"),
				}
			),
		)
