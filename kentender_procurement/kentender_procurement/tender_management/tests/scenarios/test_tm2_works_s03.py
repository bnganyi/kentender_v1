# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P12-01 / doc 7 §2 — TM2-WORKS-S03 (Addendum Affecting BOQ and Deadline).

**§2:** impact analysis, revised STD outputs + publication snapshot, supplier acknowledgement required,
deadline extension on issue. Aligns with **EX-13** / ``test_p5_05_issue_addendum`` and
``test_p5_05_timeline_patch_when_affects_deadline``.

Run::

	bench --site kentender.midas.com run-tests --app kentender_procurement \\
		--module kentender_procurement.tender_management.tests.scenarios.test_tm2_works_s03
"""

from __future__ import annotations

import json
import unittest

import frappe
from frappe.utils import add_days, cstr, get_datetime, now_datetime

from kentender_procurement.tender_management.scenarios.tm2_works_scenarios import (
	scenario_by_code,
	scenario_tracker_slug,
)
from kentender_procurement.tender_management.security.authorization.action_authorization_registry import (
	spec_for_action,
)
from kentender_procurement.tender_management.services.create_addendum import create_addendum
from kentender_procurement.tender_management.services.issue_addendum import issue_addendum
from kentender_procurement.tender_management.services.request_addendum_impact_analysis import (
	request_addendum_impact_analysis,
)
from kentender_procurement.tender_management.tests.test_p4_01_create_tender_from_package import (
	_P401Tm2Cleanup,
)
from kentender_procurement.tender_management.tests.test_p5_addendum_fixture import (
	_P5PublishedTenderChainMixin,
)

_CODE = "TM2-WORKS-S03"


class TestTM2WorksS03Catalog(unittest.TestCase):
	def test_scenario_registered_in_catalog(self) -> None:
		spec = scenario_by_code(_CODE)
		self.assertEqual(spec.code, _CODE)
		self.assertEqual(spec.name, "Addendum Affecting BOQ and Deadline")
		self.assertTrue(spec.purpose)
		self.assertTrue(spec.expected_result)

	def test_tracker_slug_matches_row_s_table(self) -> None:
		spec = scenario_by_code(_CODE)
		self.assertEqual(scenario_tracker_slug(spec), f"S-{int(_CODE.split('S')[-1]):02d}")


class TestTM2WorksS03AddendumBoqDeadlineAck(_P5PublishedTenderChainMixin, _P401Tm2Cleanup):
	"""Doc 7 §2 — TM2-WORKS-S03 (tracker **S-03**)."""

	def _mk_approved_for_publication(self, *, seed_outputs: bool = True) -> str:
		tcode = super()._mk_approved_for_publication(seed_outputs=False)
		if seed_outputs:
			self._materialize_real_std_outputs(tcode)
		return tcode

	def _materialize_real_std_outputs(self, tender_code: str) -> None:
		si = frappe.db.get_value(
			"TM2 Tender STD Binding",
			{"tender_code": tender_code, "is_active": 1},
			"tender_std_instance",
		)
		self.assertTrue(si)
		from kentender_procurement.tender_management.std_instance.generated_output import (
			StdInstanceGeneratedOutputService,
		)

		for fn in (
			StdInstanceGeneratedOutputService.generate_bundle,
			StdInstanceGeneratedOutputService.generate_dsm,
			StdInstanceGeneratedOutputService.generate_dom,
			StdInstanceGeneratedOutputService.generate_dem,
			StdInstanceGeneratedOutputService.generate_dcm,
		):
			d = fn(str(si))
			StdInstanceGeneratedOutputService.publish_output(d.name)

	def _cleanup_p505(self, tm2: str | None) -> None:
		frappe.set_user("Administrator")
		if not tm2 or not frappe.db.exists("TM2 Tender", tm2):
			return
		for ntf in frappe.get_all(
			"TM2 Notification Record",
			filters={"tm2_tender": tm2, "notification_type": "Addendum"},
			pluck="name",
		):
			if frappe.db.exists("TM2 Notification Record", ntf):
				frappe.delete_doc("TM2 Notification Record", ntf, force=True, ignore_permissions=True)
		for add in frappe.get_all("TM2 Addendum", filters={"tm2_tender": tm2}, pluck="name"):
			for ack in frappe.get_all(
				"TM2 Addendum Acknowledgement",
				filters={"tm2_addendum": add},
				pluck="name",
			):
				if frappe.db.exists("TM2 Addendum Acknowledgement", ack):
					frappe.delete_doc(
						"TM2 Addendum Acknowledgement",
						ack,
						force=True,
						ignore_permissions=True,
					)
			for air in frappe.get_all(
				"TM2 Addendum Impact Record",
				filters={"tm2_addendum": add},
				pluck="name",
			):
				if frappe.db.exists("TM2 Addendum Impact Record", air):
					frappe.delete_doc(
						"TM2 Addendum Impact Record",
						air,
						force=True,
						ignore_permissions=True,
					)
		self._cleanup_p503(tm2)

	def _impact_ctx(self) -> dict:
		spec = spec_for_action("ADD2_REQUEST_IMPACT_ANALYSIS")
		self.assertIsNotNone(spec)
		assert spec is not None
		return {"granted_permissions": [spec.required_permission]}

	def _issue_ctx(self) -> dict:
		spec = spec_for_action("ADD2_ISSUE")
		self.assertIsNotNone(spec)
		assert spec is not None
		return {"granted_permissions": [spec.required_permission]}

	def test_S_03_addendum_revises_outputs_timeline_and_requires_supplier_acknowledgement(self) -> None:
		"""BOQ + deadline impact → issue regenerates outputs + snapshot; ack stub; timeline extended."""
		tcode, tm2 = self._published_tender()
		self.addCleanup(self._cleanup_p505, tm2)

		p = self._base_payload()
		p["requires_supplier_acknowledgement"] = 1
		p["affects_deadline"] = 1
		out = create_addendum(
			"Administrator",
			tcode,
			payload=p,
			context=self._add_ctx(),
		)
		self.assertTrue(out.get("ok"), out)
		ac = str(out.get("addendum_code") or "")
		ad_name = str(out.get("addendum") or "")
		self.assertTrue(ac and ad_name)

		ia = request_addendum_impact_analysis(
			"Administrator",
			ac,
			context={
				**self._impact_ctx(),
				"proposed_changes": {
					"change_types": ["boq_quantity", "submission_deadline"],
				},
			},
		)
		self.assertTrue(ia.get("ok"), ia)

		ad = frappe.get_doc("TM2 Addendum", ad_name)
		ad.status = "Approved"
		ad.approved_by = "Administrator"
		ad.approved_at = now_datetime()
		ad.save(ignore_permissions=True)

		sup = self._ensure_supplier("S03")
		frappe.get_doc(
			{"doctype": "TM2 Supplier Participation", "tm2_tender": tm2, "supplier": sup}
		).insert(ignore_permissions=True)

		bind_name = frappe.db.get_value(
			"TM2 Tender STD Binding",
			{"tm2_tender": tm2, "is_active": 1},
			"name",
		)
		self.assertTrue(bind_name)
		pre = frappe.db.get_value(
			"TM2 Tender STD Binding",
			bind_name,
			[
				"bundle_output_code",
				"dsm_output_code",
				"dom_output_code",
				"dem_output_code",
				"dcm_output_code",
				"publication_snapshot_code",
				"published_snapshot_hash",
			],
			as_dict=True,
		)
		self.assertTrue(pre)
		for k in ("bundle_output_code", "dsm_output_code", "dom_output_code", "dem_output_code", "dcm_output_code"):
			self.assertTrue(cstr(pre.get(k) or "").strip(), f"missing pre-issue {k}")

		self._ensure_open_clarification_window(tm2)
		tl_name = frappe.db.get_value("TM2 Tender Timeline", {"tm2_tender": tm2}, "name")
		self.assertTrue(tl_name)
		tl = frappe.get_doc("TM2 Tender Timeline", tl_name)
		self.assertTrue(tl.submission_deadline_at and tl.opening_scheduled_at)
		want_sub = add_days(tl.submission_deadline_at, 3)
		want_open = add_days(tl.opening_scheduled_at, 3)

		issue_out = issue_addendum(
			"Administrator",
			ac,
			context={
				**self._issue_ctx(),
				"revised_submission_deadline_at": want_sub,
				"revised_opening_scheduled_at": want_open,
			},
		)
		self.assertTrue(issue_out.get("ok"), issue_out)
		self.assertEqual(issue_out.get("addendum_status"), "Issued")

		post_snap = cstr(issue_out.get("publication_snapshot_code") or "").strip()
		post_hash = cstr(issue_out.get("snapshot_hash") or "").strip()
		self.assertTrue(post_snap and post_hash)

		b = frappe.db.get_value(
			"TM2 Tender STD Binding",
			bind_name,
			[
				"bundle_output_code",
				"dsm_output_code",
				"dom_output_code",
				"dem_output_code",
				"dcm_output_code",
				"publication_snapshot_code",
				"published_snapshot_hash",
			],
			as_dict=True,
		)
		self.assertTrue(b)
		self.assertNotEqual(cstr(b.get("bundle_output_code")), cstr(pre.get("bundle_output_code")))
		self.assertNotEqual(cstr(b.get("dsm_output_code")), cstr(pre.get("dsm_output_code")))
		self.assertNotEqual(cstr(b.get("dom_output_code")), cstr(pre.get("dom_output_code")))
		self.assertNotEqual(cstr(b.get("dem_output_code")), cstr(pre.get("dem_output_code")))
		self.assertNotEqual(cstr(b.get("dcm_output_code")), cstr(pre.get("dcm_output_code")))
		self.assertEqual(cstr(b.get("publication_snapshot_code") or "").strip(), post_snap)
		self.assertEqual(cstr(b.get("published_snapshot_hash") or "").strip(), post_hash)

		tl.reload()
		self.assertEqual(get_datetime(tl.submission_deadline_at), get_datetime(want_sub))
		self.assertEqual(get_datetime(tl.opening_scheduled_at), get_datetime(want_open))

		acks = frappe.get_all(
			"TM2 Addendum Acknowledgement",
			filters={"tm2_addendum": ad_name},
			pluck="name",
		)
		self.assertEqual(len(acks), 1)

		ev = frappe.get_all(
			"TM2 Tender Audit Event",
			filters={"tm2_tender": tm2, "event_type": "Addendum Issued"},
			fields=["related_object_id", "event_payload"],
			order_by="creation desc",
			limit=1,
		)
		self.assertEqual(len(ev), 1)
		self.assertEqual(ev[0].get("related_object_id"), ad_name)
		pl = ev[0].get("event_payload") or {}
		if isinstance(pl, str):
			pl = json.loads(pl)
		self.assertEqual(pl.get("addendum_code"), ac)
		self.assertEqual(pl.get("tender_code"), tcode)
