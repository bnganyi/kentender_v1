# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""BUD v1.12 §6 / BUD18-AC-062 (AUD-BUD-002) — one immutable record per
submission attempt of a Budget Version: the evidence and every line exactly as
submitted, then the single decision on that attempt. Written by
`budget_readiness_contracts` only; the submitted content never changes and the
decision is set once, so a later return/edit/resubmit cannot overwrite what an
earlier attempt carried or how it was decided."""

from __future__ import annotations

import frappe
from frappe import _
from frappe.model.document import Document

from kentender_core.services.command_write_guard import CommandWriteGuardMixin
from kentender_budget.services.budget_write_family import BUDGET_WRITE_FAMILY

_CONTENT_FIELDS = (
	"budget_version", "budget", "attempt_number", "submitted_by", "submitted_at", "approval_reference",
	"approval_date", "authorised_total", "currency", "revision_type", "approval_document", "lines_snapshot",
)


class BudgetSubmissionAttempt(CommandWriteGuardMixin, Document):
	command_write_family = BUDGET_WRITE_FAMILY

	def validate(self):
		super().validate()
		before = self.get_doc_before_save()
		if not before:
			if self.outcome != "Submitted":
				frappe.throw(_("A submission attempt starts as Submitted."), frappe.ValidationError)
			return
		for field in _CONTENT_FIELDS:
			if str(self.get(field) or "") != str(before.get(field) or ""):
				frappe.throw(_("A submitted attempt cannot be changed."), frappe.ValidationError, title="BUDGET_ATTEMPT_IMMUTABLE")
		if before.outcome != "Submitted" and (
			self.outcome != before.outcome
			or (self.decided_by or "") != (before.decided_by or "")
			or (self.return_reason or "") != (before.return_reason or "")
		):
			frappe.throw(_("The decision on a submission attempt is set once."), frappe.ValidationError, title="BUDGET_ATTEMPT_IMMUTABLE")

	def on_trash(self):
		if frappe.flags.in_migrate or frappe.flags.in_install:
			return
		super().on_trash()
