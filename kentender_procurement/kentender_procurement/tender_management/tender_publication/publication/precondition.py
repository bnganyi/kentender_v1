# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PUB-0400 — ``PublicationPreconditionService``.

Cursor pack §11 / std engine §10 — verify all gates immediately before a publication
transaction (``TM2 Tender`` lifecycle). An **Approved for Publication**
``Tender Publication Approval Decision`` on the **current** Final configuration snapshot is the
publication gate alongside TM2 ``status`` / readiness rules.
"""

from __future__ import annotations

from typing import Any

import frappe
from frappe import _
from frappe.model.document import Document

from kentender_procurement.tender_management.std_instance.parameter import (
	OUTPUT_KEY_TO_PARENT_FIELD,
	parse_outputs_stale_flags,
)
from kentender_procurement.tender_management.std_instance.snapshot import _compute_hashes_and_refs
from kentender_procurement.tender_management.tender_publication.approval.approval_decision import (
	DECISION_APPROVED,
)
from kentender_procurement.tender_management.tender_publication.evidence.evidence_package import (
	EvidencePackageService,
)
from kentender_procurement.tender_management.tender_publication.readiness.publication_readiness import (
	PublicationReadinessService,
)
from kentender_procurement.tender_management.tender_publication.readiness.schema import (
	is_critical_code,
)
from kentender_procurement.tender_management.tender_publication.snapshot.configuration_snapshot import (
	ConfigurationSnapshotService,
)
from kentender_procurement.tender_management.security.authorization.denial_codes import (
	DenialCode,
)
from kentender_procurement.tender_management.services.tm2_tender_resolve import (
	resolve_tm2_tender_document,
)

# Pack §11 — stable denial titles (``frappe.throw(..., title=…)``); SEC-0200 catalogue.
PUBLISH_PERMISSION_DENIED = DenialCode.PUBLISH_PERMISSION_DENIED
PUBLISH_APPROVAL_REQUIRED = DenialCode.PUBLISH_APPROVAL_REQUIRED
PUBLISH_READINESS_NOT_READY = DenialCode.PUBLISH_READINESS_NOT_READY
PUBLISH_OUTPUT_STALE = DenialCode.PUBLISH_OUTPUT_STALE
PUBLISH_OUTPUT_MISSING = DenialCode.PUBLISH_OUTPUT_MISSING
PUBLISH_EVIDENCE_PACKAGE_FAILED = DenialCode.PUBLISH_EVIDENCE_PACKAGE_FAILED
PUBLISH_CONFIGURATION_SNAPSHOT_MISSING = DenialCode.PUBLISH_CONFIGURATION_SNAPSHOT_MISSING

_NOT_CURRENT_TO_OUTPUT_TYPE: dict[str, str] = {
	"BUNDLE_NOT_CURRENT": "Bundle",
	"DSM_NOT_CURRENT": "DSM",
	"DOM_NOT_CURRENT": "DOM",
	"DEM_NOT_CURRENT": "DEM",
	"DCM_NOT_CURRENT": "DCM",
}


def _strip(value: str | None) -> str:
	return (value or "").strip()


def _effective_actor(actor: str | None) -> str:
	return _strip(actor) or _strip(frappe.session.user) or "Administrator"


def _assert_actor_authorized_to_publish(actor: str) -> None:
	if actor == "Guest":
		frappe.throw(_("Publishing is not allowed for this user."), title=PUBLISH_PERMISSION_DENIED, exc=frappe.ValidationError)
	from kentender_procurement.tender_management.tender_publication.authorization.publication_authorization import (
		PublicationAuthorizationService,
	)

	PublicationAuthorizationService.assertCanPublishTender(actor)


def _latest_approval_decision(tender_key: str) -> Document | None:
	tk = _strip(tender_key)
	if not tk:
		return None
	tm2 = resolve_tm2_tender_document(tk)
	if not tm2:
		return None
	filters: dict[str, str] = {"tm2_tender": tm2.name}
	rows = frappe.get_all(
		"Tender Publication Approval Decision",
		filters=filters,
		pluck="name",
		order_by="decided_at desc",
		limit=1,
	)
	if not rows:
		return None
	return frappe.get_doc("Tender Publication Approval Decision", rows[0])


def _stale_output_types_norm(inst: Document) -> set[str]:
	flags = parse_outputs_stale_flags(inst)
	return {str(x).strip().lower() for x in flags if str(x).strip()}


def _denial_title_for_finding(code: str, inst: Document | None) -> str:
	if code == "EVIDENCE_PACKAGE_FAILED":
		return PUBLISH_EVIDENCE_PACKAGE_FAILED
	if code == "OUTPUT_TRACE_MISSING":
		return PUBLISH_OUTPUT_MISSING

	out_type = _NOT_CURRENT_TO_OUTPUT_TYPE.get(code)
	if out_type and inst is not None:
		stale_norm = _stale_output_types_norm(inst)
		if out_type.lower() in stale_norm:
			return PUBLISH_OUTPUT_STALE
		return PUBLISH_OUTPUT_MISSING

	if code in _NOT_CURRENT_TO_OUTPUT_TYPE:
		return PUBLISH_OUTPUT_STALE

	return PUBLISH_READINESS_NOT_READY


def _first_publish_denial_from_readiness(
	findings: list[dict[str, Any]],
	inst: Document,
) -> tuple[str, str] | None:
	"""Return ``(title, detail)`` for the highest-priority denial, or ``None`` if none."""
	critical = [f for f in findings if is_critical_code(_strip(str(f.get("code") or "")))]
	if not critical:
		return None

	priority_order = (
		"BUNDLE_NOT_CURRENT",
		"DSM_NOT_CURRENT",
		"DOM_NOT_CURRENT",
		"DEM_NOT_CURRENT",
		"DCM_NOT_CURRENT",
		"OUTPUT_TRACE_MISSING",
		"EVIDENCE_PACKAGE_FAILED",
	)

	def sort_key(f: dict[str, Any]) -> tuple[int, int]:
		c = _strip(str(f.get("code") or ""))
		try:
			p = priority_order.index(c)
		except ValueError:
			p = len(priority_order)
		return (p, critical.index(f))

	critical_sorted = sorted(critical, key=sort_key)
	for f in critical_sorted:
		code = _strip(str(f.get("code") or ""))
		if not code:
			continue
		title = _denial_title_for_finding(code, inst)
		msg = _strip(str(f.get("message") or "")) or _("Publication readiness blocked ({0}).").format(code)
		return title, msg

	return PUBLISH_READINESS_NOT_READY, _("Publication readiness is not Ready.")


def _assert_publication_snapshot_feasible(inst: Document) -> None:
	"""Pack §11 — publication snapshot *can be created* (hash/refs computable, required refs present)."""
	try:
		_ph, _wh, _ah, _bh, _ch, refs = _compute_hashes_and_refs(inst, output_ref_overrides=None)
	except Exception as exc:  # noqa: BLE001 — surface as readiness gate
		frappe.throw(
			str(exc),
			title=PUBLISH_READINESS_NOT_READY,
			exc=frappe.ValidationError,
		)
	for key in OUTPUT_KEY_TO_PARENT_FIELD:
		if not (refs.get(key) or "").strip():
			frappe.throw(
				_("Generated output reference for {0} is missing; cannot build publication snapshot.").format(key),
				title=PUBLISH_OUTPUT_MISSING,
				exc=frappe.ValidationError,
			)


class PublicationPreconditionService:
	"""Publication precondition gate (PUB-0400 / pack §11)."""

	@staticmethod
	def assertCanPublish(tender_code: str, actor: str | None = None) -> None:
		"""Raise ``frappe.ValidationError`` (or ``DoesNotExistError``) unless all pack §11 preconditions hold."""
		tc = _strip(tender_code)
		act = _effective_actor(actor)
		if not tc:
			frappe.throw(_("Tender code is required."), exc=frappe.ValidationError)
		if not resolve_tm2_tender_document(tc):
			frappe.throw(
				_("TM2 Tender {0} does not exist.").format(tc),
				frappe.DoesNotExistError,
			)

		_assert_actor_authorized_to_publish(act)

		cur = ConfigurationSnapshotService.getCurrentConfigurationSnapshot(tc)
		if not cur:
			frappe.throw(
				_("A current Final configuration snapshot is required to publish."),
				title=PUBLISH_CONFIGURATION_SNAPSHOT_MISSING,
				exc=frappe.ValidationError,
			)

		snap_code = _strip(str(cur.get("snapshot_code") or ""))
		si_name = _strip(str(cur.get("tender_std_instance") or ""))
		if not snap_code or not si_name:
			frappe.throw(
				_("Configuration snapshot summary is incomplete."),
				title=PUBLISH_CONFIGURATION_SNAPSHOT_MISSING,
				exc=frappe.ValidationError,
			)

		dec = _latest_approval_decision(tc)
		if not dec or _strip(dec.decision) != DECISION_APPROVED:
			frappe.throw(
				_("Latest publication approval decision must be Approved for Publication."),
				title=PUBLISH_APPROVAL_REQUIRED,
				exc=frappe.ValidationError,
			)
		if _strip(dec.configuration_snapshot) != snap_code:
			frappe.throw(
				_("Approval decision does not match the current configuration snapshot; re-approve after changes."),
				title=PUBLISH_APPROVAL_REQUIRED,
				exc=frappe.ValidationError,
			)
		if _strip(dec.tender_std_instance) != si_name:
			frappe.throw(
				_("Approval decision does not match the bound Tender STD Instance."),
				title=PUBLISH_APPROVAL_REQUIRED,
				exc=frappe.ValidationError,
			)

		# Use DB value — ``get_doc`` can return a stale ``instance_status`` in the same request after PUB-0600 publish.
		st_inst = _strip(frappe.db.get_value("Tender STD Instance", si_name, "instance_status") or "")
		if st_inst != "Locked for Approval":
			frappe.throw(
				_("STD Instance must be Locked for Approval before publish (current: {0}).").format(st_inst or _("Unknown")),
				title=PUBLISH_APPROVAL_REQUIRED,
				exc=frappe.ValidationError,
			)

		inst = frappe.get_doc("Tender STD Instance", si_name)
		readiness = PublicationReadinessService.runReadiness(tc, act)
		if (readiness.get("status") or "").strip() != "Ready":
			denial = _first_publish_denial_from_readiness(list(readiness.get("findings") or []), inst)
			if denial:
				title, detail = denial
				frappe.throw(detail, title=title, exc=frappe.ValidationError)
			frappe.throw(
				_("Publication readiness is not Ready (status {0}).").format(readiness.get("status")),
				title=PUBLISH_READINESS_NOT_READY,
				exc=frappe.ValidationError,
			)

		inst.reload()

		evidence = EvidencePackageService.validateEvidencePackage(tc)
		if not bool(evidence.get("ok", False)):
			frappe.throw(
				_("{0}").format(
					_strip(str(evidence.get("message") or evidence.get("reason") or ""))
					or _("Evidence package validation failed."),
				),
				title=PUBLISH_EVIDENCE_PACKAGE_FAILED,
				exc=frappe.ValidationError,
			)

		_assert_publication_snapshot_feasible(inst)
