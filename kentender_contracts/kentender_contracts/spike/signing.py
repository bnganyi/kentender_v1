"""Phase 2 spike S6 (tracker CM8-207): two parties sign one immutable package through the shared signing seam.

The seam is the hook `kt_trust_signing_services` (declared by the app that owns the test provider); this module reaches it only
through `frappe.get_hooks`, never by import, exactly as the core facade of plan D8 will.
"""

from __future__ import annotations

import hashlib
import json

import frappe

from kentender_contracts.spike import native
from kentender_core.services.command_write_guard import command_write

HOOK = "kt_trust_signing_services"
SUPPLIER_SIGNATORY = "mary.wanjiku@afyadigital.example"
ENTITY_SIGNATORY = "amina.hassan@moh.example.test"
CASE = "CM-SPIKE-CASE-S6"
NAMESPACE = "CM_SPIKE"


def provider():
	for path in reversed(frappe.get_hooks(HOOK) or []):
		found = frappe.get_attr(path)()
		if found is not None:
			return found
	return None


def package_digest(documents: dict[str, bytes], manifest: list[dict]) -> str:
	"""One digest over the manifest and every file's bytes, in manifest order."""
	h = hashlib.sha256()
	h.update(json.dumps(manifest, sort_keys=True).encode())
	for entry in manifest:
		h.update(hashlib.sha256(documents[entry["category"]]).digest())
	return h.hexdigest()


def sign(member: str, target_id: str, digest: str, correlation_id: str) -> dict:
	p = provider()
	if p is None:
		return {"outcome": "Unavailable", "proof_reference": "", "method": ""}
	return p.attest(member=member, target_id=target_id, target_digest=digest, minutes_version="", action="Sign", correlation_id=correlation_id)


def _case() -> str:
	if not frappe.db.exists("Contract Case", CASE):
		with command_write("Contract Management"):
			frappe.get_doc({"doctype": "Contract Case", "contract_id": CASE, "source_kind": "External record", "fixture_namespace": NAMESPACE}).insert(ignore_permissions=True)
		frappe.db.commit()
	return CASE


def signing_operation(subject: str, version: int, member: str, digest: str, key: str, calls: list) -> dict:
	"""One signature as a CM operation: the intent is committed BEFORE the provider is called; a replay of a succeeded intent never calls it."""
	identity = f"{CASE}|{subject}|{version}|Signing attempt|{key}"
	with command_write("Contract Management"):
		existing = frappe.db.get_value("Contract Operation Intent", {"operation_identity": identity}, ["name", "state", "result_reference"], as_dict=True)
		if existing and existing.state == "Succeeded":
			return {"replay": True, "state": existing.state, "proof": existing.result_reference}
		if existing:
			intent = frappe.get_doc("Contract Operation Intent", existing.name)
		else:
			intent = frappe.get_doc({"doctype": "Contract Operation Intent", "contract_case": CASE, "subject": subject, "subject_version": version, "operation_kind": "Signing attempt",
				"operation_key": key, "operation_identity": identity, "state": "Recorded", "recovery_owner": "Trust recovery", "fixture_namespace": NAMESPACE})
			intent.insert(ignore_permissions=True)
		intent.state = "Attempting"
		intent.save(ignore_permissions=True)
	frappe.db.commit()
	calls.append(identity)
	result = sign(member, f"{subject}-{version}", digest, identity)
	with command_write("Contract Management"):
		intent.reload()
		if result["outcome"] == "Accepted/Verified":
			intent.state, intent.result_reference = "Succeeded", result["proof_reference"]
		elif result["outcome"] == "Rejected":
			intent.state = "Failed"
		else:  # Unavailable / Indeterminate: the real outcome is unknown, so the attempt stays open for reconciliation
			intent.state = "Uncertain"
		intent.save(ignore_permissions=True)
	frappe.db.commit()
	return {"replay": False, "state": intent.state, "proof": intent.result_reference or "", "provider_outcome": result["outcome"]}


