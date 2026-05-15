# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""O-04 — doc 8 **TM2-SMOKE-PUB-006**; doc 9 §21.2 ``test_TM2_SMOKE_PUB_006_…``.

**Publish** must be denied with ``AUTH_PUBLICATION_SNAPSHOT_MISSING`` when the STD instance has
no output codes for the adapter to build/bind a publication snapshot (doc 8 Expected Denial Code).

Fixture: :class:`Tm2ApprovedForPublicationFixtureChain` with ``seed_outputs=False`` (same as
``test_p4_06_snapshot_missing_denied``).

Run::

	bench --site kentender.midas.com run-tests --app kentender_procurement \\
		--module kentender_procurement.tender_management.tests.test_o04_tm2_smoke_pub_006_block_publication_without_publication_snapshot_binding
"""

from __future__ import annotations

from kentender_procurement.tender_management.security.authorization.action_authorization_registry import (
	spec_for_action,
)
from kentender_procurement.tender_management.security.authorization.denial_codes import DenialCode
from kentender_procurement.tender_management.services.publish_tender import publish_tender
from kentender_procurement.tender_management.tests.tm2_publish_fixture_chain import (
	Tm2ApprovedForPublicationFixtureChain,
)


class TestO04Tm2SmokePub006BlockPublicationWithoutPublicationSnapshotBinding(
	Tm2ApprovedForPublicationFixtureChain,
):
	"""Doc 8 TM2-SMOKE-PUB-006 — publish denied without publication snapshot binding."""

	def test_TM2_SMOKE_PUB_006_block_publication_without_publication_snapshot_binding(self) -> None:
		"""Approved tender without STD output refs → ``AUTH_PUBLICATION_SNAPSHOT_MISSING``."""
		tcode = self._mk_approved_for_publication(seed_outputs=False)
		spec_p = spec_for_action("TND2_PUBLISH")
		self.assertIsNotNone(spec_p)
		assert spec_p is not None
		out = publish_tender(
			"Administrator",
			tcode,
			context={"granted_permissions": [spec_p.required_permission]},
		)
		self.assertFalse(out.get("ok"), out)
		self.assertEqual(out.get("denial_code"), DenialCode.AUTH_PUBLICATION_SNAPSHOT_MISSING.value)
