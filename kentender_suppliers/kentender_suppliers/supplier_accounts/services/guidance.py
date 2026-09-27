# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The Account record's next step and journey (BDS-CHG-001 v0.8 §5.12,
§10.19; KT-STD-001 §3B): three stages — Set up account / Verify email /
Account ready — and one actor answer built from the same states and guards
the commands use. Suspended is a blocked access state, never an approval
stage, and never offers the supplier a way to reactivate itself."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cstr

from kentender_core.services import next_step as ns
from kentender_suppliers.supplier_accounts.services import authorization as authz
from kentender_suppliers.supplier_accounts.services import facts
from kentender_suppliers.supplier_accounts.services.labels import datetime_label

STAGES = (("ACCOUNT_SETUP", "Set up account"), ("CONTACT_VERIFICATION", "Verify email"), ("ACTIVE", "Account ready"))
SUPPORT_LABEL = "Supplier Account support officer"


def full_name(user: str) -> str:
	return cstr(frappe.db.get_value("User", user, "full_name") or user)


def support_officers() -> list[str]:
	"""Current holders of the support responsibility, resolved now, never invented."""
	users = frappe.get_all("User Responsibility Assignment", filters={"business_role": authz.SUPPORT_ROLE, "status": "Enabled"}, pluck="user", order_by="creation asc", limit_page_length=0)
	out: list[str] = []
	for user in users:
		if user not in out and authz.is_support_officer(user):
			out.append(user)
	return out


def for_new_account(viewer: str = "") -> dict[str, Any]:
	"""`viewer` is the person registering; the current stage names them (BDS-DES-03)."""
	return {
		"next_step": ns.answer(ns.KIND_YOUR_TURN, headline="Enter the supplier organisation details.", stage="ACCOUNT_SETUP", primary_action="create_account"),
		"journey": ns.journey(STAGES, current="ACCOUNT_SETUP", holder_display=full_name(viewer) if viewer and viewer != "Guest" else ""),
	}


def for_account(org, *, viewer: str) -> dict[str, Any]:
	"""`org` is the Supplier Organisation; `viewer` an assigned supplier user."""
	missing = facts.missing_items(org)
	if org.account_status == "Suspended":
		people = [full_name(u) for u in support_officers()]
		holder = ns.holder(SUPPORT_LABEL, people)
		names = ", ".join(people)
		headline = f"{SUPPORT_LABEL} {names} is reviewing suspended access." if names else f"A {SUPPORT_LABEL.lower()} is reviewing suspended access."
		since_display = datetime_label(org.status_since) if org.status_since else ""
		return {
			"next_step": ns.answer(ns.KIND_WAITING, headline=headline, stage="ACTIVE", holder=holder, since=ns.since(org.status_since, since_display)),
			"journey": ns.journey(STAGES, current="ACTIVE", blocked=True, holder_display=holder["display"]),
		}
	if missing:
		fixes = [ns.fix("Edit organisation", responsibility="Supplier user", kind=ns.FIX_FOCUS, fix_id=f"edit_organisation:{m['field']}", target=m["field"], primary=i == 0) for i, m in enumerate(missing)]
		blockers = [ns.blocker(ns.guard(False, reason_code="BDS_ACCOUNT_REQUIRED", message=m["text"], headline=m["text"], fixes=[fixes[i]])) for i, m in enumerate(missing)]
		headline = "Add the missing official phone before continuing." if [m["field"] for m in missing] == ["official_phone"] else f"Complete {len(missing)} item{'s' if len(missing) != 1 else ''} before starting a bid."
		# One missing item is named as the sentence (§10.5 BDS-DES-04-ATTENTION); several are listed per blocker.
		sentence = f"{missing[0]['text']}." if len(missing) == 1 else ""
		return {
			"next_step": ns.answer(ns.KIND_BLOCKED, headline=headline, sentence=sentence, stage="ACCOUNT_SETUP", blockers=blockers, fixes=fixes, primary_action="edit_organisation"),
			"journey": ns.journey(STAGES, current="ACCOUNT_SETUP", blocked=True, holder_display=full_name(viewer)),
		}
	if org.account_status == "Pending verification":
		fix = ns.fix("Resend verification link", responsibility="Supplier user", kind=ns.FIX_COMMAND, fix_id="send_account_verification", primary=True)
		sentence = f"Verify {org.official_email} before starting a bid." if org.official_email else ""  # §10.5 BDS-DES-04-VERIFY
		return {
			"next_step": ns.answer(ns.KIND_YOUR_TURN, headline="Verify your email to finish setting up the supplier account.", sentence=sentence, stage="CONTACT_VERIFICATION", fixes=[fix], primary_action="send_account_verification"),
			"journey": ns.journey(STAGES, current="CONTACT_VERIFICATION", holder_display=full_name(viewer)),
		}
	return {
		"next_step": ns.answer(ns.KIND_DONE, headline="The supplier account is ready.", stage="ACTIVE"),
		"journey": ns.journey(STAGES, complete=True),
	}
