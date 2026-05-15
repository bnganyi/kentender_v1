# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PUB-0500 — ``PublicationSnapshotService`` (tender-level publication snapshot).

Creates a **``Tender Publication Snapshot``** row (pack §12 / std §11) plus a **Publication**
``Tender STD Instance Snapshot`` via ``StdInstanceSnapshotService.create_publication_snapshot``,
binding exact output codes, readiness fingerprint, approval decision, and evidence fingerprint.

**Design:** tender-level DocType (not only STD row) so ``readiness_result_code``,
``approval_decision_code``, ``evidence_package_code``, and ``complete_publication_hash`` are
first-class. STD Publication snapshot remains the technical hash anchor.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import now_datetime

from kentender_procurement.tender_management.std_instance.readiness import (
	VALID_CURRENT_OUTPUT_STATUSES,
)
from kentender_procurement.tender_management.std_instance.snapshot import StdInstanceSnapshotService
from kentender_procurement.tender_management.tender_publication.approval.approval_decision import (
	DECISION_APPROVED,
)
from kentender_procurement.tender_management.tender_publication.evidence.evidence_package import (
	EvidencePackageService,
)
from kentender_procurement.tender_management.tender_publication.publication.precondition import (
	PublicationPreconditionService,
)
from kentender_procurement.tender_management.tender_publication.readiness.publication_readiness import (
	PublicationReadinessService,
)
from kentender_procurement.tender_management.tender_publication.snapshot.configuration_snapshot import (
	ConfigurationSnapshotService,
)
from kentender_procurement.tender_management.tender_publication.audit.codes import (
	AUDIT_TENDER_PUBLICATION_PUBLICATION_SNAPSHOT_CREATED,
)
from kentender_procurement.tender_management.tender_publication.audit.publication_audit import (
	emit_publication_audit_event,
)
from kentender_procurement.tender_management.services.tm2_tender_resolve import (
	canonical_tm2_tender_code,
	resolve_tm2_tender_document,
)

PUBLICATION_SNAPSHOT_ALREADY_FINAL = "PUBLICATION_SNAPSHOT_ALREADY_FINAL"
PUBLICATION_SNAPSHOT_CONFIGURATION_INVALID = "PUBLICATION_SNAPSHOT_CONFIGURATION_INVALID"
PUBLICATION_SNAPSHOT_OUTPUT_STALE = "PUBLICATION_SNAPSHOT_OUTPUT_STALE"
PUBLICATION_SNAPSHOT_OUTPUT_MISSING = "PUBLICATION_SNAPSHOT_OUTPUT_MISSING"
PUBLICATION_SNAPSHOT_OUTPUT_INVALID = "PUBLICATION_SNAPSHOT_OUTPUT_INVALID"

_STD_REF_FIELDS: tuple[tuple[str, str], ...] = (
	("Bundle", "ref_bundle_output"),
	("DSM", "ref_dsm_output"),
	("DOM", "ref_dom_output"),
	("DEM", "ref_dem_output"),
	("DCM", "ref_dcm_output"),
)

_FIELD_TO_SNAPSHOT_ATTR: dict[str, str] = {
	"ref_bundle_output": "bundle_output_code",
	"ref_dsm_output": "dsm_output_code",
	"ref_dom_output": "dom_output_code",
	"ref_dem_output": "dem_output_code",
	"ref_dcm_output": "dcm_output_code",
}


def _strip(value: str | None) -> str:
	return (value or "").strip()


def _effective_actor(actor: str | None) -> str:
	return _strip(actor) or _strip(frappe.session.user) or "Administrator"


def _sha256_hex(text: str) -> str:
	return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _sha256_json(obj: Any) -> str:
	return _sha256_hex(json.dumps(obj, sort_keys=True, default=str, separators=(",", ":")))


