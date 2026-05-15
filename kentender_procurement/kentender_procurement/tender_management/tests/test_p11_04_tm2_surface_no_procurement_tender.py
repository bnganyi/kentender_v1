# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P11-04 (partial) — TM2 surfaces must not load ``Procurement Tender`` via document API.

Full DocType removal is **R07**-gated. This module is the automated **no get_doc PT in TM2 paths**
acceptance slice from ``IMPLEMENTATION_TRACKER.md`` P11-04.

Run::

	bench --site kentender.midas.com run-tests --app kentender_procurement \\
		--module kentender_procurement.tender_management.tests.test_p11_04_tm2_surface_no_procurement_tender
"""

from __future__ import annotations

from frappe.tests import IntegrationTestCase

from kentender_procurement.tender_management.audit.p11_04_tm2_surface_procurement_tender_scan import (
	format_p11_04_violations,
	run_p11_04_tm2_surface_procurement_tender_scan,
)


class TestP1104Tm2SurfaceNoProcurementTender(IntegrationTestCase):
	def test_p11_04_tm2_surface_has_no_procurement_tender_doc_api(self) -> None:
		violations = run_p11_04_tm2_surface_procurement_tender_scan()
		self.assertFalse(
			violations,
			msg="P11-04 TM2 surface violations:\n" + format_p11_04_violations(violations),
		)
