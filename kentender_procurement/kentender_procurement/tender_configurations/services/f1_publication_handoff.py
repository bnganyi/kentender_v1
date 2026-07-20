# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""F1 Confirmed Tender Document Package + Publication handoff helpers."""

from __future__ import annotations

import hashlib
import json
from typing import Any

import frappe
from frappe.utils import cstr, now_datetime

from kentender_procurement.tender_configurations.constants import (
	STATUS_SENT_TO_PUBLICATION,
)
from kentender_procurement.tender_configurations.services.contract_carry_forward import (
	build_carry_forward_bundle_from_contract_values,
)

PACKAGE_DOCTYPE = "Confirmed Tender Document Package"
PUBLICATION_DOCTYPE = "IT Tender Publication Record"

PACKAGE_STATUS_CONFIRMED = "Confirmed"
PACKAGE_STATUS_AWAITING = "Awaiting Publication Setup"
PACKAGE_STATUS_INVALIDATED = "Invalidated"

PUBLICATION_STATUS_AWAITING = "Awaiting Publication Setup"
PUBLICATION_STATUS_CANCELLED = "Cancelled"
PUBLICATION_STATUS_RETURNED = "Returned"

ACTIVE_PACKAGE_STATUSES = frozenset({PACKAGE_STATUS_CONFIRMED, PACKAGE_STATUS_AWAITING})

CFG_LOCK_FIELDS = (
	"tds_values",
	"it_requirements",
	"implementation_schedule",
	"system_inventory",
	"price_schedule",
	"evaluation_setup",
	"forms_and_evidence",
	"contract_values",
	"bidder_submission_schema",
	"std_version",
	"short_scope_summary",
	"lot_structure",
	"tender_title",
)


def _parse_blob(raw: Any) -> dict[str, Any]:
	if not raw:
		return {}
	if isinstance(raw, dict):
		return raw
	if isinstance(raw, str):
		try:
			parsed = json.loads(raw)
			return parsed if isinstance(parsed, dict) else {}
		except (TypeError, ValueError):
			return {}
	return {}


def _json_dump(value: Any) -> str:
	return json.dumps(value if value is not None else {}, sort_keys=True, default=str)


def compute_configuration_version(doc) -> str:
	"""Stable hash of approved configuration snapshot fields."""
	parts = []
	for field in CFG_LOCK_FIELDS:
		parts.append(f"{field}={cstr(getattr(doc, field, None) or '')}")
	parts.append(f"std={cstr(getattr(doc, 'std_version', None) or '')}")
	parts.append(f"modified={cstr(getattr(doc, 'modified', None) or '')}")
	return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()


def compute_document_hash(html_doc: str, configuration_version: str, std_version: str) -> str:
	payload = f"{cstr(html_doc)}\n{cstr(configuration_version)}\n{cstr(std_version)}"
	return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def get_active_package_name(configuration_id: str) -> str | None:
	"""Return the configuration-linked active package, if any."""
	linked = cstr(
		frappe.db.get_value("Tender Configuration", configuration_id, "confirmed_document_package")
		or ""
	)
	if linked and frappe.db.exists(PACKAGE_DOCTYPE, linked):
		status = cstr(frappe.db.get_value(PACKAGE_DOCTYPE, linked, "package_status") or "")
		if status in ACTIVE_PACKAGE_STATUSES:
			return linked
	# Fallback for mid-confirm before link is persisted.
	name = frappe.db.get_value(
		PACKAGE_DOCTYPE,
		{
			"configuration": configuration_id,
			"package_status": ["in", list(ACTIVE_PACKAGE_STATUSES)],
		},
		"name",
		order_by="creation desc",
	)
	return cstr(name) if name else None


def configuration_is_locked_for_edit(configuration_id: str) -> bool:
	"""True when the configuration still points at an active confirmed package."""
	linked = cstr(
		frappe.db.get_value("Tender Configuration", configuration_id, "confirmed_document_package")
		or ""
	)
	if not linked:
		return False
	status = cstr(frappe.db.get_value(PACKAGE_DOCTYPE, linked, "package_status") or "")
	return status in ACTIVE_PACKAGE_STATUSES


def assert_configuration_unlocked_for_edit(configuration_id: str) -> None:
	if configuration_is_locked_for_edit(configuration_id):
		frappe.throw(
			frappe._(
				"This tender configuration is locked after preview confirmation. "
				"Return for Correction before editing configuration values, STD binding, "
				"evaluation criteria, price schedule, forms, or contract values."
			),
			title="CONFIGURATION_LOCKED",
		)
	status = cstr(frappe.db.get_value("Tender Configuration", configuration_id, "status") or "")
	if status == STATUS_SENT_TO_PUBLICATION:
		frappe.throw(
			frappe._(
				"This tender configuration was sent to the publication workflow and is read-only."
			),
			title="CONFIGURATION_LOCKED",
		)