def s6_signing() -> list[dict]:
	native._ensure_world() if False else None
	_case()
	docs = {c: f"document {c} v1".encode() for c in ("agreement", "tender_form", "price_schedule", "requirements_schedule", "technical_specifications", "gcc", "scc", "award_notification")}
	manifest = [{"category": c, "digest": hashlib.sha256(b).hexdigest()} for c, b in docs.items()]
	d1 = package_digest(docs, manifest)
	native.record("S6.provider_found_through_the_hook", hook=frappe.get_hooks(HOOK), provider=type(provider()).__name__ if provider() else None)
	native.record("S6.package_digest", digest=d1, entries=len(manifest))

	calls: list[str] = []
	native.attempt("S6.supplier_signs_first", lambda: signing_operation("agreement", 1, SUPPLIER_SIGNATORY, d1, "supplier", calls))
	native.attempt("S6.entity_signs_second_on_the_same_digest", lambda: signing_operation("agreement", 1, ENTITY_SIGNATORY, d1, "entity", calls))
	native.attempt("S6.replay_of_a_succeeded_signature_does_not_call_the_provider_again", lambda: signing_operation("agreement", 1, SUPPLIER_SIGNATORY, d1, "supplier", calls))
	native.record("S6.provider_calls_so_far", calls=calls, count=len(calls))

	# the seam itself: same correlation id twice
	a = sign(SUPPLIER_SIGNATORY, "agreement-1", d1, "SPIKE-CORR-1")
	b = sign(SUPPLIER_SIGNATORY, "agreement-1", d1, "SPIKE-CORR-1")
	native.record("S6.seam_same_correlation_id_twice", first=a.get("proof_reference"), second=b.get("proof_reference"), same_proof=a.get("proof_reference") == b.get("proof_reference"),
		result_keys=sorted(a.keys()), status_or_reconcile_function_on_provider=[n for n in dir(provider()) if not n.startswith("_") and n != "attest"])

	# each non-verified outcome, and the uncertain one retried
	for outcome in ("Unavailable", "Indeterminate", "Rejected"):
		frappe.flags.kt_prc_signing_outcome = outcome
		native.attempt(f"S6.outcome_{outcome.lower()}", lambda o=outcome: signing_operation("agreement", 2, SUPPLIER_SIGNATORY, d1, f"forced-{o}", calls))
	frappe.flags.kt_prc_signing_outcome = None
	native.attempt("S6.uncertain_attempt_retried_under_the_same_identity", lambda: signing_operation("agreement", 2, SUPPLIER_SIGNATORY, d1, "forced-Indeterminate", calls))
	native.record("S6.intent_states", rows=[{"identity": r.operation_identity, "state": r.state, "proof": r.result_reference} for r in
		frappe.get_all("Contract Operation Intent", filters={"fixture_namespace": NAMESPACE}, fields=["operation_identity", "state", "result_reference"], order_by="creation asc")])

	# a changed version: new digest, old proofs bound to the old one
	docs2 = dict(docs)
	docs2["scc"] = b"document scc v2 (changed clause)"
	manifest2 = [{"category": c, "digest": hashlib.sha256(b).hexdigest()} for c, b in docs2.items()]
	d2 = package_digest(docs2, manifest2)
	native.record("S6.changed_version_changes_the_digest", old=d1, new=d2, different=d1 != d2)
	rows = frappe.get_all("Contract Operation Intent", filters={"fixture_namespace": NAMESPACE, "state": "Succeeded", "subject_version": 1}, fields=["operation_identity", "result_reference"])
	native.record("S6.version_1_proofs_remain_bound_to_version_1_only", proofs_for_version_1=len(rows), proofs_for_version_2=frappe.db.count("Contract Operation Intent", {"fixture_namespace": NAMESPACE, "state": "Succeeded", "subject_version": 2}))
	return native.save("s6_signing")
