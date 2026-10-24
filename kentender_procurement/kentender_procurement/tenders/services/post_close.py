# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The cancellation verdict, including the post-close route (TPR-CHG-001 v0.24 §5.7, §5.12, §7.6, §8, §10.13 POSTCLOSE, §10.19).

`CancelTender` is the Accounting Officer's existing decision. It is supported from **Published — open** (the existing route, unchanged) and from
**Submission period ended**, before authoritative Award notification (the post-close route). This module answers one question for the read and the
command alike — *may this Tender be cancelled now, and if not, why, who can fix it and how?* — so a screen never offers an action the command would
refuse, and the command refuses with exactly what the screen showed.

A blocker is `{code, message, holder, route, reason}`. Each carries the Tenders error code, its exact words, the holder who can resolve it and the
route to them; every current blocker is returned together:

- `TND_CANCEL_TOO_LATE` — an award notice is issued: the Award / legal process owner;
- `TND_AWARD_STATUS_UNAVAILABLE` — the Award authority record is missing, cannot be believed, is Unknown or an issue is in progress: the Award service owner;
- `TND_CANCEL_GROUND_UNVERIFIED` (post-close only) — no verified applicable ground: HOPF coordinates the documented legal-basis review, the AO retains the decision;
- `TND_CANCELLATION_UNAVAILABLE` (post-close only) — a consumer of the cancellation (Bid Opening / Proceedings) cannot take it: Opening access support.

A failed Bid Opening is evidence for review, never a ground. Nothing here reads a fault, an incident or an opening outcome to establish one."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cstr

from kentender_procurement.tenders.services import award_seam, cancellation_delivery, cancellation_grounds, clock
from kentender_procurement.tenders.services.errors import MESSAGES

OPEN = "Published — open"
ENDED = "Submission period ended"
STAGE_OPEN = "open"
STAGE_POST_CLOSE = "post_close"

HOLDER_HOPF = "Head of Procurement Function"
HOLDER_AWARD = "Award service owner"
HOLDER_AWARD_LEGAL = "Award and legal process owner"
HOLDER_SUPPORT = "Opening access support"

#: How the Award owner's neutral reasons read as Tenders codes.
AWARD_CODES = {"no_authority_record": "TND_AWARD_STATUS_UNAVAILABLE", "status_unknown": "TND_AWARD_STATUS_UNAVAILABLE", "issue_in_progress": "TND_AWARD_STATUS_UNAVAILABLE",
	"issued": "TND_CANCEL_TOO_LATE"}
#: The blocker the command reports first when several apply.
PRIORITY = ("TND_CANCEL_TOO_LATE", "TND_AWARD_STATUS_UNAVAILABLE", "TND_CANCEL_GROUND_UNVERIFIED", "TND_CANCELLATION_UNAVAILABLE")


def stage(root) -> str:
	"""The route this Tender's state supports: open, post-close, or none."""
	return {OPEN: STAGE_OPEN, ENDED: STAGE_POST_CLOSE}.get(cstr(root.overall_status), "")


def _award_blocker(b: dict[str, Any]) -> dict[str, Any]:
	code = AWARD_CODES.get(cstr(b.get("reason")), "TND_AWARD_STATUS_UNAVAILABLE")
	return {"code": code, "reason": cstr(b.get("reason")), "message": MESSAGES[code], "holder": cstr(b.get("holder")) or HOLDER_AWARD, "route": b.get("route") or {"area": "Award", "case": ""}}


def _ground_blocker() -> dict[str, Any]:
	return {"code": "TND_CANCEL_GROUND_UNVERIFIED", "reason": "ground_unverified", "message": MESSAGES["TND_CANCEL_GROUND_UNVERIFIED"],
		"holder": f"{HOLDER_HOPF} coordinates the documented review; the Accounting Officer keeps the decision", "route": {"area": "Tenders", "case": ""}}


def _integration_blocker(reasons: list[dict[str, Any]]) -> dict[str, Any]:
	return {"code": "TND_CANCELLATION_UNAVAILABLE", "reason": "cancellation_unavailable", "message": MESSAGES["TND_CANCELLATION_UNAVAILABLE"], "holder": HOLDER_SUPPORT,
		"route": {"area": "Bid Opening", "case": ""}, "detail": [r["label"] for r in reasons]}


def verdict(root, *, ground: str = "", lock: bool = False) -> dict[str, Any]:
	"""May this Tender be cancelled now? `lock=True` is the command's: it takes the shared fence's locks (Tender → authority record → case) and holds them to
	the end of the caller's transaction. A read passes `lock=False` and takes none.

	`ground` (command only) is the ground the Accounting Officer chose; on the post-close route it must be one a verifier verified."""
	from kentender_procurement.tenders.services import cancellation

	current = stage(root)
	if not current:
		return {"stage": "", "allowed": False, "blockers": [], "award": {}, "grounds": [], "checked_at": clock.now()}
	blockers: list[dict[str, Any]] = [_award_blocker(b) for b in award_seam.cancellation_blockers(root.name, lock=lock)]
	award = award_seam.authority_facts(root.name)
	grounds: list[dict[str, Any]]
	if current == STAGE_POST_CLOSE:
		verified = cancellation_grounds.verified(tender=root.name, stage=current, known=cancellation.GROUND_LABELS)["grounds"]
		grounds = [{"key": k, "label": cancellation.GROUND_LABELS[k], **verified[k]} for k in cancellation.GROUND_LABELS if k in verified]
		if not verified or (ground and ground not in verified):
			blockers.append(_ground_blocker())
		available = cancellation_delivery.availability()
		if not available["available"]:
			blockers.append(_integration_blocker(available["reasons"]))
	else:
		grounds = [{"key": k, "label": label} for k, label in cancellation.CANCELLATION_GROUNDS]
	blockers.sort(key=lambda b: PRIORITY.index(b["code"]) if b["code"] in PRIORITY else len(PRIORITY))
	return {"stage": current, "allowed": not blockers, "blockers": blockers, "award": award, "grounds": grounds, "checked_at": clock.now(),
		"ground_evidence": next((g for g in grounds if g["key"] == ground), None) if ground else None}
