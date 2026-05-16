# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""R4-012 / LV-R4-012-01 — Safe ``open_module_route`` sanitization (server + contract tests).

## Coverage

| ID | Scenario |
|---|---|
| R4-012-P01 | ``_parse_open_module_route_form_target`` rejects non-``Form`` / wrong arity |
| R4-012-P02 | ``open_module_route_permitted_for_session`` requires allowlist + exists + read |
| R4-012-P03 | ``sanitize_journey_steps_open_module_routes`` clears unsafe routes |
| R4-012-P04 | Non-allowlisted DocType (e.g. User) is never permitted |
| R4-012-INT | WORKS journey: ``tender_publication`` keeps TM2 Tender route for Administrator |

Run::

    bench --site kentender.midas.com run-tests --app kentender_procurement \\
      --module kentender_procurement.procurement_lifecycle.tests.test_r4_012_open_module_route
"""

from __future__ import annotations

from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.procurement_lifecycle.journey_aggregate import (
    _parse_open_module_route_form_target,
    get_procurement_journey,
    open_module_route_permitted_for_session,
    sanitize_journey_steps_open_module_routes,
)

_WORKS_JOURNEY_CODE = "JRN-MOH-2026-001"


class TestR4012OpenModuleRoute(IntegrationTestCase):
    """R4-012 — ``open_module_route`` allowlist and permission checks."""

    def test_parse_rejects_non_form_route(self):
        """R4-012-P01: only strict ``[\"Form\", doctype, name]`` is accepted."""
        self.assertIsNone(_parse_open_module_route_form_target('["List", "User", "x"]'))
        self.assertIsNone(_parse_open_module_route_form_target("not json"))
        self.assertIsNone(_parse_open_module_route_form_target('["Form", "TM2 Tender"]'))

    def test_parse_accepts_form_three_segments(self):
        self.assertEqual(
            _parse_open_module_route_form_target(
                '["Form", "TM2 Tender", "TND-MOH-2026-001"]',
            ),
            ("TM2 Tender", "TND-MOH-2026-001"),
        )

    @patch("frappe.has_permission", return_value=True)
    @patch("frappe.db.exists", return_value=True)
    def test_permitted_when_allowlisted_and_read(
        self,
        _mock_exists,
        _mock_perm,
    ):
        """R4-012-P02: allowlisted DocType + existing doc + read → True."""
        raw = '["Form", "TM2 Tender", "TND-MOH-2026-001"]'
        self.assertTrue(open_module_route_permitted_for_session(raw))

    @patch("frappe.has_permission", return_value=False)
    @patch("frappe.db.exists", return_value=True)
    def test_not_permitted_without_read(self, _mock_exists, _mock_perm):
        raw = '["Form", "TM2 Tender", "TND-MOH-2026-001"]'
        self.assertFalse(open_module_route_permitted_for_session(raw))

    @patch("frappe.has_permission", return_value=True)
    @patch("frappe.db.exists", return_value=False)
    def test_not_permitted_if_doc_missing(self, _mock_exists, _mock_perm):
        raw = '["Form", "TM2 Tender", "MISSING-DOC"]'
        self.assertFalse(open_module_route_permitted_for_session(raw))

    def test_user_doctype_never_allowlisted(self):
        """R4-012-P04: privilege-escalation target DocType is rejected before DB checks."""
        self.assertFalse(
            open_module_route_permitted_for_session(
                '["Form", "User", "Administrator"]',
            ),
        )

    def test_sanitize_clears_non_allowlisted_route_without_db(self):
        """R4-012-P03: cleared when not permitted."""
        steps = [
            {
                "step_key": "tender_publication",
                "open_module_route": '["Form", "User", "Administrator"]',
            },
        ]
        out = sanitize_journey_steps_open_module_routes(steps)
        self.assertIsNone(out[0].get("open_module_route"))

    @patch("frappe.has_permission", return_value=True)
    @patch("frappe.db.exists", return_value=True)
    def test_sanitize_keeps_allowlisted_when_permitted(self, _mock_exists, _mock_perm):
        raw = '["Form", "TM2 Tender", "TND-MOH-2026-001"]'
        steps = [{"step_key": "tender_publication", "open_module_route": raw}]
        out = sanitize_journey_steps_open_module_routes(steps)
        self.assertEqual(out[0].get("open_module_route"), raw)

    def test_works_journey_tender_step_has_open_route_for_administrator(self):
        """R4-012-INT: seeded WORKS journey retains tender publication deep link."""
        frappe.set_user("Administrator")
        journey = get_procurement_journey(_WORKS_JOURNEY_CODE)
        steps = journey.get("steps") or []
        pub = next(
            (s for s in steps if s.get("step_key") == "tender_publication"),
            None,
        )
        self.assertIsNotNone(pub, msg="Expected tender_publication step (WORKS seed).")
        raw = pub.get("open_module_route")
        self.assertIsNotNone(raw)
        s = str(raw)
        self.assertIn("TM2 Tender", s)
        self.assertIn("TND-MOH-2026-001", s)
