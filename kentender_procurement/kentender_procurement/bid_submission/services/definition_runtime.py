# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Binding a bid to the exact Published Bid Definition (BDS-CHG-001 v0.8
§4.4.4–4.4.5 and plan D4). The definition must be the Tender's current
Effective one, its digest must verify, this build must render its product
profile, and its template release must still verify.

The bound-release matrix for a published Tender (§4.4.4; TPR-CHG-001 v0.13,
approved by the Project Owner 28 Sep 2026, plan Phase 13):

- Available, switched On or Off, and Superseded: every bid action continues
  while the exact checks pass — nothing rebinds or substitutes a successor;
- Withdrawn, or a release whose integrity or renderer check fails: no new
  Start, definition build, Draft change, submission or replacement. The
  Draft, receipts and public reads stay readable, and a current Submitted
  bid may still be withdrawn before the deadline.

A digest that does not verify, or a product profile this build cannot
render, fails every read and command (`BDS_DEFINITION_UNSUPPORTED`)."""

from __future__ import annotations

from typing import Any

from kentender_procurement.bid_submission.services import product_profile, tenders_gateway
from kentender_procurement.bid_submission.services.errors import fail

PERMITTED_LIFECYCLE = ("Available", "Superseded")
ARRANGEMENT_FIELD = ":RR-SUPPLIER-DETAILS:bidder_arrangement"


def release_condition(definition: dict[str, Any], *, verify: bool = True) -> dict[str, Any]:
	"""{"ok", "lifecycle", "reason"}: the bound release's standing for new
	bid work. `reason` is "" (permitted), "withdrawn" or "failed" (integrity
	or renderer). A command re-hashes the release; a read (`verify=False`)
	uses the recorded result."""
	status = tenders_gateway.release_status(definition.get("template_release_id") or "", verify=verify)
	lifecycle = status.get("lifecycle") or "Unknown"
	if lifecycle == "Withdrawn":
		reason = "withdrawn"
	elif lifecycle not in PERMITTED_LIFECYCLE or not status.get("integrity_ok") or not status.get("renderer_ok"):
		reason = "failed"
	else:
		reason = ""
	return {"ok": not reason, "lifecycle": lifecycle, "reason": reason}


def check(definition: dict[str, Any], *, digest: str = "") -> None:
	"""Start bid and every definition build (an addendum refresh)."""
	if not tenders_gateway.verify_definition_digest(definition) or (digest and definition.get("definition_digest") != digest):
		fail("BDS_DEFINITION_UNSUPPORTED")
	product_profile.resolve(definition)
	if not release_condition(definition)["ok"]:
		fail("BDS_DEFINITION_UNSUPPORTED")


def bid_condition(ctx, *, verify: bool = False) -> dict[str, Any]:
	"""The release standing of the definition this bid is bound to."""
	return release_condition(ctx.model.definition, verify=verify)


def workspace_condition(ws) -> dict[str, Any]:
	"""The release standing of a bid read without its full context (lists);
	`ws` must carry `tender` and `definition_version`."""
	if not ws.get("tender") or not ws.get("definition_version"):
		raise ValueError("workspace_condition needs the bid's tender and definition_version")
	bound = tenders_gateway.definition_for(ws.tender, ws.definition_version)
	return release_condition(bound["definition"], verify=False) if bound else {"ok": False, "lifecycle": "Unknown", "reason": "failed"}


def require_release(ctx, *, verify: bool = False) -> None:
	"""A Draft change, signing, submission or replacement on a release that
	can no longer take bid work is `BDS_DEFINITION_UNSUPPORTED`."""
	if not bid_condition(ctx, verify=verify)["ok"]:
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
