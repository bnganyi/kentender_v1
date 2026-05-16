# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""R5-002 / LV-R5-002-02 — ``get_procurement_journeys_for_strategy_node`` integration tests."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.procurement_lifecycle.api.journey_api import (
    get_procurement_journeys_for_strategy_node,
)

_WORKS_JOURNEY = "JRN-MOH-2026-001"
_OBJ_CODE = "OBJ-MOH-HOSP-RENOV"
_TGT_CODE = "TGT-MOH-HOSP-RENOV-2026"
_BUD_CODE = "BUD-MOH-INFRA-2026-001"


class TestR5002ProcurementJourneysForStrategyNode(IntegrationTestCase):
    """R5-002 — strategy node → journeys + budget lines."""

    def test_missing_params_raises(self):
        with self.assertRaises(frappe.ValidationError):
            get_procurement_journeys_for_strategy_node("", "")

    def test_unsupported_doctype_raises(self):
        with self.assertRaises(frappe.ValidationError):
            get_procurement_journeys_for_strategy_node("Strategic Plan", "SP-001")

    def test_works_objective_returns_journey_and_budget_line(self):
        obj_name = frappe.db.get_value(
            "Strategy Objective", {"objective_code": _OBJ_CODE}, "name"
        )
        if not obj_name:
            self.skipTest("WORKS Strategy Objective not present on site.")

        out = get_procurement_journeys_for_strategy_node("Strategy Objective", obj_name)
        self.assertTrue(out.get("ok"), msg=out)
        codes = [j.get("journey_code") for j in out.get("journeys", [])]
        self.assertIn(
            _WORKS_JOURNEY,
            codes,
            "WORKS journey should link via strategy_ref on Procurement Journey.",
        )

    def test_works_target_returns_journey_via_budget_line(self):
        tgt_name = frappe.db.get_value(
            "Strategy Target", {"target_code": _TGT_CODE}, "name"
        )
        if not tgt_name:
            self.skipTest("WORKS Strategy Target not present on site.")

        out = get_procurement_journeys_for_strategy_node("Strategy Target", tgt_name)
        self.assertTrue(out.get("ok"), msg=out)
        codes = [j.get("journey_code") for j in out.get("journeys", [])]
        self.assertIn(_WORKS_JOURNEY, codes)
        self.assertTrue(
            any(b.get("code") == _BUD_CODE for b in out.get("budget_lines", [])),
            msg=f"budget lines: {out.get('budget_lines')}",
        )

    def test_guest_denied(self):
        obj_name = frappe.db.get_value(
            "Strategy Objective", {"objective_code": _OBJ_CODE}, "name"
        )
        if not obj_name:
            self.skipTest("WORKS Strategy Objective not present on site.")

        frappe.set_user("Guest")
        try:
            with self.assertRaises(frappe.PermissionError):
                get_procurement_journeys_for_strategy_node("Strategy Objective", obj_name)
        finally:
            frappe.set_user("Administrator")
