# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The shared signing service seam (TRUST-ADR-001 v0.1 §1(2), §4; BOP-CHG-001
v0.10 plan D6 and D16).

Proceedings asks the trust service, found on the `kt_trust_signing_services`
hook, to verify one member's proof for one exact target digest. It returns
exactly one of the four TRUST-ADR-001 v0.1 §4 outcomes with one correlation
identity. No production provider is configured on this bench, so the answer
there is Unavailable; the test attestation double answers only on a test
environment. A timeout or failure is never recorded as a verified proof."""

from __future__ import annotations

from typing import Any

import frappe

HOOK = "kt_trust_signing_services"
VERIFIED, REJECTED, UNAVAILABLE, INDETERMINATE = "Accepted/Verified", "Rejected", "Unavailable", "Indeterminate"
OUTCOMES = (VERIFIED, REJECTED, UNAVAILABLE, INDETERMINATE)


def service() -> Any | None:
	for path in reversed(frappe.get_hooks(HOOK) or []):
		found = frappe.get_attr(path)()
		if found is not None:
			return found
	return None


def attest(*, member: str, target_id: str, target_digest: str, minutes_version: str, action: str, correlation_id: str) -> dict[str, Any]:
	provider = service()
	if provider is None:
		return {"outcome": UNAVAILABLE, "method": "", "proof_reference": "", "correlation_id": correlation_id}
	try:
		result = dict(provider.attest(member=member, target_id=target_id, target_digest=target_digest, minutes_version=minutes_version, action=action,
			correlation_id=correlation_id))
	except Exception:
		frappe.log_error(title="Proceedings signing service failed")
		return {"outcome": INDETERMINATE, "method": "", "proof_reference": "", "correlation_id": correlation_id}
	if result.get("outcome") not in OUTCOMES:
		result["outcome"] = INDETERMINATE
	result["correlation_id"] = correlation_id
	return result
