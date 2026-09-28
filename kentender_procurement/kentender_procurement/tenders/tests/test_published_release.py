# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""TPR-CHG-001 v0.13 §5.8 items 14–15 (TPR13-AC-001/002, TPR13-IMP-001/002;
approved by the Project Owner 28 Sep 2026): after publication, a Tender whose
bound release became Superseded still issues a lawful addendum on that same
release while its checks pass; Withdrawn blocks the issue and keeps the
addendum awaiting issue; nothing rebinds. The release's lifecycle is changed
in memory for the test only — the installed release row is never written."""

from __future__ import annotations

import types
from unittest import mock

import frappe

from kentender_procurement.std_templates.services import binding as std_binding
from kentender_procurement.std_templates.services import runtime as std_runtime
from kentender_procurement.tenders.services import addenda, bid_definition
from kentender_procurement.tenders.services.errors import TendersError
from kentender_procurement.tenders.tests import fixtures as fx
from kentender_procurement.tenders.tests.test_open_period import OpenPeriodCase


class PublishedReleaseCase(OpenPeriodCase):
	def lifecycle(self, state: str) -> None:
		"""The STD binding check reads `state` as the release's lifecycle; the
		integrity check (which records its result on the row) sees the real
		release, so the installed row is never changed."""

		def release_doc(release_id):
			doc = std_runtime.release_doc(release_id)  # a fresh instance, never saved
			doc.lifecycle_status = state
			return doc

		view = types.SimpleNamespace(**{n: getattr(std_runtime, n) for n in dir(std_runtime) if not n.startswith("__")})
		view.release_doc = release_doc
		patcher = mock.patch.object(std_binding, "runtime", view)
		patcher.start()
		self.addCleanup(patcher.stop)

	def awaiting_issue(self) -> str:
		frappe.flags.kt_tenders_clock = "2027-05-31 08:30:00"
		name = self._addendum(values={**self.FIXTURE_ADDENDUM, "revised_submission_deadline": "2027-06-12 11:00:00"})
		addenda.submit_addendum_for_issue(tender=self.name, addendum=name, expected_record_version=self._root().record_version, idempotency_key=fx.key(), user=fx.OFFICER)
		frappe.flags.kt_tenders_clock = "2027-05-31 09:00:00"
		return name

	def issue(self, name: str):
		return addenda.issue_addendum(tender=self.name, addendum=name, expected_record_version=self._root().record_version, idempotency_key=fx.key(), user=fx.HOPF)


class TestAddendumOnABoundRelease(PublishedReleaseCase):
	def test_superseded_after_publication_still_issues_on_the_same_release(self):
		bound = frappe.db.get_value("Tender", self.name, "template_release_id")
		prior = bid_definition.current(self.name)["definition_version"]
		name = self.awaiting_issue()
		self.lifecycle("Superseded")
		self.issue(name)
		self.assertNotEqual(frappe.db.get_value("Tender Addendum", name, "status"), "Awaiting issue")
		successor = frappe.get_all("Tender Bid Definition", filters={"tender": self.name, "definition_version": prior + 1}, fields=["definition_json"])
		self.assertEqual(len(successor), 1)
		self.assertEqual(frappe.parse_json(successor[0].definition_json)["template_release_id"], bound)  # never a successor release
		self.assertEqual(frappe.db.get_value("Tender", self.name, "template_release_id"), bound)

	def test_withdrawn_after_publication_blocks_the_issue_and_keeps_the_addendum(self):
		prior = bid_definition.current(self.name)["definition_version"]
		name = self.awaiting_issue()
		self.lifecycle("Withdrawn")
		with self.assertRaises(TendersError) as ctx:
			self.issue(name)
		self.assertEqual(ctx.exception.code, "TND_TEMPLATE_RELEASE_WITHDRAWN")
		self.assertEqual(frappe.db.get_value("Tender Addendum", name, "status"), "Awaiting issue")
		self.assertEqual(bid_definition.current(self.name)["definition_version"], prior)
		self.assertEqual(frappe.db.count("Tender Bid Definition", {"tender": self.name, "definition_version": prior + 1}), 0)
