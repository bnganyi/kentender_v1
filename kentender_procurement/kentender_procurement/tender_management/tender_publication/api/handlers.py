# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PUB-0900 — Publication API (pack §17).

Maps REST-style resources to ``frappe.call`` targets::

	POST .../publication-readiness              → ``pub_api_run_publication_readiness``
	GET  .../publication-readiness/latest       → ``pub_api_get_latest_publication_readiness``
	POST .../submit-for-approval                → ``pub_api_submit_for_approval``
	GET  .../approval-review-package             → ``pub_api_get_approval_review_package``
	POST .../approval/approve                  → ``pub_api_approve_for_publication``
	POST .../approval/return                   → ``pub_api_return_for_correction``
	POST .../approval/reject                   → ``pub_api_reject_publication``
	POST .../publish                           → ``pub_api_publish_tender``
	GET  .../publication-snapshot              → ``pub_api_get_publication_snapshot``
	POST .../evidence/validate                 → ``pub_api_validate_evidence_package``
	GET  .../evidence/export                   → ``pub_api_export_evidence_package``

**Error envelope** (pack §17)::

	{"success": false, "error_code": "...", "message": "...", "details": {}}

``tender_code`` may be the **TM2 Tender** document ``name``, business ``tender_code`` (TND-*),
or a unique ``tender_reference``. Raw stack traces are never returned; unexpected errors are
logged server-side.
"""

from __future__ import annotations

import json
from typing import Any, Callable

import frappe
from frappe import _

from kentender_procurement.tender_management.services.tm2_tender_resolve import resolve_tm2_tender_document
from kentender_procurement.tender_management.tender_publication.approval.approval_decision import (
	ApprovalDecisionService,
)
from kentender_procurement.tender_management.tender_publication.approval.approval_review_package import (
	ApprovalReviewPackageService,
)
from kentender_procurement.tender_management.tender_publication.evidence.evidence_package import (
	EXPORT_FORMAT_ATTACHMENTS_ARCHIVE,
	EXPORT_FORMAT_AUDIT_LOG,
	EXPORT_FORMAT_GENERATED_MODEL_ARCHIVE,
	EXPORT_FORMAT_JSON_MANIFEST,
	EXPORT_FORMAT_PDF_BUNDLE,
	EvidencePackageService,
)
from kentender_procurement.tender_management.tender_publication.publication.transaction import (
	PublicationTransactionService,
)
from kentender_procurement.tender_management.tender_publication.readiness.publication_readiness import (
	PublicationReadinessService,
)
from kentender_procurement.tender_management.tender_publication.snapshot.configuration_snapshot import (
	ConfigurationSnapshotService,
)
from kentender_procurement.tender_management.tender_publication.snapshot.tender_publication_snapshot import (
	PublicationSnapshotService,
)

PUB_API_INTERNAL_ERROR = "PUB_API_INTERNAL_ERROR"
PUB_API_NOT_FOUND = "PUB_API_NOT_FOUND"
PUB_API_PERMISSION_DENIED = "PUB_API_PERMISSION_DENIED"
PUB_API_VALIDATION_FAILED = "PUB_API_VALIDATION_FAILED"
PUB_API_TENDER_CODE_REQUIRED = "PUB_API_TENDER_CODE_REQUIRED"
PUB_API_TENDER_AMBIGUOUS = "PUB_API_TENDER_AMBIGUOUS"
PUB_API_PAYLOAD_INVALID = "PUB_API_PAYLOAD_INVALID"

_DEFAULT_MSG_TITLE = "Message"

_FORMAT_SLUGS: dict[str, str] = {
	"json": EXPORT_FORMAT_JSON_MANIFEST,
	"manifest": EXPORT_FORMAT_JSON_MANIFEST,
	"json_manifest": EXPORT_FORMAT_JSON_MANIFEST,
	"audit": EXPORT_FORMAT_AUDIT_LOG,
	"audit_log": EXPORT_FORMAT_AUDIT_LOG,
	"audit_log_export": EXPORT_FORMAT_AUDIT_LOG,
	"model": EXPORT_FORMAT_GENERATED_MODEL_ARCHIVE,
	"model_archive": EXPORT_FORMAT_GENERATED_MODEL_ARCHIVE,
	"generated_model_json_archive": EXPORT_FORMAT_GENERATED_MODEL_ARCHIVE,
	"zip": EXPORT_FORMAT_ATTACHMENTS_ARCHIVE,
	"attachments": EXPORT_FORMAT_ATTACHMENTS_ARCHIVE,
	"document_attachments_archive": EXPORT_FORMAT_ATTACHMENTS_ARCHIVE,
	"pdf": EXPORT_FORMAT_PDF_BUNDLE,
	"pdf_bundle": EXPORT_FORMAT_PDF_BUNDLE,
}


def _api_fail(error_code: str, message: str, *, details: dict[str, Any] | None = None) -> dict[str, Any]:
	return {
		"success": False,
		"error_code": error_code,
		"message": str(message),
		"details": dict(details or {}),
	}


def _api_ok(**payload: Any) -> dict[str, Any]:
	out: dict[str, Any] = {"success": True}
	out.update(payload)
	return out


def _stable_title_from_message_log() -> str | None:
	log = frappe.get_message_log()
	if not log:
		return None
	t = (log[-1].get("title") or "").strip()
	if not t or t == _DEFAULT_MSG_TITLE or t == _("Message", context="Default title of the message dialog"):
		return None
	return t


def _wrap(handler_id: str, fn: Callable[[], dict[str, Any]]) -> dict[str, Any]:
	frappe.clear_messages()
	try:
		return fn()
	except frappe.PermissionError as exc:
		return _api_fail(PUB_API_PERMISSION_DENIED, str(exc), details={})
	except frappe.DoesNotExistError as exc:
		code = _stable_title_from_message_log() or PUB_API_NOT_FOUND
		return _api_fail(code, str(exc), details={})
	except frappe.ValidationError as exc:
		code = _stable_title_from_message_log() or PUB_API_VALIDATION_FAILED
		return _api_fail(code, str(exc), details={})
	except Exception:
		frappe.log_error(frappe.get_traceback(), f"PUB-0900 {handler_id}")
		return _api_fail(PUB_API_INTERNAL_ERROR, _("Unexpected server error."), details={})


def _resolve_tender_for_pub_api(raw: str) -> tuple[str | None, dict[str, Any] | None]:
	c = (raw or "").strip()
	if not c:
		return None, _api_fail(
			PUB_API_TENDER_CODE_REQUIRED,
			_("tender_code is required."),
			details={},
		)
	rows = frappe.get_all("TM2 Tender", filters={"tender_reference": c}, pluck="name", limit=3)
	if len(rows) > 1:
		return None, _api_fail(
			PUB_API_TENDER_AMBIGUOUS,
			_("More than one TM2 Tender matches this tender_reference."),
			details={"tender_code": c, "candidates": rows},
		)
	tm2 = resolve_tm2_tender_document(c)
	if not tm2:
		return None, _api_fail(
			PUB_API_NOT_FOUND,
			_("TM2 Tender not found."),
			details={"tender_code": c},
		)
	return tm2.name, None


def _as_payload_dict(raw: Any) -> dict[str, Any]:
	if raw is None:
		return {}
	if isinstance(raw, dict):
		return dict(raw)
	if isinstance(raw, str):
		s = raw.strip()
		if not s:
			return {}
		try:
			parsed = json.loads(s)
		except json.JSONDecodeError:
			frappe.throw(
				_("Payload must be valid JSON."),
				title=PUB_API_PAYLOAD_INVALID,
				exc=frappe.ValidationError,
			)
		if not isinstance(parsed, dict):
			frappe.throw(
				_("Payload must be a JSON object."),
				title=PUB_API_PAYLOAD_INVALID,
				exc=frappe.ValidationError,
			)
		return dict(parsed)
	frappe.throw(
		_("Payload must be a dict or JSON object."),
		title=PUB_API_PAYLOAD_INVALID,
		exc=frappe.ValidationError,
	)


@frappe.whitelist()
def pub_api_run_publication_readiness(tender_code: str, actor: str | None = None) -> dict[str, Any]:
	"""POST ``/api/tenders/{tender_code}/publication-readiness``."""

	def _run() -> dict[str, Any]:
		tn, err = _resolve_tender_for_pub_api(tender_code)
		if err:
			return err
		assert tn is not None
		res = PublicationReadinessService.runReadiness(tn, actor)
		return _api_ok(readiness=res)

	return _wrap("run_publication_readiness", _run)


@frappe.whitelist()
def pub_api_get_latest_publication_readiness(tender_code: str) -> dict[str, Any]:
	"""GET ``/api/tenders/{tender_code}/publication-readiness/latest``."""

	def _run() -> dict[str, Any]:
		tn, err = _resolve_tender_for_pub_api(tender_code)
		if err:
			return err
		assert tn is not None
		res = PublicationReadinessService.getLatestReadiness(tn)
		return _api_ok(readiness=res)

	return _wrap("get_latest_publication_readiness", _run)


@frappe.whitelist()
def pub_api_submit_for_approval(tender_code: str, actor: str | None = None) -> dict[str, Any]:
	"""POST ``/api/tenders/{tender_code}/submit-for-approval`` (configuration snapshot)."""

	def _run() -> dict[str, Any]:
		tn, err = _resolve_tender_for_pub_api(tender_code)
		if err:
			return err
		assert tn is not None
		res = ConfigurationSnapshotService.createConfigurationSnapshot(tn, actor)
		return _api_ok(configuration_snapshot=res)

	return _wrap("submit_for_approval", _run)


@frappe.whitelist()
def pub_api_get_approval_review_package(tender_code: str, actor: str | None = None) -> dict[str, Any]:
	"""GET ``/api/tenders/{tender_code}/approval-review-package``."""

	def _run() -> dict[str, Any]:
		tn, err = _resolve_tender_for_pub_api(tender_code)
		if err:
			return err
		assert tn is not None
		res = ApprovalReviewPackageService.getApprovalReviewPackage(tn, actor)
		return _api_ok(review_package=res)

	return _wrap("get_approval_review_package", _run)


@frappe.whitelist()
def pub_api_approve_for_publication(
	tender_code: str,
	decision_payload: str | dict[str, Any] | None = None,
	actor: str | None = None,
) -> dict[str, Any]:
	"""POST ``/api/tenders/{tender_code}/approval/approve``."""

	def _run() -> dict[str, Any]:
		tn, err = _resolve_tender_for_pub_api(tender_code)
		if err:
			return err
		assert tn is not None
		payload = _as_payload_dict(decision_payload)
		res = ApprovalDecisionService.approveForPublication(tn, payload, actor)
		return _api_ok(decision=res)

	return _wrap("approve_for_publication", _run)


@frappe.whitelist()
def pub_api_return_for_correction(
	tender_code: str,
	return_payload: str | dict[str, Any] | None = None,
	actor: str | None = None,
) -> dict[str, Any]:
	"""POST ``/api/tenders/{tender_code}/approval/return``."""

	def _run() -> dict[str, Any]:
		tn, err = _resolve_tender_for_pub_api(tender_code)
		if err:
			return err
		assert tn is not None
		payload = _as_payload_dict(return_payload)
		res = ApprovalDecisionService.returnForCorrection(tn, payload, actor)
		return _api_ok(return_result=res)

	return _wrap("return_for_correction", _run)


@frappe.whitelist()
def pub_api_reject_publication(
	tender_code: str,
	decision_payload: str | dict[str, Any] | None = None,
	actor: str | None = None,
) -> dict[str, Any]:
	"""POST ``/api/tenders/{tender_code}/approval/reject``."""

	def _run() -> dict[str, Any]:
		tn, err = _resolve_tender_for_pub_api(tender_code)
		if err:
			return err
		assert tn is not None
		payload = _as_payload_dict(decision_payload)
		res = ApprovalDecisionService.rejectPublication(tn, payload, actor)
		return _api_ok(decision=res)

	return _wrap("reject_publication", _run)


@frappe.whitelist()
def pub_api_publish_tender(tender_code: str, actor: str | None = None) -> dict[str, Any]:
	"""POST ``/api/tenders/{tender_code}/publish``."""

	def _run() -> dict[str, Any]:
		tn, err = _resolve_tender_for_pub_api(tender_code)
		if err:
			return err
		assert tn is not None
		res = PublicationTransactionService.publishTender(tn, actor)
		return _api_ok(publication=res)

	return _wrap("publish_tender", _run)


@frappe.whitelist()
def pub_api_get_publication_snapshot(tender_code: str) -> dict[str, Any]:
	"""GET ``/api/tenders/{tender_code}/publication-snapshot``."""

	def _run() -> dict[str, Any]:
		tn, err = _resolve_tender_for_pub_api(tender_code)
		if err:
			return err
		assert tn is not None
		res = PublicationSnapshotService.getPublicationSnapshot(tn)
		if res is None:
			return _api_ok(publication_snapshot=None)
		return _api_ok(publication_snapshot=res)

	return _wrap("get_publication_snapshot", _run)


@frappe.whitelist()
def pub_api_validate_evidence_package(tender_code: str) -> dict[str, Any]:
	"""POST ``/api/tenders/{tender_code}/evidence/validate``.

	On success, ``validation`` contains the full ``EvidencePackageService`` result
	(``ok``, ``missing``, ``message``, ``manifest``, ``fingerprint``) — business
	rule failures use ``validation.ok == false`` without transport-level failure.
	"""

	def _run() -> dict[str, Any]:
		tn, err = _resolve_tender_for_pub_api(tender_code)
		if err:
			return err
		assert tn is not None
		val = EvidencePackageService.validateEvidencePackage(tn)
		return _api_ok(validation=val)

	return _wrap("validate_evidence_package", _run)


def _normalize_export_format_slug(raw: str | None) -> str | None:
	if raw is None:
		return None
	key = (raw or "").strip().lower().replace(" ", "").replace("-", "_")
	return _FORMAT_SLUGS.get(key) or _FORMAT_SLUGS.get(key.replace("_", ""))


@frappe.whitelist()
def pub_api_export_evidence_package(
	tender_code: str,
	export_format: str | None = None,
	evidence_format: str | None = None,
) -> dict[str, Any]:
	"""GET ``/api/tenders/{tender_code}/evidence/export?format=…``.

	``export_format`` / ``evidence_format`` accept slugs: ``json``, ``audit``,
	``model_archive``, ``zip``, ``pdf`` (maps to internal ``EXPORT_FORMAT_*``).
	"""

	def _run() -> dict[str, Any]:
		tn, err = _resolve_tender_for_pub_api(tender_code)
		if err:
			return err
		assert tn is not None
		fmt_raw = (export_format or evidence_format or "").strip()
		fmt = _normalize_export_format_slug(fmt_raw)
		if not fmt:
			return _api_fail(
				PUB_API_PAYLOAD_INVALID,
				_("export_format is required (e.g. json, audit, model_archive, zip, pdf)."),
				details={"export_format": fmt_raw or None},
			)
		res = EvidencePackageService.exportEvidencePackage(tn, fmt)
		return _api_ok(export=res)

	return _wrap("export_evidence_package", _run)
