# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""R6-004 / LV-R6-004-01 — DEM missing / stale: business-readable blocker copy.

NEG-TND-MISSING-DEM-001 (works master seed spec §22.6) expects FAIL with
``DEM_MISSING_OR_STALE`` on the check while the Desk shows ``user_blocker_message``
(see also ``test_blocked_when_dem_code_missing`` in test_r3_016).
"""

from __future__ import annotations

import unittest

from kentender_procurement.procurement_lifecycle.business_readiness_summary import (
    _user_facing_dem_blocker,
)


class TestR6004DemBlockerTranslation(unittest.TestCase):
    """R6-004 — `_user_facing_dem_blocker` is business-language, not raw tokens."""

    def test_dem_missing_or_stale_message_has_no_machine_code(self):
        msg = _user_facing_dem_blocker("DEM_MISSING_OR_STALE")
        self.assertIsNotNone(msg)
        assert msg is not None
        self.assertNotIn("DEM_MISSING_OR_STALE", msg)
        self.assertIn("Evaluation", msg)

    def test_dem_pending_message(self):
        msg = _user_facing_dem_blocker("PENDING")
        self.assertIsNotNone(msg)
        assert msg is not None
        self.assertNotIn("DEM_MISSING_OR_STALE", msg)
        self.assertIn("Evaluation", msg)

    def test_unknown_returns_none(self):
        self.assertIsNone(_user_facing_dem_blocker("OTHER"))
