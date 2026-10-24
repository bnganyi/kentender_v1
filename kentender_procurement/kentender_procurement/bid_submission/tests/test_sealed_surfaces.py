# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The sealed box and the tender-security intake across every surface
(Project Owner, 10 October 2026).

An empty sealed box and a populated one answer a procuring-entity user — and
Administrator and System Manager — identically before the opening, on every
read path the framework offers: counts, lists, the report view, link search,
the form load, a direct record read and the technical search. A technical
account gets no more than anyone else; after the opening it still does not
unlock them. These are application restrictions: a database or infrastructure
operator is outside them and bound only by TRUST-ADR-001's custody controls."""

from __future__ import annotations

from kentender_core.seeds.calendar import fiscal as F, world as W  # noqa: F401
import json

import frappe

from kentender_core.tests import v16_fixtures as fx
from kentender_procurement.bid_submission.services import records, security_duty
from kentender_procurement.bid_submission.services.sealed import SEALED_DOCTYPES, refuse_sealed_files
from kentender_procurement.bid_submission.tests.support import assign_intake_officer, opening_crossed
from kentender_procurement.bid_submission.tests.test_changes_and_close import ChangeCase
from kentender_procurement.tenders.tests import fixtures as tender_fx

SYSTEM_MANAGER = "kt.test.sealed.surfaces.sysmgr@example.test"  # the address `fx.user` gives this local part
USERS = ("Administrator", SYSTEM_MANAGER, tender_fx.AO, tender_fx.HOPF, tender_fx.OFFICER, tender_fx.AUDITOR)
LISTED = ("Bid Workspace", "Bidder Arrangement", "Bid Submission Version", "Tender Box Envelope", "Bid Receipt", "Bid Submission Attempt", "Bid Opening Handoff",
	"Tender Security Intake", "Tender Security Verification", "Bid Hand-off", "Bid Submission Close", "Tender Security Exposure")


def as_user(user, fn, *args, **kwargs):
	frappe.set_user(user)
	try:
		return fn(*args, **kwargs)
	finally:
		frappe.set_user("Administrator")


def reportview(doctype: str) -> dict:
	frappe.local.form_dict = frappe._dict(doctype=doctype, fields=json.dumps(["name"]), filters="[]", start=0, page_length=20, with_comment_count=0, view="Report")
	from frappe.desk import reportview as rv

	return rv.get()


def attempt(fn, *args, **kwargs):
	"""The answer of a read path: its value, or the kind of refusal — never the detail."""
	try:
		return {"ok": fn(*args, **kwargs)}
	except frappe.PermissionError:
		return {"refused": "PermissionError"}
	except frappe.DoesNotExistError:
		return {"refused": "DoesNotExistError"}


