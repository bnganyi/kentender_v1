# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The Account portal surface (BDS-CHG-001 v0.8 plan OD-B, slices 11.3–11.4):
which screen each `/account…` address answers, for whom, with the same
first payload the screen would read (KT-STD-001 §3A.1)."""

from __future__ import annotations

import frappe

from kentender_core.services import portal_runtime
from kentender_suppliers.supplier_accounts import portal
from kentender_suppliers.supplier_accounts.tests.support import MARY, PETER, AccountsCase


class TestAccountPortal(AccountsCase):
	def test_every_account_address_needs_a_signed_in_person(self):
		for path in ("/account", "/account/register", "/account/verify"):
			self.assertEqual(portal.resolve(path=path, query={}, user="Guest")["verdict"], "SIGN_IN", path)
		answered = portal_runtime.resolve("/account/register", user="Guest")
		self.assertEqual(answered["redirect"], "/login?redirect-to=%2Faccount%2Fregister")

	def test_a_person_without_an_account_is_given_the_registration_form(self):
		for path in ("/account", "/account/register"):
			answered = portal.resolve(path=path, query={}, user=PETER)
			data = answered["payload"]["data"]
			self.assertEqual((answered["verdict"], answered["payload"]["screen"], data["user_name"]), ("OK", "register", "Peter Mwangi"), path)
			self.assertEqual((data["next_step"]["headline"], data["journey"]["stages"][0]["holder"]), ("Enter the supplier organisation details.", "Peter Mwangi"), path)

	def test_the_account_page_carries_the_account_read(self):
		org = self.active_account()
		answered = portal.resolve(path="/account", query={}, user=MARY)
		self.assertEqual((answered["payload"]["screen"], answered["payload"]["data"]["organisation"]["organisation"]), ("account", org))
		self.assertEqual(answered["title"], "Account")

	def test_another_organisations_account_is_not_found(self):
		org = self.active_account()
		answered = portal.resolve(path="/account", query={"organisation": org}, user=PETER)
		self.assertEqual(answered["verdict"], "NOT_FOUND")
		self.assertNotIn("Afya", str(answered))

	def test_the_verification_link_carries_only_its_token(self):
		answered = portal.resolve(path="/account/verify", query={"token": "abc"}, user=PETER)
		self.assertEqual(answered["payload"], {"screen": "verify", "data": {"token": "abc"}})

	def test_an_unknown_account_address_is_not_found(self):
		self.assertEqual(portal.resolve(path="/account/settings", query={}, user=MARY)["verdict"], "NOT_FOUND")

	def test_the_header_names_the_organisation_a_person_acts_for(self):
		org = self.active_account()
		self.assertEqual(portal.identity_detail(MARY), frappe.db.get_value("Supplier Organisation", org, "legal_name"))
		self.assertEqual(portal.identity_detail(PETER), "")  # no account yet: only their name shows
		self.assertEqual(portal.identity_detail("Administrator"), "")  # staff never read as a supplier
		self.assertEqual(portal.identity_detail("Guest"), "")
