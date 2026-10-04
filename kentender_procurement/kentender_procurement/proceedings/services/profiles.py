# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Owner profiles of the shared Proceedings record (EVL-CHG-001 v0.4 §6 "PRC
change is explicit", plan D4).

PRC-CHG-001 v0.9 defines one profile, Bid Opening: one session, minutes,
opening page targets. EVL-CHG-001 v0.4 adds a second, Bid Evaluation: one
case containing zero or more actual discussion sessions, member history,
ordered owner events, report versions and signature targets. An owner
adapter names its profile with a `proceeding_type` attribute; an adapter
without one is Bid Opening, so the first owner is unchanged."""

from __future__ import annotations

from typing import Any

BID_OPENING = "Bid Opening"
BID_EVALUATION = "Bid Evaluation"

PROFILES: dict[str, dict[str, Any]] = {
	BID_OPENING: {
		"initial_state": "Pending",
		"multi_session": False,
		"record_kinds": {"Opening minutes": ("Tender page", "Price location", "Change location", "Minutes page", "Final minutes page")},
		"attendance_capacities": ("Committee member", "Recorder", "Tenderer representative", "Public observer"),
	},
	BID_EVALUATION: {
		"initial_state": "Open",
		"multi_session": True,
		"record_kinds": {
			"Evaluation report": ("Report signature",),
			"Verification report": ("Verification report page", "Verification report signature"),
		},
		"attendance_capacities": ("Committee member", "Secretary"),
	},
}


def type_for(adapter: Any) -> str:
	return getattr(adapter, "proceeding_type", None) or BID_OPENING


def profile(proceeding_type: str) -> dict[str, Any]:
	return PROFILES[proceeding_type or BID_OPENING]
