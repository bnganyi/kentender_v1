# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The Test Issuer Service (Project Owner, 10 October 2026): a stand-in for the
bank or insurer that confirms a tender-security instrument, on the
`kt_bds_issuer_services` hook.

On a test environment it answers one of four responses — Confirmed, Pending,
Mismatch, Unavailable — either as the test controls force it or, in Automatic,
by the ending of the instrument reference (`-MISMATCH`, `-PENDING`,
`-UNAVAILABLE`, otherwise Confirmed). Every answer names its source, "Test Issuer
Service (simulation)", which the verification record keeps, shows beside the
result and keeps in the audit and any exported verification evidence. On any
other site it returns nothing, so no real tender security can be verified by
it: a verification there stays Pending."""

from __future__ import annotations

import hashlib

from kentender_procurement.bid_submission.services import simulation

NAME = "Test Issuer Service (simulation)"
RESPONSES = ("Confirmed", "Pending", "Mismatch", "Unavailable")


class TestIssuerService:
	__test__ = False  # not a test case

	name = NAME

	def healthy(self) -> bool:
		return True

	def verify(self, *, issuer: str, reference: str, amount: str, currency: str, correlation_id: str) -> dict:
		forced = simulation.controls().get("issuer_response") or "Automatic"
		text = str(reference or "").upper()
		if forced in RESPONSES:
			outcome = forced
		elif text.endswith("-MISMATCH"):
			outcome = "Mismatch"
		elif text.endswith("-PENDING"):
			outcome = "Pending"
		elif text.endswith("-UNAVAILABLE"):
			outcome = "Unavailable"
		else:
			outcome = "Confirmed"
		# a stable, plausible response time, so a test and a screenshot agree
		milliseconds = 120 + int(hashlib.sha256((str(reference) + str(correlation_id)).encode()).hexdigest()[:4], 16) % 260
		return {"outcome": outcome, "source": NAME, "response_ms": milliseconds, "correlation_id": correlation_id}


def service():
	return TestIssuerService() if simulation.enabled() else None
