# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""O-07 — doc 8 **TM2-SMOKE-OPEN-003**; doc 9 §21.2 ``test_TM2_SMOKE_OPEN_003_…``.

Opening register / opening-stage JSON must **not** carry BOQ arithmetic correction or DOM-forbidden
evaluation fields (DERIVED-0810 / pack §15). This smoke asserts the non-throwing gate
:meth:`~kentender_procurement.tender_management.derived_models.consumption.manual_rule_denial.ManualRuleDenialService.validate_opening_register_payload`
matches :meth:`~kentender_procurement.tender_management.derived_models.consumption.manual_rule_denial.ManualRuleDenialService.assert_no_manual_opening_evaluation_field`.

Run::

	bench --site kentender.midas.com run-tests --app kentender_procurement \\
		--module kentender_procurement.tender_management.tests.test_o07_tm2_smoke_open_003_no_arithmetic_correction_at_opening
"""

from __future__ import annotations

from frappe.tests import IntegrationTestCase

from kentender_procurement.tender_management.derived_models.consumption.manual_rule_denial import (
	ManualRuleDenialService,
)
from kentender_procurement.tender_management.security.authorization.denial_codes import DenialCode


class TestO07Tm2SmokeOpen003NoArithmeticCorrectionAtOpening(IntegrationTestCase):
	"""Doc 8 TM2-SMOKE-OPEN-003 — opening payload gate rejects arithmetic / evaluation injection."""

	def test_TM2_SMOKE_OPEN_003_no_arithmetic_correction_at_opening(self) -> None:
		ar = ManualRuleDenialService.validate_opening_register_payload(
			{"arithmetic_correction": {"applied": True}},
		)
		self.assertFalse(ar.get("ok"), ar)
		self.assertEqual(ar.get("denial_code"), DenialCode.BOQ_ARITHMETIC_CORRECTION_STAGE_VIOLATION.value)

		ev = ManualRuleDenialService.validate_opening_register_payload(
			{"register": {"evaluation_ranking": {}}},
		)
		self.assertFalse(ev.get("ok"), ev)
		self.assertEqual(ev.get("denial_code"), DenialCode.MANUAL_OPENING_EVALUATION_FIELD_DENIED.value)

		ok = ManualRuleDenialService.validate_opening_register_payload(
			{"rows": [{"bid_code": "BID-1", "submitted_total_bid_price": 96750000}]},
		)
		self.assertTrue(ok.get("ok"), ok)
