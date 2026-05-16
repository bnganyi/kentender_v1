# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""R4-013 — Journey aggregate exposes ``technical_refs`` for handoff cards (drawer data contract).

## Coverage

| ID | Scenario |
|---|---|
| R4-013-C01 | WORKS STRATREF handoff summary includes non-empty ``technical_refs`` |

Run::

    bench --site kentender.midas.com run-tests --app kentender_procurement \\
      --module kentender_procurement.procurement_lifecycle.tests.test_r4_013_technical_evidence_drawer
"""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.procurement_lifecycle.journey_aggregate import (
    get_procurement_journey,
)

_WORKS_JOURNEY = "JRN-MOH-2026-001"
_STRAT = "STRATREF-MOH-2026-001"


class TestR4013TechnicalEvidenceDrawerContract(IntegrationTestCase):
    """R4-013 — ``technical_refs`` present for Desk drawer (with WORKS seed)."""

    def test_stratref_handoff_includes_technical_refs(self):
        """R4-013-C01: Strategy Alignment Reference carries programme_code (seed §16)."""
        frappe.set_user("Administrator")
        journey = get_procurement_journey(_WORKS_JOURNEY)
        cards = journey.get("handoff_cards") or []
        strat = next((c for c in cards if c.get("handoff_code") == _STRAT), None)
        self.assertIsNotNone(strat, msg="Expected STRATREF handoff (WORKS seed).")
        refs = strat.get("technical_refs")
        self.assertIsInstance(refs, dict)
        self.assertIn("programme_code", refs)
        self.assertEqual(refs.get("programme_code"), "PROG-MOH-INFRA")
