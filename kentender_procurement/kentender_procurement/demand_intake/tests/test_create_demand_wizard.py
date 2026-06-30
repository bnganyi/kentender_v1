# Copyright (c) 2026, KenTender and contributors
# License: MIT. See LICENSE
"""Create Demand Wizard — backend wiring tests (save_demand_draft API).

Run:
  bench --site kentender.midas.com run-tests --app kentender_procurement \\
    --module kentender_procurement.demand_intake.tests.test_create_demand_wizard
"""

import json

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import add_days, today

from kentender_core.seeds._common import ensure_currency_kes, ensure_department, ensure_procuring_entity


def _call_save_draft(**kwargs):
    """Import and call save_demand_draft after the module exists."""
    from kentender_procurement.demand_intake.api.create_demand import save_demand_draft

    return save_demand_draft(**kwargs)


class TestCreateDemandWizard(IntegrationTestCase):
    def setUp(self):
        frappe.set_user("Administrator")
        if not frappe.db.exists("DocType", "Demand"):
            self._skipped_no_demand = True
            return
        self._skipped_no_demand = False
        ensure_currency_kes()
        h = frappe.generate_hash(length=6)
        self.entity = ensure_procuring_entity(f"MOH_CDW_{h}", f"Entity CDW {h}")
        self.dept = ensure_department(f"Dept CDW {h}", self.entity)
        self._demand_names: list[str] = []

    def tearDown(self):
        if getattr(self, "_skipped_no_demand", False):
            return
        frappe.set_user("Administrator")
        for name in getattr(self, "_demand_names", []):
            if frappe.db.exists("Demand", name):
                frappe.delete_doc("Demand", name, force=True, ignore_permissions=True)
        dept = getattr(self, "dept", None)
        if dept and frappe.db.exists("Procuring Department", dept):
            frappe.delete_doc("Procuring Department", dept, force=True, ignore_permissions=True)
        ent = getattr(self, "entity", None)
        if ent and frappe.db.exists("Procuring Entity", ent):
            frappe.delete_doc("Procuring Entity", ent, force=True, ignore_permissions=True)

    def _rby(self, offset=30):
        return add_days(today(), offset)

    # ------------------------------------------------------------------
    # cd-w0-T1  Title-only draft creation
    # ------------------------------------------------------------------
    def test_create_demand_draft_title_only(self):
        if getattr(self, "_skipped_no_demand", False):
            self.skipTest("Demand DocType not installed")

        result = _call_save_draft(title="CDW Test Demand T1")
        self._demand_names.append(result["demand_name"])

        self.assertTrue(result["ok"])
        self.assertIsNotNone(result["demand_name"])

        doc = frappe.get_doc("Demand", result["demand_name"])
        self.assertEqual(doc.title, "CDW Test Demand T1")
        self.assertEqual(doc.status, "Draft")

    # ------------------------------------------------------------------
    # cd-w0-T2  All Step-1 scalar fields saved correctly
    # ------------------------------------------------------------------
    def test_create_demand_draft_all_fields(self):
        if getattr(self, "_skipped_no_demand", False):
            self.skipTest("Demand DocType not installed")

        result = _call_save_draft(
            title="CDW All Fields",
            requesting_department=self.dept,
            requisition_type="Works",
            procuring_entity=self.entity,
            required_by_date=self._rby(),
            priority_level="High",
            beneficiary_summary="CDW justification text",
        )
        self._demand_names.append(result["demand_name"])

        self.assertTrue(result["ok"])
        doc = frappe.get_doc("Demand", result["demand_name"])
        self.assertEqual(doc.title, "CDW All Fields")
        self.assertEqual(doc.requesting_department, self.dept)
        self.assertEqual(doc.requisition_type, "Works")
        self.assertEqual(doc.procuring_entity, self.entity)
        self.assertEqual(doc.priority_level, "High")
        self.assertEqual(doc.beneficiary_summary, "CDW justification text")
        self.assertEqual(doc.status, "Draft")

    # ------------------------------------------------------------------
    # cd-w0-T3  demand_id is returned after first save with procuring_entity
    # ------------------------------------------------------------------
    def test_demand_id_returned_after_entity_set(self):
        if getattr(self, "_skipped_no_demand", False):
            self.skipTest("Demand DocType not installed")

        result = _call_save_draft(
            title="CDW ID Return",
            procuring_entity=self.entity,
            required_by_date=self._rby(),
        )
        self._demand_names.append(result["demand_name"])

        self.assertTrue(result["ok"])
        # demand_id is auto-assigned once procuring_entity + request_date are set
        self.assertIsNotNone(result.get("demand_id"))
        self.assertTrue(result["demand_id"].startswith("DIA-"))

    # ------------------------------------------------------------------
    # cd-w0-T4  Second call updates items on existing draft
    # ------------------------------------------------------------------
    def test_save_draft_updates_items(self):
        if getattr(self, "_skipped_no_demand", False):
            self.skipTest("Demand DocType not installed")

        # Step 1: create the demand
        r1 = _call_save_draft(
            title="CDW Items Update",
            procuring_entity=self.entity,
            requesting_department=self.dept,
            required_by_date=self._rby(),
        )
        demand_name = r1["demand_name"]
        self._demand_names.append(demand_name)

        # Step 2: update with items
        items = json.dumps([
            {"desc": "Floor Tiles", "qty": 100, "unit_price": 2500},
            {"desc": "Paint 20L", "qty": 5, "unit_price": 1800},
        ])
        r2 = _call_save_draft(demand_name=demand_name, items=items)
        self.assertTrue(r2["ok"])

        doc = frappe.get_doc("Demand", demand_name)
        self.assertEqual(len(doc.items), 2)
        self.assertEqual(doc.items[0].item_description, "Floor Tiles")
        self.assertEqual(doc.items[0].quantity, 100)
        self.assertEqual(doc.items[0].estimated_unit_cost, 2500)
        self.assertEqual(doc.items[1].item_description, "Paint 20L")

    # ------------------------------------------------------------------
    # cd-w0-T5  Item UOM defaults to "Units" when not provided
    # ------------------------------------------------------------------
    def test_save_draft_defaults_item_uom(self):
        if getattr(self, "_skipped_no_demand", False):
            self.skipTest("Demand DocType not installed")

        r1 = _call_save_draft(
            title="CDW UOM Default",
            procuring_entity=self.entity,
            required_by_date=self._rby(),
        )
        demand_name = r1["demand_name"]
        self._demand_names.append(demand_name)

        items = json.dumps([{"desc": "Item A", "qty": 2, "unit_price": 100}])
        _call_save_draft(demand_name=demand_name, items=items)

        doc = frappe.get_doc("Demand", demand_name)
        self.assertEqual(len(doc.items), 1)
        self.assertEqual(doc.items[0].uom, "Units")

    # ------------------------------------------------------------------
    # cd-w0-T6  Item category defaults to demand requisition_type
    # ------------------------------------------------------------------
    def test_save_draft_defaults_item_category(self):
        if getattr(self, "_skipped_no_demand", False):
            self.skipTest("Demand DocType not installed")

        r1 = _call_save_draft(
            title="CDW Cat Default",
            requisition_type="Services",
            procuring_entity=self.entity,
            required_by_date=self._rby(),
        )
        demand_name = r1["demand_name"]
        self._demand_names.append(demand_name)

        items = json.dumps([{"desc": "Consulting", "qty": 1, "unit_price": 50000}])
        _call_save_draft(demand_name=demand_name, items=items)

        doc = frappe.get_doc("Demand", demand_name)
        self.assertEqual(doc.items[0].category, "Services")

    # ------------------------------------------------------------------
    # cd-w0-T7  Empty title raises ValidationError
    # ------------------------------------------------------------------
    def test_save_draft_requires_title(self):
        if getattr(self, "_skipped_no_demand", False):
            self.skipTest("Demand DocType not installed")

        with self.assertRaises(frappe.ValidationError):
            _call_save_draft(title="")

    # ------------------------------------------------------------------
    # cd-w0-T8  Cannot update a non-Draft demand
    # ------------------------------------------------------------------
    def test_save_draft_rejects_non_draft(self):
        if getattr(self, "_skipped_no_demand", False):
            self.skipTest("Demand DocType not installed")

        # Build a fully complete demand and submit it
        doc = frappe.get_doc(
            {
                "doctype": "Demand",
                "title": "CDW NonDraft",
                "procuring_entity": self.entity,
                "requesting_department": self.dept,
                "request_date": today(),
                "required_by_date": self._rby(),
                "items": [
                    {
                        "item_description": "Test item",
                        "category": "Works",
                        "uom": "Units",
                        "quantity": 1,
                        "estimated_unit_cost": 100,
                    }
                ],
            }
        )
        doc.flags.ignore_mandatory = True
        doc.insert(ignore_permissions=True)
        self._demand_names.append(doc.name)

        # Force status to Pending to simulate a submitted demand
        frappe.db.set_value("Demand", doc.name, "status", "Pending HoD Approval")
        frappe.db.commit()

        with self.assertRaises(frappe.ValidationError):
            _call_save_draft(demand_name=doc.name, title="Updated Title")
