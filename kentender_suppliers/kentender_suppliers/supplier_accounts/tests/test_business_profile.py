# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The supplier Account's business profile: the standing facts of the Form of
Tender's business questionnaire (business structure, owners, capital, trade
licence, maximum business value, state-owned status, year of registration),
held once on the Account and copied into each bid (release 1.4 plan, WP-2).
Any active member of the organisation may keep it; every save is version
checked, idempotent and audited by field name only (personal data)."""

from __future__ import annotations

import json

import frappe

from kentender_suppliers.supplier_accounts.services import business_profile
from kentender_suppliers.supplier_accounts.services.errors import AccountError
from kentender_suppliers.supplier_accounts.tests.support import DAVID, GRACE, MARY, AccountsCase, key

COMPANY = {
	"business_structure": "Registered company", "company_type": "Private company", "nominal_capital": "5000000.00", "issued_capital": "2500000.00",
	"trade_licence_number": "TL-2027-0451", "trade_licence_expiry": "2027-12-31", "maximum_business_value": "80000000.00",
	"state_owned": "No", "year_of_registration": 2014,
	"directors": [
		{"name": "Mary Wanjiku", "nationality": "Kenyan", "citizenship": "Kenyan", "shares": "60"},
		{"name": "John Kamau", "nationality": "Kenyan", "citizenship": "Kenyan", "shares": "40"},
	],
}


class TestBusinessProfile(AccountsCase):
	def save(self, org: str, values: dict, user: str = MARY, version=None):
		if version is None:
			version = business_profile.get_business_profile(organisation=org, user=user)["record_version"]
		return business_profile.update_business_profile(organisation=org, values=values, expected_version=version, idempotency_key=key(), user=user)

	def test_a_new_account_has_an_empty_profile_that_lists_what_is_missing(self):
		org = self.active_account()
		profile = business_profile.get_business_profile(organisation=org, user=MARY)
		self.assertEqual((profile["record_version"], profile["values"]["business_structure"]), (0, ""))
		self.assertEqual(profile["missing"][0], {"field": "business_structure", "text": "Choose the business structure"})

	def test_a_company_profile_is_saved_read_back_and_complete(self):
		org = self.active_account()
		saved = self.save(org, COMPANY)
		self.assertEqual((saved["ok"], saved["record_version"]), (True, 1))
		profile = business_profile.get_business_profile(organisation=org, user=MARY)
		self.assertEqual(profile["missing"], [])
		self.assertEqual([(r["name"], r["shares"]) for r in profile["values"]["directors"]], [("Mary Wanjiku", "60.00"), ("John Kamau", "40.00")])
		self.assertEqual((profile["values"]["nominal_capital"], profile["values"]["state_owned"]), ("5000000.00", "No"))

	def test_shares_must_total_one_hundred_and_the_error_names_the_table(self):
		org = self.active_account()
		bad = {**COMPANY, "directors": [{"name": "Mary Wanjiku", "nationality": "Kenyan", "citizenship": "Kenyan", "shares": "60"}]}
		result = self.save(org, bad)
		self.assertFalse(result["ok"])
		self.assertIn("directors", result["errors"])
		self.assertIn("100", result["errors"]["directors"])
		self.assertEqual(frappe.db.count("Supplier Business Profile", {"organisation": org}), 0)

	def test_a_cell_error_names_the_row_and_the_column(self):
		org = self.active_account()
		bad = {**COMPANY, "directors": [{"name": "Mary Wanjiku", "nationality": "Kenyan", "citizenship": "Kenyan", "shares": "sixty"}, {"name": "John Kamau", "nationality": "Kenyan", "citizenship": "Kenyan", "shares": "40"}]}
		self.assertEqual(list(self.save(org, bad)["errors"]), ["directors.0.shares"])

	def test_more_than_ten_rows_are_refused(self):
		org = self.active_account()
		rows = [{"name": f"Partner {i}", "nationality": "Kenyan", "citizenship": "Kenyan", "shares": "10"} for i in range(11)]
		result = self.save(org, {"business_structure": "Partnership", "partners": rows})
		self.assertIn("at most 10", result["errors"]["partners"])

	def test_a_sole_proprietor_needs_the_proprietors_details_and_drops_the_other_structures(self):
		org = self.active_account()
		self.save(org, COMPANY)
		sole = {"business_structure": "Sole proprietor", "sole_proprietor_name": "Mary Wanjiku", "sole_proprietor_age": 41, "sole_proprietor_nationality": "Kenyan", "sole_proprietor_country_of_origin": "Kenya", "sole_proprietor_citizenship": "Kenyan"}
		self.save(org, sole)
		values = business_profile.get_business_profile(organisation=org, user=MARY)["values"]
		self.assertEqual((values["directors"], values["company_type"], values["nominal_capital"]), ([], "", ""))
		self.assertEqual(values["sole_proprietor_age"], 41)

	def test_the_missing_list_follows_the_structure(self):
		org = self.active_account()
		self.save(org, {"business_structure": "Partnership"})
		fields = [m["field"] for m in business_profile.get_business_profile(organisation=org, user=MARY)["missing"]]
		self.assertIn("partners", fields)
		self.assertNotIn("directors", fields)

	def test_a_representative_may_edit_but_a_stranger_may_not(self):
		from kentender_suppliers.supplier_accounts.services import assignments

		org = self.active_account()
		assignments.assign_supplier_representative(organisation=org, email=DAVID, full_name="David Ouma", job_title="Bid Officer", idempotency_key=key(), user=MARY)
		self.assertTrue(self.save(org, COMPANY, user=DAVID)["ok"])
		with self.assertRaises(Exception):
			business_profile.get_business_profile(organisation=org, user=GRACE)

	def test_the_version_is_checked_and_a_repeated_key_returns_the_recorded_result(self):
		org = self.active_account()
		request = key()
		first = business_profile.update_business_profile(organisation=org, values=COMPANY, expected_version=0, idempotency_key=request, user=MARY)
		again = business_profile.update_business_profile(organisation=org, values=COMPANY, expected_version=0, idempotency_key=request, user=MARY)
		self.assertEqual(first, again)
		with self.assertRaises(AccountError) as ctx:
			business_profile.update_business_profile(organisation=org, values={"state_owned": "Yes"}, expected_version=0, idempotency_key=key(), user=MARY)
		self.assertEqual(ctx.exception.code, "BDS_STALE_VERSION")

	def test_the_audit_event_names_the_changed_fields_and_never_the_values(self):
		org = self.active_account()
		self.save(org, COMPANY)
		rows = frappe.get_all("Audit Event", filters={"document_name": org, "action": "update_business_profile"}, fields=["metadata"], limit=1)
		text = rows[0].metadata if isinstance(rows[0].metadata, str) else json.dumps(rows[0].metadata)
		self.assertIn("directors", text)
		self.assertNotIn("John Kamau", text)
		self.assertNotIn("TL-2027-0451", text)

	def test_a_suspended_account_cannot_be_edited(self):
		from kentender_suppliers.supplier_accounts.services import access
		from kentender_suppliers.supplier_accounts.tests.support import AMINA

		org = self.active_account()
		access.suspend_supplier_account(organisation=org, reason="Reported misuse of the account.", expected_version=frappe.db.get_value("Supplier Organisation", org, "record_version"), idempotency_key=key(), user=AMINA)
		with self.assertRaises(AccountError) as ctx:
			self.save(org, COMPANY, version=0)
		self.assertEqual(ctx.exception.code, "BDS_ACCOUNT_SUSPENDED")

	def test_the_provider_answers_the_profile_as_facts(self):
		from kentender_suppliers.supplier_accounts.services import provider

		org = self.active_account()
		self.save(org, COMPANY)
		facts = provider.business_profile(organisation_id=org)
		self.assertEqual(facts["business_structure"], "Registered company")
		self.assertEqual(facts["directors"][0]["name"], "Mary Wanjiku")
		self.assertEqual(facts["complete"], True)
		self.assertIsNone(provider.business_profile(organisation_id="NO-SUCH"))
