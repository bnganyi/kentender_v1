# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The Test Trust Service (owner decision OD-C; plan D6), on the
`kt_bds_trust_services` hook.

A stand-in for an approved licensed certifying agency and signing service,
answering only on a test environment. It holds synthetic certificates (Test
Trust Certificate) issued by fixtures, takes a signing request for one exact
package digest from one person of one organisation, lets that person sign it
through the simulated signing step, and verifies the returned signature
against the package, person, organisation and certificate state at the
verification instant. It is record-keeping, not cryptography: nothing here
is a certificate authority or a signature scheme (BDS-CHG-001 v0.8 §16), and
every result says "simulation"."""

from __future__ import annotations

import secrets
from typing import Any

import frappe
from frappe.utils import cstr, get_datetime

from kentender_procurement.bid_submission.services import simulation

NAME = "Test Trust Service (simulation)"
CERTIFICATE = "Test Trust Certificate"
SIGNATURE = "Test Trust Signature"


def _insert(values: dict[str, Any]):
	doc = frappe.get_doc(values)
	doc.flags.kt_bds_test_service = True
	doc.insert(ignore_permissions=True)
	return doc


def _save(doc):
	doc.flags.kt_bds_test_service = True
	doc.save(ignore_permissions=True)
	return doc


class TestTrustService:
	name = NAME

	def healthy(self) -> bool:
		return not simulation.controls()["trust_service_down"]

	def certificate(self, *, user: str, organisation: str, at) -> dict[str, Any]:
		"""The person's certificate for the organisation at `at`: `Ready`, or why
		not (`None`, `Expired`, `Revoked`, `Not yet valid`)."""
		at = get_datetime(at)
		rows = frappe.get_all(CERTIFICATE, filters={"user": user, "organisation": organisation}, fields=["certificate_ref", "subject_name", "valid_from", "valid_to", "status"], order_by="valid_to desc")
		for row in rows:
			if row.status == "Valid" and get_datetime(row.valid_from) <= at <= get_datetime(row.valid_to):
				return {"status": "Ready", "certificate_ref": row.certificate_ref, "subject_name": row.subject_name, "valid_to": row.valid_to, "service": NAME, "simulation": True}
		if not rows:
			return {"status": "None", "service": NAME, "simulation": True}
		latest = rows[0]
		reason = "Revoked" if latest.status == "Revoked" else "Expired" if get_datetime(latest.valid_to) < at else "Not yet valid"
		return {"status": reason, "certificate_ref": latest.certificate_ref, "valid_to": latest.valid_to, "service": NAME, "simulation": True}

	def request_signature(self, *, package_digest: str, user: str, organisation: str, at) -> dict[str, Any]:
		certificate = self.certificate(user=user, organisation=organisation, at=at)
		if certificate["status"] != "Ready":
			return {"ok": False, "certificate": certificate}
		row = _insert({
			"doctype": SIGNATURE, "signing_request_id": "TSR-" + secrets.token_hex(6).upper(), "package_digest": package_digest, "user": user, "organisation": organisation,
			"certificate_ref": certificate["certificate_ref"], "requested_at": get_datetime(at), "status": "Requested", "fixture_namespace": cstr(frappe.flags.get("kt_bds_fixture_namespace") or ""),
		})
		return {"ok": True, "signing_request_id": row.signing_request_id, "service": NAME, "simulation": True}

	def sign(self, *, signing_request_id: str, user: str, at) -> dict[str, Any]:
		"""The signatory's own signing step (a real service runs this in its own
		signing client). Only the person the request names can sign it."""
		name = frappe.db.get_value(SIGNATURE, {"signing_request_id": cstr(signing_request_id)}, "name")
		if not name:
			raise frappe.DoesNotExistError("No such signing request.")
		row = frappe.get_doc(SIGNATURE, name)
		if row.user != user:
			raise frappe.PermissionError("Only the person named in the signing request can sign it.")
		if row.status != "Signed":
			row.signature_ref = "TSG-" + secrets.token_hex(8).upper()
			row.signed_at = get_datetime(at)
			row.status = "Signed"
			_save(row)
		return {"signature": row.signature_ref, "service": NAME, "simulation": True}

	def verify(self, *, signature: str, package_digest: str, user: str, organisation: str, at) -> dict[str, Any]:
		row = frappe.db.get_value(SIGNATURE, {"signature_ref": cstr(signature), "status": "Signed"}, ["package_digest", "user", "organisation", "certificate_ref", "signed_at", "signing_request_id"], as_dict=True) if cstr(signature) else None
		if not row:
			return {"valid": False, "reason": "No signature of the approved trust service has this reference."}
		if row.package_digest != package_digest:
			return {"valid": False, "reason": "The signature is for a different bid package."}
		if row.user != user:
			return {"valid": False, "reason": "The signature belongs to another person."}
		if row.organisation != organisation:
			return {"valid": False, "reason": "The signature was made for another organisation."}
		certificate = frappe.db.get_value(CERTIFICATE, row.certificate_ref, ["status", "valid_from", "valid_to", "subject_name"], as_dict=True)
		at = get_datetime(at)
		if not certificate or certificate.status == "Revoked":
			return {"valid": False, "reason": "The signing certificate has been revoked."}
		if not (get_datetime(certificate.valid_from) <= at <= get_datetime(certificate.valid_to)):
			return {"valid": False, "reason": "The signing certificate is not valid at this time."}
		return {
			"valid": True, "certificate_ref": row.certificate_ref, "signed_at": row.signed_at,
			"evidence": {
				"service": NAME, "simulation": True, "signing_request_id": row.signing_request_id, "signature_ref": cstr(signature), "certificate_ref": row.certificate_ref,
				"subject_name": certificate.subject_name, "certificate_valid_to": str(certificate.valid_to), "verified_at": str(at),
			},
		}


def service() -> TestTrustService | None:
	return TestTrustService() if simulation.enabled() else None


# -- fixture helpers (test environment only) ---------------------------------


def issue_certificate(*, user: str, organisation: str, subject_name: str, valid_from, valid_to, certificate_ref: str = "") -> str:
	if not simulation.enabled():
		frappe.throw("Test certificates exist only on a test environment.")
	return _insert({
		"doctype": CERTIFICATE, "certificate_ref": certificate_ref or "TCERT-" + secrets.token_hex(5).upper(), "user": user, "organisation": organisation,
		"subject_name": subject_name, "valid_from": get_datetime(valid_from), "valid_to": get_datetime(valid_to), "status": "Valid",
		"fixture_namespace": cstr(frappe.flags.get("kt_bds_fixture_namespace") or ""),
	}).certificate_ref


def revoke_certificate(certificate_ref: str) -> None:
	if not simulation.enabled():
		frappe.throw("Test certificates exist only on a test environment.")
	doc = frappe.get_doc(CERTIFICATE, certificate_ref)
	doc.status = "Revoked"
	_save(doc)
