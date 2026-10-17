# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Award demo profiles (plan Phase 11; tracker AWD4-1102): the canonical award
at one step of its §13 story, with the site's test clock at that moment, for
walking in a browser as the real people. `restore_base` tells the whole story
again. Test environment only; the canonical evaluation must be seeded."""

from __future__ import annotations

from kentender_core.seeds import calendar
from kentender_core.seeds.calendar import fiscal as F, world as W  # noqa: F401
from typing import Any

import frappe

from kentender_procurement.award.seeds import kentender_mvp_v1 as base

PROFILES = {
	"AWD-DEMO-OPINION": ("received", W("2027-06-17 09:00:00"), "Charles Mutiso prepares and signs the professional opinion (D02)."),
	"AWD-DEMO-DECISION": ("signed", W("2027-06-17 10:00:00"), "Amina Hassan decides the award (D03)."),
	"AWD-DEMO-NOTICE": ("notified", W("2027-06-17 10:10:00"), "Mary Wanjiku reads Award notice 1 and replies (D04); David Ouma can only read (V13)."),
	"AWD-DEMO-WAIT": ("accepted", W("2027-06-18 09:05:00"), "The waiting period runs (D05)."),
	"AWD-DEMO-DELIVERED": ("delivered", calendar.shift(W("2027-06-18 09:00:00"), 14), "Contracting has received the award (D06)."),
}


def list_profiles() -> list[dict[str, str]]:
	return [{"profile": k, "step": v[0], "instant": v[1], "story": v[2]} for k, v in PROFILES.items()]


def load_profile(*, profile: str) -> dict[str, Any]:
	from kentender_core.services.test_clock import set_instant

	if profile not in PROFILES:
		frappe.throw(f"Unknown Award profile {profile!r}. Profiles: {', '.join(PROFILES)}")
	step, instant, story = PROFILES[profile]
	from kentender_core.seeds import calendar

	if calendar.mode() == "anchored":
		# SEED-002 v0.8 R1: no moment later than the real clock. The delivery to Contracting is after the world's anchor (the
		# waiting period has to run), so it can be loaded from its own instant on, once real time reaches it.
		problem = calendar.never_ahead_problem(instant)
		if problem:
			frappe.throw(f"The profile {profile} stands at {problem}; it can be loaded from {instant} onwards (no simulated moment is later than the real clock).")
	out = base.upsert_award_base(commit=False, through=step)
	set_instant(instant)
	frappe.db.commit()
	return {**out, "profile": profile, "instant": instant, "story": story}


def restore_base() -> dict[str, Any]:
	from kentender_core.seeds import calendar
	from kentender_core.services.test_clock import set_instant

	out = base.upsert_award_base(commit=False)
	# the canonical world's own moment (two-year seed world plan D1)
	set_instant(calendar.as_at())
	frappe.db.commit()
	return out
