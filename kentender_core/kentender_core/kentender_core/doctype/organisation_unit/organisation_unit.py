# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

from __future__ import annotations

import frappe
from frappe.model.naming import make_autoname
from frappe.utils.nestedset import NestedSet


class OrganisationUnit(NestedSet):
	"""The one organisational hierarchy KenTender business scope resolves against.

	AUTH-ADR-001 v1.6 §4.2 makes this a site-local Frappe nested set: one site
	is exactly one Procuring Entity, so exactly one root exists (named for the
	site PE) and every unit belongs to the site by construction — there is no
	`procuring_entity` dimension in the contract. An OU-scoped responsibility
	assignment covers its node and every descendant through a single
	`lft`/`rgt` range predicate.

	`validate_one_root` from the framework is not used because it depends on
	`is_group`; the single-root rule here is explicit: a second parentless
	unit is refused while a root exists.
	"""

	nsm_parent_field = "parent_organisation_unit"

	def validate(self):
		if not (self.org_unit_reference or "").strip():
			self.org_unit_reference = make_autoname("OU-.########")
		if not self.status:
			self.status = "Active"
		self._validate_single_root()

	def _validate_single_root(self):
		if self.parent_organisation_unit:
			if self.parent_organisation_unit == self.name:
				frappe.throw("Organisation Unit cannot be its own parent.")
			return
		# The governed repair recreates a missing root while orphaned subtree
		# tops are still parentless; it adopts them immediately afterwards in
		# the same transaction (site_configuration._ensure_root_unit).
		if getattr(self.flags, "kt_repair_root", False):
			return
		other_root = frappe.db.get_value(
			"Organisation Unit",
			{"parent_organisation_unit": ("is", "not set"), "name": ("!=", self.name or "")},
			"name",
		)
		if other_root:
			frappe.throw(
				"Exactly one root organisation unit exists per site. "
				"Add this unit beneath the existing structure instead.",
				title="Invalid organisation hierarchy",
			)
