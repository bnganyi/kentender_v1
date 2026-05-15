# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""O-05 — doc 8 **TM2-SMOKE-WORKS-001**; doc 9 §21.2 ``test_TM2_SMOKE_WORKS_001_…``.

Supplier Works BOQ payload must **not** change procuring-entity quantities: mismatch →
``BOQ_QUANTITY_LOCKED`` (doc 8 Expected Denial Code; also ``AUTH_CONTEXT_DENIED`` is listed as
alternate in the smoke table — this implementation uses ``BOQ_QUANTITY_LOCKED``).

Run::

	bench --site kentender.midas.com run-tests --app kentender_procurement \\
		--module kentender_procurement.tender_management.tests.test_o05_tm2_smoke_works_001_supplier_cannot_edit_boq_quantities
"""

from __future__ import annotations

from kentender_procurement.tender_management.security.authorization.denial_codes import DenialCode
from kentender_procurement.tender_management.services.validate_works_boq_payload import (
	validate_works_boq_payload,
)
from kentender_procurement.tender_management.tests.p6_published_tm2_fixture import P6PublishedTm2Fixture
from kentender_procurement.tender_management.tests.test_p4_01_create_tender_from_package import (
	_P401Tm2Cleanup,
)
from kentender_procurement.tender_management.tests.tm2_works_boq_supplier_fixture import (
	Tm2WorksBoqSupplierFixture,
)


class TestO05Tm2SmokeWorks001SupplierCannotEditBoqQuantities(
	Tm2WorksBoqSupplierFixture,
	_P401Tm2Cleanup,
	P6PublishedTm2Fixture,
):
	"""Doc 8 TM2-SMOKE-WORKS-001 — supplier cannot override published BOQ quantities."""

	p6_supplier_fixture_prefix = "O05"

	def test_TM2_SMOKE_WORKS_001_supplier_cannot_edit_boq_quantities(self) -> None:
		"""Item 1.1 PE quantity is 100; supplier sends 99 → ``BOQ_QUANTITY_LOCKED``."""
		tcode, _tm2, sup, _si = self._published_si_supplier_boq()
		lines = [{"item_number": "1.1", "rate": 1, "quantity": 99}, {"item_number": "1.2"}]
		out = validate_works_boq_payload(tcode, sup, {"lines": lines})
		self.assertFalse(out.get("ok"), out)
		self.assertEqual(out.get("denial_code"), DenialCode.BOQ_QUANTITY_LOCKED.value)
