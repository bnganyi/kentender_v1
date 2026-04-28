# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

from __future__ import annotations

import json
from datetime import datetime

import frappe
from frappe import _
from frappe.model.document import Document

VERSION_STATUS = (
	"Draft",
	"Structure In Progress",
	"Validation Blocked",
	"Validation Passed",
	"Legal Review Pending",
	"Approved",
	"Active",
	"Suspended",
	"Superseded",
	"Retired",
	"Archived",
)
REVIEW_STATUS = ("Not Required", "Pending", "Returned", "Approved")
STRUCTURE_VALIDATION_STATUS = ("Not Run", "Pass", "Fail")
PROCUREMENT_CATEGORIES = ("Works", "Goods", "Services")
ACTIVE_IMMUTABLE_ALLOWED_FIELDS = {
	"version_status",
	"is_current_active_version",
	"superseded_by_version_code",
	"retired_at",
	"retired_by",
	"modified",
	"modified_by",
}


class STDTemplateVersion(Document):
	def validate(self):
		self._set_defaults()
		self._validate_status_fields()
		self._validate_links_and_category_alignment()
		self._validate_current_active_consistency()
		self._validate_active_immutability()

	def on_trash(self):
		if self._is_referenced_by_std_instance():
			frappe.throw(
				_(
					"Cannot delete STD Template Version {0} because it is referenced by an STD instance."
				).format(self.version_code),
				title=_("Delete blocked"),
			)

	def after_insert(self):
		self._emit_audit_event("TEMPLATE_VERSION_CREATED")

	def on_update(self):
		if self.has_value_changed("version_status"):
			self._emit_audit_event("TEMPLATE_VERSION_STATUS_CHANGED")

	def _set_defaults(self):
		if self.immutable_after_activation is None:
			self.immutable_after_activation = 1
		if self.is_current_active_version is None:
			self.is_current_active_version = 0
		if not self.version_status:
			self.version_status = "Draft"
		if not self.legal_review_status:
			self.legal_review_status = "Pending"
		if not self.policy_review_status:
			self.policy_review_status = "Pending"
		if not self.structure_validation_status:
			self.structure_validation_status = "Not Run"
		if self.version_status == "Active" and not self.activated_at:
			self.activated_at = datetime.utcnow()
		if self.version_status == "Active" and not self.activated_by:
			self.activated_by = frappe.session.user

	def _validate_status_fields(self):
		if self.procurement_category not in PROCUREMENT_CATEGORIES:
			frappe.throw(
				_("Procurement Category must be one of: Works, Goods, Services."),
				title=_("Invalid procurement category"),
			)
		if self.version_status not in VERSION_STATUS:
			frappe.throw(_("Invalid version status."), title=_("Invalid version status"))
		if self.legal_review_status not in REVIEW_STATUS:
			frappe.throw(_("Invalid legal review status."), title=_("Invalid legal review status"))
		if self.policy_review_status not in REVIEW_STATUS:
			frappe.throw(_("Invalid policy review status."), title=_("Invalid policy review status"))
		if self.structure_validation_status not in STRUCTURE_VALIDATION_STATUS:
			frappe.throw(
				_("Invalid structure validation status."),
				title=_("Invalid structure validation status"),
			)

	def _validate_links_and_category_alignment(self):
		if not frappe.db.exists("STD Template Family", self.template_code):
			frappe.throw(_("Template Code is not valid."), title=_("Invalid template family"))
		if not frappe.db.exists("Source Document Registry", self.source_document_code):
			frappe.throw(
				_("Source Document Code is not valid."),
				title=_("Invalid source document"),
			)
		template_category = frappe.db.get_value("STD Template Family", self.template_code, "procurement_category")
		source_category = frappe.db.get_value(
			"Source Document Registry", self.source_document_code, "procurement_category"
		)
		if template_category and template_category != self.procurement_category:
			frappe.throw(
				_("Procurement Category must match STD Template Family."),
				title=_("Category mismatch"),
			)
		if source_category and source_category != self.procurement_category:
			frappe.throw(
				_("Procurement Category must match Source Document Registry."),
				title=_("Category mismatch"),
			)
		if self.version_status == "Active":
			family_active = frappe.db.get_value("STD Template Family", self.template_code, "is_active_family")
			if not int(family_active or 0):
				frappe.throw(
					_("Only active template families may be used by active template versions."),
					title=_("Inactive template family"),
				)
		if self.supersedes_version_code and not frappe.db.exists(
			"STD Template Version", self.supersedes_version_code
		):
			frappe.throw(
				_("Supersedes Version Code is not valid."),
				title=_("Invalid version lineage"),
			)
		if self.superseded_by_version_code and not frappe.db.exists(
			"STD Template Version", self.superseded_by_version_code
		):
			frappe.throw(
				_("Superseded By Version Code is not valid."),
				title=_("Invalid version lineage"),
			)

	def _validate_current_active_consistency(self):
		if self.is_current_active_version and self.version_status != "Active":
			frappe.throw(
				_("If is_current_active_version is enabled, Version Status must be Active."),
				title=_("Invalid active version state"),
			)

	def _validate_active_immutability(self):
		if self.is_new():
			return
		before = self.get_doc_before_save()
		if not before:
			return
		if before.version_status != "Active" or not int(before.immutable_after_activation or 0):
			return
		changed = {
			df.fieldname
			for df in self.meta.fields
			if df.fieldname and self.has_value_changed(df.fieldname)
		}
		disallowed = {f for f in changed if f not in ACTIVE_IMMUTABLE_ALLOWED_FIELDS}
		if disallowed:
			frappe.throw(
				_(
					"Active immutable template versions cannot be directly edited outside approved transition fields."
				),
				title=_("Immutable active version"),
			)

	def _is_referenced_by_std_instance(self) -> bool:
		if not frappe.db.exists("DocType", "STD Instance"):
			return False
		columns = set(frappe.db.get_table_columns("STD Instance"))
		if "template_version_code" in columns:
			filters = {"template_version_code": self.version_code}
		elif "std_template_version_code" in columns:
			filters = {"std_template_version_code": self.version_code}
		else:
			return False
		return bool(frappe.db.exists("STD Instance", filters))

	def _emit_audit_event(self, event_type: str):
		frappe.logger("std_engine_audit").info(
			json.dumps(
				{
					"event_type": event_type,
					"doctype": "STD Template Version",
					"name": self.name,
					"version_code": self.version_code,
					"version_status": self.version_status,
				}
			)
		)

