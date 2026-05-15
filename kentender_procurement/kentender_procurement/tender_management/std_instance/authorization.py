# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Authorization assertions for STD Instance operations (roles, publish lock, addendum).

STDINST-1000.
"""

from __future__ import annotations

import frappe
from frappe import _

from kentender_procurement.tender_management.std_instance.audit import emit_std_instance_event
from kentender_procurement.tender_management.std_instance.events import (
	EVT_STDINST_DENIED_EDIT_ATTEMPT,
)

EDIT_DRAFT_ROLES: frozenset[str] = frozenset({"Procurement Officer", "Procurement Assistant", "System Manager"})
CREATE_INSTANCE_ROLES: frozenset[str] = frozenset({"Procurement Officer", "System Manager"})
GENERATE_OUTPUT_ROLES: frozenset[str] = frozenset({"Procurement Officer", "Procurement Assistant", "System Manager"})
PUBLISH_ROLES: frozenset[str] = frozenset(
	{"Procurement Manager", "Purchase Manager", "System Manager"},
)

PUBLISHED_INSTANCE_STATUSES: frozenset[str] = frozenset({"Published Locked", "Addendum Pending", "Addendum Regenerated"})


def _get_user_roles(user: str | None = None) -> set[str]:
	target_user = user or frappe.session.user
	if not target_user:
		return set()
	try:
		return set(frappe.get_roles(target_user))
	except Exception:
		return set()


def _assert_user_has_any_role(allowed_roles: frozenset[str], *, action_label: str) -> None:
	roles = _get_user_roles()
	if roles.intersection(allowed_roles):
		return
	emit_std_instance_event(
		EVT_STDINST_DENIED_EDIT_ATTEMPT,
		details={
			"action_label": action_label,
			"allowed_roles": sorted(allowed_roles),
			"user_roles": sorted(roles),
		},
		document_name=frappe.session.user or "Guest",
		document_type="User",
		entity="STD_INSTANCE_AUTH",
	)
	frappe.throw(
		_("Not authorized to {0}. Required role: {1}.").format(action_label, ", ".join(sorted(allowed_roles))),
		title=_("STD Authorization Denied"),
	)


class StdAuthorizationService:
	"""Role-based authorization assertions for STD instance operations."""

	@staticmethod
	def assert_can_create_instance(procurement_tender: str) -> None:
		_assert_user_has_any_role(CREATE_INSTANCE_ROLES, action_label=_("create STD Instance"))

	@staticmethod
	def assert_can_edit_draft_instance(instance_name: str, *, attempted_change: str | None = None) -> None:
		doc = frappe.get_doc("Tender STD Instance", instance_name)
		if (doc.instance_status or "").strip() in PUBLISHED_INSTANCE_STATUSES:
			StdAuthorizationService.assert_can_mutate_published(
				instance_name,
				attempted_change=attempted_change or "edit_draft_instance",
			)
		_assert_user_has_any_role(EDIT_DRAFT_ROLES, action_label=_("edit draft STD Instance"))

	@staticmethod
	def assert_can_generate_outputs(instance_name: str, *, attempted_change: str | None = None) -> None:
		doc = frappe.get_doc("Tender STD Instance", instance_name)
		if (doc.instance_status or "").strip() in PUBLISHED_INSTANCE_STATUSES:
			StdAuthorizationService.assert_can_mutate_published(
				instance_name,
				attempted_change=attempted_change or "generate_outputs",
			)
		_assert_user_has_any_role(GENERATE_OUTPUT_ROLES, action_label=_("generate STD outputs"))

	@staticmethod
	def assert_can_publish(instance_name: str) -> None:
		_assert_user_has_any_role(PUBLISH_ROLES, action_label=_("publish/lock STD Instance"))

	@staticmethod
	def assert_can_mutate_published(instance_name: str, *, attempted_change: str | None = None) -> None:
		doc = frappe.get_doc("Tender STD Instance", instance_name)
		status = (doc.instance_status or "").strip()
		if status in PUBLISHED_INSTANCE_STATUSES:
			ac = (attempted_change or "mutate_published_instance").strip()
			from kentender_procurement.tender_management.tender_publication.audit.post_publication_denial import (
				emit_post_publication_edit_denied_audit,
			)

			emit_post_publication_edit_denied_audit(
				instance_code=instance_name,
				attempted_change=ac,
				performed_by=frappe.session.user,
			)
			emit_std_instance_event(
				EVT_STDINST_DENIED_EDIT_ATTEMPT,
				instance_code=instance_name,
				details={
					"reason": "published_locked",
					"instance_status": status,
					"attempted_change": ac,
				},
			)
			frappe.throw(
				_(
					"Published tender content cannot be changed directly after publication. "
					"Use addendum workflow to issue a formal change to the tender package."
				),
				title=_("POST_PUBLICATION_EDIT_DENIED_ADDENDUM_REQUIRED"),
			)
