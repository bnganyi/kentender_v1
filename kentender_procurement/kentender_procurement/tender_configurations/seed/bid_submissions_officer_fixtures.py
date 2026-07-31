# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Officer Bid Submissions fixtures (docs/bids §23)."""

from __future__ import annotations

import json
from typing import Any

import frappe
from frappe.utils import add_to_date, cstr, now_datetime

from kentender_procurement.tender_configurations.services.bid_submissions import (
	officer_link_supersession,
	officer_withdraw_sealed_bid,
	open_submitted_bids,
)

def ensure_pub_with_deadlines(*, past_deadline: bool = True, past_opening: bool = True):
	"""Create a minimal Published publication + sealed bids for officer tests."""
	from kentender_procurement.std_engine.constants import CANONICAL_PACKAGE_ID
	from kentender_procurement.std_engine.services.ensure_active_canonical_std import (
		ensure_active_canonical_ppra_it_std,
	)
	from kentender_procurement.tender_configurations.seed.preview_fixtures import (
		_approve,
		_seed_bidder_facing_config,
	)
	from kentender_procurement.tender_configurations.seed.ui00_seed import seed_ui00_dashboard
	from kentender_procurement.tender_configurations.services.document_preview import (
		confirm_document_preview,
		generate_document_preview,
	)
	from kentender_procurement.tender_configurations.services.electronic_bid import (
		create_or_get_draft,
		fill_draft_for_tests,
		submit_and_seal,
	)
	from kentender_procurement.tender_configurations.services.publication_setup import (
		publish_tender_for_development_preview,
		save_publication_setup,
	)
	from kentender_procurement.tender_configurations.services.schema_compiler import (
		persist_compiled_schema,
	)

	ensure_active_canonical_ppra_it_std(force_reimport=False)
	seed = seed_ui00_dashboard(clear=True)
	cfg_id = seed["configurations"][0]
	frappe.db.set_value("Tender Configuration", cfg_id, "std_version", CANONICAL_PACKAGE_ID)
	_approve(cfg_id)
	_seed_bidder_facing_config(cfg_id)
	persist_compiled_schema(cfg_id)
	# Soften preview blockers for unit fixture when CFG-04 schedule gate fires.
	sched = frappe.db.get_value("Tender Configuration", cfg_id, "implementation_schedule")
	blob = {}
	try:
		blob = json.loads(sched or "{}")
	except (TypeError, ValueError):
		blob = {}
	if isinstance(blob, dict):
		blob.setdefault("milestones", [{"name": "Delivery", "date": "2026-12-01"}])
		blob.setdefault("delivery_timing_complete", 1)
		frappe.db.set_value(
			"Tender Configuration", cfg_id, "implementation_schedule", json.dumps(blob)
		)
	frappe.db.commit()

	gen = generate_document_preview(cfg_id)
	if gen.get("preview_status") != "Generated":
		# Bypass: stamp a minimal confirmed package path via direct publication seed
		return seed_publication_direct(cfg_id, past_deadline=past_deadline, past_opening=past_opening)

	conf = confirm_document_preview(cfg_id, {"confirm_ready_for_handoff": 1})
	pub_id = conf["publication_id"]
	now = now_datetime()
	sub = add_to_date(now, days=-2) if past_deadline else add_to_date(now, days=14)
	opn = add_to_date(now, days=-1) if past_opening else add_to_date(now, days=15)
	save_publication_setup(
		pub_id,
		{
			"publication_mode": "immediate",
			"publication_datetime": str(add_to_date(now, days=-3)),
			"tender_notice": "Bid Submissions officer fixture notice.",
			"clarification_deadline": str(add_to_date(sub, days=-1)),
			"submission_deadline": str(sub),
			"opening_datetime": str(opn),
			"bidder_visibility": "All Registered Bidders",
			"activate_bidder_workspace": 1,
			"acknowledgement_confirmed": 1,
		},
	)
	publish_tender_for_development_preview(pub_id)
	# Ensure deadlines stick after publish.
	frappe.db.set_value(
		"IT Tender Publication Record",
		pub_id,
		{"submission_deadline": sub, "opening_datetime": opn},
	)
	frappe.db.commit()

	bids = seal_three_bidders(cfg_id, pub_id)
	frappe.set_user("Administrator")
	return {"publication_id": pub_id, "configuration_id": cfg_id, "bid_ids": bids}


def seal_three_bidders(cfg_id: str, pub_id: str) -> list[str]:
	from kentender_procurement.tender_configurations.services.electronic_bid import (
		fill_draft_for_tests,
		submit_and_seal,
	)
	from kentender_procurement.tender_configurations.services.schema_compiler import (
		persist_compiled_schema,
	)

	schema = persist_compiled_schema(cfg_id)
	bids = []
	for i, label in enumerate(("Alpha Systems Ltd", "Beta Soft PLC", "Gamma Tech Ltd")):
		doc = frappe.get_doc(
			{
				"doctype": "Electronic Bid Submission",
				"configuration": cfg_id,
				"configuration_ref": cfg_id,
				"publication": pub_id,
				"bidder_label": label,
				"bidder_legal_name": label,
				"offer_type": "Main",
				"status": "Draft",
				"schema_hash": cstr(schema.get("schema_hash") or ""),
				"schema_snapshot": json.dumps(schema),
				"responses": "{}",
			}
		)
		doc.insert(ignore_permissions=True)
		frappe.db.set_value("Electronic Bid Submission", doc.name, "owner", f"bidder{i}@test.local")
		fill_draft_for_tests(doc.name)
		submit_and_seal(doc.name)
		# Received before deadline (deadline is typically now-2d in fixtures).
		sealed_before = add_to_date(now_datetime(), days=-3)
		frappe.db.set_value(
			"Electronic Bid Submission",
			doc.name,
			{
				"publication": pub_id,
				"bidder_legal_name": label,
				"offer_type": "Main",
				"sealed_at": sealed_before,
				"receipt_issued_at": sealed_before,
			},
		)
		bids.append(doc.name)
	frappe.db.commit()
	return bids