def build_confirmed_package_from_doc(doc, *, preview_blob: dict[str, Any]) -> dict[str, Any]:
	"""Assemble F1 §3 package payload (not yet persisted)."""
	html_doc = cstr(preview_blob.get("preview_html") or "")
	if not html_doc.strip():
		frappe.throw(
			frappe._("Cannot confirm an empty tender document preview."),
			title="PACKAGE_EMPTY",
		)
	std_version = cstr(preview_blob.get("std_version") or getattr(doc, "std_version", None) or "")
	configuration_version = compute_configuration_version(doc)
	document_hash = compute_document_hash(html_doc, configuration_version, std_version)

	contract_blob = _parse_blob(getattr(doc, "contract_values", None))
	carry = build_carry_forward_bundle_from_contract_values(contract_blob)

	readiness = _parse_blob(getattr(doc, "readiness_report", None))
	review = _parse_blob(getattr(doc, "review_workspace", None))
	preview_confirmation = {
		"confirmed_at": preview_blob.get("confirmed_at") or str(now_datetime()),
		"confirmed_by": preview_blob.get("confirmed_by") or frappe.session.user,
		"user_confirmed": 1,
		"preview_status": "Confirmed",
	}

	return {
		"configuration": doc.name,
		"configuration_ref": cstr(doc.configuration_ref or doc.name),
		"procurement_package_ref": cstr(doc.procurement_package_ref or ""),
		"std_version": std_version,
		"configuration_version": configuration_version,
		"package_status": PACKAGE_STATUS_CONFIRMED,
		"document_hash": document_hash,
		"tender_html": html_doc,
		"bidder_submission_schema": cstr(getattr(doc, "bidder_submission_schema", None) or ""),
		"evaluation_schema": _json_dump(_parse_blob(getattr(doc, "evaluation_setup", None))),
		"price_schedule_schema": _json_dump(_parse_blob(getattr(doc, "price_schedule", None))),
		"forms_evidence_schema": _json_dump(_parse_blob(getattr(doc, "forms_and_evidence", None))),
		"contract_carry_forward": _json_dump(carry),
		"readiness_report_ref": _json_dump(
			{
				"last_checked_at": readiness.get("last_checked_at"),
				"overall_result": readiness.get("overall_result"),
				"blocker_count": readiness.get("blocker_count"),
				"warning_count": readiness.get("warning_count"),
			}
		),
		"review_approval_ref": _json_dump(
			{
				"approved_at": review.get("approved_at"),
				"approved_by": review.get("approved_by"),
			}
		),
		"preview_confirmation": _json_dump(preview_confirmation),
		"confirmed_at": preview_confirmation["confirmed_at"],
		"confirmed_by": preview_confirmation["confirmed_by"],
	}


def create_confirmed_package(doc, *, preview_blob: dict[str, Any]) -> Any:
	"""Persist immutable Confirmed Tender Document Package; invalidate any prior active package."""
	prior = get_active_package_name(doc.name)
	if prior:
		invalidate_package(prior, reason="Superseded by new preview confirmation")

	payload = build_confirmed_package_from_doc(doc, preview_blob=preview_blob)
	pkg = frappe.get_doc({"doctype": PACKAGE_DOCTYPE, **payload})
	pkg.flags.ignore_permissions = True
	pkg.insert(ignore_permissions=True)

	# Best-effort PDF artifact (HTML remains source of truth if PDF engine fails).
	try:
		from kentender_procurement.tender_configurations.services.document_preview import (
			_html_to_pdf_bytes,
		)

		pdf_bytes = _html_to_pdf_bytes(payload["tender_html"])
		file_doc = frappe.get_doc(
			{
				"doctype": "File",
				"file_name": f"{payload['configuration_ref']}-confirmed.pdf",
				"content": pdf_bytes,
				"is_private": 1,
				"attached_to_doctype": PACKAGE_DOCTYPE,
				"attached_to_name": pkg.name,
				"attached_to_field": "tender_pdf",
			}
		)
		file_doc.save(ignore_permissions=True)
		pkg.db_set("tender_pdf", file_doc.file_url, update_modified=False)
	except Exception:
		frappe.log_error(
			title="F1 confirmed package PDF attach failed",
			message=frappe.get_traceback(),
		)

	frappe.db.set_value(
		"Tender Configuration",
		doc.name,
		"confirmed_document_package",
		pkg.name,
		update_modified=False,
	)
	return pkg


def invalidate_package(package_name: str, *, reason: str = "") -> None:
	if not package_name or not frappe.db.exists(PACKAGE_DOCTYPE, package_name):
		return
	pkg = frappe.get_doc(PACKAGE_DOCTYPE, package_name)
	if cstr(pkg.package_status) == PACKAGE_STATUS_INVALIDATED:
		return
	pkg.flags.ignore_package_immutability = True
	pkg.package_status = PACKAGE_STATUS_INVALIDATED
	pkg.invalidated_at = now_datetime()
	pkg.invalidated_by = frappe.session.user
	pkg.invalidation_reason = cstr(reason or "Returned for Correction")[:500]
	pkg.save(ignore_permissions=True)


