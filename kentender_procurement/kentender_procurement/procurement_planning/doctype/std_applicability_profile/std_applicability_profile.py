# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

from __future__ import annotations

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils.data import parse_json
from kentender_procurement.std_engine.state_transition_guard import assert_transition_service_controlled

PROFILE_STATUS = ("Draft", "Validation Blocked", "Approved", "Active", "Suspended", "Retired")
PROCUREMENT_CATEGORIES = ("Works", "Goods", "Services")
IMMUTABLE_ACTIVE_ALLOWED_FIELDS = {"profile_status", "modified", "modified_by"}


class STDApplicabilityProfile(Document):
	def validate(self):
		assert_transition_service_controlled(self, "profile_status")
		self._set_defaults()
		self._validate_enums()
		self._validate_methods()
		self._validate_version_compatibility()
		self._validate_active_immutability()

	def _set_defaults(self):
		if self.profile_status is None or self.profile_status == "":
			self.profile_status = "Draft"

	def _validate_enums(self):
		if self.profile_status not in PROFILE_STATUS:
			frappe.throw(_("Invalid profile status."), title=_("Invalid profile status"))
		if self.procurement_category not in PROCUREMENT_CATEGORIES:
			frappe.throw(
				_("Procurement Category must be one of: Works, Goods, Services."),
				title=_("Invalid procurement category"),
			)

	def _validate_methods(self):
		parsed = parse_json(self.allowed_methods) if isinstance(self.allowed_methods, str) else self.allowed_methods
		if not isinstance(parsed, list) or not parsed:
			frappe.throw(_("Allowed Methods must be a non-empty JSON list."), title=_("Invalid allowed methods"))
		for m in parsed:
			if not isinstance(m, str) or not m.strip():
				frappe.throw(
					_("Allowed Methods entries must be non-empty strings."),
					title=_("Invalid allowed methods"),
				)

	def _validate_version_compatibility(self):
		if not frappe.db.exists("STD Template Version", self.version_code):
			frappe.throw(_("Version Code is not valid."), title=_("Invalid version link"))
		version_category = frappe.db.get_value("STD Template Version", self.version_code, "procurement_category")
		if version_category and version_category != self.procurement_category:
			frappe.throw(
				_("Incompatible applicability profile category for selected version."),
				title=_("Incompatible profile"),
			)

	def _validate_active_immutability(self):
		if self.is_new():
			return
		before = self.get_doc_before_save()
		if not before or before.profile_status != "Active":
			return
		changed = {df.fieldname for df in self.meta.fields if df.fieldname and self.has_value_changed(df.fieldname)}
		disallowed = {f for f in changed if f not in IMMUTABLE_ACTIVE_ALLOWED_FIELDS}
		if disallowed:
			frappe.throw(
				_("Active applicability profiles cannot be edited directly."),
				title=_("Immutable active profile"),
			)