def _latest_approved_decision(tender_key: str) -> Document:
	tk = _strip(tender_key)
	tm2 = resolve_tm2_tender_document(tk)
	if not tm2:
		frappe.throw(_("TM2 Tender {0} does not exist.").format(tk), exc=frappe.DoesNotExistError)
	filters: dict[str, str] = {"tm2_tender": tm2.name}
	rows = frappe.get_all(
		"Tender Publication Approval Decision",
		filters=filters,
		pluck="name",
		order_by="decided_at desc",
		limit=1,
	)
	if not rows:
		frappe.throw(_("No publication approval decision found."), exc=frappe.ValidationError)
	doc = frappe.get_doc("Tender Publication Approval Decision", rows[0])
	if _strip(doc.decision) != DECISION_APPROVED:
		frappe.throw(_("Latest approval decision is not Approved for Publication."), exc=frappe.ValidationError)
	return doc


def _assert_std_publication_refs_valid(std_pub: Document) -> None:
	if (_strip(std_pub.snapshot_type) != "Publication") or (_strip(std_pub.snapshot_status) != "Final"):
		frappe.throw(
			_("STD publication snapshot is not a Final Publication row."),
			title=PUBLICATION_SNAPSHOT_CONFIGURATION_INVALID,
			exc=frappe.ValidationError,
		)
	for _label, field in _STD_REF_FIELDS:
		code = _strip(std_pub.get(field))
		if not code:
			frappe.throw(
				_("{0} output reference is missing on publication snapshot.").format(_label),
				title=PUBLICATION_SNAPSHOT_OUTPUT_MISSING,
				exc=frappe.ValidationError,
			)
		if not frappe.db.exists("Tender STD Generated Output", code):
			frappe.throw(
				_("Generated output {0} does not exist.").format(code),
				title=PUBLICATION_SNAPSHOT_OUTPUT_MISSING,
				exc=frappe.ValidationError,
			)
		row = frappe.get_doc("Tender STD Generated Output", code)
		st = _strip(row.output_status)
		if st == "Stale":
			frappe.throw(
				_("Generated output {0} is Stale.").format(_label),
				title=PUBLICATION_SNAPSHOT_OUTPUT_STALE,
				exc=frappe.ValidationError,
			)
		if st not in VALID_CURRENT_OUTPUT_STATUSES:
			frappe.throw(
				_("Generated output {0} has invalid status {1}.").format(_label, st or _("Unknown")),
				title=PUBLICATION_SNAPSHOT_OUTPUT_INVALID,
				exc=frappe.ValidationError,
			)


def _assert_no_final_tender_publication_snapshot(tender_key: str) -> None:
	tk = _strip(tender_key)
	tm2 = resolve_tm2_tender_document(tk)
	if not tm2:
		frappe.throw(_("TM2 Tender {0} does not exist.").format(tk), exc=frappe.DoesNotExistError)
	filters: dict[str, Any] = {"snapshot_status": "Final", "tm2_tender": tm2.name}
	found = frappe.get_all(
		"Tender Publication Snapshot",
		filters=filters,
		limit=1,
		pluck="name",
	)
	if found:
		frappe.throw(
			_("A Final tender publication snapshot already exists for this tender."),
			title=PUBLICATION_SNAPSHOT_ALREADY_FINAL,
			exc=frappe.ValidationError,
		)


def _readiness_result_code(readiness: dict[str, Any]) -> str:
	return "READINESS|" + _sha256_json(readiness)


def _evidence_package_code(tender_code: str, evidence: dict[str, Any]) -> str:
	return EvidencePackageService.evidence_package_code_from_validation(tender_code, evidence)


def _complete_publication_hash(
	*,
	std_pub: Document,
	readiness_code: str,
	approval_decision: str,
	evidence_code: str,
) -> str:
	parts = [
		_strip(std_pub.name),
		_strip(std_pub.complete_instance_hash),
		readiness_code,
		approval_decision,
		evidence_code,
	]
	return _sha256_hex("|".join(parts))


