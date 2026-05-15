# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""ObjectScopeService — SEC-0310 / Cursor pack §9.

Validates whether ``actor`` may act on a concrete object (package, tender, STD
template/instance, committee assignment, audit target). Rules follow the pack
table where the bench has data; committee membership uses an explicit in-process
registry until a first-class assignment model exists.

**Administrator** is treated as break-glass and passes all checks here.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from typing import ClassVar

import frappe
from frappe import _

from kentender_procurement.tender_management.security.authorization.denial_codes import (
	DenialCode,
)


@dataclass(frozen=True)
class ObjectScopeOutcome:
	allowed: bool
	denial_code: str | None = None
	message: str = ""


def _norm_user(uid: str | None) -> str:
	return (uid or "").strip()


def _break_glass(actor: str) -> bool:
	return _norm_user(actor) == "Administrator"


def _outcome_ok() -> ObjectScopeOutcome:
	return ObjectScopeOutcome(True, None, "")


def _outcome_deny(message: str, *, denial_code: str | None = None) -> ObjectScopeOutcome:
	dc = denial_code or DenialCode.STD_AUTH_OBJECT_SCOPE_DENIED
	return ObjectScopeOutcome(False, dc, (message or "").strip() or str(dc))


class ObjectScopeService:
	"""Pack §9 — object scope assertions for authorization."""

	# (tender_code, committee_type) -> user ids with committee duty for that tender.
	_committee_registry: ClassVar[dict[tuple[str, str], frozenset[str]]] = {}

	@classmethod
	def register_committee_members(
		cls,
		tender_code: str,
		committee_type: str,
		user_ids: Iterable[str],
	) -> None:
		"""Register opening/evaluation committee members for ``tender_code`` (in-process).

		``committee_type`` is ``opening`` or ``evaluation`` (case-insensitive). Production
		callers should invoke this when committee assignment data is persisted.
		"""
		key = (_norm_user(tender_code), _norm_user(committee_type).lower())
		cls._committee_registry[key] = frozenset(_norm_user(u) for u in user_ids if _norm_user(u))

	@classmethod
	def clear_committee_registry(cls) -> None:
		"""Test helper — remove all committee registrations."""
		cls._committee_registry.clear()

	@classmethod
	def unregister_committee(cls, tender_code: str, committee_type: str) -> None:
		key = (_norm_user(tender_code), _norm_user(committee_type).lower())
		cls._committee_registry.pop(key, None)

	# --- check_* (non-throwing) -------------------------------------------------

	@classmethod
	def check_package_scope(cls, actor: str, package_code: str) -> ObjectScopeOutcome:
		"""Release package rule: actor is owner / created_by / approved_by on ``Procurement Package``."""
		act = _norm_user(actor)
		pkg = _norm_user(package_code)
		if not act or not pkg:
			return _outcome_deny("Actor and package code are required.")
		if _break_glass(act):
			return _outcome_ok()
		if not frappe.db.exists("Procurement Package", pkg):
			return _outcome_deny(f"Procurement Package {pkg!r} not found.")
		row = frappe.db.get_value(
			"Procurement Package",
			pkg,
			["owner", "created_by", "approved_by"],
			as_dict=True,
		)
		if not row:
			return _outcome_deny("Procurement Package could not be loaded.")
		allowed_users = {x for x in (_norm_user(row.get(k)) for k in ("owner", "created_by", "approved_by")) if x}
		if act in allowed_users:
			return _outcome_ok()
		return _outcome_deny(
			_("Actor is not assigned to this procurement package."),
		)

	@classmethod
	def check_tender_scope(cls, actor: str, tender_code: str) -> ObjectScopeOutcome:
		"""Tender rule: actor is document owner (assignment proxy until explicit officer field)."""
		act = _norm_user(actor)
		tn = _norm_user(tender_code)
		if not act or not tn:
			return _outcome_deny("Actor and tender code are required.")
		if _break_glass(act):
			return _outcome_ok()
		if not frappe.db.exists("TM2 Tender", tn):
			return _outcome_deny(f"TM2 Tender {tn!r} not found.")
		owner = _norm_user(frappe.db.get_value("TM2 Tender", tn, "owner"))
		if owner and act == owner:
			return _outcome_ok()
		return _outcome_deny(_("Actor is not in scope for this tender."))

	@classmethod
	def check_std_template_scope(cls, actor: str, template_version_code: str) -> ObjectScopeOutcome:
		"""Template governance: actor appears on governance trail or owns ``STD Template``."""
		act = _norm_user(actor)
		tc = _norm_user(template_version_code)
		if not act or not tc:
			return _outcome_deny("Actor and template code are required.")
		if _break_glass(act):
			return _outcome_ok()
		if not frappe.db.exists("STD Template", tc):
			return _outcome_deny(f"STD Template {tc!r} not found.")
		fields = [
			"owner",
			"submitted_for_approval_by",
			"reviewed_by",
			"approved_by",
			"activated_by",
			"status_changed_by",
			"suspended_by",
		]
		row = frappe.db.get_value("STD Template", tc, fields, as_dict=True)
		if not row:
			return _outcome_deny("STD Template could not be loaded.")
		actors = {_norm_user(row[f]) for f in fields if _norm_user(row.get(f))}
		if act in actors:
			return _outcome_ok()
		return _outcome_deny(_("Actor is not in scope for this STD template."))

	@classmethod
	def check_std_instance_scope(cls, actor: str, instance_code: str) -> ObjectScopeOutcome:
		"""Instance rule: actor owns / created / lock metadata on instance or owns tender."""
		act = _norm_user(actor)
		inst = _norm_user(instance_code)
		if not act or not inst:
			return _outcome_deny("Actor and instance code are required.")
		if _break_glass(act):
			return _outcome_ok()
		if not frappe.db.exists("Tender STD Instance", inst):
			return _outcome_deny(f"Tender STD Instance {inst!r} not found.")
		row = frappe.db.get_value(
			"Tender STD Instance",
			inst,
			[
				"owner",
				"created_by",
				"locked_for_approval_by",
				"published_locked_by",
				"tm2_tender",
			],
			as_dict=True,
		)
		if not row:
			return _outcome_deny("Tender STD Instance could not be loaded.")
		inst_users = {
			_norm_user(row.get(k))
			for k in ("owner", "created_by", "locked_for_approval_by", "published_locked_by")
		}
		inst_users.discard("")
		if act in inst_users:
			return _outcome_ok()
		tm2 = _norm_user(row.get("tm2_tender"))
		if tm2:
			t2_owner = _norm_user(frappe.db.get_value("TM2 Tender", tm2, "owner"))
			if t2_owner and act == t2_owner:
				return _outcome_ok()
		return _outcome_deny(_("Actor is not in scope for this STD instance."))

	@classmethod
	def check_committee_scope(
		cls,
		actor: str,
		tender_code: str,
		committee_type: str,
	) -> ObjectScopeOutcome:
		"""Opening / evaluation: actor must be registered for ``tender_code`` + committee."""
		act = _norm_user(actor)
		tn = _norm_user(tender_code)
		ct = _norm_user(committee_type).lower()
		if not act or not tn or not ct:
			return _outcome_deny("Actor, tender code, and committee type are required.")
		if _break_glass(act):
			return _outcome_ok()
		if ct not in ("opening", "evaluation"):
			return _outcome_deny(_("committee_type must be opening or evaluation."))
		if not frappe.db.exists("TM2 Tender", tn):
			return _outcome_deny(f"TM2 Tender {tn!r} not found.")
		members = cls._committee_registry.get((tn, ct), frozenset())
		if not members:
			return _outcome_deny(
				_("No committee assignment recorded for this tender."),
			)
		if act in members:
			return _outcome_ok()
		return _outcome_deny(
			_("Actor is not assigned to this committee for the tender."),
		)

	@classmethod
	def check_audit_scope(cls, actor: str, object_type: str, object_code: str) -> ObjectScopeOutcome:
		"""Evidence / audit: actor must have Frappe read permission on the target document."""
		act = _norm_user(actor)
		dt = _norm_user(object_type)
		dn = _norm_user(object_code)
		if not act or not dt or not dn:
			return _outcome_deny("Actor, object type, and object code are required.")
		if _break_glass(act):
			return _outcome_ok()
		if not frappe.db.exists(dt, dn):
			return _outcome_deny(_("Audit target not found."), denial_code=DenialCode.STD_AUTH_OBJECT_SCOPE_DENIED)
		try:
			doc = frappe.get_doc(dt, dn)
		except frappe.DoesNotExistError:
			return _outcome_deny(_("Audit target not found."), denial_code=DenialCode.STD_AUTH_OBJECT_SCOPE_DENIED)
		try:
			if bool(frappe.has_permission(dt, "read", doc=doc, user=act)):
				return _outcome_ok()
		except Exception:
			return _outcome_deny(_("Unable to evaluate read permission for audit scope."))
		return _outcome_deny(
			_("Actor lacks read scope for this audit target."),
		)

	# --- assert_* (throwing) ---------------------------------------------------

	@classmethod
	def assert_package_scope(cls, actor: str, package_code: str) -> None:
		cls._raise_if_denied(cls.check_package_scope(actor, package_code))

	@classmethod
	def assert_tender_scope(cls, actor: str, tender_code: str) -> None:
		cls._raise_if_denied(cls.check_tender_scope(actor, tender_code))

	@classmethod
	def assert_std_template_scope(cls, actor: str, template_version_code: str) -> None:
		cls._raise_if_denied(cls.check_std_template_scope(actor, template_version_code))

	@classmethod
	def assert_std_instance_scope(cls, actor: str, instance_code: str) -> None:
		cls._raise_if_denied(cls.check_std_instance_scope(actor, instance_code))

	@classmethod
	def assert_committee_scope(cls, actor: str, tender_code: str, committee_type: str) -> None:
		cls._raise_if_denied(cls.check_committee_scope(actor, tender_code, committee_type))

	@classmethod
	def assert_audit_scope(cls, actor: str, object_type: str, object_code: str) -> None:
		cls._raise_if_denied(cls.check_audit_scope(actor, object_type, object_code))

	@staticmethod
	def _raise_if_denied(out: ObjectScopeOutcome) -> None:
		if out.allowed:
			return
		title = str(out.denial_code or DenialCode.STD_AUTH_OBJECT_SCOPE_DENIED)
		frappe.throw(
			_(out.message or title),
			title=title,
			exc=frappe.ValidationError,
		)
