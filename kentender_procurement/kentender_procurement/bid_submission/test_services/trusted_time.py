# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The trusted test clock (owner decision OD-C; plan D18), on the
`kt_bds_time_services` hook. On a test environment it reads Bid Submission's
own clock (the injected fixture instant in tests and seeds) and is healthy
unless the test controls say otherwise. Elsewhere it does not answer, so no
trusted-time source is configured and submission stays unavailable."""

from __future__ import annotations

from kentender_procurement.bid_submission.services import clock, simulation

NAME = "Trusted test clock (simulation)"


class TestTrustedTime:
	name = NAME

	def healthy(self) -> bool:
		return not simulation.controls()["time_service_down"]

	def now(self):
		return clock.now()


def service() -> TestTrustedTime | None:
	return TestTrustedTime() if simulation.enabled() else None