def _doc_to_public_dict(doc: Document) -> dict[str, Any]:
	tm2_link = _strip(getattr(doc, "tm2_tender", None))
	if not tm2_link:
		frappe.throw(_("Tender publication snapshot has no TM2 tender."), exc=frappe.ValidationError)
	tm2_row = frappe.get_doc("TM2 Tender", tm2_link)
	tcode = canonical_tm2_tender_code(tm2_row)
	return {
		"snapshot_code": doc.name,
		"tender_code": tcode,
		"package_code": _strip(doc.procurement_package) or None,
		"std_instance_code": doc.tender_std_instance,
		"template_version_code": doc.source_template_version_code,
		"applicability_profile_code": doc.applicability_profile_code,
		"configuration_snapshot_code": doc.configuration_snapshot,
		"std_publication_snapshot_code": doc.std_publication_snapshot,
		"bundle_output_code": doc.bundle_output_code,
		"dsm_output_code": doc.dsm_output_code,
		"dom_output_code": doc.dom_output_code,
		"dem_output_code": doc.dem_output_code,
		"dcm_output_code": doc.dcm_output_code,
		"readiness_result_code": doc.readiness_result_code,
		"approval_decision_code": doc.approval_decision_code,
		"evidence_package_code": doc.evidence_package_code,
		"complete_publication_hash": doc.complete_publication_hash,
		"created_by": doc.created_by,
		"created_at": doc.created_at,
		"snapshot_status": doc.snapshot_status,
	}


