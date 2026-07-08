# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""STD template governance — lifecycle transitions (doc 7 §13.3, §14, STD-GOV-007).

Role gates follow **doc 3** (matrix) aligned with **doc 7 §14** shorthand. Saves use
``ignore_permissions=True`` after explicit role checks because DocPerms for governance roles
may lag GOV-010.
"""

from __future__ import annotations

from typing import Any

import frappe
from frappe import _
from frappe.utils import getdate, now_datetime

from kentender_procurement.tender_management.services.std_template_governance import (
	EVT_ACTIVATED,
	EVT_APPROVED,
	EVT_ARCHIVED,
	EVT_OVERRIDE_USED,
	EVT_REJECTED,
	EVT_RETIRED,
	EVT_RETURNED,
	EVT_REINSTATED,
	EVT_SUBMITTED,
	EVT_SUPERSEDED,
	EVT_SUSPENDED,
	STATUS_ACTIVE,
	STATUS_APPROVED,
	STATUS_ARCHIVED,
	STATUS_REJECTED,
	STATUS_RETIRED,
	STATUS_RETURNED,
	STATUS_SUBMITTED,
	STATUS_SUPERSEDED,
	STATUS_SUSPENDED,
	STATUS_VALIDATED,
	VALIDATION_PASS,
	VALIDATION_PASS_WARNINGS,
)
from kentender_procurement.tender_management.services.std_template_governance_events import (
	write_std_template_lifecycle_event,
)
from kentender_procurement.tender_management.services.std_template_governance_usage import (
	get_std_template_usage_impact,
)
from kentender_procurement.tender_management.security.authorization.integration import (
	enforce_sec_authorization,
)

ROLE_STD_TEMPLATE_ADMINISTRATOR = "STD Template Administrator"
ROLE_STD_TEMPLATE_APPROVER = "STD Template Approver"
ROLE_STD_TEMPLATE_REVIEWER = "STD Template Reviewer"
ROLE_STD_TEMPLATE_ACTIVATOR = "STD Template Activator"
ROLE_SYSTEM_MANAGER = "System Manager"


def _json_safe_usage_impact(impact: dict[str, Any]) -> dict[str, Any]:
	"""Strip non-JSON-serializable values from ``get_std_template_usage_impact`` for audit payloads."""
	out = dict(impact)
	last = out.get("last_usage_row")
	if isinstance(last, dict):
		safe: dict[str, Any] = {}
		for k, v in last.items():
			safe[k] = v.isoformat() if hasattr(v, "isoformat") else v
		out["last_usage_row"] = safe
	return out


def _guest_blocked() -> None:
	if not frappe.session.user or frappe.session.user == "Guest":
		frappe.throw(_("Not permitted"), frappe.PermissionError)


def _is_site_user_administrator() -> bool:
	return frappe.session.user == "Administrator"


def _has_any_role(roles: frozenset[str]) -> bool:
	return bool(roles.intersection(frappe.get_roles()))


def _assert_roles(
	roles: frozenset[str],
	*,
	action: str,
	allow_site_user_administrator: bool = False,
) -> None:
	if allow_site_user_administrator and _is_site_user_administrator():
		return
	if _has_any_role(roles):
		return
	frappe.throw(
		_("Not permitted for action {0}").format(action),
		frappe.PermissionError,
	)


def _can_record_system_manager_override(override_reason: str | None) -> bool:
	"""Doc 7 §14.5 — override path is for **System Manager** with a documented reason."""
	text = (override_reason or "").strip()
	if not text:
		return False
	return ROLE_SYSTEM_MANAGER in frappe.get_roles()


def _assert_roles_submit() -> None:
	_assert_roles(
		frozenset({ROLE_SYSTEM_MANAGER, ROLE_STD_TEMPLATE_ADMINISTRATOR}),
		action="submit_std_template_for_approval",
		allow_site_user_administrator=True,
	)


def _assert_roles_return() -> None:
	_assert_roles(
		frozenset(
			{
				ROLE_SYSTEM_MANAGER,
				ROLE_STD_TEMPLATE_REVIEWER,
				ROLE_STD_TEMPLATE_APPROVER,
			}
		),
		action="return_std_template_for_correction",
		allow_site_user_administrator=True,
	)


def _assert_roles_reject() -> None:
	_assert_roles(
		frozenset({ROLE_SYSTEM_MANAGER, ROLE_STD_TEMPLATE_APPROVER}),
		action="reject_std_template",
		allow_site_user_administrator=True,
	)


def _assert_roles_approve() -> None:
	_assert_roles(
		frozenset({ROLE_SYSTEM_MANAGER, ROLE_STD_TEMPLATE_APPROVER}),
		action="approve_std_template",
		allow_site_user_administrator=True,
	)


def _assert_roles_activate_ops() -> None:
	_assert_roles(
		frozenset({ROLE_SYSTEM_MANAGER, ROLE_STD_TEMPLATE_ACTIVATOR}),
		action="activate_or_operational_transition",
		allow_site_user_administrator=True,
	)


def _assert_roles_archive() -> None:
	_assert_roles(
		frozenset({ROLE_SYSTEM_MANAGER, ROLE_STD_TEMPLATE_ADMINISTRATOR}),
		action="archive_std_template",
		allow_site_user_administrator=True,
	)


def _require_non_empty_reason(reason: str | None, *, label: str) -> str:
	text = (reason or "").strip()
	if not text:
		frappe.throw(_("{0} is required").format(label), frappe.ValidationError)
	return text[:140]


def _touch_status_change(doc: Any, reason: str | None) -> None:
	doc.previous_lifecycle_status = doc.get("lifecycle_status")
	doc.status_changed_at = now_datetime()
	doc.status_changed_by = frappe.session.user
	if reason:
		doc.status_reason = reason[:140]


def _save_governance_doc(doc: Any) -> None:
	doc.save(ignore_permissions=True)


def _assert_separation_of_duty_for_approval(doc: Any, override_reason: str | None) -> None:
	submitter = doc.get("submitted_for_approval_by")
	if not submitter or submitter != frappe.session.user:
		return
	if _can_record_system_manager_override(override_reason):
		return
	frappe.throw(
		_("Approver cannot approve their own submission unless a System Manager override reason is provided."),
		frappe.ValidationError,
	)


def _assert_package_hashes_aligned_for_activation(doc: Any) -> None:
	ph = (doc.get("package_hash") or "").strip()
	if not ph:
		frappe.throw(_("Package hash is required before activation."), frappe.ValidationError)
	for label, val in (
		("approval_package_hash", doc.get("approval_package_hash")),
		("latest_validation_package_hash", doc.get("latest_validation_package_hash")),
	):
		if (val or "").strip() != ph:
			frappe.throw(
				_("Activation blocked: {0} does not match current package_hash.").format(label),
				frappe.ValidationError,
			)


def _assert_no_active_profile_conflict(doc: Any, is_default_active_version: bool) -> None:
	if not is_default_active_version:
		return
	key = (doc.get("active_profile_key") or "").strip()
	if not key:
		return
	other = frappe.db.exists(
		"STD Template",
		{
			"name": ("!=", doc.name),
			"lifecycle_status": STATUS_ACTIVE,
			"active_profile_key": key,
		},
	)
	if other:
		frappe.throw(
			_("Another active template already uses active_profile_key {0}.").format(key),
			frappe.ValidationError,
		)


def submit_std_template_for_approval(std_template: str, comment: str | None = None) -> dict[str, Any]:
	"""Doc 7 §14.4 — ``Validated`` → ``Submitted for Approval``."""
	_guest_blocked()
	_assert_roles_submit()
	doc = frappe.get_doc("STD Template", std_template)
	if doc.lifecycle_status != STATUS_VALIDATED:
		frappe.throw(_("Submit requires lifecycle status Validated."), frappe.ValidationError)
	if not int(doc.get("validation_is_current") or 0):
		frappe.throw(_("Submit requires current validation."), frappe.ValidationError)
	if doc.get("latest_validation_status") not in (VALIDATION_PASS, VALIDATION_PASS_WARNINGS):
		frappe.throw(_("Submit requires a passing validation status."), frappe.ValidationError)
	if int(doc.get("critical_finding_count") or 0) > 0:
		frappe.throw(_("Submit is blocked while critical validation findings exist."), frappe.ValidationError)

	prev = doc.lifecycle_status
	_touch_status_change(doc, comment)
	doc.lifecycle_status = STATUS_SUBMITTED
	doc.submitted_for_approval_by = frappe.session.user
	doc.submitted_for_approval_at = now_datetime()
	doc.submission_comment = (comment or "").strip()[:140] or None
	doc.payload_locked = 1

	write_std_template_lifecycle_event(
		doc,
		EVT_SUBMITTED,
		"governance",
		{"comment": (comment or "").strip()[:140] or None},
		from_status=prev,
		to_status=STATUS_SUBMITTED,
		reason=None,
		save=False,
	)
	_save_governance_doc(doc)
	return {"ok": True, "std_template": doc.name, "lifecycle_status": doc.lifecycle_status}


def return_std_template_for_correction(std_template: str, reason: str) -> dict[str, Any]:
	"""Doc 7 §14.x / doc 3 §8.4 — ``Submitted for Approval`` → ``Returned for Correction``."""
	_guest_blocked()
	_assert_roles_return()
	text = _require_non_empty_reason(reason, label=_("Return reason"))
	doc = frappe.get_doc("STD Template", std_template)
	if doc.lifecycle_status != STATUS_SUBMITTED:
		frappe.throw(_("Return requires lifecycle status Submitted for Approval."), frappe.ValidationError)

	prev = doc.lifecycle_status
	_touch_status_change(doc, text)
	doc.lifecycle_status = STATUS_RETURNED
	doc.reviewed_by = frappe.session.user
	doc.reviewed_at = now_datetime()
	doc.review_comment = text
	doc.approval_decision = "Returned"
	doc.validation_is_current = 0
	doc.payload_locked = 0

	write_std_template_lifecycle_event(
		doc,
		EVT_RETURNED,
		"governance",
		{"reason": text},
		from_status=prev,
		to_status=STATUS_RETURNED,
		reason=text,
		save=False,
	)
	_save_governance_doc(doc)
	return {"ok": True, "std_template": doc.name, "lifecycle_status": doc.lifecycle_status}


def reject_std_template(std_template: str, reason: str) -> dict[str, Any]:
	"""``Submitted for Approval`` → ``Rejected`` (doc 3 §8.4)."""
	_guest_blocked()
	_assert_roles_reject()
	text = _require_non_empty_reason(reason, label=_("Rejection reason"))
	doc = frappe.get_doc("STD Template", std_template)
	if doc.lifecycle_status != STATUS_SUBMITTED:
		frappe.throw(_("Reject requires lifecycle status Submitted for Approval."), frappe.ValidationError)

	prev = doc.lifecycle_status
	_touch_status_change(doc, text)
	doc.lifecycle_status = STATUS_REJECTED
	doc.approved_by = frappe.session.user
	doc.approved_at = now_datetime()
	doc.approval_decision = "Rejected"
	doc.approval_comments = text
	doc.allowed_for_tender_creation = 0
	doc.payload_locked = 0

	write_std_template_lifecycle_event(
		doc,
		EVT_REJECTED,
		"governance",
		{"reason": text},
		from_status=prev,
		to_status=STATUS_REJECTED,
		reason=text,
		save=False,
	)
	_save_governance_doc(doc)
	return {"ok": True, "std_template": doc.name, "lifecycle_status": doc.lifecycle_status}


def approve_std_template(
	std_template: str, comments: str, override_reason: str | None = None
) -> dict[str, Any]:
	"""Doc 7 §14.5 — ``Submitted for Approval`` → ``Approved``."""
	_guest_blocked()
	_assert_roles_approve()
	doc = frappe.get_doc("STD Template", std_template)
	if doc.lifecycle_status != STATUS_SUBMITTED:
		frappe.throw(_("Approve requires lifecycle status Submitted for Approval."), frappe.ValidationError)
	if not int(doc.get("validation_is_current") or 0):
		frappe.throw(_("Approve requires current validation."), frappe.ValidationError)
	if int(doc.get("critical_finding_count") or 0) > 0:
		frappe.throw(_("Approve is blocked while critical validation findings exist."), frappe.ValidationError)

	_assert_separation_of_duty_for_approval(doc, override_reason)

	prev = doc.lifecycle_status
	comments = (comments or "").strip()[:140] or "-"
	override = (override_reason or "").strip()[:140] or None
	same_submitter = doc.get("submitted_for_approval_by") == frappe.session.user
	override_used = bool(same_submitter and _can_record_system_manager_override(override_reason))

	_touch_status_change(doc, comments)
	doc.lifecycle_status = STATUS_APPROVED
	doc.approved_by = frappe.session.user
	doc.approved_at = now_datetime()
	doc.approval_decision = "Approved"
	doc.approval_comments = comments
	doc.approval_validation_run_id = doc.get("latest_validation_run_id")
	doc.approval_package_hash = doc.get("package_hash")
	doc.approval_override_used = 1 if override_used else 0
	doc.approval_override_reason = override if override_used else None
	doc.allowed_for_tender_creation = 0

	write_std_template_lifecycle_event(
		doc,
		EVT_APPROVED,
		"governance",
		{"comments": comments, "override_reason": override},
		from_status=prev,
		to_status=STATUS_APPROVED,
		reason=comments,
		override_used=override_used,
		override_reason=override if override_used else None,
		save=False,
	)
	if override_used:
		write_std_template_lifecycle_event(
			doc,
			EVT_OVERRIDE_USED,
			"governance",
			{"scope": "approval", "override_reason": override},
			from_status=STATUS_APPROVED,
			to_status=STATUS_APPROVED,
			reason=override,
			override_used=True,
			override_reason=override,
			save=False,
		)
	_save_governance_doc(doc)
	return {"ok": True, "std_template": doc.name, "lifecycle_status": doc.lifecycle_status}


def activate_std_template(
	std_template: str,
	reason: str,
	active_from: str | None = None,
	active_until: str | None = None,
	is_default_active_version: bool = True,
) -> dict[str, Any]:
	"""Doc 7 §14.6 — ``Approved`` → ``Active``."""
	_guest_blocked()
	enforce_sec_authorization(
		action_code="ACTIVATE_STD_TEMPLATE",
		actor=frappe.session.user,
		object_type="STD Template",
		object_code=std_template,
		context={"object_exists": bool(frappe.db.exists("STD Template", std_template))},
		fallback_message="Not authorized to activate STD template.",
	)
	_assert_roles_activate_ops()
	text = _require_non_empty_reason(reason, label=_("Activation reason"))
	doc = frappe.get_doc("STD Template", std_template)
	if doc.lifecycle_status != STATUS_APPROVED:
		frappe.throw(_("Activate requires lifecycle status Approved."), frappe.ValidationError)

	_assert_package_hashes_aligned_for_activation(doc)
	_assert_no_active_profile_conflict(doc, bool(is_default_active_version))

	prev = doc.lifecycle_status
	_touch_status_change(doc, text)
	doc.lifecycle_status = STATUS_ACTIVE
	doc.activated_by = frappe.session.user
	doc.activated_at = now_datetime()
	doc.activation_reason = text
	doc.activation_package_hash = doc.get("package_hash")
	doc.activation_approval_reference = doc.get("approval_validation_run_id")
	doc.active_from = getdate(active_from) if active_from else None
	doc.active_until = getdate(active_until) if active_until else None
	doc.is_default_active_version = 1 if is_default_active_version else 0
	doc.allowed_for_tender_creation = 1
	doc.is_suspended = 0

	write_std_template_lifecycle_event(
		doc,
		EVT_ACTIVATED,
		"governance",
		{"reason": text, "is_default_active_version": bool(is_default_active_version)},
		from_status=prev,
		to_status=STATUS_ACTIVE,
		reason=text,
		save=False,
	)
	_save_governance_doc(doc)
	return {"ok": True, "std_template": doc.name, "lifecycle_status": doc.lifecycle_status}


def suspend_std_template(std_template: str, reason: str) -> dict[str, Any]:
	"""``Active`` → ``Suspended`` (doc 3 §8.8)."""
	_guest_blocked()
	_assert_roles_activate_ops()
	text = _require_non_empty_reason(reason, label=_("Suspension reason"))
	doc = frappe.get_doc("STD Template", std_template)
	if doc.lifecycle_status != STATUS_ACTIVE:
		frappe.throw(_("Suspend requires lifecycle status Active."), frappe.ValidationError)

	prev = doc.lifecycle_status
	_touch_status_change(doc, text)
	doc.lifecycle_status = STATUS_SUSPENDED
	doc.is_suspended = 1
	doc.suspended_by = frappe.session.user
	doc.suspended_at = now_datetime()
	doc.suspension_reason = text
	doc.allowed_for_tender_creation = 0

	write_std_template_lifecycle_event(
		doc,
		EVT_SUSPENDED,
		"governance",
		{"reason": text},
		from_status=prev,
		to_status=STATUS_SUSPENDED,
		reason=text,
		save=False,
	)
	_save_governance_doc(doc)
	return {"ok": True, "std_template": doc.name, "lifecycle_status": doc.lifecycle_status}


def reinstate_std_template(std_template: str, reason: str) -> dict[str, Any]:
	"""``Suspended`` → ``Active`` (doc 3 §8.9)."""
	_guest_blocked()
	_assert_roles_activate_ops()
	text = _require_non_empty_reason(reason, label=_("Reinstatement reason"))
	doc = frappe.get_doc("STD Template", std_template)
	if doc.lifecycle_status != STATUS_SUSPENDED:
		frappe.throw(_("Reinstate requires lifecycle status Suspended."), frappe.ValidationError)

	prev = doc.lifecycle_status
	_touch_status_change(doc, text)
	doc.lifecycle_status = STATUS_ACTIVE
	doc.is_suspended = 0
	doc.reinstated_by = frappe.session.user
	doc.reinstated_at = now_datetime()
	doc.reinstatement_reason = text
	doc.allowed_for_tender_creation = 1

	write_std_template_lifecycle_event(
		doc,
		EVT_REINSTATED,
		"governance",
		{"reason": text},
		from_status=prev,
		to_status=STATUS_ACTIVE,
		reason=text,
		save=False,
	)
	_save_governance_doc(doc)
	return {"ok": True, "std_template": doc.name, "lifecycle_status": doc.lifecycle_status}


def supersede_std_template(
	std_template: str,
	replacement_template: str,
	reason: str,
	effective_date: str | None = None,
) -> dict[str, Any]:
	"""``Active`` / ``Suspended`` → ``Superseded`` (doc 3 §8.8 / §8.9)."""
	_guest_blocked()
	_assert_roles_activate_ops()
	text = _require_non_empty_reason(reason, label=_("Supersession reason"))
	doc = frappe.get_doc("STD Template", std_template)
	if doc.lifecycle_status not in (STATUS_ACTIVE, STATUS_SUSPENDED):
		frappe.throw(
			_("Supersede requires lifecycle status Active or Suspended."),
			frappe.ValidationError,
		)
	if replacement_template == doc.name:
		frappe.throw(_("Replacement template must differ from the current template."), frappe.ValidationError)

	rep = frappe.get_doc("STD Template", replacement_template)
	if rep.lifecycle_status not in (STATUS_APPROVED, STATUS_ACTIVE):
		frappe.throw(
			_("Replacement template must be Approved or Active."),
			frappe.ValidationError,
		)

	impact = get_std_template_usage_impact(std_template)
	prev = doc.lifecycle_status
	_touch_status_change(doc, text)
	doc.lifecycle_status = STATUS_SUPERSEDED
	doc.superseded_by_template = replacement_template
	doc.superseded_by = frappe.session.user
	doc.superseded_at = now_datetime()
	doc.supersession_reason = text
	doc.supersession_effective_date = getdate(effective_date) if effective_date else None
	doc.allowed_for_tender_creation = 0
	doc.is_suspended = 0

	write_std_template_lifecycle_event(
		doc,
		EVT_SUPERSEDED,
		"governance",
		{
			"replacement_template": replacement_template,
			"usage_impact": _json_safe_usage_impact(impact),
			"reason": text,
		},
		from_status=prev,
		to_status=STATUS_SUPERSEDED,
		reason=text,
		save=False,
	)
	_save_governance_doc(doc)
	frappe.db.set_value("STD Template", replacement_template, "supersedes_template", doc.name)
	return {"ok": True, "std_template": doc.name, "lifecycle_status": doc.lifecycle_status}


def retire_std_template(std_template: str, reason: str) -> dict[str, Any]:
	"""``Active`` / ``Suspended`` / ``Approved`` → ``Retired`` (doc 3 §8.8)."""
	_guest_blocked()
	_assert_roles_activate_ops()
	text = _require_non_empty_reason(reason, label=_("Retirement reason"))
	doc = frappe.get_doc("STD Template", std_template)
	if doc.lifecycle_status not in (STATUS_ACTIVE, STATUS_SUSPENDED, STATUS_APPROVED):
		frappe.throw(
			_("Retire requires lifecycle status Active, Suspended, or Approved."),
			frappe.ValidationError,
		)

	impact = get_std_template_usage_impact(std_template)
	prev = doc.lifecycle_status
	_touch_status_change(doc, text)
	doc.lifecycle_status = STATUS_RETIRED
	doc.retired_by = frappe.session.user
	doc.retired_at = now_datetime()
	doc.retirement_reason = text
	doc.allowed_for_tender_creation = 0
	doc.is_suspended = 0

	write_std_template_lifecycle_event(
		doc,
		EVT_RETIRED,
		"governance",
		{"usage_impact": _json_safe_usage_impact(impact), "reason": text},
		from_status=prev,
		to_status=STATUS_RETIRED,
		reason=text,
		save=False,
	)
	_save_governance_doc(doc)
	return {"ok": True, "std_template": doc.name, "lifecycle_status": doc.lifecycle_status}


def archive_std_template(std_template: str, reason: str) -> dict[str, Any]:
	"""``Rejected`` / ``Retired`` / ``Superseded`` → ``Archived`` (doc 3 §8.10)."""
	_guest_blocked()
	_assert_roles_archive()
	text = _require_non_empty_reason(reason, label=_("Archive reason"))
	doc = frappe.get_doc("STD Template", std_template)
	if doc.lifecycle_status not in (STATUS_REJECTED, STATUS_RETIRED, STATUS_SUPERSEDED):
		frappe.throw(
			_("Archive requires lifecycle status Rejected, Retired, or Superseded."),
			frappe.ValidationError,
		)

	prev = doc.lifecycle_status
	_touch_status_change(doc, text)
	doc.lifecycle_status = STATUS_ARCHIVED
	doc.allowed_for_tender_creation = 0

	write_std_template_lifecycle_event(
		doc,
		EVT_ARCHIVED,
		"governance",
		{"reason": text},
		from_status=prev,
		to_status=STATUS_ARCHIVED,
		reason=text,
		save=False,
	)
	_save_governance_doc(doc)
	return {"ok": True, "std_template": doc.name, "lifecycle_status": doc.lifecycle_status}
