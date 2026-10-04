# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The Contracting receiver seam (AWD-CHG-001 v0.4 §5.8, AWD-IF-05; plan D10).

Award hands over three things and never more: the `AwardDecisionRecorded v1`
event for each committed decision (Contracting owns any publication
obligation it triggers), the frozen Award package once every §5.8 condition
holds, and later restriction updates as separate immutable records. The
receiver comes from `kt_award_contracting_receivers`. No Contracting module
exists on this bench: the only receiver is the simulation stand-in; without
one, delivery waits with a named technical owner and never asks the Head of
Procurement to approve transmission."""

from __future__ import annotations

from typing import Any

import frappe


class ReceiverUnavailable(Exception):
	pass


def receiver():
	for path in reversed(frappe.get_hooks("kt_award_contracting_receivers") or []):
		found = frappe.get_attr(path)()
		if found is not None:
			return found
	return None


def _call(method: str, payload: dict[str, Any]) -> dict[str, Any]:
	r = receiver()
	if r is None:
		raise ReceiverUnavailable("No Contracting receiver is available.")
	try:
		result = getattr(r, method)(payload)
	except ReceiverUnavailable:
		raise
	except Exception as exc:
		frappe.log_error(title=f"Contracting receiver {method} failed")
		raise ReceiverUnavailable(str(exc)) from exc
	if not result or not result.get("receipt"):
		raise ReceiverUnavailable("The Contracting receiver did not confirm receipt.")
	return result


def deliver_event(payload: dict[str, Any]) -> dict[str, Any]:
	return _call("receive_decision_event", payload)


def deliver_package(payload: dict[str, Any]) -> dict[str, Any]:
	return _call("receive_package", payload)


def deliver_update(payload: dict[str, Any]) -> dict[str, Any]:
	return _call("receive_update", payload)
