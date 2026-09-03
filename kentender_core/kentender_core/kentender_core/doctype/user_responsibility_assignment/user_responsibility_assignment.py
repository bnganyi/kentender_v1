# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""AUTH-ADR-001 v1.6 §4.5 — the sole authority for KenTender business scope.

One record answers one complete question: which business responsibility may
this user exercise, for which organisational scope, and during what effective
period. The site is exactly one Procuring Entity, so scope is either the whole
site or one Organisation Unit subtree — no Procuring Entity dimension exists.

This controller holds only the invariants that belong to the record itself.
Overlap, exclusive office, the actor's own grant authority and the Frappe Role
projection are the administration service's work, because each of them spans
more than one record and has to happen inside one transaction (§9.2).
"""

from __future__ import annotations

import frappe
from frappe.model.document import Document
from frappe.utils import get_datetime

from kentender_core.services.business_role_registry import require_registered
from kentender_core.services.authorization import (
	APPOINTMENT_ACTING,
	STATUS_ENABLED,
)


class UserResponsibilityAssignment(Document):
	def validate(self):
		entry = require_registered(self.business_role)
		self._validate_scope(entry)
		self._validate_period()
		self._validate_appointment()

	def _validate_scope(self, entry):
		"""§4.5 — an Organisation Unit is required for OU-scoped roles and
		prohibited for Site-wide roles. No other scope dimension exists."""
		if entry.requires_organisation_unit and not self.organisation_unit:
			frappe.throw(
				f"{self.business_role} is scoped to a department, so an Organisation Unit must be selected.",
				title="Incomplete responsibility scope",
			)
		if not entry.requires_organisation_unit and self.organisation_unit:
			frappe.throw(
				f"{self.business_role} is a site-wide responsibility and cannot name an Organisation Unit.",
				title="Invalid responsibility scope",
			)

	def _validate_period(self):
		"""§4.5 — `effective_to` is optional but must be later than `effective_from`."""
		if self.effective_from and self.effective_to:
			if get_datetime(self.effective_to) <= get_datetime(self.effective_from):
				frappe.throw(
					"The end of the effective period must be later than its start.",
					title="Invalid effective period",
				)

	def _validate_appointment(self):
		"""§4.5 — an acting appointment must cite the instrument appointing it.

		Appointment type changes evidence, not capability: an acting officer
		receives exactly the same responsibility and scope as the substantive
		one (§4.3 descendant rule aside), so nothing else here branches on it.
		"""
		if self.appointment_type == APPOINTMENT_ACTING and not (self.authority_reference or "").strip():
			frappe.throw(
				"An acting appointment requires the authority reference that appoints it.",
				title="Authority reference required",
			)

	def is_effective(self, at=None) -> bool:
		"""Only `Enabled` within its effective period authorizes (§4.6).

		Expiry is evaluated here, at command time, rather than trusted from a
		stored display status: §4.6 makes a scheduled job a display and
		projection convenience, never the security control, so an assignment
		whose `effective_to` has passed stops authorizing even if no job has
		yet reconciled its Role projection.
		"""
		if self.status != STATUS_ENABLED:
			return False
		at = get_datetime(at or frappe.utils.now_datetime())
		if self.effective_from and get_datetime(self.effective_from) > at:
			return False
		if self.effective_to and get_datetime(self.effective_to) < at:
			return False
		return True
