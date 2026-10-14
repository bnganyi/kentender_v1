# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The shared signing facade (TRUST-ADR-001 v0.1 §1(2), §4; BOP-CHG-001 v0.10 plan D6 and D16; CM-CHG-001 v0.8 plan D8).

A module asks the trust service, found on the `kt_trust_signing_services` hook, to verify one party's proof for one exact target
digest. Every answer is exactly one of the four TRUST-ADR-001 §4 outcomes with one correlation identity. A missing provider is
Unavailable, a failing one Indeterminate, and neither is ever recorded as a verified proof.

Two things sit beyond what Proceedings had (CM spike S6, FU-CM-30, FU-CM-49). The first is `reconcile(correlation_id)`: an attempt
whose outcome is unknown is settled by asking the provider what it holds under that identity, never by signing again, so a retry
cannot create a second proof. The result's `known` is True (the provider holds it), False (the provider never received it, so
retrying under the same identity is safe) or None (it cannot be established: no provider, or one that cannot reconcile). The second is
`serves`: a provider may declare the consumers it answers for, so a simulation provider written for one module cannot answer
another's requests. A provider with no `serves` answers everyone, which is how the Proceedings test attestation behaves.

A production provider must be idempotent on the correlation id and implement `reconcile`; Proceedings and Contract Management
reach this module, not the hook."""

from __future__ import annotations

from typing import Any

import frappe

HOOK = "kt_trust_signing_services"
VERIFIED, REJECTED, UNAVAILABLE, INDETERMINATE = "Accepted/Verified", "Rejected", "Unavailable", "Indeterminate"
OUTCOMES = (VERIFIED, REJECTED, UNAVAILABLE, INDETERMINATE)


def service(consumer: str = "") -> Any | None:
	"""The provider that answers for this consumer: the last hook entry that returns one and serves it."""
	for path in reversed(frappe.get_hooks(HOOK) or []):
		found = frappe.get_attr(path)()
		if found is None:
			continue
		serves = getattr(found, "serves", None)
		if serves is None or consumer in serves:
			return found
	return None


def attest(*, member: str, target_id: str, target_digest: str, minutes_version: str, action: str, correlation_id: str, consumer: str = "") -> dict[str, Any]:
	provider = service(consumer)
	if provider is None:
		return {"outcome": UNAVAILABLE, "method": "", "proof_reference": "", "correlation_id": correlation_id}
	try:
		result = dict(provider.attest(member=member, target_id=target_id, target_digest=target_digest, minutes_version=minutes_version, action=action,
			correlation_id=correlation_id))
	except Exception:
		frappe.log_error(title="Signing service failed")
		return {"outcome": INDETERMINATE, "method": "", "proof_reference": "", "correlation_id": correlation_id}
	if result.get("outcome") not in OUTCOMES:
		result["outcome"] = INDETERMINATE
	result["correlation_id"] = correlation_id
	return result


def reconcile(correlation_id: str, *, consumer: str = "") -> dict[str, Any]:
	"""What the provider holds for an earlier attempt. Reads only: it never signs, and a retry is the caller's decision."""
	unknown = {"known": None, "outcome": UNAVAILABLE, "method": "", "proof_reference": "", "correlation_id": correlation_id}
	provider = service(consumer)
	if provider is None or not callable(getattr(provider, "reconcile", None)):
		return unknown
	try:
		result = dict(provider.reconcile(correlation_id))
	except Exception:
		frappe.log_error(title="Signing service reconcile failed")
		return {**unknown, "outcome": INDETERMINATE}
	result["correlation_id"] = correlation_id
	if result.get("known") is not True:
		return {**unknown, "known": False if result.get("known") is False else None}
	if result.get("outcome") not in OUTCOMES:
		result["outcome"] = INDETERMINATE
	return result
