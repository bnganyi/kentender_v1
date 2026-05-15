# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""StateAuthorizationService — SEC-0320 / Cursor pack §10.

Blocks actions inconsistent with template / STD instance / output / snapshot /
tender lifecycle state. Aligns with DocType Select values (STD Template
``lifecycle_status``, Tender STD Instance ``instance_status``, etc.).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

import frappe
from frappe import _

from kentender_procurement.tender_management.security.authorization.denial_codes import (
	DenialCode,
)


@dataclass(frozen=True)
class StateAuthorizationOutcome:
	allowed: bool
	denial_code: str | None = None
	message: str = ""


def _norm(s: str | None) -> str:
	return (s or "").strip()


def _ok() -> StateAuthorizationOutcome:
	return StateAuthorizationOutcome(True, None, "")


def _deny(message: str, *, denial_code: str | None = None) -> StateAuthorizationOutcome:
	dc = denial_code or DenialCode.STD_AUTH_ACTIVE_VERSION_LOCKED
	return StateAuthorizationOutcome(False, dc, (message or "").strip() or str(dc))


class StateAuthorizationService:
	"""Pack §10 — state gates vs ``action_code`` (std engine §9.5 registry)."""

	# --- Action groups (registry keys) -----------------------------------------

	_READ_LIKE: ClassVar[frozenset[str]] = frozenset(
		{
			"CONSUME_DSM",
			"CONSUME_DOM",
			"CONSUME_DEM",
			"CONSUME_DCM",
			"EXPORT_EVIDENCE_PACKAGE",
		}
	)

	_TEMPLATE_MUTATIONS: ClassVar[frozenset[str]] = frozenset(
		{
			"IMPORT_OFFICIAL_STD_PACKAGE",
			"VALIDATE_STD_TEMPLATE",
			"ACTIVATE_STD_TEMPLATE",
		}
	)

	_TEMPLATE_CONFIG_MUTATIONS: ClassVar[frozenset[str]] = frozenset(
		{
			"IMPORT_OFFICIAL_STD_PACKAGE",
			"ACTIVATE_STD_TEMPLATE",
		}
	)

	_TEMPLATE_READ_ONLY_STATES: ClassVar[frozenset[str]] = frozenset(
		{
			"Active",
			"Suspended",
			"Superseded",
			"Retired",
			"Archived",
			"Rejected",
		}
	)

	_TEMPLATE_REVIEW_BLOCK_CONFIG_STATES: ClassVar[frozenset[str]] = frozenset(
		{"Submitted for Approval"}
	)

	_INSTANCE_CONTENT_MUTATIONS: ClassVar[frozenset[str]] = frozenset(
		{
			"EDIT_STD_INSTANCE_PARAMETERS",
			"UPLOAD_STD_SECTION_ATTACHMENT",
			"CONFIGURE_WORKS_BOQ",
			"GENERATE_STD_OUTPUTS",
		}
	)

	_INSTANCE_READ_ONLY_STATES: ClassVar[frozenset[str]] = frozenset(
		{
			"Superseded",
			"Cancelled",
		}
	)

	_INSTANCE_LOCKED_APPROVAL_STATES: ClassVar[frozenset[str]] = frozenset(
		{"Locked for Approval"}
	)

	_INSTANCE_PUBLISHED_LOCKED_STATES: ClassVar[frozenset[str]] = frozenset(
		{"Published Locked"}
	)

	_OUTPUT_MUTATIONS: ClassVar[frozenset[str]] = frozenset({"GENERATE_STD_OUTPUTS"})

	_OUTPUT_READINESS_PUBLICATION: ClassVar[frozenset[str]] = frozenset(
		{
			"RUN_PUBLICATION_READINESS",
			"PUBLISH_TENDER",
		}
	)

	_SNAPSHOT_READ_OK: ClassVar[frozenset[str]] = frozenset(
		{
			"CONSUME_DSM",
			"CONSUME_DOM",
			"CONSUME_DEM",
			"CONSUME_DCM",
			"EXPORT_EVIDENCE_PACKAGE",
		}
	)

	_SNAPSHOT_IMMUTABLE_STATES: ClassVar[frozenset[str]] = frozenset(
		{
			"Final",
			"Superseded",
			"Archived",
		}
	)

	_TENDER_PUBLISHED_ALLOWED: ClassVar[frozenset[str]] = frozenset(
		{
			"CONSUME_DSM",
			"CONSUME_DOM",
			"CONSUME_DEM",
			"CONSUME_DCM",
			"EXPORT_EVIDENCE_PACKAGE",
			"CREATE_ADDENDUM",
			"APPROVE_TENDER_PUBLICATION",
		}
	)

	# --- check_* (non-throwing) -------------------------------------------------

	@classmethod
	def check_template_state_allows(cls, action_code: str, template_state: str) -> StateAuthorizationOutcome:
		"""``template_state`` = STD Template ``lifecycle_status``."""
		ac = _norm(action_code)
		st = _norm(template_state)
		if not ac:
			return _deny(_("Action code is required."), denial_code=DenialCode.STD_AUTH_PERMISSION_DENIED)
		if ac not in cls._TEMPLATE_MUTATIONS:
			return _ok()
		if st in cls._TEMPLATE_READ_ONLY_STATES:
			return _deny(
				_("This template version is locked for its lifecycle state."),
				denial_code=DenialCode.STD_AUTH_ACTIVE_VERSION_LOCKED,
			)
		if st in cls._TEMPLATE_REVIEW_BLOCK_CONFIG_STATES and ac in cls._TEMPLATE_CONFIG_MUTATIONS:
			return _deny(
				_("Configuration changes are not allowed while the template is under review."),
				denial_code=DenialCode.STD_AUTH_ACTIVE_VERSION_LOCKED,
			)
		return _ok()

	@classmethod
	def check_instance_state_allows(cls, action_code: str, instance_state: str) -> StateAuthorizationOutcome:
		"""``instance_state`` = Tender STD Instance ``instance_status``."""
		ac = _norm(action_code)
		st = _norm(instance_state)
		if not ac:
			return _deny(_("Action code is required."), denial_code=DenialCode.STD_AUTH_PERMISSION_DENIED)
		if ac not in cls._INSTANCE_CONTENT_MUTATIONS:
			return _ok()
		if st in cls._INSTANCE_READ_ONLY_STATES:
			return _deny(
				_("This STD instance cannot be changed in its current state."),
				denial_code=DenialCode.STD_AUTH_ACTIVE_VERSION_LOCKED,
			)
		if st in cls._INSTANCE_LOCKED_APPROVAL_STATES:
			return _deny(
				_("Ordinary edits are blocked while the instance is locked for approval."),
				denial_code=DenialCode.STD_AUTH_ACTIVE_VERSION_LOCKED,
			)
		if st in cls._INSTANCE_PUBLISHED_LOCKED_STATES:
			return _deny(
				_("Direct edits after publication require an addendum workflow."),
				denial_code=DenialCode.POST_PUBLICATION_EDIT_DENIED_ADDENDUM_REQUIRED,
			)
		return _ok()

	@classmethod
	def check_output_state_allows(cls, action_code: str, output_state: str) -> StateAuthorizationOutcome:
		"""``output_state`` = Tender STD Generated Output ``output_status``."""
		ac = _norm(action_code)
		st = _norm(output_state)
		if not ac:
			return _deny(_("Action code is required."), denial_code=DenialCode.STD_AUTH_PERMISSION_DENIED)

		if ac in cls._OUTPUT_MUTATIONS:
			if st == "Published":
				return _deny(
					_("Published outputs cannot be overwritten."),
					denial_code=DenialCode.STD_AUTH_OUTPUT_LOCKED,
				)
			if st in {"Stale", "Superseded", "Archived", "Failed"}:
				return _deny(
					_("This output cannot be regenerated in its current state."),
					denial_code=DenialCode.STD_AUTH_OUTPUT_LOCKED,
				)

		if ac in cls._READ_LIKE or ac in cls._OUTPUT_READINESS_PUBLICATION:
			if st == "Stale":
				return _deny(
					_("Stale outputs cannot be used for readiness or publication."),
					denial_code=DenialCode.OUTPUT_STALE,
				)
			if st == "Superseded":
				return _deny(
					_("Superseded outputs are historical only."),
					denial_code=DenialCode.OUTPUT_SUPERSEDED,
				)
			if st == "Archived":
				return _deny(
					_("Archived outputs cannot be used."),
					denial_code=DenialCode.OUTPUT_SUPERSEDED,
				)
			if st == "Failed":
				return _deny(
					_("Failed outputs cannot be used for downstream steps."),
					denial_code=DenialCode.OUTPUT_STALE,
				)

		return _ok()

	@classmethod
	def check_snapshot_state_allows(cls, action_code: str, snapshot_state: str) -> StateAuthorizationOutcome:
		"""``snapshot_state`` = ``snapshot_status`` on Tender STD Instance Snapshot or Tender Publication Snapshot."""
		ac = _norm(action_code)
		st = _norm(snapshot_state)
		if not ac:
			return _deny(_("Action code is required."), denial_code=DenialCode.STD_AUTH_PERMISSION_DENIED)
		if st not in cls._SNAPSHOT_IMMUTABLE_STATES:
			return _ok()
		if ac in cls._SNAPSHOT_READ_OK:
			return _ok()
		return _deny(
			_("This snapshot cannot be modified in its current state."),
			denial_code=DenialCode.STD_AUTH_ACTIVE_VERSION_LOCKED,
		)

	@classmethod
	def check_tender_state_allows(cls, action_code: str, tender_state: str) -> StateAuthorizationOutcome:
		"""``tender_state`` = Procurement Tender ``tender_status``."""
		ac = _norm(action_code)
		st = _norm(tender_state)
		if not ac:
			return _deny(_("Action code is required."), denial_code=DenialCode.STD_AUTH_PERMISSION_DENIED)
		if st == "Cancelled":
			if ac in cls._READ_LIKE:
				return _ok()
			return _deny(
				_("This tender is cancelled."),
				denial_code=DenialCode.STD_AUTH_ACTIVE_VERSION_LOCKED,
			)
		if st == "Published":
			if ac in cls._TENDER_PUBLISHED_ALLOWED:
				return _ok()
			return _deny(
				_("This action is not allowed on a published tender without an addendum path."),
				denial_code=DenialCode.POST_PUBLICATION_EDIT_DENIED_ADDENDUM_REQUIRED,
			)
		return _ok()

	@classmethod
	def check(cls, action_code: str, *, kind: str, status: str) -> StateAuthorizationOutcome:
		"""Dispatch by ``kind`` for :class:`AuthorizationDecisionEngine` ``context["state_authorization"]``."""
		k = _norm(kind).lower()
		st = _norm(status)
		if k == "template":
			return cls.check_template_state_allows(action_code, st)
		if k == "instance":
			return cls.check_instance_state_allows(action_code, st)
		if k == "output":
			return cls.check_output_state_allows(action_code, st)
		if k in {"snapshot", "publication_snapshot", "instance_snapshot"}:
			return cls.check_snapshot_state_allows(action_code, st)
		if k == "tender":
			return cls.check_tender_state_allows(action_code, st)
		return _deny(
			_("Unknown state authorization kind."),
			denial_code=DenialCode.STD_AUTH_PERMISSION_DENIED,
		)

	# --- assert_* (throwing) ----------------------------------------------------

	@classmethod
	def assert_template_state_allows(cls, action_code: str, template_state: str) -> None:
		cls._raise_if_denied(cls.check_template_state_allows(action_code, template_state))

	@classmethod
	def assert_instance_state_allows(cls, action_code: str, instance_state: str) -> None:
		cls._raise_if_denied(cls.check_instance_state_allows(action_code, instance_state))

	@classmethod
	def assert_output_state_allows(cls, action_code: str, output_state: str) -> None:
		cls._raise_if_denied(cls.check_output_state_allows(action_code, output_state))

	@classmethod
	def assert_snapshot_state_allows(cls, action_code: str, snapshot_state: str) -> None:
		cls._raise_if_denied(cls.check_snapshot_state_allows(action_code, snapshot_state))

	@classmethod
	def assert_tender_state_allows(cls, action_code: str, tender_state: str) -> None:
		cls._raise_if_denied(cls.check_tender_state_allows(action_code, tender_state))

	@staticmethod
	def _raise_if_denied(out: StateAuthorizationOutcome) -> None:
		if out.allowed:
			return
		title = str(out.denial_code or DenialCode.STD_AUTH_ACTIVE_VERSION_LOCKED)
		frappe.throw(
			_(out.message or title),
			title=title,
			exc=frappe.ValidationError,
		)