class TestSealedSurfaces(ChangeCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		frappe.set_user("Administrator")
		cls.manager = fx.user("sealed.surfaces.sysmgr", "Sealed Surfaces System Manager", roles=("System Manager",))

	def snapshot(self, tender_name: str) -> dict:
		"""Every read path's answer, for every user, about the sealed families."""
		from frappe.client import get_count, get_list
		from frappe.desk.search import search_link

		out: dict = {}
		for user in USERS:
			who = SYSTEM_MANAGER if user == SYSTEM_MANAGER else user
			for doctype in LISTED:
				key = f"{user}|{doctype}"
				out[key + "|count"] = attempt(as_user, who, get_count, doctype)
				out[key + "|list"] = attempt(as_user, who, get_list, doctype, fields=["name"], limit_page_length=20)
				out[key + "|report"] = attempt(as_user, who, reportview, doctype)
				out[key + "|search"] = attempt(as_user, who, search_link, doctype, "")
		return out

	def test_an_empty_and_a_populated_box_answer_every_user_identically_before_opening(self):
		empty = self.snapshot(self.name)
		self.submitted()
		assign_intake_officer(self)
		populated = self.snapshot(self.name)
		self.assertEqual(populated, empty)
		# every count is zero, every list empty: no user, Administrator included, learns that a bid exists
		for key, answer in populated.items():
			if key.endswith("|count"):
				self.assertIn(answer, ({"ok": 0}, {"refused": "PermissionError"}), key)
			if key.endswith("|list"):
				self.assertIn(answer, ({"ok": []}, {"refused": "PermissionError"}), key)

	def test_a_direct_record_read_is_refused_to_everyone_including_administrator(self):
		receipt = self.submitted()
		names = {
			"Bid Workspace": self.bid, "Tender Box Envelope": frappe.db.get_value("Tender Box Envelope", {"tender": self.name}, "name"),
			"Bid Receipt": frappe.db.get_value("Bid Receipt", {"receipt_reference": receipt}, "name"),
			"Bid Submission Version": frappe.db.get_value("Bid Submission Version", {"tender": self.name}, "name"),
		}
		from frappe.client import get
		from frappe.desk.form.load import getdoc

		for user in USERS:
			for doctype, name in names.items():
				with self.subTest(user=user, doctype=doctype):
					self.assertTrue(name)
					self.assertEqual(attempt(as_user, user, get, doctype, name), {"refused": "PermissionError"})
					self.assertEqual(attempt(as_user, user, getdoc, doctype, name), {"refused": "PermissionError"})

	def test_the_tender_security_intake_is_not_a_record_anyone_reads_not_even_its_recorder_on_the_desk(self):
		assign_intake_officer(self)
		from kentender_procurement.bid_submission.services import security_intake

		facts = next(g["published_facts"] for s in __import__("kentender_procurement.tenders.services.bid_definition", fromlist=["current"]).current(self.name)["definition"]["sections"] for g in s["groups"] if g["rule_id"] == "RR-TENDER-SECURITY")
		recorded = security_intake.record_physical_tender_security_receipt(tender_reference=self.reference, instrument_type=facts["permitted_forms"][0], issuer="KCB Bank Kenya", instrument_reference="KCB/TG/SURF/1",
			amount=facts["amount"], currency=facts["currency"], received_at=W("2027-05-19 09:00:00"), confirmed=True, idempotency_key=records.uuid4().hex, user=tender_fx.OFFICER)
		name = frappe.db.get_value("Tender Security Intake", {"intake_reference": recorded["intake_reference"]}, "name")
		from frappe.client import get

		for user in USERS:
			with self.subTest(user=user):
				self.assertEqual(attempt(as_user, user, get, "Tender Security Intake", name), {"refused": "PermissionError"})
		# the officer reads it only through the intake service, which is POST, scoped and logged
		self.assertEqual([r["intake_reference"] for r in security_intake.list_my_intakes(user=tender_fx.OFFICER)["rows"]], [recorded["intake_reference"]])

	def test_opening_does_not_unlock_the_records_for_a_technical_account(self):
		self.submitted()
		opening_crossed(self)
		for user in ("Administrator", SYSTEM_MANAGER):
			for doctype in ("Bid Workspace", "Tender Box Envelope", "Bid Receipt"):
				with self.subTest(user=user, doctype=doctype):
					from frappe.client import get_count

					self.assertIn(attempt(as_user, user, get_count, doctype), ({"ok": 0}, {"refused": "PermissionError"}))

	def test_the_technical_record_search_finds_no_sealed_record(self):
		from kentender_core.services import technical_search

		receipt = self.submitted()
		for query in (self.bid, receipt, self.reference, "Afya", "KCB"):
			text = json.dumps(technical_search.search(query=query, user="Administrator"))
			for doctype in SEALED_DOCTYPES:
				self.assertNotIn(doctype, text, (query, doctype))

	def test_a_private_bid_file_is_not_served_by_its_url_to_anyone(self):
		stored = frappe.get_doc({"doctype": "File", "file_name": "sealed-probe.txt", "attached_to_doctype": "Bid Evidence", "attached_to_name": "probe", "is_private": 1, "content": b"sealed probe"})
		stored.flags.ignore_permissions = True
		stored.insert()
		self.addCleanup(frappe.delete_doc, "File", stored.name, force=True, ignore_permissions=True)
		for user in ("Administrator", SYSTEM_MANAGER):
			frappe.set_user(user)
			frappe.local.request = frappe._dict(path=stored.file_url)
			try:
				with self.assertRaises(frappe.PermissionError):
					refuse_sealed_files()
			finally:
				frappe.set_user("Administrator")
		frappe.local.request = frappe._dict(path="/private/files/not-a-sealed-file.pdf")
		refuse_sealed_files()  # another file is untouched
		frappe.local.request = None
