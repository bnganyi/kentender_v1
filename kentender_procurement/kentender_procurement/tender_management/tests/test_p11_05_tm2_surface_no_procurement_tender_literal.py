# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P11-05 — TM2 surfaces must not embed the ``Procurement Tender`` DocType literal."""

import unittest

from kentender_procurement.tender_management.audit.p11_05_tm2_surface_procurement_tender_literal_scan import (
	format_p11_05_violations,
	run_p11_05_tm2_surface_procurement_tender_literal_scan,
)


class TestP11Tm2SurfaceNoProcurementTenderLiteral(unittest.TestCase):
	def test_p11_05_tm2_surface_has_no_procurement_tender_doctype_literal(self) -> None:
		violations = run_p11_05_tm2_surface_procurement_tender_literal_scan()
		self.assertFalse(
			violations,
			"P11-05 TM2 surface must not quote Procurement Tender doctype:\n"
			+ format_p11_05_violations(violations),
		)


if __name__ == "__main__":
	unittest.main()
