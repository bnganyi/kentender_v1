# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""A bid answered from the Tender's own published requirements (EVL-CHG-001
v0.4 plan D17, C22): every automatic evaluation check can meet, with named
overrides for a branch (for example the 8 GB memory of EVL-CHG-001 v0.4 §9.5
D04-FAIL). Used by the canonical seed (under its own §10.1 facts) and by the
Bid Evaluation test and browser worlds. The answers go through Bid
Submission's own filling commands; nothing here writes a bid directly.
Seed and test only: never registered on a hook or used by a product path."""

from __future__ import annotations

from datetime import timedelta
from typing import Any

from frappe.utils import cstr, getdate

TEXT = {
	"processor_requirement": "64-bit business-class processor with 12 cores",
	"operating_system_compatibility": "Windows 11 Pro compatible with the organisational environment",
	"service_location_constraint": "Nairobi service centre",
	"support_description": "Escalation and warranty contacts supplied",
}
COMPANY = {
	"state_owned_enterprise": "No",
	"procuring_entity_interest": "No",
	**{f"conflict_{i:02d}": "No" for i in range(1, 9)},  # item 9 (resolution) stays hidden until item 7 or 8 is Yes
	"disclosure": "Arrived at the Tender independently",
	"business_structure": "Registered company",
}


def _offered(facts: dict[str, Any], key: str, overrides: dict[str, Any]):
	if key in overrides:
		return overrides[key]
	from kentender_procurement.bid_submission.services import consistency

	value = consistency.meeting_value(facts)
	return value if value is not None else TEXT.get(key, "As published")


def answers(bid: str, *, actor: str, at: str, overrides: dict[str, Any] | None = None) -> dict[str, dict[str, Any]]:
	"""Each task's values by field handle. `overrides` maps a requirement's
	characteristic or obligation key (for a technical or warranty value) or a
	company field key to the value to submit instead."""
	from frappe.utils import get_datetime

	from kentender_procurement.bid_submission.services import bid_context, consistency

	overrides = overrides or {}
	ctx = bid_context.load(bid, actor=actor, organisation="", at=get_datetime(at))
	out: dict[str, dict[str, Any]] = {"company": {}, "requirements": {}, "price": {}}
	for group in ctx.model.groups_of("requirements"):
		facts = group.published_facts or {}
		key = cstr(facts.get("characteristic_key") or facts.get("obligation_key"))
		for field in group.fields:
			if not field.editable:
				continue
			if field.field_key == "compliance":
				# the bidder states the truth: "Comply" unless the value offered (an override can fall short) does not meet it;
				# Bid Evaluation judges the value itself, so a branch like D04-FAIL still fails
				offered = _offered(facts, key, overrides) if key else None
				falls_short = key and consistency.meets(facts, offered) is False
				out["requirements"][field.handle] = "Do not comply" if falls_short else "Comply"
			elif field.field_key == "offered_value" and key:
				out["requirements"][field.handle] = _offered(facts, key, overrides)
			elif field.field_key == "offered_make_model":
				out["requirements"][field.handle] = overrides.get("offered_make_model", "ApexBook Pro 14")
			elif field.field_key == "offered_delivery_date" and facts.get("latest_delivery_date"):
				out["requirements"][field.handle] = overrides.get("offered_delivery_date",
					str(getdate(facts["latest_delivery_date"]) - timedelta(days=15)))
			elif field.field_key == "completion_date" and facts.get("window_end"):
				out["requirements"][field.handle] = str(getdate(facts["window_end"]) - timedelta(days=90 * int(facts.get("entry_number") or 1)))
			elif field.field_key == "contract_value":
				out["requirements"][field.handle] = "18000000.00"
	for group in ctx.model.groups_of("company"):
		for field in group.fields:
			if field.editable and field.field_key in {**COMPANY, **overrides}:
				out["company"][field.handle] = overrides.get(field.field_key, COMPANY.get(field.field_key))
	return out


def fill(bid: str, *, actor: str, at: str, overrides: dict[str, Any] | None = None) -> None:
	"""Answer the bid, then confirm every requirement override is what the bid now holds."""
	from frappe.utils import get_datetime

	from kentender_procurement.bid_submission.seeds import filling
	from kentender_procurement.bid_submission.services import bid_context

	filling.fill_everything(bid, user=actor, answers=answers(bid, actor=actor, at=at, overrides=overrides))
	if not overrides:
		return
	ctx = bid_context.load(bid, actor=actor, organisation="", at=get_datetime(at))
	for group in ctx.model.groups_of("requirements"):
		key = cstr((group.published_facts or {}).get("characteristic_key") or (group.published_facts or {}).get("obligation_key"))
		for field in group.fields:
			if field.field_key == "offered_value" and key in overrides and cstr(ctx.values.get(field.response_id)) != cstr(overrides[key]):
				raise AssertionError(f"the bid holds {ctx.values.get(field.response_id)!r} for {key}, not the override {overrides[key]!r}")
