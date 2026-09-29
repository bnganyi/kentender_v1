# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The test attestation service (TRUST-ADR-001 v0.1 §2 "Member
signature/initial"; BOP-CHG-001 v0.10 plan D6, D15), on the
`kt_trust_signing_services` hook.

It answers only on a test environment (site_config
`kt_bds_simulation_environment`, owner decision OD-C) and records an
individually attributable attestation bound to one member and one exact
target digest. It is not an electronic signature, issues no certificate and
draws no initials; every result carries its own label saying so."""

from __future__ import annotations

import frappe
from frappe.utils import cint

LABEL = "Test attestation — not an electronic signature"
METHOD = "Test attestation (simulation)"


def enabled() -> bool:
	return bool(cint(frappe.conf.get("kt_bds_simulation_environment")))


class TestAttestationService:
	def attest(self, *, member: str, target_id: str, target_digest: str, minutes_version: str, action: str, correlation_id: str) -> dict:
		# Contract tests force a non-verified outcome with this flag.
		outcome = frappe.flags.get("kt_prc_signing_outcome") or "Accepted/Verified"
		reference = f"TATT-{frappe.generate_hash(length=10).upper()}" if outcome == "Accepted/Verified" else ""
		return {"outcome": outcome, "method": METHOD, "proof_reference": reference, "label": LABEL}


def service():
	return TestAttestationService() if enabled() else None
