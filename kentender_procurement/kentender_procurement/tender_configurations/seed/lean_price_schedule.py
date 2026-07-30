# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Lean Price Schedule fixtures (pack 11 — PE-neutral, config-driven)."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

SECTION_KEY = "price_schedule"

FIXTURE_SINGLE_LOT = "single_lot"
FIXTURE_MULTI_LOT = "multi_lot"
FIXTURE_MULTI_CURRENCY = "multi_currency"

SCHEDULE_SUPPLY = "supply_installation"
SCHEDULE_RECURRENT = "recurrent_costs"

OFFER_MAIN = "main"


def _line(
	line_id: str,
	*,
	ref: str,
	description: str,
	schedule_key: str,
	quantity: str,
	unit: str,
	order: int,
	lot_id: str = "",
	required: bool = True,
	country_of_origin_required: bool = False,
	permitted_currencies: list[str] | None = None,
	zero_allowed: bool = False,
	periods: list[str] | None = None,
) -> dict[str, Any]:
	return {
		"line_id": line_id,
		"display_reference": ref,
		"description": description,
		"schedule_key": schedule_key,
		"lot_id": lot_id,
		"quantity": quantity,
		"unit": unit,
		"required": 1 if required else 0,
		"country_of_origin_required": 1 if country_of_origin_required else 0,
		"permitted_currencies": list(permitted_currencies or ["KES"]),
		"zero_allowed": 1 if zero_allowed else 0,
		"periods": list(periods or []),
		"display_order": order,
	}


def lean_price_schedule_flags(fixture: str = FIXTURE_SINGLE_LOT) -> dict[str, Any]:
	raw = (fixture or FIXTURE_SINGLE_LOT).strip().lower()
	if raw == FIXTURE_MULTI_LOT:
		return {
			"single_lot": 0,
			"lots": [
				{"lot_id": "lot-a", "label": "Lot A — Core systems"},
				{"lot_id": "lot-b", "label": "Lot B — Support services"},
			],
			"alternatives_permitted": 0,
			"offers": [{"offer_id": OFFER_MAIN, "label": "Main offer"}],
			"currency_precision": 2,
			"separate_tax_required": 0,
		}
	if raw == FIXTURE_MULTI_CURRENCY:
		return {
			"single_lot": 1,
			"lots": [],
			"alternatives_permitted": 1,
			"offers": [
				{"offer_id": OFFER_MAIN, "label": "Main offer"},
				{"offer_id": "alt-1", "label": "Alternative offer 1"},
			],
			"currency_precision": 2,
			"separate_tax_required": 0,
		}
	return {
		"single_lot": 1,
		"lots": [],
		"alternatives_permitted": 0,
		"offers": [{"offer_id": OFFER_MAIN, "label": "Main offer"}],
		"currency_precision": 2,
		"separate_tax_required": 0,
	}


