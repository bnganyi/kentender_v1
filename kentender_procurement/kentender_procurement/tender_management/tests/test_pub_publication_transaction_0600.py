# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PUB-0600 — ``PublicationTransactionService.publishTender`` (**TM2 Tender**).

Run::

	bench --site kentender.midas.com run-tests --app kentender_procurement \\
		--module kentender_procurement.tender_management.tests.test_pub_publication_transaction_0600
"""

from __future__ import annotations

from unittest.mock import patch

import frappe

from kentender_procurement.tender_management.seeds.std_template_governance_seed import (
	seed_std_template_governance_for_existing_works_poc,
)
from kentender_procurement.tender_management.security.authorization.action_authorization_registry import (
	spec_for_action,
)
from kentender_procurement.tender_management.services.approve_tender_publication import (
	approve_tender_publication,
)
from kentender_procurement.tender_management.services.bind_tender_std_instance import bind_tender_std_instance
from kentender_procurement.tender_management.services.create_tender_from_package import create_tender_from_package
from kentender_procurement.tender_management.services.run_publication_readiness import run_publication_readiness
from kentender_procurement.tender_management.services.std_template_loader import (
	TEMPLATE_CODE,
	upsert_std_template,
)
from kentender_procurement.tender_management.services.submit_tender_for_publication_review import (
	submit_tender_for_publication_review,
)
from kentender_procurement.tender_management.std_instance.binding import TenderStdBindingService
from kentender_procurement.tender_management.std_instance.boq import StdInstanceBoqService
from kentender_procurement.tender_management.std_instance.generated_output import (
	StdInstanceGeneratedOutputService,
)
from kentender_procurement.tender_management.std_instance.parameter import StdInstanceParameterService
from kentender_procurement.tender_management.std_instance.readiness import StdInstanceReadinessService
from kentender_procurement.tender_management.std_instance.works_requirement import (
	StdInstanceWorksRequirementService,
)
from kentender_procurement.tender_management.tender_publication.publication.transaction import (
	PublicationTransactionService,
)
from kentender_procurement.tender_management.tender_publication.readiness import (
	publication_readiness as pub_read_mod,
)
from kentender_procurement.tender_management.tests.test_p4_01_create_tender_from_package import (
	_P401Tm2Cleanup,
)


class TestPubPublicationTransaction0600(_P401Tm2Cleanup):
	@classmethod
	def setUpClass(cls) -> None:
		super().setUpClass()
		frappe.set_user("Administrator")
		upsert_std_template()
		seed_std_template_governance_for_existing_works_poc(force_mode="active")

	def setUp(self) -> None:
		super().setUp()
		frappe.set_user("Administrator")
		pub_read_mod.clear_publication_readiness_cache()

	def tearDown(self) -> None:
		frappe.set_user("Administrator")
		pub_read_mod.clear_publication_readiness_cache()
		super().tearDown()

	def _publish_all_outputs(self, instance_name: str) -> None:
		for fn in (
			StdInstanceGeneratedOutputService.generate_bundle,
			StdInstanceGeneratedOutputService.generate_dsm,
			StdInstanceGeneratedOutputService.generate_dom,
			StdInstanceGeneratedOutputService.generate_dem,
			StdInstanceGeneratedOutputService.generate_dcm,
		):
			out = fn(instance_name)
			StdInstanceGeneratedOutputService.publish_output(out.name)

	def _ensure_minimum_boq(self, instance_name: str) -> None:
		existing = frappe.get_all(
			"Tender STD Instance BOQ",
			filters={"tender_std_instance": instance_name},
			pluck="name",
			limit=1,
		)
		if existing:
			boq = frappe.get_doc("Tender STD Instance BOQ", existing[0])
		else:
			boq = StdInstanceBoqService.create_boq_for_instance(
				instance_name,
				ignore_boq_publication_lock=True,
			)
		if not (boq.boq_bills or []):
			boq = StdInstanceBoqService.add_bill(
				boq.name,
				"1",
				"General",
				"Works",
				ignore_boq_publication_lock=True,
			)
		bill_code = (boq.boq_bills or [])[0].bill_instance_code
		try:
			StdInstanceBoqService.add_item(
				boq.name,
				bill_code,
				"1.1",
				"Site mobilization",
				"Item",
				1,
				ignore_boq_publication_lock=True,
			)
		except frappe.ValidationError:
			pass

	def _mk_publishable_tm2(self, ref: str) -> tuple[str, str, str]:
		"""Return ``(tender_code, tm2_name, tender_std_instance)`` ready for ``publish_tender``."""
		plan = self._mk_plan()
		frappe.db.set_value("Procurement Plan", plan.name, "status", "Approved")
		tpl = self._mk_template()
		pkg = self._mk_package(plan.name, tpl.name)
		self._add_seed_budget_line_and_demand(pkg.name)
		frappe.db.set_value("Procurement Package", pkg.name, "status", "Ready for Tender")
		spec_c = spec_for_action("TND2_CREATE_FROM_PACKAGE")
		spec_b = spec_for_action("TND2_BIND_STD")
		spec_r = spec_for_action("TND2_RUN_READINESS")
		spec_sub = spec_for_action("TND2_SUBMIT_PUBLICATION_REVIEW")
		spec_ap = spec_for_action("TND2_APPROVE_PUBLICATION")
		self.assertIsNotNone(spec_c)
		self.assertIsNotNone(spec_b)
		self.assertIsNotNone(spec_r)
		self.assertIsNotNone(spec_sub)
		self.assertIsNotNone(spec_ap)
		assert spec_c and spec_b and spec_r and spec_sub and spec_ap
		pc = frappe.db.get_value("Procurement Package", pkg.name, "package_code") or pkg.name
		out = create_tender_from_package(
			"Administrator",
			pc,
			context={"granted_permissions": [spec_c.required_permission]},
		)
		self.assertTrue(out.get("ok"), out)
		tm2_name = str(out.get("tm2_tender") or "")
		self.addCleanup(self._cleanup_tm2, tm2_name)
		tcode = str(out.get("tender_code") or "")
		self.assertTrue(tcode)
		pkg_code = (frappe.db.get_value("Procurement Package", pkg.name, "package_code") or "").strip()
		if pkg_code:
			frappe.db.set_value("TM2 Tender", tm2_name, "source_package_code", pkg_code)

		ver, prof = TenderStdBindingService._codes_from_std_template(TEMPLATE_CODE)
		bout = bind_tender_std_instance(
			"Administrator",
			tcode,
			ver,
			prof,
			context={"granted_permissions": [spec_b.required_permission]},
		)
		self.assertTrue(bout.get("ok"), bout)
		si_name = str(bout.get("tender_std_instance") or "")
		self.assertTrue(si_name)

		StdInstanceParameterService.set_parameter_value(
			si_name,
			"submission_deadline",
			"2026-12-31",
			ignore_publication_lock=True,
		)
		StdInstanceWorksRequirementService.set_works_requirement(
			si_name,
			"WR-COMP-001",
			structured_text=f"PUB-0600 {ref} requirement.",
			requirement_status="Complete",
			attachment_required=False,
			attachment_status="Not Required",
			ignore_publication_lock=True,
		)
		self._ensure_minimum_boq(si_name)
		self._publish_all_outputs(si_name)
		self.assertEqual(StdInstanceReadinessService.evaluate(si_name, persist=False)["status"], "Ready")

		fake = {
			"ok": True,
			"status": "Ready",
			"blockers": [],
			"warnings": [],
			"instance": si_name,
			"bundle_current": True,
			"dsm_current": True,
			"dom_current": True,
			"dem_current": True,
			"dcm_current": True,
		}
		with patch(
			"kentender_procurement.tender_management.services.run_publication_readiness.validate_tender_std_readiness",
			return_value=fake,
		):
			rout = run_publication_readiness(
				"Administrator",
				tcode,
				context={"granted_permissions": [spec_r.required_permission]},
			)
		self.assertTrue(rout.get("ok"), rout)

		sout = submit_tender_for_publication_review(
			"Administrator",
			tcode,
			context={"granted_permissions": [spec_sub.required_permission]},
		)
		self.assertTrue(sout.get("ok"), sout)

		aout = approve_tender_publication(
			"Administrator",
			tcode,
			comments="PUB-0600 fixture",
			context={
				"granted_permissions": [spec_ap.required_permission],
				"sod_delegated_override_reason": "PUB-0600 test — single Administrator actor.",
			},
		)
		self.assertTrue(aout.get("ok"), aout)
		return tcode, tm2_name, si_name

	def test_pub_0600_publish_atomic_happy_path(self) -> None:
		tcode, tm2_name, si_name = self._mk_publishable_tm2("PUB0600-ATOM")
		before_audit = frappe.db.count(
			"TM2 Tender Audit Event",
			{"tm2_tender": tm2_name, "event_type": "Tender Published"},
		)
		spec_p = spec_for_action("TND2_PUBLISH")
		self.assertIsNotNone(spec_p)
		assert spec_p is not None
		res = PublicationTransactionService.publishTender(
			tcode,
			actor="Administrator",
			context={"granted_permissions": [spec_p.required_permission]},
		)
		self.assertTrue(res.get("ok"))
		self.assertEqual(res.get("tender_status"), "Published")
		self.assertEqual((frappe.db.get_value("TM2 Tender", tm2_name, "status") or "").strip(), "Published")
		self.assertEqual(
			(frappe.db.get_value("Tender STD Instance", si_name, "instance_status") or "").strip(),
			"Published Locked",
		)
		after_audit = frappe.db.count(
			"TM2 Tender Audit Event",
			{"tm2_tender": tm2_name, "event_type": "Tender Published"},
		)
		self.assertGreater(after_audit, before_audit)

	def test_pub_0600_second_publish_denied(self) -> None:
		tcode, tm2_name, si_name = self._mk_publishable_tm2("PUB0600-2ND")
		spec_p = spec_for_action("TND2_PUBLISH")
		assert spec_p is not None
		ctx = {"granted_permissions": [spec_p.required_permission]}
		PublicationTransactionService.publishTender(tcode, actor="Administrator", context=ctx)
		frappe.db.commit()
		st_after_first = (frappe.db.get_value("Tender STD Instance", si_name, "instance_status") or "").strip()
		self.assertEqual(
			st_after_first,
			"Published Locked",
			msg="first publish must lock instance before second attempt is tested",
		)
		pub_rows = frappe.get_all(
			"TM2 Publication Record",
			filters={"tm2_tender": tm2_name, "status": "Published"},
		)
		self.assertEqual(len(pub_rows), 1, msg="first publish must create exactly one publication record")
		with self.assertRaises(frappe.ValidationError):
			PublicationTransactionService.publishTender(tcode, actor="Administrator", context=ctx)
		self.assertEqual(frappe.db.get_value("Tender STD Instance", si_name, "instance_status"), "Published Locked")
		self.assertEqual(
			len(
				frappe.get_all(
					"TM2 Publication Record",
					filters={"tm2_tender": tm2_name, "status": "Published"},
				)
			),
			1,
		)
