# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Package completeness (governance spec §9) — single place for Draft→Completed / release gates."""

from __future__ import annotations

from typing import TYPE_CHECKING

import frappe
from frappe import _

if TYPE_CHECKING:
	from frappe.model.document import Document


def get_package_completeness_blockers(doc: "Document") -> list[str]:
	"""Return human-readable blocker strings; empty means complete enough for Completed / release."""
	blockers: list[str] = []
	if not doc.get("template_id"):
		blockers.append(_("Procurement Template is required."))
		return blockers

	if doc.name:
		n = frappe.db.sql(
			"""select count(*) from `tabProcurement Package Line`
			where package_id = %s and ifnull(is_active, 1) = 1""",
			doc.name,
		)[0][0]
	else:
		n = 0
	if not n:
			blockers.append(_("At least one active demand line is required."))

	for field, label in (
		("risk_profile_id", _("Risk Profile")),
		("kpi_profile_id", _("KPI Profile")),
		("vendor_management_profile_id", _("Vendor Management Profile")),
	):
		if not doc.get(field):
			blockers.append(_("{0} is required.").format(label))

	if doc.get("procurement_method") in ("Open Tender", "RFQ") and not doc.get("decision_criteria_profile_id"):
		blockers.append(_("Decision Criteria Profile is required for competitive methods."))

	tpl = frappe.db.get_value(
		"Procurement Template",
		doc.template_id,
		("schedule_required",),
		as_dict=True,
	) if doc.get("template_id") else None
	if tpl and tpl.get("schedule_required"):
		if not doc.get("schedule_start") or not doc.get("schedule_end"):
			blockers.append(_("Schedule start and end are required for this template."))

	return blockers


def is_package_complete(doc: "Document") -> bool:
	return len(get_package_completeness_blockers(doc)) == 0
