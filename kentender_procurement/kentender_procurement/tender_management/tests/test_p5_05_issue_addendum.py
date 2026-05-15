# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P5-05 — doc 9 §10.5 ``issue_addendum``.

Doc 9 §25 **EX-13** (exit gate): first issued addendum regenerates Bundle / DSM / DOM / DEM / DCM
and binds a revised publication snapshot — ``test_EX_13_*``.

Run::

	bench --site kentender.midas.com run-tests --app kentender_procurement \\
		--module kentender_procurement.tender_management.tests.test_p5_05_issue_addendum
"""

from __future__ import annotations

import json

import frappe
from frappe.utils import add_days, cstr, get_datetime, now_datetime

from kentender_procurement.tender_management.security.authorization.action_authorization_registry import (
	spec_for_action,
)
from kentender_procurement.tender_management.security.authorization.denial_codes import DenialCode
from kentender_procurement.tender_management.services.create_addendum import create_addendum
from kentender_procurement.tender_management.services.issue_addendum import issueAddendum, issue_addendum
from kentender_procurement.tender_management.services.request_addendum_impact_analysis import (
	request_addendum_impact_analysis,
)
from kentender_procurement.tender_management.tests.test_p4_01_create_tender_from_package import (
	_P401Tm2Cleanup,
)
from kentender_procurement.tender_management.tests.test_p5_addendum_fixture import (
	_P5PublishedTenderChainMixin,
)


class TestP505IssueAddendum(_P5PublishedTenderChainMixin, _P401Tm2Cleanup):
	"""``issue_addendum`` runs ``regenerate_outputs_for_addendum`` — SI must reference real generated outputs."""

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

	def _approved_structural_addendum(
		self,
		*,
		requires_ack: bool = True,
		affects_deadline: bool = False,
	) -> tuple[str, str, str, str, str]:
		"""Return ``(tender_code, tm2, addendum_name, addendum_code, binding_name)``."""
		tcode, tm2 = self._published_tender()
		self.addCleanup(self._cleanup_p505, tm2)
		p = self._base_payload()
		if requires_ack:
			p["requires_supplier_acknowledgement"] = 1
		if affects_deadline:
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
			context=self._impact_ctx(),
		)
		self.assertTrue(ia.get("ok"), ia)

		ad = frappe.get_doc("TM2 Addendum", ad_name)
		ad.status = "Approved"
		ad.approved_by = "Administrator"
		ad.approved_at = now_datetime()
		ad.save(ignore_permissions=True)

		sup = self._ensure_supplier("P505")
		frappe.get_doc(
			{"doctype": "TM2 Supplier Participation", "tm2_tender": tm2, "supplier": sup}
		).insert(ignore_permissions=True)

		bind = frappe.db.get_value(
			"TM2 Tender STD Binding",
			{"tm2_tender": tm2, "is_active": 1},
			"name",
		)
		self.assertTrue(bind)
		return tcode, tm2, ad_name, ac, str(bind)

	def _approved_addendum_ex13_all_five_outputs(
		self,
	) -> tuple[str, str, str, str, str, dict[str, str]]:
		"""First addendum with impact analysis caching ``boq_quantity`` + ``submission_deadline`` (all five outputs).

		Returns ``(tcode, tm2, ad_name, ac, bind_name, pre_codes)`` where ``pre_codes`` maps
		``bundle_output_code``, …, ``publication_snapshot_code``, ``published_snapshot_hash`` from the binding.
		"""
		tcode, tm2 = self._published_tender()
		self.addCleanup(self._cleanup_p505, tm2)
		p = self._base_payload()
		p["requires_supplier_acknowledgement"] = 0
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

		bind = frappe.db.get_value(
			"TM2 Tender STD Binding",
			{"tm2_tender": tm2, "is_active": 1},
			[
				"name",
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
		self.assertTrue(bind and bind.get("name"))
		pre = {
			"bundle_output_code": cstr(bind.get("bundle_output_code") or ""),
			"dsm_output_code": cstr(bind.get("dsm_output_code") or ""),
			"dom_output_code": cstr(bind.get("dom_output_code") or ""),
			"dem_output_code": cstr(bind.get("dem_output_code") or ""),
			"dcm_output_code": cstr(bind.get("dcm_output_code") or ""),
			"publication_snapshot_code": cstr(bind.get("publication_snapshot_code") or ""),
			"published_snapshot_hash": cstr(bind.get("published_snapshot_hash") or ""),
		}
		for k in ("bundle_output_code", "dsm_output_code", "dom_output_code", "dem_output_code", "dcm_output_code"):
			self.assertTrue(pre[k].strip(), f"missing pre-issue {k}: {pre!r}")
		self.assertTrue(pre["publication_snapshot_code"].strip())
		return tcode, tm2, ad_name, ac, str(bind["name"]), pre

	def test_EX_13_addendum_01_regenerates_all_std_outputs_and_revised_publication_snapshot(self) -> None:
		"""Doc 9 §25 / doc 8 TM2-SMOKE-SVC-008 — Bundle..DCM + publication snapshot superseded on issue."""
		_tcode, _tm2, _ad_name, ac, bind_name, pre = self._approved_addendum_ex13_all_five_outputs()

		out = issue_addendum("Administrator", ac, context=self._issue_ctx())
		self.assertTrue(out.get("ok"), out)
		post_snap = cstr(out.get("publication_snapshot_code") or "").strip()
		post_hash = cstr(out.get("snapshot_hash") or "").strip()
		self.assertTrue(post_snap)
		self.assertTrue(post_hash)
		if pre["published_snapshot_hash"].strip():
			self.assertNotEqual(post_hash, pre["published_snapshot_hash"])

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
		self.assertNotEqual(cstr(b.get("bundle_output_code")), pre["bundle_output_code"])
		self.assertNotEqual(cstr(b.get("dsm_output_code")), pre["dsm_output_code"])
		self.assertNotEqual(cstr(b.get("dom_output_code")), pre["dom_output_code"])
		self.assertNotEqual(cstr(b.get("dem_output_code")), pre["dem_output_code"])
		self.assertNotEqual(cstr(b.get("dcm_output_code")), pre["dcm_output_code"])
		self.assertEqual(
			cstr(b.get("publication_snapshot_code") or "").strip(),
			post_snap,
		)
		self.assertEqual(
			cstr(b.get("published_snapshot_hash") or "").strip(),
			post_hash,
		)

	def test_p5_05_success_binding_notifications_audit(self) -> None:
		tcode, tm2, ad_name, ac, bind_name = self._approved_structural_addendum(requires_ack=True)
		prev_hash = frappe.db.get_value("TM2 Tender STD Binding", bind_name, "published_snapshot_hash")

		out = issueAddendum("Administrator", ac, context=self._issue_ctx())
		self.assertTrue(out.get("ok"), out)
		self.assertEqual(out.get("addendum_status"), "Issued")

		ad = frappe.get_doc("TM2 Addendum", ad_name)
		self.assertEqual(ad.status, "Issued")

		new_hash = frappe.db.get_value("TM2 Tender STD Binding", bind_name, "published_snapshot_hash")
		self.assertTrue(new_hash)
		self.assertNotEqual((prev_hash or "").strip(), (new_hash or "").strip())

		acks = frappe.get_all(
			"TM2 Addendum Acknowledgement",
			filters={"tm2_addendum": ad_name},
			pluck="name",
		)
		self.assertEqual(len(acks), 1)

		ntf = frappe.get_all(
			"TM2 Notification Record",
			filters={"tm2_tender": tm2, "notification_type": "Addendum"},
			pluck="name",
		)
		self.assertEqual(len(ntf), 1)

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

	def test_p5_05_not_approved_denied(self) -> None:
		_tcode, _tm2, ad_name, ac, _bind = self._approved_structural_addendum()
		frappe.db.set_value("TM2 Addendum", ad_name, "status", "Draft", update_modified=False)
		out = issue_addendum("Administrator", ac, context=self._issue_ctx())
		self.assertFalse(out.get("ok"))
		self.assertEqual(out.get("denial_code"), DenialCode.AUTH_STATE_DENIED.value)

	def test_p5_05_structural_missing_air_denied(self) -> None:
		tcode, tm2 = self._published_tender()
		self.addCleanup(self._cleanup_p505, tm2)
		out = create_addendum(
			"Administrator",
			tcode,
			payload=self._base_payload(),
			context=self._add_ctx(),
		)
		self.assertTrue(out.get("ok"), out)
		ac = str(out.get("addendum_code") or "")
		ad_name = str(out.get("addendum") or "")
		frappe.db.set_value(
			"TM2 Addendum",
			ad_name,
			{"status": "Approved", "approved_by": "Administrator", "approved_at": now_datetime()},
			update_modified=True,
		)
		issue_out = issue_addendum("Administrator", ac, context=self._issue_ctx())
		self.assertFalse(issue_out.get("ok"))
		self.assertEqual(issue_out.get("denial_code"), DenialCode.AUTH_CONTEXT_DENIED.value)

	def test_p5_05_role_denied(self) -> None:
		_tcode, _tm2, _ad_name, ac, _bind = self._approved_structural_addendum()
		out = issue_addendum("Administrator", ac, context={"granted_permissions": []})
		self.assertFalse(out.get("ok"))
		self.assertEqual(out.get("denial_code"), DenialCode.AUTH_ROLE_DENIED.value)

	def test_p5_05_timeline_patch_when_affects_deadline(self) -> None:
		tcode, tm2, ad_name, ac, _bind = self._approved_structural_addendum(
			requires_ack=False,
			affects_deadline=True,
		)
		self._ensure_open_clarification_window(tm2)
		tl_name = frappe.db.get_value("TM2 Tender Timeline", {"tm2_tender": tm2}, "name")
		self.assertTrue(tl_name)
		tl = frappe.get_doc("TM2 Tender Timeline", tl_name)
		self.assertTrue(tl.submission_deadline_at and tl.opening_scheduled_at)
		want_sub = add_days(tl.submission_deadline_at, 3)
		want_open = add_days(tl.opening_scheduled_at, 3)
		out = issue_addendum(
			"Administrator",
			ac,
			context={
				**self._issue_ctx(),
				"revised_submission_deadline_at": want_sub,
				"revised_opening_scheduled_at": want_open,
			},
		)
		self.assertTrue(out.get("ok"), out)
		tl.reload()
		self.assertEqual(get_datetime(tl.submission_deadline_at), get_datetime(want_sub))
		self.assertEqual(get_datetime(tl.opening_scheduled_at), get_datetime(want_open))

	def test_p5_05_alias_matches_snake(self) -> None:
		tcode, tm2, _ad_name, ac, _bind = self._approved_structural_addendum(requires_ack=False)
		p2 = self._base_payload()
		p2["title"] = "Addendum No. 2 — second issue alias"
		o2 = create_addendum("Administrator", tcode, payload=p2, context=self._add_ctx())
		self.assertTrue(o2.get("ok"), o2)
		ac2 = str(o2.get("addendum_code") or "")
		self.assertTrue(request_addendum_impact_analysis("Administrator", ac2, context=self._impact_ctx()).get("ok"))
		ad2 = frappe.get_doc("TM2 Addendum", str(o2.get("addendum") or ""))
		ad2.status = "Approved"
		ad2.approved_by = "Administrator"
		ad2.approved_at = now_datetime()
		ad2.save(ignore_permissions=True)

		a = issueAddendum("Administrator", ac, context=self._issue_ctx())
		b = issue_addendum("Administrator", ac2, context=self._issue_ctx())
		self.assertTrue(a.get("ok"), a)
		self.assertTrue(b.get("ok"), b)
