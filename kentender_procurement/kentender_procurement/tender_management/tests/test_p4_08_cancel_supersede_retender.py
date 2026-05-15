# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P4-08 — doc 4 cancel / mark retender required / supersede (TM2).

Run::

	bench --site kentender.midas.com run-tests --app kentender_procurement \\
		--module kentender_procurement.tender_management.tests.test_p4_08_cancel_supersede_retender
"""

from __future__ import annotations

import frappe

from kentender_procurement.tender_management.security.authorization.action_authorization_registry import (
	spec_for_action,
)
from kentender_procurement.tender_management.security.authorization.denial_codes import DenialCode
from kentender_procurement.tender_management.services.create_tender_from_package import create_tender_from_package
from kentender_procurement.tender_management.services.std_template_loader import upsert_std_template
from kentender_procurement.tender_management.services.tm2_cancel_supersede_retender import (
	cancelTender,
	cancel_tender,
	mark_retender_required,
	supersede_tender,
)
from kentender_procurement.tender_management.tests.test_p4_01_create_tender_from_package import (
	_P401Tm2Cleanup,
)


class TestP408CancelSupersedeRetender(_P401Tm2Cleanup):
	def _mk_released_package_and_tender(self) -> tuple[str, str]:
		upsert_std_template()
		plan = self._mk_plan()
		frappe.db.set_value("Procurement Plan", plan.name, "status", "Approved")
		tpl = self._mk_template()
		pkg = self._mk_package(plan.name, tpl.name)
		self._add_seed_budget_line_and_demand(pkg.name)
		frappe.db.set_value("Procurement Package", pkg.name, "status", "Ready for Tender")
		spec_c = spec_for_action("TND2_CREATE_FROM_PACKAGE")
		assert spec_c is not None
		pc = frappe.db.get_value("Procurement Package", pkg.name, "package_code") or pkg.name
		out = create_tender_from_package(
			"Administrator",
			pc,
			context={"granted_permissions": [spec_c.required_permission]},
		)
		self.assertTrue(out.get("ok"), out)
		self.addCleanup(self._cleanup_tm2, out.get("tm2_tender"))
		return pc, str(out.get("tender_code") or "")

	def test_p4_08_cancel_success_draft(self) -> None:
		_, tcode = self._mk_released_package_and_tender()
		spec = spec_for_action("TND2_CANCEL")
		assert spec is not None
		reason = "Procurement scope withdrawn pending cabinet re-prioritisation."
		out = cancel_tender(
			"Administrator",
			tcode,
			reason,
			context={"granted_permissions": [spec.required_permission]},
		)
		self.assertTrue(out.get("ok"), out)
		self.assertEqual(out.get("status"), "Cancelled")
		tm2 = out.get("tm2_tender")
		row = frappe.db.get_value(
			"TM2 Tender",
			tm2,
			["status", "is_active", "cancellation_reason", "cancelled_by"],
			as_dict=True,
		)
		self.assertEqual(row.get("status"), "Cancelled")
		self.assertEqual(int(row.get("is_active") or 0), 0)
		self.assertIn("withdrawn", (row.get("cancellation_reason") or "").lower())
		self.assertTrue(row.get("cancelled_by"))

		ev = frappe.get_all(
			"TM2 Tender Audit Event",
			filters={"tm2_tender": tm2, "event_type": "Tender Cancelled"},
			fields=["reason", "previous_state", "new_state"],
			limit=1,
		)
		self.assertEqual(len(ev), 1)
		self.assertEqual(ev[0].get("new_state"), "Cancelled")
		self.assertEqual(ev[0].get("previous_state"), "Draft")
		self.assertIn("withdrawn", (ev[0].get("reason") or "").lower())

	def test_p4_08_cancel_camel_case_alias(self) -> None:
		_, tcode = self._mk_released_package_and_tender()
		spec = spec_for_action("TND2_CANCEL")
		assert spec is not None
		out = cancelTender(
			"Administrator",
			tcode,
			"Duplicate fixture cancel via CamelCase alias.",
			context={"granted_permissions": [spec.required_permission]},
		)
		self.assertTrue(out.get("ok"), out)

	def test_p4_08_cancel_duplicate_state_denied(self) -> None:
		_, tcode = self._mk_released_package_and_tender()
		spec = spec_for_action("TND2_CANCEL")
		assert spec is not None
		ctx = {"granted_permissions": [spec.required_permission]}
		self.assertTrue(cancel_tender("Administrator", tcode, "First cancel.", context=ctx).get("ok"))
		out2 = cancel_tender("Administrator", tcode, "Second cancel must fail.", context=ctx)
		self.assertFalse(out2.get("ok"))
		self.assertEqual(out2.get("denial_code"), DenialCode.AUTH_STATE_DENIED.value)

	def test_p4_08_cancel_empty_reason_denied(self) -> None:
		_, tcode = self._mk_released_package_and_tender()
		spec = spec_for_action("TND2_CANCEL")
		assert spec is not None
		out = cancel_tender(
			"Administrator",
			tcode,
			"   ",
			context={"granted_permissions": [spec.required_permission]},
		)
		self.assertFalse(out.get("ok"))
		self.assertEqual(out.get("denial_code"), DenialCode.AUTH_REASON_REQUIRED.value)

	def test_p4_08_cancel_auth_denied(self) -> None:
		_, tcode = self._mk_released_package_and_tender()
		out = cancel_tender(
			"Administrator",
			tcode,
			"No permission path.",
			context={"granted_permissions": []},
		)
		self.assertFalse(out.get("ok"))
		self.assertEqual(out.get("denial_code"), DenialCode.AUTH_ROLE_DENIED.value)

	def test_p4_08_mark_retender_from_closed_no_valid(self) -> None:
		_, tcode = self._mk_released_package_and_tender()
		tm2 = frappe.db.get_value("TM2 Tender", {"tender_code": tcode}, "name")
		frappe.db.set_value("TM2 Tender", tm2, "status", "Closed - No Valid Submissions")
		spec = spec_for_action("TND2_MARK_RETENDER_REQUIRED")
		assert spec is not None
		out = mark_retender_required(
			"Administrator",
			tcode,
			"No compliant bids received; retender with revised eligibility.",
			context={"granted_permissions": [spec.required_permission]},
		)
		self.assertTrue(out.get("ok"), out)
		self.assertEqual(out.get("status"), "Retender Required")
		row = frappe.db.get_value(
			"TM2 Tender",
			tm2,
			["status", "is_active"],
			as_dict=True,
		)
		self.assertEqual(row.get("status"), "Retender Required")
		self.assertEqual(int(row.get("is_active") or 0), 0)
		ev = frappe.get_all(
			"TM2 Tender Audit Event",
			filters={"tm2_tender": tm2, "event_type": "Retender Required"},
			fields=["reason", "previous_state", "new_state"],
			limit=1,
		)
		self.assertEqual(len(ev), 1)
		self.assertEqual(ev[0].get("previous_state"), "Closed - No Valid Submissions")
		self.assertEqual(ev[0].get("new_state"), "Retender Required")

	def test_p4_08_mark_retender_from_cancelled(self) -> None:
		pc, tcode = self._mk_released_package_and_tender()
		spec_c = spec_for_action("TND2_CANCEL")
		spec_m = spec_for_action("TND2_MARK_RETENDER_REQUIRED")
		assert spec_c is not None and spec_m is not None
		self.assertTrue(
			cancel_tender(
				"Administrator",
				tcode,
				"Cancelled before retender mark (fixture).",
				context={"granted_permissions": [spec_c.required_permission]},
			).get("ok")
		)
		out = mark_retender_required(
			"Administrator",
			tcode,
			"Cancelled tender flagged for replacement procurement cycle.",
			context={"granted_permissions": [spec_m.required_permission]},
		)
		self.assertTrue(out.get("ok"), out)
		self.assertEqual(out.get("status"), "Retender Required")
		# Package slot released: second tender without lineage context keys.
		spec_create = spec_for_action("TND2_CREATE_FROM_PACKAGE")
		assert spec_create is not None
		out2 = create_tender_from_package(
			"Administrator",
			pc,
			context={"granted_permissions": [spec_create.required_permission]},
		)
		self.assertTrue(out2.get("ok"), out2)
		self.addCleanup(self._cleanup_tm2, out2.get("tm2_tender"))

	def test_p4_08_mark_retender_wrong_status_denied(self) -> None:
		_, tcode = self._mk_released_package_and_tender()
		spec = spec_for_action("TND2_MARK_RETENDER_REQUIRED")
		assert spec is not None
		out = mark_retender_required(
			"Administrator",
			tcode,
			"Draft cannot jump to retender required.",
			context={"granted_permissions": [spec.required_permission]},
		)
		self.assertFalse(out.get("ok"))
		self.assertEqual(out.get("denial_code"), DenialCode.AUTH_STATE_DENIED.value)

	def test_p4_08_mark_retender_auth_denied(self) -> None:
		_, tcode = self._mk_released_package_and_tender()
		tm2 = frappe.db.get_value("TM2 Tender", {"tender_code": tcode}, "name")
		frappe.db.set_value("TM2 Tender", tm2, "status", "Closed - No Valid Submissions")
		out = mark_retender_required(
			"Administrator",
			tcode,
			"No grant path.",
			context={"granted_permissions": []},
		)
		self.assertFalse(out.get("ok"))
		self.assertEqual(out.get("denial_code"), DenialCode.AUTH_ROLE_DENIED.value)

	def test_p4_08_supersede_success(self) -> None:
		pc, old_tc = self._mk_released_package_and_tender()
		tm2_old = frappe.db.get_value("TM2 Tender", {"tender_code": old_tc}, "name")
		frappe.db.set_value("TM2 Tender", tm2_old, "status", "Published")
		spec_c = spec_for_action("TND2_CREATE_FROM_PACKAGE")
		spec_s = spec_for_action("TND2_SUPERSEDE")
		assert spec_c is not None and spec_s is not None
		out_new = create_tender_from_package(
			"Administrator",
			pc,
			context={
				"granted_permissions": [spec_c.required_permission],
				"supersedes_tender_code": old_tc,
			},
		)
		self.assertTrue(out_new.get("ok"), out_new)
		self.addCleanup(self._cleanup_tm2, out_new.get("tm2_tender"))
		new_tc = str(out_new.get("tender_code") or "")
		sout = supersede_tender(
			"Administrator",
			old_tc,
			new_tc,
			"Published tender superseded by revised STD-bound replacement draft.",
			context={"granted_permissions": [spec_s.required_permission]},
		)
		self.assertTrue(sout.get("ok"), sout)
		self.assertEqual(sout.get("status"), "Superseded")
		old_row = frappe.db.get_value(
			"TM2 Tender",
			tm2_old,
			["status", "is_active"],
			as_dict=True,
		)
		self.assertEqual(old_row.get("status"), "Superseded")
		self.assertEqual(int(old_row.get("is_active") or 0), 0)
		self.assertEqual(
			frappe.db.get_value("TM2 Tender", out_new.get("tm2_tender"), "supersedes_tender_code"),
			old_tc,
		)
		ev = frappe.get_all(
			"TM2 Tender Audit Event",
			filters={"tm2_tender": tm2_old, "event_type": "Tender Superseded"},
			fields=["reason", "previous_state", "new_state", "event_payload"],
			limit=1,
		)
		self.assertEqual(len(ev), 1)
		self.assertEqual(ev[0].get("previous_state"), "Published")
		self.assertEqual(ev[0].get("new_state"), "Superseded")
		payload = ev[0].get("event_payload") or {}
		if isinstance(payload, str):
			import json

			payload = json.loads(payload)
		self.assertEqual(payload.get("replacement_tender_code"), new_tc)
		self.assertEqual(payload.get("superseded_tender_code"), old_tc)

	def test_p4_08_supersede_wrong_old_status_denied(self) -> None:
		pc, old_tc = self._mk_released_package_and_tender()
		spec_c = spec_for_action("TND2_CREATE_FROM_PACKAGE")
		spec_s = spec_for_action("TND2_SUPERSEDE")
		assert spec_c is not None and spec_s is not None
		out_new = create_tender_from_package(
			"Administrator",
			pc,
			context={
				"granted_permissions": [spec_c.required_permission],
				"supersedes_tender_code": old_tc,
			},
		)
		self.assertTrue(out_new.get("ok"), out_new)
		self.addCleanup(self._cleanup_tm2, out_new.get("tm2_tender"))
		new_tc = str(out_new.get("tender_code") or "")
		# old still Draft — supersede not allowed
		sout = supersede_tender(
			"Administrator",
			old_tc,
			new_tc,
			"Must be denied when prior tender is not in a supersede-allowed state.",
			context={"granted_permissions": [spec_s.required_permission]},
		)
		self.assertFalse(sout.get("ok"))
		self.assertEqual(sout.get("denial_code"), DenialCode.AUTH_STATE_DENIED.value)

	def test_p4_08_supersede_auth_denied(self) -> None:
		pc, old_tc = self._mk_released_package_and_tender()
		tm2_old = frappe.db.get_value("TM2 Tender", {"tender_code": old_tc}, "name")
		frappe.db.set_value("TM2 Tender", tm2_old, "status", "Published")
		spec_c = spec_for_action("TND2_CREATE_FROM_PACKAGE")
		assert spec_c is not None
		out_new = create_tender_from_package(
			"Administrator",
			pc,
			context={
				"granted_permissions": [spec_c.required_permission],
				"supersedes_tender_code": old_tc,
			},
		)
		self.assertTrue(out_new.get("ok"), out_new)
		self.addCleanup(self._cleanup_tm2, out_new.get("tm2_tender"))
		new_tc = str(out_new.get("tender_code") or "")
		sout = supersede_tender(
			"Administrator",
			old_tc,
			new_tc,
			"No supersede permission.",
			context={"granted_permissions": []},
		)
		self.assertFalse(sout.get("ok"))
		self.assertEqual(sout.get("denial_code"), DenialCode.AUTH_ROLE_DENIED.value)
