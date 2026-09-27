# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Supplier Account endpoints (BDS-CHG-001 v0.8 §7.1–7.2, §11.3). Thin: each
forwards to one service, which owns authority and every rule. Uploads come
as multipart form data (the file field named per endpoint). A masked read
returns NOT_FOUND as data; command refusals raise the §8 code."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cstr

from kentender_suppliers.supplier_accounts.services import access, assignments, read, registration, verification
from kentender_suppliers.supplier_accounts.services import evidence as evidence_service
from kentender_suppliers.supplier_accounts.services import organisation as organisation_service
from kentender_suppliers.supplier_accounts.services.errors import NOT_FOUND_TEXT


def _upload(field: str) -> tuple[str, bytes]:
	files = getattr(getattr(frappe, "request", None), "files", None)
	upload = files.get(field) if files else None
	if not upload:
		return "", b""
	return cstr(upload.filename), upload.stream.read()


@frappe.whitelist(methods=["GET"])
def get_supplier_account(organisation: str = "") -> dict[str, Any]:
	try:
		return {"outcome": "OK", **read.get_supplier_account(organisation=organisation)}
	except frappe.DoesNotExistError:
		return {"outcome": "NOT_FOUND", "heading": "Account not found", "text": NOT_FOUND_TEXT}


@frappe.whitelist(methods=["POST"])
def register_supplier_organisation(legal_name: str = "", country: str = "", registration_number: str = "", registered_address: str = "", official_email: str = "", official_phone: str = "", tax_identifier: str = "", job_title: str = "", idempotency_key: str = "") -> dict[str, Any]:
	filename, content = _upload("authority_evidence")
	return registration.register_supplier_organisation(
		legal_name=legal_name, country=country, registration_number=registration_number, registered_address=registered_address, official_email=official_email,
		official_phone=official_phone, tax_identifier=tax_identifier, job_title=job_title, authority_filename=filename, authority_content=content, idempotency_key=idempotency_key,
	)


@frappe.whitelist(methods=["POST"])
def send_account_verification(organisation: str, idempotency_key: str = "") -> dict[str, Any]:
	return verification.send_account_verification(organisation=organisation, idempotency_key=idempotency_key)


@frappe.whitelist(methods=["POST"])
def verify_account_communication(token: str = "") -> dict[str, Any]:
	return verification.verify_account_communication(token=token)


@frappe.whitelist(methods=["POST"])
def update_supplier_organisation(organisation: str, values=None, expected_version=None, idempotency_key: str = "") -> dict[str, Any]:
	return organisation_service.update_supplier_organisation(organisation=organisation, values=frappe.parse_json(values) or {}, expected_version=expected_version, idempotency_key=idempotency_key)


@frappe.whitelist(methods=["POST"])
def assign_supplier_representative(organisation: str, email: str = "", full_name: str = "", job_title: str = "", effective_from: str = "", effective_to: str = "", idempotency_key: str = "") -> dict[str, Any]:
	return assignments.assign_supplier_representative(organisation=organisation, email=email, full_name=full_name, job_title=job_title, effective_from=effective_from or None, effective_to=effective_to or None, idempotency_key=idempotency_key)


@frappe.whitelist(methods=["POST"])
def assign_authorised_signatory(organisation: str, email: str = "", full_name: str = "", job_title: str = "", effective_from: str = "", effective_to: str = "", idempotency_key: str = "") -> dict[str, Any]:
	filename, content = _upload("authority_evidence")
	return assignments.assign_authorised_signatory(organisation=organisation, email=email, full_name=full_name, job_title=job_title, effective_from=effective_from or None, effective_to=effective_to or None, authority_filename=filename, authority_content=content, idempotency_key=idempotency_key)


@frappe.whitelist(methods=["POST"])
def upload_account_evidence(organisation: str, evidence_type: str = "", reference: str = "", valid_until: str = "", title: str = "", idempotency_key: str = "") -> dict[str, Any]:
	filename, content = _upload("file")
	return evidence_service.upload_account_evidence(organisation=organisation, evidence_type=evidence_type, filename=filename, content=content, reference=reference, valid_until=valid_until, title=title, idempotency_key=idempotency_key)


@frappe.whitelist(methods=["GET"])
def download_account_evidence(organisation: str, evidence: str, inline: int = 0) -> None:
	"""The exact stored bytes; `inline` shows the file in the browser (View)."""
	result = evidence_service.get_account_evidence_file(organisation=organisation, evidence=evidence)
	frappe.local.response.filename = result["file_name"]
	frappe.local.response.filecontent = result["content"]
	frappe.local.response.type = "download"
	frappe.local.response.display_content_as = "inline" if frappe.utils.cint(inline) else "attachment"


@frappe.whitelist(methods=["POST"])
def suspend_supplier_account(organisation: str, reason: str = "", expected_version=None, idempotency_key: str = "") -> dict[str, Any]:
	return access.suspend_supplier_account(organisation=organisation, reason=reason, expected_version=expected_version, idempotency_key=idempotency_key)


@frappe.whitelist(methods=["POST"])
def restore_supplier_account(organisation: str, reason: str = "", expected_version=None, idempotency_key: str = "") -> dict[str, Any]:
	return access.restore_supplier_account(organisation=organisation, reason=reason, expected_version=expected_version, idempotency_key=idempotency_key)
