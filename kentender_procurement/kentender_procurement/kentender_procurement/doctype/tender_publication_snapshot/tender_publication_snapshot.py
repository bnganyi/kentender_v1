# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Tender Publication Snapshot — tender-level publication binding (PUB-0500)."""

from __future__ import annotations

import frappe
from frappe import _
from frappe.model.document import Document

_FROZEN_WHEN_FINAL: tuple[str, ...] = (
	"tm2_tender",
	"procurement_package",
	"tender_std_instance",
	"configuration_snapshot",
	"std_publication_snapshot",
	"source_template_version_code",
	"applicability_profile_code",
	"bundle_output_code",
	"dsm_output_code",
	"dom_output_code",
	"dem_output_code",
	"dcm_output_code",
	"readiness_result_code",
	"approval_decision_code",
	"evidence_package_code",
	"complete_publication_hash",
)


def _strip(value: str | None) -> str:
	return (value or "").strip()


class TenderPublicationSnapshot(Document):
	def validate(self) -> None:
		if self.is_new():
			tm2 = (self.tm2_tender or "").strip()
			if not tm2:
				frappe.throw(
					_("Set TM2 Tender."),
					title=_("Tender Publication Snapshot"),
					exc=frappe.ValidationError,
				)
			return
		prev = frappe.get_doc("Tender Publication Snapshot", self.name)
		prev_st = _strip(prev.snapshot_status)
		if prev_st != "Final":
			return
		for fn in _FROZEN_WHEN_FINAL:
			if _strip(self.get(fn)) != _strip(prev.get(fn)):
				frappe.throw(
					_("Final publication snapshot evidence cannot change ({0}).").format(fn),
					title=_("Tender Publication Snapshot"),
					exc=frappe.ValidationError,
				)
		new_st = _strip(self.snapshot_status)
		if new_st == prev_st:
			return
		if new_st in ("Superseded", "Archived"):
			return
		frappe.throw(
			_("Final publication snapshot cannot change to status {0}.").format(new_st or _("Unknown")),
			title=_("Tender Publication Snapshot"),
			exc=frappe.ValidationError,
		)
