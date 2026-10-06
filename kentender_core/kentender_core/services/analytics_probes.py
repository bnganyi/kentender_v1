"""ANL-CHG-001 v0.8 plan D12 — Analytics' reads in the technical-read conformance gate
(KT-STD-001 v1.22 §3A.6, AUTH-ADR-001 §9). A technical reader (Administrator, System Manager) reads every
tab site-wide and decides nothing, so each probe must return a permitted verdict and no command authority."""

from __future__ import annotations

from kentender_core.api import analytics as api


def read_probes() -> list[dict]:
	return [
		{"label": "analytics.get_procurement_analytics.overview", "call": api.get_procurement_analytics, "kwargs": lambda: {}},
		{"label": "analytics.get_procurement_analytics.tender_proceedings", "call": api.get_procurement_analytics,
			"kwargs": lambda: {"tab": "tender-proceedings"}},
		{"label": "analytics.get_analytics_access", "call": api.get_analytics_access, "kwargs": lambda: {}},
	]
