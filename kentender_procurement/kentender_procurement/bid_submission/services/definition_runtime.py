# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Binding a bid to the exact Published Bid Definition (BDS-CHG-001 v0.8
§4.4.4–4.4.5 and plan D4). The definition must be the Tender's current
Effective one, its digest must verify, this build must render its product
profile, and its template release must still verify. A release switched On
or Off is permitted for a published Tender (owner decision OD5: the switch
governs new Tenders only); a Superseded or Withdrawn release, or one whose
integrity or renderer check fails, is `BDS_DEFINITION_UNSUPPORTED` until
TPR-CHG-001 v0.13 is approved (BDS08-AC-008)."""

from __future__ import annotations

from typing import Any

from kentender_procurement.bid_submission.services import product_profile, tenders_gateway
from kentender_procurement.bid_submission.services.errors import fail

PERMITTED_LIFECYCLE = ("Available",)
ARRANGEMENT_FIELD = ":RR-SUPPLIER-DETAILS:bidder_arrangement"


def check(definition: dict[str, Any], *, digest: str = "") -> None:
	if not tenders_gateway.verify_definition_digest(definition) or (digest and definition.get("definition_digest") != digest):
		fail("BDS_DEFINITION_UNSUPPORTED")
	product_profile.resolve(definition)
	status = tenders_gateway.release_status(definition.get("template_release_id") or "")
	if status.get("lifecycle") not in PERMITTED_LIFECYCLE or not status.get("integrity_ok") or not status.get("renderer_ok"):
		fail("BDS_DEFINITION_UNSUPPORTED")


def bind_current(tender_name: str) -> dict[str, Any]:
	"""The verified current definition a new Draft binds to."""
	current = tenders_gateway.current_definition(tender_name)
	if not current:
		fail("BDS_DEFINITION_UNSUPPORTED")
	definition = current["definition"]
	check(definition, digest=current["definition_digest"])
	return {
		"bid_definition_id": current["bid_definition_id"], "definition_version": int(current["definition_version"]),
		"definition_digest": current["definition_digest"], "definition": definition,
	}


def arrangement_options(definition: dict[str, Any]) -> list[str]:
	"""The bidder arrangements this Tender permits, from its own definition
	(§5.2 item 6: a joint venture only when the Published Tender permits it)."""
	for row in definition.get("response_rows") or []:
		if row.get("stable_key", "").endswith(ARRANGEMENT_FIELD):
			options = ((row.get("validation") or {}).get("parameters") or {}).get("options") or []
			return [str(o) for o in options] if isinstance(options, list) else []
	return ["Single organisation"]
