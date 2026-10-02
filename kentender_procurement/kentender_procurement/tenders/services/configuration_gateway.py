# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""TPR-CHG-001 v0.8 §3 "Advertising rule and required channels" / §4.6 /
§5.5 — the one seam to Configuration (plan D6).

The publication rule is resolved from CFG-CHG-002 v0.11's own
"Publication obligations" reference kind: every version in force on the
applicability date whose `trigger_event` is `TenderInvitation` contributes
one required channel; `TenderCancellation` rows contribute the cancellation
obligations. The profile's `bid_opening` row carries two separate numbers
(TPR-CHG-001 v0.16 §5.5): the verified legal **minimum** preparation period,
which blocks, and the **default** (the usual period), which pre-fills the
form and, when the officer goes below it, requires a stated reason but never
blocks. A profile with no verified minimum has nothing to block on. Every MVP channel is Evidence based: a row that
names an integration evidence contract is refused, never activated
(§5.5.1). The snapshot taken at authorisation controls afterwards
(§5.5(8)); a new rule never reclassifies an authorised publication."""

from __future__ import annotations

import json
from datetime import timedelta
from typing import Any

import frappe
from frappe.utils import cstr, getdate

from kentender_core.services import procurement_settings, regulatory_reference
from kentender_procurement.tenders.services.errors import TendersError, fail

KIND = "Publication obligations"
TRIGGER_INVITATION = "TenderInvitation"
TRIGGER_CANCELLATION = "TenderCancellation"
CONFIRMATION_MODE = "Evidence based"

# FOLLOW_UPS FU-15: the CFG payload carries channel codes only.
CHANNEL_LABELS: dict[str, str] = {
	"STATE_PORTAL": "State Portal",
	"MINISTRY_WEBSITE": "Ministry website",
	"NOTICE_BOARD": "Notice board",
	"NATIONAL_NEWSPAPERS": "Two national newspapers",
	"PPRA_REPORT": "PPRA cancellation report",
	"CANDIDATE_NOTICE": "Candidate cancellation notice",
}
ONLINE_CHANNELS = ("STATE_PORTAL", "MINISTRY_WEBSITE")


def channel_label(code: str) -> str:
	label = CHANNEL_LABELS.get(cstr(code))
	if not label:
		fail("TND_PUBLICATION_RULE_UNAVAILABLE", f"The publication channel {code!r} has no configured label.")
	return label


def _versions_in_force(applicability_date, *, trigger: str) -> list[dict[str, Any]]:
	date = getdate(applicability_date)
	out = []
	for reference_set in regulatory_reference.list_reference_sets(KIND):
		for version in regulatory_reference.list_regulatory_reference_versions(reference_set["reference_set"]):
			if version["status"] != "Active":
				continue
			if getdate(version["effective_from"]) > date or (version["effective_until"] and getdate(version["effective_until"]) < date):
				continue
			payload = version.get("payload") or {}
			if cstr(payload.get("trigger_event")) != trigger:
				continue
			out.append({**version, "reference_key": reference_set["reference_key"], "display_name": reference_set["display_name"]})
	return sorted(out, key=lambda v: (v["reference_key"], v["version_number"]))


def resolve_publication_rule(*, applicability_date, procurement_category: str = "Goods") -> dict[str, Any]:
	"""The exact rule snapshot for one authorisation: required channels,
	contributing version identities, minimum preparation days, threshold
	snapshot. `TND_PUBLICATION_RULE_UNAVAILABLE` when nothing is configured
	or a row would require an integration that MVP does not have."""
	versions = _versions_in_force(applicability_date, trigger=TRIGGER_INVITATION)
	if not versions:
		fail("TND_PUBLICATION_RULE_UNAVAILABLE", detail={"applicability_date": str(getdate(applicability_date)), "trigger": TRIGGER_INVITATION})
	channels = []
	seen: set[str] = set()
	rule_ids: set[str] = set()
	for version in versions:
		payload = version["payload"]
		code = cstr(payload.get("channel")).strip()
		if not code or code in seen:
			continue
		if cstr(payload.get("integration_evidence_contract_code")).strip():
			fail("TND_PUBLICATION_RULE_UNAVAILABLE", "A publication channel is configured for an integrated acknowledgement, which is not available in this release (TPR-CHG-001 v0.8 §5.5.1).", detail={"channel": code})
		seen.add(code)
		# The rule identity is the reference-set key's rule prefix
		# ("PUB-RULE-MOH-OT-2027-01/STATE_PORTAL"); `source_reference` is the
		# statutory citation ("s.96(2)") since the 24 Sep 2026 seed change.
		rule_ids.add(cstr(version["reference_key"]).split("/", 1)[0] or cstr(payload.get("source_reference")))
		channels.append(
			{
				"channel": code, "label": channel_label(code), "confirmation_mode": CONFIRMATION_MODE, "public_url_expected": code in ONLINE_CHANNELS,
				"reference": version["reference"], "reference_key": version["reference_key"], "version_number": version["version_number"], "verification_status": version["verification_status"],
				"obligation_id": cstr(payload.get("obligation_id")), "accountable_actor_role": cstr(payload.get("accountable_actor_role")), "recipient": cstr(payload.get("recipient")),
			}
		)
	# §10.1 order: State Portal; Ministry website; Notice board; Two national newspapers.
	order = list(CHANNEL_LABELS)
	channels.sort(key=lambda c: order.index(c["channel"]) if c["channel"] in order else len(order))
	profile = _schedule_profile(applicability_date, procurement_category)
	minimum, default = _preparation_period(profile)
	rule_id = sorted(rule_ids)[0] if len(rule_ids) == 1 else " / ".join(sorted(rule_ids))
	return {
		"rule_snapshot_id": rule_id, "applicability_date": str(getdate(applicability_date)), "channels": channels,
		"contributing_versions": [{"reference": c["reference"], "reference_key": c["reference_key"], "version_number": c["version_number"], "verification_status": c["verification_status"]} for c in channels],
		"minimum_preparation_days": minimum, "default_preparation_days": default, "schedule_profile": {"profile": profile.get("profile", ""), "version_number": profile.get("version_number"), "verification_status": profile.get("verification_status", ""), "basis": profile.get("basis", "")},
		"threshold_snapshot": _threshold_snapshot(applicability_date, procurement_category),
	}


def _schedule_profile(applicability_date, procurement_category: str) -> dict[str, Any]:
	try:
		profile = procurement_settings.resolve_schedule_profile(procurement_method="Open Tender", procurement_category=procurement_category, applicability_date=applicability_date)
	except Exception as exc:  # CFG_RULE_UNRESOLVED
		fail("TND_PUBLICATION_RULE_UNAVAILABLE", detail={"reason": str(exc)})
		return {}
	if not profile.get("found"):
		fail("TND_PUBLICATION_RULE_UNAVAILABLE", "No Open Tender schedule profile is in force for this Tender.", detail={"applicability_date": str(getdate(applicability_date))})
	return profile


def _preparation_period(profile: dict[str, Any]) -> tuple[int, int]:
	"""(verified legal minimum, default) days for the `bid_opening` period; 0 means not set."""
	for row in profile.get("milestones") or []:
		if row.get("milestone") == "bid_opening" and row.get("applies"):
			minimum, default = int(row.get("minimum_days") or 0), int(row.get("default_days") or 0)
			if minimum or default:
				profile["basis"] = "verified minimum" if minimum else f"profile default ({row.get('basis') or 'unverified'}); no verified minimum"
				return minimum, default
	fail("TND_PUBLICATION_RULE_UNAVAILABLE", "The schedule profile carries no minimum or default preparation period.")
	return 0, 0


def preparation_period(applicability_date, procurement_category: str) -> dict[str, int] | None:
	"""{"minimum_days": verified legal minimum (0 when none), "default_days": the usual period (0 when none)}, or None when no schedule
	profile resolves (authorisation reports that separately as TND_PUBLICATION_RULE_UNAVAILABLE)."""
	try:
		minimum, default = _preparation_period(_schedule_profile(applicability_date, procurement_category))
	except TendersError:
		return None
	return {"minimum_days": minimum, "default_days": default}


def minimum_preparation_days(applicability_date, procurement_category: str) -> int | None:
	"""The verified legal minimum, or None when no profile resolves; 0 when the profile records none."""
	period = preparation_period(applicability_date, procurement_category)
	return None if period is None else period["minimum_days"]


def period_shortfall(*, issue_date, submission_deadline, today, minimum_days: int) -> dict[str, Any] | None:
	"""§5.5.6: the earliest publication is the later of the issue date and
	today; the deadline must fall at least `minimum_days` after it. None when
	it does; otherwise the figures behind TND_PUBLICATION_PERIOD_INVALID."""
	if not submission_deadline or not minimum_days:
		return None
	published = max(getdate(issue_date), getdate(today)) if issue_date else getdate(today)
	earliest = published + timedelta(days=int(minimum_days))
	if getdate(submission_deadline) >= earliest:
		return None
	return {
		"minimum_days": int(minimum_days), "days_allowed": (getdate(submission_deadline) - published).days, "earliest_publication": str(published),
		"earliest_deadline": str(earliest), "submission_deadline": str(getdate(submission_deadline)),
	}


def _threshold_snapshot(applicability_date, procurement_category: str) -> dict[str, Any]:
	fiscal_year = frappe.db.get_value("Fiscal Year", {"year_start_date": ("<=", getdate(applicability_date)), "year_end_date": (">=", getdate(applicability_date))}, "name")
	if not fiscal_year:
		return {}
	try:
		register = regulatory_reference.get_regulatory_reference(cstr(fiscal_year))
	except Exception:
		return {}
	rows = [r for r in register.get("threshold_matrix") or [] if cstr(r.get("procurement_method")) == "Open Tender" and (not r.get("procurement_category") or r.get("procurement_category") == procurement_category)]
	return {"fiscal_year": cstr(fiscal_year), "currency": "KES", "rows": rows[:5], "reference": cstr(register.get("reference"))}


def cancellation_obligations(*, applicability_date) -> list[dict[str, Any]]:
	"""§4.10 — configured cancellation obligations with their due rules."""
	out = []
	for version in _versions_in_force(applicability_date, trigger=TRIGGER_CANCELLATION):
		payload = version["payload"]
		code = cstr(payload.get("channel")).strip()
		if not code:
			continue
		out.append(
			{
				"code": code, "label": CHANNEL_LABELS.get(code, code), "recipient": cstr(payload.get("recipient")), "due_rule": cstr(payload.get("due_rule")) or "Immediate", "days": payload.get("days"),
				"obligation_id": cstr(payload.get("obligation_id")), "reference": version["reference"], "reference_key": version["reference_key"], "version_number": version["version_number"],
			}
		)
	# §10.13 order: the notice channels first, then the PPRA report, then the candidate notice.
	order = list(CHANNEL_LABELS)
	out.sort(key=lambda o: (order.index(o["code"]) if o["code"] in order else len(order), o["reference_key"]))
	return out


def due_date(obligation: dict[str, Any], decided_on) -> Any:
	"""Calendar-day due rules only in MVP; a working-day rule falls back to
	calendar days and says so in the obligation label."""
	from datetime import timedelta

	base = getdate(decided_on)
	rule = obligation.get("due_rule") or "Immediate"
	days = int(obligation.get("days") or 0)
	if rule == "Immediate":
		return base
	return base + timedelta(days=days)


def snapshot_json(rule: dict[str, Any]) -> str:
	return json.dumps(rule, sort_keys=True, default=str)
