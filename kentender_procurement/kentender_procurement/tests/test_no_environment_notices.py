# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""No screen, receipt, form or portal shell announces a test environment.

Simulated services may answer on a test site, but nothing they do puts a
"Test environment" banner, a "not a production ..." disclaimer or a
"test attestation" label in front of a user (owner decision, 10 Oct 2026). The
simulation is visible in the test controls and the stored provenance flags only.
These tests read the served sources, so they fail if such a notice returns.
"""

from __future__ import annotations

import re
from pathlib import Path

from frappe.tests import IntegrationTestCase

_APP = Path(__file__).resolve().parents[1]
_CORE = _APP.parents[1] / "kentender_core" / "kentender_core"
_SERVED = (".vue", ".js", ".html", ".jinja")
_SKIPPED = ("fixtures", "node_modules", ".spec.", "vitest.setup", "/dist/")
_NOTICE = re.compile(
	r"Test environment[:—]|not a production|simulated Test Tender Box|Test attestation|not an electronic signature|kt_portal_environment_notices|awd-test-environment|data\.test_environment|proof_label",
	re.IGNORECASE,
)


def _served_files():
	for root in (_APP / "public" / "js", _APP / "templates", _CORE / "public" / "js", _CORE / "templates"):
		for path in root.rglob("*"):
			text = path.as_posix()
			if path.suffix in _SERVED and not any(skip in text for skip in _SKIPPED):
				yield path


class TestNoEnvironmentNotices(IntegrationTestCase):
	def test_no_served_screen_or_template_carries_a_test_environment_notice(self):
		found = [f"{p.relative_to(_APP.parents[1])}: {m.group(0)}" for p in _served_files() for m in [_NOTICE.search(p.read_text(errors="ignore"))] if m]
		self.assertEqual(found, [])

	def test_the_receipt_print_view_has_no_simulation_note(self):
		from kentender_procurement.bid_submission.services import receipts

		self.assertFalse(hasattr(receipts, "SIMULATION_NOTE"))
		data = {"receipt_reference": "RCPT-X", "notice": receipts.NOT_A_RESULT, "deadline": "", "summary": {}}
		html = receipts.receipt_html(data)
		self.assertNotRegex(html, _NOTICE)

	def test_the_award_screens_carry_no_test_label(self):
		from kentender_procurement.award.services import simulation

		self.assertFalse(hasattr(simulation, "TEST_LABEL"))
		self.assertFalse((_APP / "award" / "services" / "opinion.py").read_text().count("SIGNING_LABEL"))
