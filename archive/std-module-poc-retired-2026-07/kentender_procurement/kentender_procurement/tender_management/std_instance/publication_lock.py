# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Publication and approval locks — ``StdPublicationLockService``.

STDINST-0600.
"""

from __future__ import annotations

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import now_datetime

from kentender_procurement.tender_management.std_instance.audit import emit_std_instance_event
from kentender_procurement.tender_management.std_instance.events import (
	EVT_STDINST_PUBLICATION_LOCK_APPLIED,
)
from kentender_procurement.tender_management.std_instance.snapshot import (
	assert_final_publication_snapshot_exists,
)
from kentender_procurement.tender_management.std_instance.state import StdInstanceStateService

EDITABLE_INSTANCE_STATUSES: frozenset[str] = frozenset(
	{"Draft", "In Configuration", "Validation Blocked", "Ready for Publication"}
)

NON_EDITABLE_INSTANCE_STATUSES: frozenset[str] = frozenset(
	{
		"Locked for Approval",
		"Published Locked",
		"Addendum Pending",
		"Addendum Regenerated",
		"Superseded",
		"Cancelled",
	}
)

ADDENDUM_REQUIRED_INSTANCE_STATUSES: frozenset[str] = frozenset(
	{"Published Locked", "Addendum Pending", "Addendum Regenerated"}
)


class StdPublicationLockService:
	"""Publication/approval locks for ``Tender STD Instance`` lifecycle mutations."""

	@staticmethod
	def assert_editable(instance_name: str, *, operation_label: str = "edit") -> Document:
		doc = frappe.get_doc("Tender STD Instance", instance_name)
		status = (doc.instance_status or "").strip()

		if status in EDITABLE_INSTANCE_STATUSES:
			return doc

		if status in ADDENDUM_REQUIRED_INSTANCE_STATUSES:
			StdPublicationLockService.assert_addendum_required(
				instance_name,
				attempted_change=operation_label,
			)

		if status in NON_EDITABLE_INSTANCE_STATUSES:
			cat = (doc.get("procurement_category") or "").strip()
			if cat == "WORKS":
				try:
					from kentender_procurement.tender_management.works_completion.audit import (
						WORKS_EDIT_DENIED_LOCKED,
						emit_works_completion_audit,
					)

					emit_works_completion_audit(
						WORKS_EDIT_DENIED_LOCKED,
						instance_name,
						details={
							"reason": "std_instance_not_editable",
							"operation": operation_label,
							"instance_status": status,
						},
					)
				except Exception:
					pass
			frappe.throw(
				_("STD Instance cannot {0} while status is {1}.").format(operation_label, status),
				title=_("STD Instance Locked"),
			)

		frappe.throw(
			_("STD Instance cannot {0} while status is {1}.").format(operation_label, status or "Unknown"),
			title=_("STD Instance Locked"),
		)
		return doc

	@staticmethod
	def assert_addendum_required(instance_name: str, *, attempted_change: str | None = None) -> None:
		status = (frappe.db.get_value("Tender STD Instance", instance_name, "instance_status") or "").strip()
		if status in ADDENDUM_REQUIRED_INSTANCE_STATUSES:
			from kentender_procurement.tender_management.std_instance.authorization import (
				StdAuthorizationService,
			)

			StdAuthorizationService.assert_can_mutate_published(
				instance_name,
				attempted_change=attempted_change or "mutate_after_publication",
			)

	@staticmethod
	def lock_for_approval(
		instance_name: str,
		*,
		user: str | None = None,
		ignore_permissions: bool = True,
	) -> Document:
		from kentender_procurement.tender_management.std_instance.authorization import (
			StdAuthorizationService,
		)

		StdAuthorizationService.assert_can_publish(instance_name)
		StdPublicationLockService.assert_editable(instance_name, operation_label="lock for approval")
		doc = StdInstanceStateService.apply_transition(
			instance_name,
			"Locked for Approval",
			ignore_permissions=ignore_permissions,
		)
		doc.locked_for_approval_at = now_datetime()
		doc.locked_for_approval_by = user or frappe.session.user
		doc.save(ignore_permissions=ignore_permissions)
		emit_std_instance_event(
			EVT_STDINST_PUBLICATION_LOCK_APPLIED,
			instance_code=instance_name,
			details={"lock_type": "approval", "status": doc.instance_status},
		)
		return doc

	@staticmethod
	def lock_for_publication(
		instance_name: str,
		*,
		user: str | None = None,
		ignore_permissions: bool = True,
	) -> Document:
		from kentender_procurement.tender_management.std_instance.authorization import (
			StdAuthorizationService,
		)

		StdAuthorizationService.assert_can_publish(instance_name)
		assert_final_publication_snapshot_exists(instance_name)
		doc = StdInstanceStateService.apply_transition(
			instance_name,
			"Published Locked",
			ignore_permissions=ignore_permissions,
		)
		doc.published_locked_at = now_datetime()
		doc.published_locked_by = user or frappe.session.user
		doc.save(ignore_permissions=ignore_permissions)
		emit_std_instance_event(
			EVT_STDINST_PUBLICATION_LOCK_APPLIED,
			instance_code=instance_name,
			details={"lock_type": "publication", "status": doc.instance_status},
		)
		return doc
