# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""WORKS-COMP-0700 — Configuration snapshot + approval lock when Works readiness is Ready."""

from __future__ import annotations

from typing import Any

import frappe
from frappe import _

from kentender_procurement.tender_management.std_instance.publication_lock import StdPublicationLockService
from kentender_procurement.tender_management.std_instance.snapshot import StdInstanceSnapshotService
from kentender_procurement.tender_management.std_instance.state import StdInstanceStateService
from kentender_procurement.tender_management.works_completion.services.context_validator import (
	validate_works_completion_context,
)
from kentender_procurement.tender_management.std_instance.authorization import StdAuthorizationService
from kentender_procurement.tender_management.works_completion.audit import (
	WORKS_CONFIGURATION_SNAPSHOT_CREATED,
	WORKS_LOCKED_FOR_APPROVAL,
	WORKS_RETURNED_TO_PREPARATION,
	emit_works_completion_audit,
)
from kentender_procurement.tender_management.works_completion.services.works_readiness import (
	WorksReadinessService,
)

_WORKS_READINESS_LOCK_TITLE = "WORKS_READINESS_REQUIRED_FOR_LOCK"
_WORKS_READINESS_LOCK_MESSAGE = _(
	"Works STD Instance cannot be locked for approval until readiness is Ready."
)
_SNAPSHOT_REASON = _("Works tender-stage completion — configuration snapshot before approval lock.")


def _readiness_evidence_payload(readiness: dict[str, Any]) -> dict[str, Any]:
	blockers = list(readiness.get("blockers") or [])
	codes = sorted({str((b.get("code") or "").strip()) for b in blockers if (b.get("code") or "").strip()})
	return {
		"status": (readiness.get("status") or "").strip(),
		"blocker_codes": codes,
		"warnings": list(readiness.get("warnings") or []),
	}


def _ensure_ready_for_publication(instance_code: str) -> None:
	"""Advance instance status to ``Ready for Publication`` when allowed by STDINST-0120."""
	max_steps = 8
	for _ in range(max_steps):
		st = (frappe.db.get_value("Tender STD Instance", instance_code, "instance_status") or "").strip()
		if st == "Ready for Publication":
			return
		if st == "Draft":
			StdInstanceStateService.apply_transition(
				instance_code, "In Configuration", ignore_permissions=True
			)
			continue
		if st == "Validation Blocked":
			StdInstanceStateService.apply_transition(
				instance_code, "In Configuration", ignore_permissions=True
			)
			continue
		if st == "In Configuration":
			StdInstanceStateService.apply_transition(
				instance_code, "Ready for Publication", ignore_permissions=True
			)
			continue
		frappe.throw(
			_(
				"Cannot move STD Instance to Ready for Publication from status {0}. "
				"Resolve validation or use the appropriate lifecycle flow."
			).format(st or _("Unknown")),
			title=_("WORKS_SNAPSHOT_LOCK_STATE"),
		)
	frappe.throw(
		_("Could not reach Ready for Publication."),
		title=_("WORKS_SNAPSHOT_LOCK_STATE"),
	)