def lean_price_schedule_lines(fixture: str = FIXTURE_SINGLE_LOT) -> list[dict[str, Any]]:
	raw = (fixture or FIXTURE_SINGLE_LOT).strip().lower()
	if raw == FIXTURE_MULTI_LOT:
		return [
			_line(
				"ps-si-a-001",
				ref="A.1",
				description="Application servers (Enterprise Grade)",
				schedule_key=SCHEDULE_SUPPLY,
				quantity="4",
				unit="Users",
				order=10,
				lot_id="lot-a",
				country_of_origin_required=True,
				permitted_currencies=["KES"],
			),
			_line(
				"ps-si-a-002",
				ref="A.2",
				description="Network storage array (100TB)",
				schedule_key=SCHEDULE_SUPPLY,
				quantity="1",
				unit="Lump sum",
				order=20,
				lot_id="lot-a",
				country_of_origin_required=True,
				permitted_currencies=["KES"],
			),
			_line(
				"ps-rc-b-001",
				ref="B.1",
				description="Annual software support",
				schedule_key=SCHEDULE_RECURRENT,
				quantity="1",
				unit="Annual",
				order=30,
				lot_id="lot-b",
				permitted_currencies=["KES"],
				periods=["year_1", "year_2", "year_3"],
			),
			_line(
				"ps-rc-b-002",
				ref="B.2",
				description="Optional extended helpdesk window",
				schedule_key=SCHEDULE_RECURRENT,
				quantity="1",
				unit="Per month",
				order=40,
				lot_id="lot-b",
				required=False,
				permitted_currencies=["KES"],
				periods=["year_1", "year_2", "year_3"],
			),
		]
	if raw == FIXTURE_MULTI_CURRENCY:
		return [
			_line(
				"ps-si-001",
				ref="1.1",
				description="Application servers (Enterprise Grade)",
				schedule_key=SCHEDULE_SUPPLY,
				quantity="4",
				unit="Users",
				order=10,
				country_of_origin_required=True,
				permitted_currencies=["KES", "USD"],
			),
			_line(
				"ps-si-002",
				ref="1.2",
				description="Network storage array (100TB)",
				schedule_key=SCHEDULE_SUPPLY,
				quantity="1",
				unit="Lump sum",
				order=20,
				country_of_origin_required=True,
				permitted_currencies=["KES", "USD"],
				zero_allowed=True,
			),
			_line(
				"ps-si-003",
				ref="1.3",
				description="Optional spare parts kit",
				schedule_key=SCHEDULE_SUPPLY,
				quantity="1",
				unit="Lump sum",
				order=30,
				required=False,
				permitted_currencies=["KES", "USD"],
			),
		]
	# single_lot — supply only (CFG-06 preview units: Users / Lump sum / Per month / Per GB/month / Annual)
	return [
		_line(
			"ps-si-001",
			ref="1.1",
			description="Application servers (Enterprise Grade)",
			schedule_key=SCHEDULE_SUPPLY,
			quantity="4",
			unit="Users",
			order=10,
			country_of_origin_required=True,
			permitted_currencies=["KES"],
		),
		_line(
			"ps-si-002",
			ref="1.2",
			description="Network storage array (100TB)",
			schedule_key=SCHEDULE_SUPPLY,
			quantity="1",
			unit="Lump sum",
			order=20,
			country_of_origin_required=True,
			permitted_currencies=["KES"],
		),
		_line(
			"ps-si-003",
			ref="1.3",
			description="Optional spare parts kit",
			schedule_key=SCHEDULE_SUPPLY,
			quantity="1",
			unit="Lump sum",
			order=30,
			required=False,
			permitted_currencies=["KES"],
			zero_allowed=True,
		),
	]


def lean_price_schedule_schedules(fixture: str = FIXTURE_SINGLE_LOT) -> list[dict[str, Any]]:
	lines = lean_price_schedule_lines(fixture)
	keys = []
	for row in lines:
		sk = row["schedule_key"]
		if sk not in keys:
			keys.append(sk)
	labels = {
		SCHEDULE_SUPPLY: "Supply and Installation",
		SCHEDULE_RECURRENT: "Recurrent Costs",
	}
	out = []
	for i, sk in enumerate(keys):
		periods: list[str] = []
		for row in lines:
			if row["schedule_key"] != sk:
				continue
			for p in row.get("periods") or []:
				if p not in periods:
					periods.append(p)
		out.append(
			{
				"schedule_key": sk,
				"title": labels.get(sk, sk.replace("_", " ").title()),
				"display_order": (i + 1) * 10,
				"periods": periods,
				"period_labels": {
					"year_1": "Year 1",
					"year_2": "Year 2",
					"year_3": "Year 3",
				},
			}
		)
	return out


def lean_price_schedule_as_cfg_items(fixture: str = FIXTURE_SINGLE_LOT) -> list[dict[str, Any]]:
	"""CFG-06-shaped items for Tender Configuration.price_schedule."""
	group_map = {
		SCHEDULE_SUPPLY: "Supply and Installation",
		SCHEDULE_RECURRENT: "Recurrent Costs",
	}
	out = []
	for row in lean_price_schedule_lines(fixture):
		out.append(
			{
				"item_id": row["line_id"],
				"item_name": row["description"],
				"bidder_facing_description": row["description"],
				"display_reference": row["display_reference"],
				"price_group": group_map.get(row["schedule_key"], row["schedule_key"]),
				"quantity": row["quantity"],
				"unit": row["unit"],
				"currency": (row["permitted_currencies"] or ["KES"])[0],
				"pricing_basis": "Unit price",
				"lot_id": row.get("lot_id") or "",
				"required": row["required"],
				"country_of_origin_required": row["country_of_origin_required"],
				"permitted_currencies": row["permitted_currencies"],
				"zero_allowed": row["zero_allowed"],
				"periods": row.get("periods") or [],
				"display_order": row["display_order"],
			}
		)
	return out