def create_publication_record(doc, package) -> Any:
	"""Create Publication record linked to confirmed package (does not publish)."""
	payload = {
		"package_id": package.name,
		"configuration_ref": cstr(package.configuration_ref or doc.configuration_ref or doc.name),
		"std_version": cstr(package.std_version or ""),
		"configuration_version": cstr(package.configuration_version or ""),
		"document_hash": cstr(package.document_hash or ""),
		"bidder_submission_schema_present": 1 if package.bidder_submission_schema else 0,
		"evaluation_schema_present": 1 if package.evaluation_schema else 0,
		"price_schedule_schema_present": 1 if package.price_schedule_schema else 0,
		"forms_evidence_schema_present": 1 if package.forms_evidence_schema else 0,
		"contract_carry_forward_present": 1 if package.contract_carry_forward else 0,
		"readiness_report_ref": _parse_blob(package.readiness_report_ref),
		"review_approval_ref": _parse_blob(package.review_approval_ref),
		"preview_confirmation": _parse_blob(package.preview_confirmation),
		"note": (
			"This action does not publish the tender. "
			"It makes the confirmed package available for publication setup."
		),
	}
	pub = frappe.get_doc(
		{
			"doctype": PUBLICATION_DOCTYPE,
			"configuration": doc.name,
			"configuration_ref": cstr(doc.configuration_ref or doc.name),
			"confirmed_package": package.name,
			"document_hash": package.document_hash,
			"status": PUBLICATION_STATUS_AWAITING,
			"received_at": now_datetime(),
			"received_by": frappe.session.user,
			"package_payload": _json_dump(payload),
		}
	)
	pub.flags.ignore_publication_boundary = True
	pub.insert(ignore_permissions=True)

	package.flags.ignore_package_immutability = True
	package.package_status = PACKAGE_STATUS_AWAITING
	package.save(ignore_permissions=True)

	frappe.db.set_value(
		"Tender Configuration",
		doc.name,
		"it_publication_record",
		pub.name,
		update_modified=False,
	)
	return pub


def cancel_publication_for_configuration(
	configuration_id: str, *, reason: str = ""
) -> str | None:
	name = frappe.db.get_value(
		PUBLICATION_DOCTYPE,
		{
			"configuration": configuration_id,
			"status": PUBLICATION_STATUS_AWAITING,
		},
		"name",
		order_by="creation desc",
	)
	if not name:
		# Also cancel any non-terminal record linked on the config.
		name = frappe.db.get_value(
			"Tender Configuration", configuration_id, "it_publication_record"
		)
	if not name or not frappe.db.exists(PUBLICATION_DOCTYPE, name):
		return None
	pub = frappe.get_doc(PUBLICATION_DOCTYPE, name)
	if cstr(pub.status) in (
		PUBLICATION_STATUS_CANCELLED,
		PUBLICATION_STATUS_RETURNED,
		"Published",
	):
		return pub.name
	pub.flags.ignore_publication_boundary = True
	pub.status = PUBLICATION_STATUS_RETURNED
	pub.cancelled_at = now_datetime()
	pub.cancelled_by = frappe.session.user
	pub.cancel_reason = cstr(reason or "Returned for Correction")[:500]
	pub.save(ignore_permissions=True)
	return pub.name


def package_summary_dto(package_name: str | None) -> dict[str, Any]:
	if not package_name or not frappe.db.exists(PACKAGE_DOCTYPE, package_name):
		return {}
	pkg = frappe.get_doc(PACKAGE_DOCTYPE, package_name)
	return {
		"package_id": pkg.name,
		"package_status": cstr(pkg.package_status or ""),
		"document_hash": cstr(pkg.document_hash or ""),
		"configuration_version": cstr(pkg.configuration_version or ""),
		"std_version": cstr(pkg.std_version or ""),
		"confirmed_at": cstr(pkg.confirmed_at or ""),
		"has_pdf": 1 if pkg.tender_pdf else 0,
		"items": [
			"Generated tender PDF",
			"Tender configuration reference",
			"Procurement package reference",
			"STD version",
			"Configuration version",
			"Bidder submission schema",
			"Evaluation schema",
			"Price schedule schema",
			"Forms/evidence schema",
			"Contract carry-forward values",
			"Readiness report",
			"Review approval record",
			"Preview confirmation record",
			"Document hash",
		],
	}


def publication_summary_dto(publication_name: str | None) -> dict[str, Any]:
	if not publication_name or not frappe.db.exists(PUBLICATION_DOCTYPE, publication_name):
		return {}
	pub = frappe.get_doc(PUBLICATION_DOCTYPE, publication_name)
	return {
		"publication_id": pub.name,
		"status": cstr(pub.status or ""),
		"confirmed_package": cstr(pub.confirmed_package or ""),
		"document_hash": cstr(pub.document_hash or ""),
		"received_at": cstr(pub.received_at or ""),
		"received_by": cstr(pub.received_by or ""),
	}
