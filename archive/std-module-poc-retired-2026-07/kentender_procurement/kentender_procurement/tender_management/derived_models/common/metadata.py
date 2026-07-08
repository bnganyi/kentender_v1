# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""DERIVED-0100 — Common generated output metadata helpers.

Keep ``OUTPUT_TYPES`` / ``OUTPUT_STATUSES`` in sync with
``Tender STD Generated Output`` Select options and
``std_instance.generated_output`` (single source there for runtime services).
"""

from __future__ import annotations

import frappe
from frappe import _

# Mirror ``std_instance.generated_output.OUTPUT_TYPES`` / DocType output_type options.
OUTPUT_TYPES: frozenset[str] = frozenset({"Bundle", "DSM", "DOM", "DEM", "DCM"})
OUTPUT_STATUSES: frozenset[str] = frozenset(
	{"Draft", "Current", "Published", "Superseded", "Archived", "Stale", "Failed"}
)


def validate_output_type(value: str | None) -> str:
	"""Return stripped output type or throw if invalid."""
	ot = (value or "").strip()
	if ot not in OUTPUT_TYPES:
		frappe.throw(_("Invalid output type."), title=_("STD Generated Output"))
	return ot


def validate_output_status(value: str | None) -> str:
	"""Return stripped output status or throw if invalid."""
	st = (value or "").strip()
	if st not in OUTPUT_STATUSES:
		frappe.throw(_("Invalid output status."), title=_("STD Generated Output"))
	return st


def output_code_from_name(name: str | None) -> str:
	"""Pack ``output_code`` maps to Frappe document name."""
	return (name or "").strip()


def tender_code_for_instance(instance_name: str) -> str:
	"""Business tender reference for denormalized ``tender_code`` on generated output rows."""
	if not instance_name or not frappe.db.exists("Tender STD Instance", instance_name):
		return ""
	tender = frappe.db.get_value("Tender STD Instance", instance_name, "tm2_tender")
	if not tender:
		return ""
	ref = frappe.db.get_value("TM2 Tender", tender, "tender_reference")
	return (ref or "").strip()
