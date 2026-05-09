# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Controller for Tender STD Instance — STDINST-0100 aggregate validation."""

from __future__ import annotations

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import now_datetime

from kentender_procurement.tender_management.std_instance.instance import (
	INSTANCE_STATUS_RELEASES_SLOT,
	is_valid_instance_status,
	is_valid_readiness_status,
)
from kentender_procurement.tender_management.std_instance.attachment import (
	assert_no_duplicate_attachment_codes,
	assert_published_attachment_rows_honored,
	assert_section_attachment_rows_bound,
	section_attachments_snapshot,
	StdInstanceAttachmentService,
)
from kentender_procurement.tender_management.std_instance.parameter import (
	assert_locked_parameter_rows_not_mutated,
	assert_no_duplicate_parameter_codes,
	parameter_values_snapshot,
	StdInstanceParameterService,
)
from kentender_procurement.tender_management.std_instance.works_requirement import (
	assert_no_duplicate_component_codes,
	assert_no_duplicate_requirement_codes,
	assert_works_requirement_rows_have_component_code,
	works_requirements_snapshot,
	StdInstanceWorksRequirementService,
)
from kentender_procurement.tender_management.std_instance.state import StdInstanceStateService


class TenderSTDInstance(Document):
	def before_insert(self) -> None:
		if not self.created_by:
			self.created_by = frappe.session.user
		if not self.created_at:
			self.created_at = now_datetime()

	def validate(self) -> None:
		self._validate_tender_context()
		self._validate_status_enums()
		self._validate_instance_status_transition()
		self._validate_procurement_tender_immutable()
		self._validate_parameter_value_rules()
		self._validate_section_attachment_rules()
		self._validate_works_requirement_rules()
		if self.is_new():
			self._validate_single_active_instance_per_tender_on_insert()

	def _validate_instance_status_transition(self) -> None:
		if self.is_new():
			self._prev_instance_status_audit = None
			return
		prev = frappe.db.get_value("Tender STD Instance", self.name, "instance_status")
		self._prev_instance_status_audit = prev
		if prev != self.instance_status:
			StdInstanceStateService.assert_transition_allowed(prev, self.instance_status)

	def on_update(self) -> None:
		prev = getattr(self, "_prev_instance_status_audit", None)
		if prev is not None and prev != self.instance_status:
			self.add_comment(
				comment_type="Comment",
				text=_("Instance status: {0} → {1} (user {2})").format(
					prev,
					self.instance_status,
					frappe.session.user,
				),
				comment_by=frappe.session.user,
			)

	def _validate_tender_context(self) -> None:
		if not self.created_from_tender_context:
			frappe.throw(
				_("STD Instances may only be created from a Tender context."),
				title=_("STD Instance Orphan Creation Denied"),
			)

	def _validate_status_enums(self) -> None:
		if not is_valid_instance_status(self.instance_status):
			frappe.throw(_("Invalid Instance Status: {0}").format(self.instance_status))
		if not is_valid_readiness_status(self.readiness_status):
			frappe.throw(_("Invalid Readiness Status: {0}").format(self.readiness_status))

	def _validate_works_requirement_rules(self) -> None:
		assert_no_duplicate_requirement_codes(self)
		assert_no_duplicate_component_codes(self)
		assert_works_requirement_rows_have_component_code(self)
		if self.is_new():
			return
		prev_doc = frappe.get_doc("Tender STD Instance", self.name)
		if getattr(self.flags, "ignore_works_requirement_publication_lock", False):
			return
		if not StdInstanceWorksRequirementService.status_blocks_works_requirement_edits(self.instance_status):
			return
		if works_requirements_snapshot(prev_doc) != works_requirements_snapshot(self):
			frappe.throw(
				_(
					"Works requirements cannot be changed while Instance Status is {0}. "
					"Use an addendum workflow when implemented."
				).format(self.instance_status),
				title=_("STD Works Requirements Locked"),
			)

	def _validate_section_attachment_rules(self) -> None:
		assert_no_duplicate_attachment_codes(self)
		assert_section_attachment_rows_bound(self)
		if self.is_new():
			return
		prev_doc = frappe.get_doc("Tender STD Instance", self.name)
		assert_published_attachment_rows_honored(prev_doc, self)
		if getattr(self.flags, "ignore_attachment_publication_lock", False):
			return
		if not StdInstanceAttachmentService.status_blocks_attachment_edits(self.instance_status):
			return
		if section_attachments_snapshot(prev_doc) != section_attachments_snapshot(self):
			frappe.throw(
				_(
					"STD section attachments cannot be changed while Instance Status is {0}. "
					"Use an addendum workflow when implemented."
				).format(self.instance_status),
				title=_("STD Attachments Locked"),
			)

	def _validate_parameter_value_rules(self) -> None:
		assert_no_duplicate_parameter_codes(self)
		if self.is_new():
			return
		prev_doc = frappe.get_doc("Tender STD Instance", self.name)
		assert_locked_parameter_rows_not_mutated(prev_doc, self)
		if getattr(self.flags, "ignore_parameter_publication_lock", False):
			return
		if not StdInstanceParameterService.status_blocks_parameter_edits(self.instance_status):
			return
		if parameter_values_snapshot(prev_doc) != parameter_values_snapshot(self):
			frappe.throw(
				_(
					"STD parameter values cannot be changed while Instance Status is {0}. "
					"Use an addendum workflow when implemented."
				).format(self.instance_status),
				title=_("STD Parameters Locked"),
			)

	def _validate_procurement_tender_immutable(self) -> None:
		if self.is_new():
			return
		prev = frappe.db.get_value(
			"Tender STD Instance",
			self.name,
			"procurement_tender",
		)
		if prev and prev != self.procurement_tender:
			frappe.throw(
				_("Procurement Tender cannot be changed after creation."),
				title=_("STD Instance Tender Immutable"),
			)

	def _validate_single_active_instance_per_tender_on_insert(self) -> None:
		if not self.procurement_tender:
			return
		others = frappe.get_all(
			"Tender STD Instance",
			filters={
				"procurement_tender": self.procurement_tender,
				"instance_status": ["not in", list(INSTANCE_STATUS_RELEASES_SLOT)],
			},
			pluck="name",
		)
		if others:
			frappe.throw(
				_("Another active STD Instance already exists for this tender: {0}").format(
					", ".join(others)
				),
				title=_("Duplicate STD Instance"),
			)
