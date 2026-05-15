# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P11-03 — v1 contamination static audit (TM2 surfaces / doc 1 §28).

Run::

	bench --site kentender.midas.com run-tests --app kentender_procurement \\
		--module kentender_procurement.tender_management.tests.test_p11_03_tm2_v1_contamination_audit

``make tm2-v1-contamination-audit`` (from ``apps/kentender_v1``) runs the same module.

**S-13 / TM2-SMOKE-LEGACY:** doc 7 §2 scenario module ``tests/scenarios/test_tm2_works_s13`` (scan + **Procurement Tender**
``AUTH_LEGACY_PATH_DENIED``); allowlisted in :mod:`tm2_v1_contamination_scan` for literal legacy keys.
``test_p11_01_legacy_path_guard`` (including **EX-20** ``test_EX_20_*``) remains the canonical guard tests.
"""

from __future__ import annotations

from frappe.tests import IntegrationTestCase

from kentender_procurement.tender_management.audit.tm2_v1_contamination_scan import (
	format_violations,
	run_tm2_v1_contamination_scan,
)


class TestP1103Tm2V1ContaminationAudit(IntegrationTestCase):
	def test_p11_03_tm2_v1_contamination_scan_passes(self) -> None:
		violations = run_tm2_v1_contamination_scan()
		self.assertFalse(
			violations,
			msg="P11-03 contamination violations:\n" + format_violations(violations),
		)

	def test_p11_03_legacy_rule_injection_keys_frozen_catalog(self) -> None:
		"""Guard catalogue must expose exactly five WORKS-LEGACY identifiers (doc §18.8)."""
		from kentender_procurement.tender_management.security.legacy_v1_path_guard import (
			LEGACY_RULE_INJECTION_KEYS,
		)

		self.assertEqual(len(LEGACY_RULE_INJECTION_KEYS), 5)
