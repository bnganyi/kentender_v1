# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

from __future__ import annotations

import json

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils.data import parse_json

ALLOWED_STATUS = (
	"Draft",
	"Under Review",
	"Approved",
	"Active",
	"Suspended",
	"Archived",
)
ALLOWED_PROCUREMENT_CATEGORIES = ("Works", "Goods", "Services")


class STDTemplateFamily(Document):
	def validate(self):
		self._set_defaults()
		self._validate_procurement_category()
		self._validate_allowed_methods()
		self._validate_active_state_consistency()
		self._validate_archive_dependencies()

	def after_insert(self):
		self._emit_audit_event("TEMPLATE_FAMILY_CREATED")

	def on_update(self):
		if self.has_value_changed("family_status"):
			self._emit_audit_event("TEMPLATE_FAMILY_STATUS_CHANGED")

	def _set_defaults(self):
		if not self.default_language:
			self.default_language = "English"
		if self.is_active_family is None:
			self.is_active_family = 0
		if not self.family_status:
			self.family_status = "Draft"

	def _validate_procurement_category(self):
		if self.procurement_category not in ALLOWED_PROCUREMENT_CATEGORIES:
			frappe.throw(
				_("Procurement Category must be one of: Works, Goods, Services."),
				title=_("Invalid procurement category"),
			)
		if self.family_status not in ALLOWED_STATUS:
			frappe.throw(
				_(
					"Family Status must be one of: Draft, Under Review, Approved, Active, Suspended, Archived."
				),
				title=_("Invalid family status"),
			)

	def _validate_allowed_methods(self):
		parsed = (
			parse_json(self.allowed_procurement_methods)
			if isinstance(self.allowed_procurement_methods, str)
			else self.allowed_procurement_methods
		)
		if not isinstance(parsed, list) or not parsed:
			frappe.throw(
				_("Allowed Procurement Methods must be a non-empty JSON list."),
				title=_("Invalid allowed methods"),
			)
		for method in parsed:
			if not isinstance(method, str) or not method.strip():
				frappe.throw(
					_("Allowed Procurement Methods entries must be non-empty strings."),
					title=_("Invalid allowed methods"),
				)

	def _validate_active_state_consistency(self):
		if self.is_active_family and self.family_status != "Active":
			frappe.throw(
				_("is_active_family can only be enabled when Family Status is Active."),
				title=_("Invalid active family state"),
			)

	def _validate_archive_dependencies(self):
		if self.family_status != "Archived":
			return
		if self._has_active_template_version_dependency():
			frappe.throw(
				_(
					"Cannot archive this template family while it has active template version dependencies."
				),
				title=_("Archive blocked"),
			)

	def _has_active_template_version_dependency(self) -> bool:
		if not frappe.db.exists("DocType", "STD Template Version"):
			return False
		columns = set(frappe.db.get_table_columns("STD Template Version"))
		filters: dict[str, object] = {}
		if "template_code" in columns:
			filters["template_code"] = self.template_code
		elif "template_family_code" in columns:
			filters["template_family_code"] = self.template_code
		else:
			return False
		if "version_status" in columns:
			filters["version_status"] = "Active"
		return bool(frappe.db.exists("STD Template Version", filters))

	def _emit_audit_event(self, event_type: str):
		frappe.logger("std_engine_audit").info(
			json.dumps(
				{
					"event_type": event_type,
					"doctype": "STD Template Family",
					"name": self.name,
					"template_code": self.template_code,
					"family_status": self.family_status,
				}
			)
		)

