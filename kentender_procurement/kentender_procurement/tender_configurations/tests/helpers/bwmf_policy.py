# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Explicit submission_policy objects for tests/seeds only — not runtime defaults."""

from __future__ import annotations

from typing import Any


def explicit_submission_policy(**overrides: Any) -> dict[str, Any]:
	"""Return a complete closed submission_policy. Callers must pass overrides explicitly."""
	policy = {
		"deadline_at": "2099-12-31T23:59:59+03:00",
		"timezone": "Africa/Nairobi",
		"server_time_authoritative": True,
		"late_submission_behavior": "reject",
		"withdrawal_mode": "not_permitted",
		"replacement_mode": "not_permitted",
		"submission_authority_policy_ref": "POL-SUB-AUTH-1",
		"reauthentication_policy_ref": "POL-REAUTH-1",
		"seal_policy_ref": "POL-SEAL-1",
		"receipt_policy_ref": "POL-RECEIPT-1",
		"concurrent_submission_policy": "single_authoritative_transaction",
		"idempotency_policy": "required",
	}
	policy.update(overrides)
	return policy