class WorksSnapshotLockService:
	"""Pack §17 — snapshot evidence then ``Locked for Approval``."""

	@staticmethod
	def create_configuration_snapshot_and_lock(
		instance_code: str,
		actor: str | None = None,
	) -> dict[str, Any]:
		"""Validate Works context + readiness, create Configuration snapshot, lock for approval.

		:param actor: optional user for ``frappe.set_user`` for the duration of the call.
		:returns: dict with ``ok``, ``snapshot``, ``instance_status``, ``readiness``.
		:raises frappe.ValidationError: invalid context or readiness not Ready.
		"""
		code = (instance_code or "").strip()
		prev_user = frappe.session.user
		act = (actor or "").strip()
		if act:
			frappe.set_user(act)
		try:
			if not code:
				frappe.throw(_("Instance code is required."), title=_("WORKS_INSTANCE_NOT_FOUND"))

			ctx = validate_works_completion_context(code)
			if not ctx.get("valid"):
				blockers = list(ctx.get("blockers") or [])
				first = blockers[0] if blockers else {}
				title = (first.get("code") or "WORKS_COMPLETION_CONTEXT").strip()
				msg = (first.get("message") or "").strip() or title
				frappe.throw(_(msg), title=_(title))

			_ensure_ready_for_publication(code)

			readiness = WorksReadinessService.run_works_readiness(code, actor=act or None, persist=True)
			if (readiness.get("status") or "").strip() != "Ready":
				# Stable code in message body: Frappe ValidationError does not attach ``title`` to the exception.
				frappe.throw(
					_("[{0}] {1}").format(_WORKS_READINESS_LOCK_TITLE, _WORKS_READINESS_LOCK_MESSAGE),
					title=_WORKS_READINESS_LOCK_TITLE,
				)

			evidence = _readiness_evidence_payload(readiness)
			snap = StdInstanceSnapshotService.create_configuration_snapshot(
				code,
				str(_SNAPSHOT_REASON),
				readiness_evidence=evidence,
			)
			locked = StdPublicationLockService.lock_for_approval(
				code,
				user=act or None,
				ignore_permissions=True,
			)
			audit_user = act or frappe.session.user
			emit_works_completion_audit(
				WORKS_CONFIGURATION_SNAPSHOT_CREATED,
				code,
				details={
					"snapshot": snap.name,
					"complete_instance_hash": snap.complete_instance_hash,
				},
				performed_by=audit_user,
			)
			emit_works_completion_audit(
				WORKS_LOCKED_FOR_APPROVAL,
				code,
				details={
					"snapshot": snap.name,
					"instance_status": (locked.instance_status or "").strip(),
				},
				performed_by=audit_user,
			)
			return {
				"ok": True,
				"snapshot": snap.name,
				"instance_status": (locked.instance_status or "").strip(),
				"readiness": readiness,
				"complete_instance_hash": snap.complete_instance_hash,
			}
		finally:
			frappe.set_user(prev_user)

	@staticmethod
	def return_to_preparation_from_approval_lock(instance_code: str, actor: str | None = None) -> dict[str, Any]:
		"""Move ``Locked for Approval`` Works instance back to ``In Configuration`` (pack LOCK-002).

		Requires Works completion context (tender-bound, Works category, lineage) and
		``StdAuthorizationService.assert_can_publish`` (same privilege as locking for approval).
		"""
		code = (instance_code or "").strip()
		prev_user = frappe.session.user
		act = (actor or "").strip()
		if act:
			frappe.set_user(act)
		try:
			if not code:
				frappe.throw(_("Instance code is required."), title=_("WORKS_INSTANCE_NOT_FOUND"))
			st = (frappe.db.get_value("Tender STD Instance", code, "instance_status") or "").strip()
			if st != "Locked for Approval":
				frappe.throw(
					_("Return to preparation is only allowed from Locked for Approval (current: {0}).").format(
						st or _("Unknown")
					),
					title=_("WORKS_RETURN_TO_PREPARATION_STATE"),
				)
			ctx = validate_works_completion_context(code, allow_return_from_approval_lock=True)
			if not ctx.get("valid"):
				blockers = list(ctx.get("blockers") or [])
				first = blockers[0] if blockers else {}
				title = (first.get("code") or "WORKS_COMPLETION_CONTEXT").strip()
				msg = (first.get("message") or "").strip() or title
				frappe.throw(_(msg), title=_(title))

			StdAuthorizationService.assert_can_publish(code)

			StdInstanceStateService.apply_transition(code, "In Configuration", ignore_permissions=True)
			inst = frappe.get_doc("Tender STD Instance", code)
			inst.locked_for_approval_at = None
			inst.locked_for_approval_by = None
			inst.save(ignore_permissions=True)

			audit_user = act or frappe.session.user
			emit_works_completion_audit(
				WORKS_RETURNED_TO_PREPARATION,
				code,
				details={"instance_status": "In Configuration"},
				performed_by=audit_user,
			)
			return {"ok": True, "instance_status": "In Configuration"}
		finally:
			frappe.set_user(prev_user)
