# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P12-01 / doc 7 §2 — TM2-WORKS-S08 (Retender / Superseding Tender).

**§2:** lineage from a prior tender — replacement **TM2 Tender** carries ``supersedes_tender_code``;
``supersede_tender`` records **Tender Superseded** on the original. Aligns with **P4-08**
``test_p4_08_supersede_success`` (supersede path; ``retender_of_tender_code`` create path remains
optional / doc-7 §6 golden).

Run::

	bench --site kentender.midas.com run-tests --app kentender_procurement \\
		--module kentender_procurement.tender_management.tests.scenarios.test_tm2_works_s08
"""

from __future__ import annotations

import json
import unittest

import frappe

from kentender_procurement.tender_management.scenarios.tm2_works_scenarios import (
	scenario_by_code,
	scenario_tracker_slug,
)
from kentender_procurement.tender_management.security.authorization.action_authorization_registry import (
	spec_for_action,
)
from kentender_procurement.tender_management.services.create_tender_from_package import create_tender_from_package
from kentender_procurement.tender_management.services.std_template_loader import upsert_std_template
from kentender_procurement.tender_management.services.tm2_cancel_supersede_retender import supersede_tender
from kentender_procurement.tender_management.tests.test_p4_01_create_tender_from_package import (
	_P401Tm2Cleanup,
)

_CODE = "TM2-WORKS-S08"


class TestTM2WorksS08Catalog(unittest.TestCase):
	def test_scenario_registered_in_catalog(self) -> None:
		spec = scenario_by_code(_CODE)
		self.assertEqual(spec.code, _CODE)
		self.assertEqual(spec.name, "Retender / Superseding Tender")
		self.assertTrue(spec.purpose)
		self.assertTrue(spec.expected_result)

	def test_tracker_slug_matches_row_s_table(self) -> None:
		spec = scenario_by_code(_CODE)
		self.assertEqual(scenario_tracker_slug(spec), f"S-{int(_CODE.split('S')[-1]):02d}")


class TestTM2WorksS08SupersedeLineage(_P401Tm2Cleanup):
	"""Doc 7 §2 — TM2-WORKS-S08 supersede lineage (tracker **S-08**)."""

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

	def test_S_08_supersede_links_replacement_tender_to_original_with_audit(self) -> None:
		"""``create_tender_from_package`` + ``supersede_tender`` — replacement row + **Tender Superseded**."""
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
			"S-08: published tender superseded by replacement draft (lineage).",
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
			payload = json.loads(payload)
		self.assertEqual(payload.get("replacement_tender_code"), new_tc)
		self.assertEqual(payload.get("superseded_tender_code"), old_tc)
