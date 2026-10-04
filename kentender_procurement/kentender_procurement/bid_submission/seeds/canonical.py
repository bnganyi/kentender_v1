# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The canonical Start bid (BDS-CHG-001 v0.8 §13.3; retires the Tenders
stand-in, TPR FU-25): on 19 May 2027 at 09:20 David Ouma starts Afya Digital
Supplies Limited's bid on the canonical Tender. The Tenders seed calls
`seed_candidate` through the `kt_tender_seed_candidate` hook at that step,
and the arrangement it returns is the candidate the rest of the Tenders
chronology (the clarification and its answer, the addendum notices) uses.

The supplier account comes first, through the `kt_canonical_supplier_accounts`
hook (Supplier Accounts' own seed), since this app never imports that one."""

from __future__ import annotations

from typing import Any

import frappe

NAMESPACE = "KENTENDER_MVP_1_R1_BDS"
DAVID = "david.ouma@afyadigital.example"
AFYA_COUNTRY, AFYA_REGISTRATION = "Kenya", "PVT-9X7K2M"
OFFICIAL_EMAIL = "tenders@afyadigital.example"


def _hook(name: str):
	hooks = frappe.get_hooks(name) or []
	if not hooks:
		frappe.throw(f"No supplier account seed is installed (hook {name}); install kentender_suppliers.")
	return frappe.get_attr(hooks[-1])


def remove_seeded_suppliers(*, namespace: str, users: tuple[str, ...] = ()) -> dict[str, int]:
	"""`kt_tender_seed_candidate_cleanup`: remove the supplier accounts (and
	their portal users) a browser-test world seeded in `namespace`, and that
	namespace's Bid Submission journal entries."""
	from kentender_procurement.bid_submission.seeds import clear

	deleted = clear.wipe(tenders=[], namespace=namespace)
	for doctype, count in (_hook("kt_seed_supplier_account_removal")(namespace=namespace, users=tuple(users)) or {}).items():
		deleted[doctype] = deleted.get(doctype, 0) + count
	return deleted


def seed_candidate(*, tender_reference: str, at, supplier: dict[str, Any] | None = None) -> str:
	"""Start a bid at `at` as the supplier's representative; returns the bidder
	arrangement, which is the candidate registration. Without `supplier` it is
	the canonical Afya bid (David Ouma). `supplier` names `facts` (the
	registration facts), `registrant`/`registrant_name`, `representative`/
	`representative_name` and optionally `namespace`, for a browser-test world.
	Idempotent: Start bid returns the existing bid."""
	from kentender_procurement.bid_submission.services import start_bid, supplier_gateway

	if supplier:
		_hook("kt_seed_supplier_account")(
			facts=supplier["facts"], registrant=supplier["registrant"], registrant_name=supplier["registrant_name"], representative=supplier["representative"],
			representative_name=supplier["representative_name"], namespace=supplier.get("namespace", NAMESPACE), key_prefix=supplier.get("namespace", NAMESPACE).lower(),
		)
		country, registration, email, person = supplier["facts"]["country"], supplier["facts"]["registration_number"], supplier["facts"]["official_email"], supplier["representative"]
	else:
		_hook("kt_canonical_supplier_accounts")()
		country, registration, email, person = AFYA_COUNTRY, AFYA_REGISTRATION, OFFICIAL_EMAIL, DAVID
	organisation = (supplier_gateway.find_active_account(country=country, registration_number=registration) or {}).get("organisation_id")
	if not organisation:
		frappe.throw(f"The supplier account {registration} is not Active.")
	contact = next((c for c in supplier_gateway.verified_contacts(organisation_id=organisation) if c.get("value") == email), None)
	if not contact:
		frappe.throw(f"{email} is not a verified contact of supplier account {registration}.")
	from kentender_procurement.bid_submission.services import tenders_gateway

	root = tenders_gateway.tender_root(tender_reference)
	if not root:
		frappe.throw(f"No published Tender has the reference {tender_reference}.")
	namespace = (supplier or {}).get("namespace", NAMESPACE)
	saved = {flag: frappe.flags.get(flag) for flag in ("kt_bds_clock", "kt_bds_fixture_namespace")}
	frappe.flags.kt_bds_clock = at
	frappe.flags.kt_bds_fixture_namespace = namespace
	try:
		result: dict[str, Any] = start_bid.start_bid(
			tender_reference=tender_reference, organisation=organisation, arrangement={"arrangement_type": "Single organisation"},
			notice_contact_id=contact["contact_id"], idempotency_key=f"seed-start-bid-{root.name}-{registration}", user=person,
		)
	finally:
		for flag, value in saved.items():
			frappe.flags[flag] = value
	if not result.get("ok"):
		frappe.throw(f"Start bid was refused for {registration}: {result}")
	return result["bidder_arrangement_id"]