def materialize_lean_price_schedule(fixture: str = FIXTURE_SINGLE_LOT) -> dict[str, Any]:
	"""Published section payload for bidder schema hydrate."""
	return {
		"section_key": SECTION_KEY,
		"title": "Price Schedule",
		"section_type": "price_schedule",
		"slice_status": "price_schedule_implemented",
		"bidder_instructions": "Enter your prices for the goods and services specified in this tender.",
		"price_lines": deepcopy(lean_price_schedule_lines(fixture)),
		"schedules": deepcopy(lean_price_schedule_schedules(fixture)),
		"price_schedule_flags": deepcopy(lean_price_schedule_flags(fixture)),
	}


def publish_lean_price_schedule_for_tests(
	*,
	fixture: str = FIXTURE_SINGLE_LOT,
	clear: bool = True,
) -> dict[str, Any]:
	"""Seed ui00 + lean PS fixture + publish for Playwright / integration smoke."""
	import json

	import frappe
	from frappe.utils import add_to_date, cstr, now_datetime

	from kentender_procurement.std_engine.constants import CANONICAL_PACKAGE_ID
	from kentender_procurement.tender_configurations.seed.preview_fixtures import (
		_approve,
		_seed_bidder_facing_config,
	)
	from kentender_procurement.tender_configurations.seed.ui00_seed import seed_ui00_dashboard
	from kentender_procurement.tender_configurations.services.document_preview import (
		confirm_document_preview,
		generate_document_preview,
	)
	from kentender_procurement.tender_configurations.services.publication_setup import (
		publish_tender_for_development_preview,
		save_publication_setup,
	)

	seed = seed_ui00_dashboard(clear=clear)
	cfg_id = seed["configurations"][0]
	flags = lean_price_schedule_flags(fixture)
	frappe.db.set_value(
		"Tender Configuration",
		cfg_id,
		{
			"std_version": CANONICAL_PACKAGE_ID,
			"short_scope_summary": "Lean price schedule publish for tests.",
			"price_schedule": json.dumps(
				{
					"items": lean_price_schedule_as_cfg_items(fixture),
					"flags": flags,
					"lean_fixture": fixture,
				}
			),
		},
	)
	_approve(cfg_id)
	_seed_bidder_facing_config(cfg_id)
	# Re-apply after bidder-facing seed (which may overwrite price_schedule).
	frappe.db.set_value(
		"Tender Configuration",
		cfg_id,
		{
			"price_schedule": json.dumps(
				{
					"items": lean_price_schedule_as_cfg_items(fixture),
					"flags": flags,
					"lean_fixture": fixture,
				}
			),
		},
	)
	for name in frappe.get_all(
		"Electronic Bid Submission",
		filters={"configuration": cfg_id},
		pluck="name",
	):
		frappe.delete_doc("Electronic Bid Submission", name, force=1, ignore_permissions=True)
	frappe.db.commit()

	gen = generate_document_preview(cfg_id)
	if cstr(gen.get("preview_status")) != "Generated":
		frappe.throw(
			frappe._("PS lean preview failed: {0}").format(gen.get("render_exception")),
			title="PS_LEAN_SEED_PREVIEW",
		)
	conf = confirm_document_preview(cfg_id, {"confirm_ready_for_handoff": 1})
	pub_id = conf["publication_id"]
	now = now_datetime()
	save_publication_setup(
		pub_id,
		{
			"publication_mode": "immediate",
			"publication_datetime": str(now),
			"tender_notice": "Price schedule notice.",
			"clarification_deadline": str(add_to_date(now, days=2)),
			"submission_deadline": str(add_to_date(now, days=14)),
			"opening_datetime": str(add_to_date(now, days=15, hours=1)),
			"bidder_visibility": "All Registered Bidders",
			"activate_bidder_workspace": 1,
			"acknowledgement_confirmed": 1,
		},
	)
	published = publish_tender_for_development_preview(pub_id)
	pub_ref = cstr(published.get("publication_ref") or "") or cstr(
		frappe.db.get_value("IT Tender Publication Record", pub_id, "publication_ref") or ""
	)
	return {
		"configuration_id": cfg_id,
		"publication_id": pub_id,
		"publication_ref": pub_ref,
		"fixture": fixture,
	}