class PublicationSnapshotService:
	"""Tender-level publication snapshot (PUB-0500)."""

	@staticmethod
	def insert_publication_snapshots_after_precheck(tender_code: str, actor: str | None = None) -> dict[str, Any]:
		"""Persist STD **Publication** snapshot + **Tender Publication Snapshot** (Final).

		Caller must already have run ``PublicationPreconditionService.assertCanPublish`` and
		``_assert_no_final_tender_publication_snapshot`` (PUB-0600 atomic publish).
		"""
		tc = _strip(tender_code)
		act = _effective_actor(actor)
		cur = ConfigurationSnapshotService.getCurrentConfigurationSnapshot(tc)
		if not cur:
			frappe.throw(
				_("Current configuration snapshot is missing."),
				title=PUBLICATION_SNAPSHOT_CONFIGURATION_INVALID,
				exc=frappe.ValidationError,
			)
		cfg_code = _strip(str(cur.get("snapshot_code") or ""))
		si_name = _strip(str(cur.get("tender_std_instance") or ""))
		cfg_doc = frappe.get_doc("Tender STD Instance Snapshot", cfg_code)
		if _strip(cfg_doc.snapshot_type) != "Configuration" or _strip(cfg_doc.snapshot_status) != "Final":
			frappe.throw(
				_("Configuration snapshot is not Final."),
				title=PUBLICATION_SNAPSHOT_CONFIGURATION_INVALID,
				exc=frappe.ValidationError,
			)
		tm2_doc = resolve_tm2_tender_document(tc)
		if not tm2_doc:
			frappe.throw(
				_("TM2 Tender {0} does not exist.").format(tc),
				frappe.DoesNotExistError,
			)
		if _strip(cfg_doc.tender_std_instance) != si_name:
			frappe.throw(
				_("Configuration snapshot does not match tender or STD instance."),
				title=PUBLICATION_SNAPSHOT_CONFIGURATION_INVALID,
				exc=frappe.ValidationError,
			)
		si_tm2 = _strip(frappe.db.get_value("Tender STD Instance", si_name, "tm2_tender") or "")
		if not si_tm2 or si_tm2 != tm2_doc.name:
			frappe.throw(
				_("Configuration snapshot STD instance is not bound to this TM2 tender."),
				title=PUBLICATION_SNAPSHOT_CONFIGURATION_INVALID,
				exc=frappe.ValidationError,
			)

		canon_tc = canonical_tm2_tender_code(tm2_doc)
		dec = _latest_approved_decision(tc)
		if _strip(dec.configuration_snapshot) != cfg_code:
			frappe.throw(
				_("Approval decision does not reference the current configuration snapshot."),
				title=PUBLICATION_SNAPSHOT_CONFIGURATION_INVALID,
				exc=frappe.ValidationError,
			)

		readiness = PublicationReadinessService.runReadiness(tc, act)
		readiness_code = _readiness_result_code(readiness)

		evidence = EvidencePackageService.validateEvidencePackage(tc)
		if not bool(evidence.get("ok", False)):
			frappe.throw(
				_("Evidence package validation failed."),
				exc=frappe.ValidationError,
			)
		evidence_code = _evidence_package_code(tc, evidence)

		std_pub = StdInstanceSnapshotService.create_publication_snapshot(
			si_name,
			_("Tender publication binding (PUB-0500)."),
			snapshot_status="Final",
		)
		_assert_std_publication_refs_valid(std_pub)

		tm2_doc = resolve_tm2_tender_document(tc)
		if not tm2_doc:
			frappe.throw(
				_("TM2 Tender {0} does not exist.").format(tc),
				frappe.DoesNotExistError,
			)
		inst = frappe.get_doc("Tender STD Instance", si_name)

		pub_hash = _complete_publication_hash(
			std_pub=std_pub,
			readiness_code=readiness_code,
			approval_decision=dec.name,
			evidence_code=evidence_code,
		)

		user = frappe.session.user
		if user == "Guest":
			user = "Administrator"

		row = frappe.new_doc("Tender Publication Snapshot")
		row.tm2_tender = tm2_doc.name
		pkg = _strip(tm2_doc.procurement_package)
		if pkg:
			row.procurement_package = pkg
		row.tender_std_instance = si_name
		row.configuration_snapshot = cfg_code
		row.std_publication_snapshot = std_pub.name
		row.source_template_version_code = _strip(inst.template_version_code) or _strip(std_pub.source_template_version_code)
		row.applicability_profile_code = _strip(inst.applicability_profile_code)
		for ref_field, attr in _FIELD_TO_SNAPSHOT_ATTR.items():
			setattr(row, attr, _strip(std_pub.get(ref_field)))
		row.readiness_result_code = readiness_code
		row.approval_decision_code = dec.name
		row.evidence_package_code = evidence_code
		row.complete_publication_hash = pub_hash
		row.snapshot_status = "Final"
		row.created_by = user
		row.created_at = now_datetime()
		row.insert(ignore_permissions=True)

		emit_publication_audit_event(
			event_type=AUDIT_TENDER_PUBLICATION_PUBLICATION_SNAPSHOT_CREATED,
			tender_code=canon_tc,
			action="publication_snapshot_created",
			performed_by=user,
			instance_code=si_name,
			configuration_snapshot_code=cfg_code,
			publication_snapshot_code=row.name,
			std_publication_snapshot_code=std_pub.name,
			details={
				"evidence_package_code": evidence_code,
				"readiness_result_code": readiness_code,
				"approval_decision_code": dec.name,
			},
		)

		return {
			"publication_snapshot": _doc_to_public_dict(frappe.get_doc("Tender Publication Snapshot", row.name)),
			"tender_std_instance": si_name,
		}

	@staticmethod
	def createPublicationSnapshot(tender_code: str, actor: str | None = None) -> dict[str, Any]:
		"""Create Final **Tender Publication Snapshot** and underlying STD **Publication** snapshot."""
		tc = _strip(tender_code)
		act = _effective_actor(actor)
		if not tc:
			frappe.throw(_("Tender code is required."), exc=frappe.ValidationError)
		if not resolve_tm2_tender_document(tc):
			frappe.throw(
				_("TM2 Tender {0} does not exist.").format(tc),
				frappe.DoesNotExistError,
			)

		prev_user = frappe.session.user
		if act:
			frappe.set_user(act)
		try:
			_assert_no_final_tender_publication_snapshot(tc)
			PublicationPreconditionService.assertCanPublish(tc, act)

			inner = PublicationSnapshotService.insert_publication_snapshots_after_precheck(tc, act)
			return {"ok": True, "publication_snapshot": inner["publication_snapshot"]}
		finally:
			frappe.set_user(prev_user)

	@staticmethod
	def getPublicationSnapshot(tender_code: str) -> dict[str, Any] | None:
		"""Return the latest **Final** tender publication snapshot summary, or ``None``."""
		tc = _strip(tender_code)
		if not tc:
			return None
		tm2 = resolve_tm2_tender_document(tc)
		if not tm2:
			return None
		filters: dict[str, Any] = {"tm2_tender": tm2.name, "snapshot_status": "Final"}
		names = frappe.get_all(
			"Tender Publication Snapshot",
			filters=filters,
			pluck="name",
			order_by="created_at desc, modified desc",
			limit=1,
		)
		if not names:
			return None
		doc = frappe.get_doc("Tender Publication Snapshot", names[0])
		return _doc_to_public_dict(doc)
