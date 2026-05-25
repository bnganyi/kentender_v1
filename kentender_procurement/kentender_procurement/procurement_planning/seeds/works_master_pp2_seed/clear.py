# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P3-003 — PP2 WORKS master planning seed clear/reset (dev/test only, R2-002 pattern)."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cint

from kentender_procurement.procurement_planning.seeds.works_master_pp2_seed.constants import (
	INCLUSION_CODE,
	JOURNEY_CODE,
	PKGREL_CODE,
	PKG_CODE,
	PKG_LINE_CODE,
	PLAN_CODE,
)

_MASTER_HANDOFF_CODES: tuple[str, ...] = (
	INCLUSION_CODE,
	PKGREL_CODE,
)
_PKG_CHILD_DOCTYPES: tuple[tuple[str, str], ...] = (
	("Package Review Decision", "package_code"),
	("Package Readiness Result", "package_code"),
	("Package Method Decision", "package_code"),
	("Planning Correction Supersession Record", "package_code"),
)


def _dev_or_test_clear_allowed() -> bool:
	if frappe.in_test:
		return True
	if getattr(frappe.conf, "developer_mode", False):
		return True
	if getattr(frappe.conf, "allow_tests", False):
		return True
	return False


def _blocked_response() -> dict[str, Any]:
	return {
		"ok": False,
		"error_code": "SEED_CLEAR_BLOCKED",
		"message": (
			"clear_procurement_planning_works_master_seed is allowed only in development/test "
			"(frappe.in_test, developer_mode, or allow_tests)."
		),
	}


def _has_master_seed_field(doctype: str) -> bool:
	return bool(frappe.get_meta(doctype).has_field("is_master_seed"))


def _is_master_seed_row(doctype: str, name: str) -> bool:
	if not frappe.db.exists(doctype, name):
		return False
	if not _has_master_seed_field(doctype):
		return True
	return cint(frappe.db.get_value(doctype, name, "is_master_seed")) == 1


def run_clear(*, skip_guard: bool = False) -> dict[str, Any]:
	"""Delete WORKS master planning seed rows (allowlisted codes; plan/inclusion gated by ``is_master_seed``)."""
	frappe.set_user("Administrator")
	if not skip_guard and not _dev_or_test_clear_allowed():
		return _blocked_response()

	gate_master_seed = not skip_guard
	deleted: dict[str, int] = {}
	cleared_codes: list[str] = []

	def _delete_doctype(
		doctype: str,
		name: str,
		*,
		code_label: str | None = None,
		require_master_seed: bool = False,
	) -> None:
		if not frappe.db.exists(doctype, name):
			return
		if require_master_seed and not _is_master_seed_row(doctype, name):
			return
		frappe.delete_doc(doctype, name, force=True, ignore_permissions=True)
		deleted[doctype] = deleted.get(doctype, 0) + 1
		if code_label:
			cleared_codes.append(code_label)

	def _delete_package_line(name: str) -> None:
		if not frappe.db.exists("Procurement Package Line", name):
			return
		frappe.flags.skip_package_line_rollup = True
		try:
			frappe.delete_doc("Procurement Package Line", name, force=True, ignore_permissions=True)
			deleted["Procurement Package Line"] = deleted.get("Procurement Package Line", 0) + 1
		finally:
			frappe.flags.pop("skip_package_line_rollup", None)

	def _delete_master_handoff(handoff_code: str) -> None:
		if handoff_code not in _MASTER_HANDOFF_CODES:
			return
		if not frappe.db.exists("Procurement Handoff Card", handoff_code):
			return
		if handoff_code == PKGREL_CODE:
			source_code = (
				frappe.db.get_value("Procurement Handoff Card", handoff_code, "source_object_code") or ""
			).strip()
			if source_code != PKG_CODE:
				return
			_delete_doctype("Procurement Handoff Card", handoff_code, code_label=handoff_code)
			return
		_delete_doctype(
			"Procurement Handoff Card",
			handoff_code,
			code_label=handoff_code,
			require_master_seed=gate_master_seed,
		)

	for name in frappe.get_all(
		"Planning Release Consumption Record",
		filters={"consumption_code": ["like", "PKGCONSUME-MOH-2026-%"]},
		pluck="name",
	):
		_delete_doctype("Planning Release Consumption Record", name)

	for name in frappe.get_all(
		"Planning Release Consumption Record",
		filters={"release_code": PKGREL_CODE, "package_code": PKG_CODE},
		pluck="name",
	):
		_delete_doctype("Planning Release Consumption Record", name)

	for doctype, filter_field in _PKG_CHILD_DOCTYPES:
		for name in frappe.get_all(doctype, filters={filter_field: PKG_CODE}, pluck="name"):
			_delete_doctype(doctype, name)

	line_name = frappe.db.get_value(
		"Procurement Package Line", {"package_line_code": PKG_LINE_CODE}, "name"
	)
	if line_name:
		_delete_package_line(line_name)
		cleared_codes.append(PKG_LINE_CODE)

	for line_name in frappe.get_all(
		"Procurement Package Line",
		filters={"package_id": PKG_CODE},
		pluck="name",
	):
		_delete_package_line(line_name)

	inclusion = frappe.db.get_value("Procurement Handoff Card", INCLUSION_CODE, "locked_summary")
	if inclusion:
		locked = frappe.parse_json(inclusion)
		if isinstance(locked, dict):
			orphan = (locked.get("created_package_code") or "").strip()
			if orphan and orphan != PKG_CODE and frappe.db.exists("Procurement Package", orphan):
				if not gate_master_seed or _is_master_seed_row("Procurement Package", orphan):
					for line_name in frappe.get_all(
						"Procurement Package Line",
						filters={"package_id": orphan},
						pluck="name",
					):
						_delete_package_line(line_name)
					_delete_doctype(
						"Procurement Package",
						orphan,
						code_label=orphan,
						require_master_seed=gate_master_seed,
					)

	_delete_doctype(
		"Procurement Package",
		PKG_CODE,
		code_label=PKG_CODE,
		require_master_seed=gate_master_seed,
	)

	for handoff_code in _MASTER_HANDOFF_CODES:
		_delete_master_handoff(handoff_code)

	_delete_doctype(
		"Procurement Plan",
		PLAN_CODE,
		code_label=PLAN_CODE,
		require_master_seed=gate_master_seed,
	)

	for event_code in frappe.get_all(
		"Planning Audit Event",
		filters={"journey_code": JOURNEY_CODE, "is_master_seed": 1},
		pluck="name",
	):
		_delete_doctype("Planning Audit Event", event_code)

	frappe.db.commit()
	return {"ok": True, "deleted": deleted, "cleared_codes": cleared_codes}