def seed_publication_direct(cfg_id: str, *, past_deadline: bool, past_opening: bool):
	"""Fallback when preview generation is blocked — minimal Published pub + sealed bids."""
	from kentender_procurement.tender_configurations.services.electronic_bid import (
		create_or_get_draft,
		fill_draft_for_tests,
		submit_and_seal,
	)
	from kentender_procurement.tender_configurations.services.f1_publication_handoff import (
		PACKAGE_DOCTYPE,
	)
	from kentender_procurement.tender_configurations.services.schema_compiler import (
		persist_compiled_schema,
	)

	persist_compiled_schema(cfg_id)
	now = now_datetime()
	sub = add_to_date(now, days=-2) if past_deadline else add_to_date(now, days=14)
	opn = add_to_date(now, days=-1) if past_opening else add_to_date(now, days=15)
	pkg = frappe.get_doc(
		{
			"doctype": PACKAGE_DOCTYPE,
			"configuration": cfg_id,
			"configuration_ref": cfg_id,
			"package_status": "Awaiting Publication Setup",
			"document_hash": frappe.generate_hash(length=32),
			"tender_html": "<html><body>fixture</body></html>",
			"bidder_submission_schema": json.dumps({"sections": []}),
			"evaluation_schema": json.dumps({}),
			"price_schedule_schema": json.dumps({}),
			"forms_evidence_schema": json.dumps({}),
		}
	)
	pkg.flags.ignore_permissions = True
	pkg.insert(ignore_permissions=True)
	pub = frappe.get_doc(
		{
			"doctype": "IT Tender Publication Record",
			"configuration": cfg_id,
			"configuration_ref": cfg_id,
			"confirmed_package": pkg.name,
			"document_hash": pkg.document_hash,
			"status": "Published",
			"submission_deadline": sub,
			"opening_datetime": opn,
			"publication_datetime": add_to_date(now, days=-3),
			"tender_notice": "Direct fixture notice",
			"activate_bidder_workspace": 1,
			"electronic_template_snapshot": json.dumps(
				{
					"sections": [
						{"section_key": "form_of_tender", "label": "Form of Tender"},
						{"section_key": "price_schedule", "label": "Price Schedule"},
					]
				}
			),
		}
	)
	pub.flags.ignore_publication_boundary = True
	pub.insert(ignore_permissions=True)
	frappe.db.commit()
	bids = seal_three_bidders(cfg_id, pub.name)
	return {"publication_id": pub.name, "configuration_id": cfg_id, "bid_ids": bids}




def seed_bid_submissions_officer_fixtures(*, clear: bool = True) -> dict[str, Any]:
	frappe.set_user("Administrator")
	if clear:
		for name in frappe.get_all("IT Bid Opening Record", pluck="name"):
			frappe.delete_doc("IT Bid Opening Record", name, force=True, ignore_permissions=True)

	out: dict[str, Any] = {"scenarios": {}}
	out["scenarios"]["receiving"] = ensure_pub_with_deadlines(past_deadline=False, past_opening=False)
	sealed = ensure_pub_with_deadlines(past_deadline=True, past_opening=True)
	out["scenarios"]["closed_sealed"] = sealed
	opened = ensure_pub_with_deadlines(past_deadline=True, past_opening=True)
	open_submitted_bids(opened["publication_id"])
	out["scenarios"]["opened_three"] = opened
	supersede = ensure_pub_with_deadlines(past_deadline=True, past_opening=True)
	officer_link_supersession(supersede["bid_ids"][0], supersede["bid_ids"][1])
	out["scenarios"]["supersession"] = supersede
	withdrawn = ensure_pub_with_deadlines(past_deadline=True, past_opening=True)
	officer_withdraw_sealed_bid(withdrawn["bid_ids"][0])
	out["scenarios"]["withdrawn"] = withdrawn
	multi = ensure_pub_with_deadlines(past_deadline=True, past_opening=True)
	frappe.db.set_value("Electronic Bid Submission", multi["bid_ids"][0], "lots_json", json.dumps(["Lot A", "Lot B"]))
	out["scenarios"]["multi_lot"] = multi
	alt = ensure_pub_with_deadlines(past_deadline=True, past_opening=True)
	frappe.db.set_value("Electronic Bid Submission", alt["bid_ids"][0], "offer_type", "Alternative")
	out["scenarios"]["alternative"] = alt
	empty = ensure_pub_with_deadlines(past_deadline=True, past_opening=True)
	for bid_id in empty["bid_ids"]:
		officer_withdraw_sealed_bid(bid_id)
	open_submitted_bids(empty["publication_id"])
	out["scenarios"]["opened_empty"] = empty
	out["roles"] = {"metadata_only": "Purchase User", "authorised_opener": "Administrator"}
	out["seeded_at"] = str(now_datetime())
	frappe.db.commit()
	return out
