# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""BOP-CHG-001 v0.10 plan Phase 7 (BOP10-701, 702, 705): the endpoints are thin
and name their arguments; a refusal comes back as data with its §8 code and
sentence; refused and protected attempts are audited; pages are guarded;
technical search reaches status records only. BOP-A02 (direct API part)."""

from __future__ import annotations

import inspect

import frappe

from kentender_procurement.bid_opening import api
from kentender_procurement.bid_opening.tests.support import AO, AUDITOR, CHAIR, INDEPENDENT, MEMBER, OUTSIDER
from kentender_procurement.bid_opening.tests.test_bop_ceremony import CeremonyCase
from kentender_procurement.bid_submission.tests.support import key


class ApiCase(CeremonyCase):
	def as_user(self, user: str, fn, *args, **kwargs):
		frappe.set_user(user)
		try:
			return fn(*args, **kwargs)
		finally:
			frappe.set_user("Administrator")

	def audits(self, action: str) -> list:
		return frappe.get_all("Audit Event", filters={"action": action, "document_name": self.reference}, fields=["event_type", "performed_by"], order_by="creation asc")


class TestShape(ApiCase):
	def test_every_endpoint_names_its_arguments_and_forwards_nothing_else(self):
		endpoints = [f for name, f in inspect.getmembers(api, inspect.isfunction) if not name.startswith("_") and f.__module__ == api.__name__]
		self.assertEqual(len(endpoints), 33)  # a removed endpoint must be a deliberate change
		# the public opening page's read is the only endpoint a guest reaches (BOP v0.10 §10.5)
		self.assertEqual({f.__name__ for f in endpoints if f in frappe.guest_methods}, {"get_public_opening"})
		for fn in endpoints:
			with self.subTest(endpoint=fn.__name__):
				kinds = {p.kind for p in inspect.signature(fn).parameters.values()}
				self.assertNotIn(inspect.Parameter.VAR_KEYWORD, kinds)  # no **kwargs: no cmd/csrf_token forwarded into a service
				self.assertIn("tender_reference", inspect.signature(fn).parameters)
		self.assertFalse([n for n in dir(api) if any(w in n.lower() for w in ("decrypt", "release_box", "approve", "override"))])


class TestRefusalsAndAudit(ApiCase):
	def test_bop_a02_the_chair_alone_cannot_act_through_the_api(self):
		self.assertTrue(self.submit(self.signed())["ok"])
		self.prepared()
		self.at(self.minutes_before(0.5))
		self.as_user(CHAIR, api.join_opening, self.reference, key())
		self.close_box()
		self.heartbeat_all((CHAIR,))
		self.receive()
		self.at(self.minutes_after(0.2))
		refused = self.as_user(CHAIR, api.begin_opening, self.reference, self.case_version(), key())
		self.assertEqual((refused["ok"], refused["code"]), (False, "BOP_MEMBER_ABSENT"))
		self.assertEqual(self.case_doc().state, "Ready to open")
		self.assertEqual([a.performed_by for a in self.audits("BeginOpening")], [CHAIR])
		for user in ("Administrator", MEMBER):
			with self.subTest(user=user), self.assertRaises(frappe.DoesNotExistError) as ctx:
				self.as_user(user, api.begin_opening, self.reference, self.case_version(), key())
			self.assertEqual(str(ctx.exception), "Not found")
		self.assertEqual({a.event_type for a in self.audits("BeginOpening")}, {"Bid opening refused", "Bid opening not found"})
		stale = self.as_user(AO, api.record_not_held, self.reference, "x", 0, key())
		self.assertEqual((stale["ok"], stale["code"], stale["message"]), (False, "BOP_VERSION_CONFLICT", "Someone updated this opening record. Refresh the page before continuing."))

	def test_a_guessed_tender_or_route_confers_nothing(self):
		with self.assertRaises(frappe.DoesNotExistError):
			self.as_user(CHAIR, api.get_opening, "TND-DOES-NOT-EXIST")
		self.prepared()
		with self.assertRaises(frappe.DoesNotExistError):
			self.as_user(OUTSIDER, api.get_opening, self.reference)
		self.assertEqual(self.as_user(AUDITOR, api.get_opening, self.reference)["opening"]["tender_reference"], self.reference)


class TestPages(ApiCase):
	def test_bid_pages_only_for_the_committee(self):
		entry = self.opened()
		self.as_user(MEMBER, api.get_bid_pages, self.reference, entry)
		self.assertTrue(frappe.local.response.filecontent.startswith(b"%PDF"))
		for user in (AUDITOR, "Administrator", OUTSIDER, AO):
			with self.subTest(user=user), self.assertRaises(frappe.DoesNotExistError):
				self.as_user(user, api.get_bid_pages, self.reference, entry)

	def test_technical_search_reaches_status_records_only(self):
		from kentender_procurement.bid_opening.services import technical_read

		doctypes = {r["doctype"] for r in technical_read.reference_resolvers()}
		self.assertEqual(doctypes, {"Bid Opening Case", "Opening Access Incident", "Proceeding"})
		for doctype in doctypes:
			self.assertTrue(frappe.get_meta(doctype).permissions)
