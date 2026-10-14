# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The shared signing service seam (TRUST-ADR-001 v0.1 §1(2), §4; BOP-CHG-001
v0.10 plan D6 and D16).

The lookup, the four TRUST-ADR-001 §4 outcomes and the handling of a missing or
failing provider moved to `kentender_core.services.signing` (CM-CHG-001 v0.8
plan D8, FU-CM-30) so that other modules can use them without importing
Proceedings. This module keeps its names and behaviour for its callers and
tests. No production provider is configured on this bench, so the answer there
is Unavailable; the test attestation double answers only on a test
environment. A timeout or failure is never recorded as a verified proof."""

from __future__ import annotations

from typing import Any

from kentender_core.services import signing as _facade

HOOK = _facade.HOOK
VERIFIED, REJECTED, UNAVAILABLE, INDETERMINATE = _facade.VERIFIED, _facade.REJECTED, _facade.UNAVAILABLE, _facade.INDETERMINATE
OUTCOMES = _facade.OUTCOMES
CONSUMER = "proceedings"


def service() -> Any | None:
	return _facade.service(CONSUMER)


def attest(*, member: str, target_id: str, target_digest: str, minutes_version: str, action: str, correlation_id: str) -> dict[str, Any]:
	return _facade.attest(member=member, target_id=target_id, target_digest=target_digest, minutes_version=minutes_version, action=action, correlation_id=correlation_id,
		consumer=CONSUMER)
