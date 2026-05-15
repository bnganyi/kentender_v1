# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PUB-0200 — ``ConfigurationSnapshotService`` (tender-level gate before approval).

Std engine §7 / Cursor pack §7: immutable configuration capture, ``Locked for Approval`` on the
bound ``Tender STD Instance``, denial ``CONFIG_SNAPSHOT_READINESS_REQUIRED`` when publication
readiness is not **Ready**.

Reuses ``StdInstanceSnapshotService.create_configuration_snapshot`` (``Tender STD Instance Snapshot``,
``snapshot_type=Configuration``) and ``StdPublicationLockService.lock_for_approval``.
"""

from __future__ import annotations

import json
from typing import Any

import frappe
from frappe import _
from frappe.model.document import Document

from kentender_procurement.tender_management.services.tm2_tender_resolve import (
	canonical_tm2_tender_code,
	resolve_tm2_tender_document,
)
from kentender_procurement.tender_management.std_instance.binding import TenderStdBindingService
from kentender_procurement.tender_management.std_instance.publication_lock import StdPublicationLockService
from kentender_procurement.tender_management.std_instance.snapshot import StdInstanceSnapshotService
from kentender_procurement.tender_management.std_instance.state import StdInstanceStateService
from kentender_procurement.tender_management.tender_publication.authorization.publication_authorization import (
	PublicationAuthorizationService,
)
from kentender_procurement.tender_management.tender_publication.audit.codes import (
	AUDIT_TENDER_PUBLICATION_CONFIGURATION_SNAPSHOT_CREATED,
	AUDIT_TENDER_PUBLICATION_SUBMITTED_FOR_APPROVAL,
)
from kentender_procurement.tender_management.tender_publication.audit.publication_audit import (
	emit_publication_audit_event,
)
from kentender_procurement.tender_management.tender_publication.readiness.publication_readiness import (
	PublicationReadinessService,
)
from kentender_procurement.tender_management.security.authorization.integration import (
	enforce_sec_authorization,
)

# Cursor pack §7 — denial when publication readiness is not Ready.
CONFIG_SNAPSHOT_READINESS_REQUIRED = "CONFIG_SNAPSHOT_READINESS_REQUIRED"

_SNAPSHOT_REASON = _("Publication readiness — configuration snapshot before approval (PUB-0200).")


def _ensure_ready_for_publication(instance_code: str) -> None:
	"""Advance instance to ``Ready for Publication`` when allowed (STDINST-0120; same as WORKS-COMP-0700)."""
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
			title=_("PUB_CONFIGURATION_SNAPSHOT_STATE"),
			exc=frappe.ValidationError,
		)
	frappe.throw(
		_("Could not reach Ready for Publication."),
		title=_("PUB_CONFIGURATION_SNAPSHOT_STATE"),
		exc=frappe.ValidationError,
	)


def _publication_readiness_evidence(readiness: dict[str, Any]) -> dict[str, Any]:
	findings = list(readiness.get("findings") or [])
	codes = sorted({str((f.get("code") or "").strip()) for f in findings if (f.get("code") or "").strip()})
	return {
		"status": (readiness.get("status") or "").strip(),
		"finding_codes": codes,
		"tender_code": (readiness.get("tender_code") or "").strip(),
	}


def _snapshot_summary(doc: Document) -> dict[str, Any]:
	return {
		"snapshot_code": doc.name,
		"tm2_tender": getattr(doc, "tm2_tender", None),
		"tender_std_instance": doc.tender_std_instance,
		"snapshot_type": doc.snapshot_type,
		"snapshot_status": doc.snapshot_status,
		"snapshot_reason": doc.snapshot_reason,
		"ref_bundle_output": doc.ref_bundle_output,
		"ref_dsm_output": doc.ref_dsm_output,
		"ref_dom_output": doc.ref_dom_output,
		"ref_dem_output": doc.ref_dem_output,
		"ref_dcm_output": doc.ref_dcm_output,
		"parameter_values_hash": doc.parameter_values_hash,
		"works_requirements_hash": doc.works_requirements_hash,
		"attachments_hash": doc.attachments_hash,
		"boq_hash": doc.boq_hash,
		"complete_instance_hash": doc.complete_instance_hash,
		"source_template_version_code": doc.source_template_version_code,
		"created_at": str(doc.created_at) if doc.created_at else None,
		"created_by": doc.created_by,
	}


class ConfigurationSnapshotService:
	"""Tender-scoped configuration snapshot + approval lock (PUB-0200)."""

	@staticmethod
	def createConfigurationSnapshot(tender_code: str, actor: str | None = None) -> dict[str, Any]:
		"""Run publication readiness, persist STD **Configuration** snapshot, lock instance for approval.

		Preconditions (pack §7): readiness **Ready** (same rule as ``assertReadyForApproval`` — not
		``Warning``); instance must still be editable so snapshot + lock succeed atomically from a
		business perspective (``assert_editable`` before snapshot to avoid orphan rows).

		:param actor: optional user id; ``frappe.set_user`` for the duration of the call when set.
		:returns: envelope with ``ok``, ``snapshot``, ``tender_std_instance``, ``instance_status``, ``readiness``.
		"""
		raw = (tender_code or "").strip()
		if not raw:
			frappe.throw(_("Tender code is required."), exc=frappe.ValidationError)
		tm2 = resolve_tm2_tender_document(raw)
		if not tm2:
			frappe.throw(
				_("TM2 Tender {0} does not exist.").format(raw),
				frappe.DoesNotExistError,
			)
		canon = canonical_tm2_tender_code(tm2)
		enforce_sec_authorization(
			action_code="SUBMIT_TENDER_FOR_APPROVAL",
			actor=actor or frappe.session.user,
			object_type="TM2 Tender",
			object_code=canon,
			context={"object_exists": True},
			fallback_message="Not authorized to submit tender for approval.",
		)

		prev_user = frappe.session.user
		act = (actor or "").strip()
		if act:
			frappe.set_user(act)
		try:
			PublicationAuthorizationService.assertCanSubmitForApproval(act or None)
			readiness = PublicationReadinessService.runReadiness(raw, act or None)
			if (readiness.get("status") or "").strip() != "Ready":
				codes = ", ".join(
					(f.get("code") or "") for f in (readiness.get("findings") or []) if f.get("code")
				)
				frappe.throw(
					_("Publication readiness is not Ready (status {0}). Findings: {1}").format(
						readiness.get("status"),
						codes or _("none"),
					),
					title=CONFIG_SNAPSHOT_READINESS_REQUIRED,
					exc=frappe.ValidationError,
				)

			si = TenderStdBindingService.get_current_std_instance_for_tm2_tender(tm2.name)
			if not si:
				frappe.throw(
					_("No Tender STD Instance is bound to this tender."),
					title=CONFIG_SNAPSHOT_READINESS_REQUIRED,
					exc=frappe.ValidationError,
				)

			StdPublicationLockService.assert_editable(
				si.name,
				operation_label=_("create configuration snapshot"),
			)
			_ensure_ready_for_publication(si.name)

			evidence = _publication_readiness_evidence(readiness)
			snap = StdInstanceSnapshotService.create_configuration_snapshot(
				si.name,
				str(_SNAPSHOT_REASON),
				readiness_evidence=evidence,
				readiness_summary_json=json.dumps(readiness, default=str),
			)
			locked = StdPublicationLockService.lock_for_approval(
				si.name,
				user=act or None,
				ignore_permissions=True,
			)
			act_log = act or prev_user
			emit_publication_audit_event(
				event_type=AUDIT_TENDER_PUBLICATION_CONFIGURATION_SNAPSHOT_CREATED,
				tender_code=canon,
				action="configuration_snapshot_created",
				performed_by=act_log,
				instance_code=si.name,
				configuration_snapshot_code=snap.name,
				details={"readiness_status": (readiness.get("status") or "").strip()},
			)
			emit_publication_audit_event(
				event_type=AUDIT_TENDER_PUBLICATION_SUBMITTED_FOR_APPROVAL,
				tender_code=canon,
				action="tender_submitted_for_approval",
				performed_by=act_log,
				instance_code=si.name,
				configuration_snapshot_code=snap.name,
				details={"readiness_status": (readiness.get("status") or "").strip()},
			)
			return {
				"ok": True,
				"tender_code": canon,
				"snapshot": snap.name,
				"snapshot_summary": _snapshot_summary(snap),
				"tender_std_instance": si.name,
				"instance_status": (locked.instance_status or "").strip(),
				"readiness": readiness,
			}
		finally:
			frappe.set_user(prev_user)

	@staticmethod
	def getCurrentConfigurationSnapshot(tender_code: str) -> dict[str, Any] | None:
		"""Return the latest **Final** ``Configuration`` snapshot for the tender's current STD instance."""
		raw = (tender_code or "").strip()
		tm2 = resolve_tm2_tender_document(raw)
		if not tm2:
			return None

		si = TenderStdBindingService.get_current_std_instance_for_tm2_tender(tm2.name)
		if not si:
			return None

		row = frappe.db.sql(
			"""
			select name
			from `tabTender STD Instance Snapshot`
			where tender_std_instance = %s
				and snapshot_type = 'Configuration'
				and snapshot_status = 'Final'
			order by created_at desc, modified desc
			limit 1
			""",
			(si.name,),
			as_dict=True,
		)
		if not row:
			return None
		doc = frappe.get_doc("Tender STD Instance Snapshot", row[0].name)
		return _snapshot_summary(doc)

	@staticmethod
	def invalidateConfigurationSnapshot(snapshot_code: str, reason: str, actor: str | None = None) -> None:
		"""Mark a **Final** configuration snapshot as **Superseded** (immutable evidence rule: Final→Superseded only).

		Does not unlock the STD instance; return-to-preparation / supersede flows are PUB-0320+.
		"""
		sc = (snapshot_code or "").strip()
		rs = (reason or "").strip()
		if not sc:
			frappe.throw(_("Snapshot code is required."), exc=frappe.ValidationError)
		if not rs:
			frappe.throw(_("Invalidation reason is required."), exc=frappe.ValidationError)

		prev_user = frappe.session.user
		act = (actor or "").strip()
		if act:
			frappe.set_user(act)
		try:
			if not frappe.db.exists("Tender STD Instance Snapshot", sc):
				frappe.throw(
					_("Tender STD Instance Snapshot {0} does not exist.").format(sc),
					frappe.DoesNotExistError,
				)
			doc = frappe.get_doc("Tender STD Instance Snapshot", sc)
			if (doc.snapshot_type or "").strip() != "Configuration":
				frappe.throw(
					_("Only Configuration snapshots can be invalidated through this service."),
					exc=frappe.ValidationError,
				)
			if (doc.snapshot_status or "").strip() != "Final":
				frappe.throw(
					_("Only Final configuration snapshots can be invalidated (status is {0}).").format(
						doc.snapshot_status,
					),
					exc=frappe.ValidationError,
				)
			doc.snapshot_status = "Superseded"
			doc.save(ignore_permissions=True)
		finally:
			frappe.set_user(prev_user)
