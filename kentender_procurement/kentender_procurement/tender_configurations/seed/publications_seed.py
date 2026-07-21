# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Seed helper: ensure at least one publication row per A2 tab for demo/UI smoke."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import add_to_date, cstr, now_datetime

from kentender_procurement.std_engine.constants import CANONICAL_PACKAGE_ID
from kentender_procurement.tender_configurations.seed.ui00_seed import seed_ui00_dashboard
from kentender_procurement.tender_configurations.services.document_preview import (
	confirm_document_preview,
	generate_document_preview,
)
from kentender_procurement.tender_configurations.services.f1_publication_handoff import (
	PUBLICATION_DOCTYPE,
	PUBLICATION_STATUS_AWAITING,
	PUBLICATION_STATUS_PUBLISHED,
	PUBLICATION_STATUS_READY,
	PUBLICATION_STATUS_RETURNED,
	PUBLICATION_STATUS_SCHEDULED,
)
from kentender_procurement.tender_configurations.services.publication_setup import (
	publish_tender,
	return_publication_for_correction,
	save_publication_setup,
)
from kentender_procurement.tender_configurations.seed.preview_fixtures import (
	_approve,
	_seed_bidder_facing_config,
)


def _prepare_config(cfg_id: str) -> str:
	# Reset prior confirm/publish state so seed can re-run on the same configs.
	frappe.db.set_value(
		"Tender Configuration",
		cfg_id,
		{
			"std_version": CANONICAL_PACKAGE_ID,
			"document_preview": None,
			"publication_package": None,
			"confirmed_document_package": None,
			"it_publication_record": None,
		},
		update_modified=False,
	)
	frappe.db.commit()
	_approve(cfg_id)
	_seed_bidder_facing_config(cfg_id)
	gen = generate_document_preview(cfg_id)
	if cstr(gen.get("preview_status")) != "Generated":
		frappe.throw(f"Preview failed for {cfg_id}: {gen.get('render_exception')}")
	conf = confirm_document_preview(cfg_id, {"confirm_ready_for_handoff": 1})
	pub_id = cstr(conf.get("publication_id") or "")
	if not pub_id:
		frappe.throw(f"Confirm did not create publication for {cfg_id}")
	return pub_id


def seed_publications_demo(*, clear: bool = False) -> dict[str, Any]:
	"""Create publication records covering Awaiting / Ready / Scheduled / Published / Returned."""
	frappe.set_user("Administrator")
	seed = seed_ui00_dashboard(clear=bool(clear))
	configs = list(seed.get("configurations") or [])
	if len(configs) < 5:
		# Reuse first config repeatedly when seed is small.
		while len(configs) < 5:
			configs.append(configs[0])

	now = now_datetime()
	result: dict[str, Any] = {"publications": {}}

	# 1) Awaiting Setup — leave after confirm
	pub_await = _prepare_config(configs[0])
	result["publications"][PUBLICATION_STATUS_AWAITING] = pub_await

	# 2) Ready to Publish
	pub_ready = _prepare_config(configs[1])
	save_publication_setup(
		pub_ready,
		{
			"publication_datetime": str(now),
			"tender_notice": "Demo tender notice — ready to publish.",
			"submission_deadline": str(add_to_date(now, days=14)),
			"opening_datetime": str(add_to_date(now, days=14, hours=1)),
			"bidder_visibility": "All Registered Bidders",
			"activate_bidder_workspace": 1,
		},
	)
	result["publications"][PUBLICATION_STATUS_READY] = pub_ready

	# 3) Scheduled
	pub_sched = _prepare_config(configs[2])
	future = add_to_date(now, days=5)
	save_publication_setup(
		pub_sched,
		{
			"publication_datetime": str(future),
			"tender_notice": "Demo tender notice — scheduled.",
			"submission_deadline": str(add_to_date(future, days=14)),
			"opening_datetime": str(add_to_date(future, days=14, hours=1)),
			"bidder_visibility": "Invited Bidders Only",
			"activate_bidder_workspace": 1,
		},
	)
	result["publications"][PUBLICATION_STATUS_SCHEDULED] = pub_sched

	# 4) Published
	pub_pub = _prepare_config(configs[3])
	save_publication_setup(
		pub_pub,
		{
			"publication_datetime": str(now),
			"tender_notice": "Demo tender notice — published.",
			"submission_deadline": str(add_to_date(now, days=14)),
			"opening_datetime": str(add_to_date(now, days=14, hours=1)),
			"bidder_visibility": "All Registered Bidders",
			"activate_bidder_workspace": 1,
		},
	)
	publish_tender(pub_pub)
	result["publications"][PUBLICATION_STATUS_PUBLISHED] = pub_pub

	# 5) Returned
	pub_ret = _prepare_config(configs[4])
	return_publication_for_correction(pub_ret, {"reason": "Demo return for correction"})
	result["publications"][PUBLICATION_STATUS_RETURNED] = pub_ret

	result["counts"] = {
		PUBLICATION_STATUS_AWAITING: frappe.db.count(
			PUBLICATION_DOCTYPE, {"status": PUBLICATION_STATUS_AWAITING}
		),
		PUBLICATION_STATUS_READY: frappe.db.count(
			PUBLICATION_DOCTYPE, {"status": PUBLICATION_STATUS_READY}
		),
		PUBLICATION_STATUS_SCHEDULED: frappe.db.count(
			PUBLICATION_DOCTYPE, {"status": PUBLICATION_STATUS_SCHEDULED}
		),
		PUBLICATION_STATUS_PUBLISHED: frappe.db.count(
			PUBLICATION_DOCTYPE, {"status": PUBLICATION_STATUS_PUBLISHED}
		),
		PUBLICATION_STATUS_RETURNED: frappe.db.count(
			PUBLICATION_DOCTYPE, {"status": PUBLICATION_STATUS_RETURNED}
		),
	}
	return result
