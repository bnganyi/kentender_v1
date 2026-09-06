# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Post-removal cleanup for the retired ``STD Engine`` module (2026-09-05).

The ``std_engine`` package, its 23 Desk Pages and its 19 DocTypes were deleted
outright. ``bench migrate`` removes orphan Pages on its own, but DocType rows
and the ``Module Def`` row survive a source deletion, so they are dropped here.

Distinct from the older :mod:`retire_std_engine_cleanup`, which retired an
earlier *generation* of the STD module (``STD Template Family`` /
``STD Instance`` / ``STD Generated Output`` and friends). The two share exactly
one DocType name — ``STD Audit Event`` — so every deletion below is guarded by
``frappe.db.exists`` and is a no-op when the older patch already removed it.

Idempotent: safe on sites that never had these DocTypes, and safe to re-run.
"""

from __future__ import annotations

import frappe

RETIRED_MODULE = "STD Engine"

# Dependents before parents; the multi-pass loop below absorbs any residual
# link-field ordering problems rather than relying on this order being perfect.
STD_ENGINE_DOCTYPES_ORDERED: tuple[str, ...] = (
	"STD Validation Finding",
	"STD Validation Run",
	"STD Import Run",
	"STD Usage Binding",
	# Shared name with the older retire_std_engine_cleanup patch — exists-guarded.
	"STD Audit Event",
	"STD Render Block",
	"STD Evaluation Schema",
	"STD Price Schedule Schema",
	"STD Requirement Schema",
	"STD Form Field",
	"STD Form Schema",
	"STD Rule",
	"STD Parameter",
	"STD Source Anchor",
	"STD Source Document",
	"STD Clause",
	"STD Section",
	"STD Version",
	"STD Family",
)


def _delete_custom_docperms() -> None:
	ph = ", ".join(["%s"] * len(STD_ENGINE_DOCTYPES_ORDERED))
	frappe.db.sql(
		f"DELETE FROM `tabCustom DocPerm` WHERE parent IN ({ph})",
		list(STD_ENGINE_DOCTYPES_ORDERED),
	)


def _delete_property_setters() -> None:
	for dt in STD_ENGINE_DOCTYPES_ORDERED:
		frappe.db.delete("Property Setter", {"doc_type": dt})


def _delete_doctypes_multi_pass() -> None:
	remaining = list(STD_ENGINE_DOCTYPES_ORDERED)
	for _ in range(6):
		if not remaining:
			break
		next_remaining: list[str] = []
		for dt in remaining:
			# Guard: the older cleanup patch may already have dropped
			# "STD Audit Event", and a fresh site may never have had any of these.
			if not frappe.db.exists("DocType", dt):
				continue
			try:
				frappe.delete_doc("DocType", dt, force=True, ignore_permissions=True)
			except Exception:
				next_remaining.append(dt)
		remaining = next_remaining
	for dt in remaining:
		frappe.log_error(
			title=f"KenTender retire_std_engine_v2_cleanup: could not delete DocType {dt}",
			message=frappe.get_traceback(),
		)


def _delete_module_def() -> None:
	if frappe.db.exists("Module Def", RETIRED_MODULE):
		frappe.delete_doc("Module Def", RETIRED_MODULE, force=True, ignore_permissions=True)


def execute() -> None:
	_delete_custom_docperms()
	_delete_property_setters()
	_delete_doctypes_multi_pass()
	_delete_module_def()
	frappe.db.commit()
