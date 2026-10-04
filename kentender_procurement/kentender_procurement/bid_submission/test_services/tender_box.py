# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The Test Tender Box (owner decision OD-C; plan D7), on the
`kt_bds_custody_services` hook.

A stand-in for the approved electronic tender box, answering only on a test
environment. A deposit names one correlation, carries the exact signed
package and its digest, and ends in one outcome the test controls choose:
Accepted (a sealed envelope and a custody acknowledgement), Rejected (a
rejection reference; nothing kept), or no answer (the caller records the
attempt as uncertain and later asks `status` for the same correlation; a
repeated deposit under that correlation never makes a second envelope).
Package bytes are kept under `private/kt_test_tender_box/` on the site,
outside every DocType and File, with no read path from the application.
There is no encryption here and none is claimed; the production custody
design is an owner-gate item (FU-V08-16)."""

from __future__ import annotations

import hashlib
import json
import os
import secrets
from datetime import timedelta
from typing import Any

import frappe
from frappe.utils import cint, cstr, get_datetime

from kentender_procurement.bid_submission.services import simulation

NAME = "Test Tender Box (simulation)"
FOLDER = "kt_test_tender_box"


def folder() -> str:
	return frappe.get_site_path("private", FOLDER)


def _paths(correlation_id: str) -> tuple[str, str]:
	safe = "".join(c for c in cstr(correlation_id) if c.isalnum() or c in "-_")
	return os.path.join(folder(), f"{safe}.package"), os.path.join(folder(), f"{safe}.state.json")


def _read_state(correlation_id: str) -> dict[str, Any] | None:
	_package, state = _paths(correlation_id)
	if not os.path.exists(state):
		return None
	with open(state, encoding="utf-8") as fh:
		return json.load(fh)


def _write_state(correlation_id: str, state: dict[str, Any]) -> None:
	_package, path = _paths(correlation_id)
	tmp = path + ".tmp"
	with open(tmp, "w", encoding="utf-8") as fh:
		json.dump(state, fh, sort_keys=True)
	os.replace(tmp, path)


def _accepted(state: dict[str, Any], at) -> dict[str, Any]:
	state.update({"result": "Accepted", "envelope_ref": "TBX-ENV-" + secrets.token_hex(6).upper(), "custody_receipt": "TBX-ACK-" + secrets.token_hex(6).upper(), "accepted_at": str(at)})
	return state


def _rejected(state: dict[str, Any], reference: str, reason: str) -> dict[str, Any]:
	package, _state = _paths(state["correlation_id"])
	if os.path.exists(package):
		os.remove(package)  # rejected content is not kept in custody
	state.update({"result": "Rejected", "rejection_reference": reference or "TBX-REJECT-" + secrets.token_hex(4).upper(), "rejection_reason": reason})
	return state


def _public(state: dict[str, Any]) -> dict[str, Any]:
	out = {k: state.get(k) for k in ("result", "envelope_ref", "custody_receipt", "accepted_at", "rejection_reference", "rejection_reason") if state.get(k)}
	if out.get("result") == "Pending":
		out["result"] = "Uncertain"
	return {**out, "service": NAME, "simulation": True}


class TestTenderBox:
	name = NAME

	def healthy(self) -> bool:
		return not simulation.controls()["custody_service_down"]

	def deposit(self, *, correlation_id: str, tender: str, package: bytes, package_digest: str, deadline, at) -> dict[str, Any]:
		existing = _read_state(correlation_id)
		if existing:
			return _public(existing)  # one correlation, one outcome
		os.makedirs(folder(), exist_ok=True)
		state: dict[str, Any] = {"correlation_id": correlation_id, "tender": tender, "package_digest": package_digest, "received_at": str(get_datetime(at)), "deadline": str(get_datetime(deadline))}
		if _box_closed(tender):
			_write_state(correlation_id, _rejected(state, "", "The tender box for this Tender is closed."))
			return _public(_read_state(correlation_id))
		if hashlib.sha256(package).hexdigest() != package_digest:
			_write_state(correlation_id, _rejected(state, "", "The package does not match its signed binding."))
			return _public(_read_state(correlation_id))
		package_path, _state = _paths(correlation_id)
		with open(package_path, "wb") as fh:
			fh.write(package)
		controls = simulation.controls()
		accepted_at = get_datetime(at) + timedelta(seconds=cint(controls["accept_after_seconds"]))
		outcome = controls["deposit_outcome"]
		if outcome == "Reject":
			state = _rejected(state, cstr(controls["rejection_reference"]), "The tender box rejected this deposit.")
		elif accepted_at >= get_datetime(deadline):
			state = _rejected(state, "", "The tender box closed at the deadline.")
		elif outcome == "Uncertain":
			state.update({"result": "Pending", "accept_at": str(accepted_at)})
		else:
			state = _accepted(state, accepted_at)
		_write_state(correlation_id, state)
		return _public(state)

	def close_box(self, *, tender: str, at) -> dict[str, Any]:
		return close_box(tender=tender, at=at)

	def confirm_release(self, **kwargs) -> dict[str, Any]:
		return confirm_release(**kwargs)

	def reveal(self, **kwargs) -> dict[str, Any]:
		return reveal(**kwargs)

	def release_for_evaluation(self, **kwargs) -> dict[str, Any]:
		return release_for_evaluation(**kwargs)

	def status(self, *, correlation_id: str) -> dict[str, Any]:
		"""The outcome of an earlier deposit, for the reconciler: Accepted,
		Rejected, Uncertain (still pending) or NotReceived."""
		state = _read_state(correlation_id)
		if not state:
			return {"result": "NotReceived", "service": NAME, "simulation": True}
		if state["result"] == "Pending":
			resolution = simulation.controls()["uncertain_resolution"]
			if resolution == "Accept":
				state = _accepted(state, get_datetime(state["accept_at"]))
				_write_state(correlation_id, state)
			elif resolution == "Reject":
				state = _rejected(state, "", "The tender box did not accept this deposit.")
				_write_state(correlation_id, state)
		return _public(state)


def _close_path(tender: str) -> str:
	safe = "".join(c for c in cstr(tender) if c.isalnum() or c in "-_")
	return os.path.join(folder(), f"BOX-{safe}.close.json")


def _box_closed(tender: str) -> dict[str, Any] | None:
	path = _close_path(tender)
	if not os.path.exists(path):
		return None
	with open(path, encoding="utf-8") as fh:
		return json.load(fh)


def close_box(*, tender: str, at) -> dict[str, Any]:
	"""Close one Tender's box at its deadline: no deposit is accepted after
	this. Returns the box's own inventory of accepted envelopes. Idempotent."""
	closed = _box_closed(tender)
	if closed:
		return {**closed, "service": NAME, "simulation": True}
	os.makedirs(folder(), exist_ok=True)
	envelopes = []
	for name in sorted(os.listdir(folder())):
		if name.endswith(".state.json"):
			with open(os.path.join(folder(), name), encoding="utf-8") as fh:
				state = json.load(fh)
			if state.get("tender") == tender and state.get("result") == "Accepted":
				envelopes.append(state["envelope_ref"])
	closed = {"result": "Closed", "close_receipt": "TBX-CLOSE-" + secrets.token_hex(5).upper(), "closed_at": str(get_datetime(at)), "envelopes": envelopes}
	path = _close_path(tender)
	with open(path + ".tmp", "w", encoding="utf-8") as fh:
		json.dump(closed, fh, sort_keys=True)
	os.replace(path + ".tmp", path)
	return {**closed, "service": NAME, "simulation": True}


# -- opening release and reveal (BOP-CHG-001 v0.10 plan D4; TRUST-ADR-001 v0.1 §2) ----


def _release_path(tender: str) -> str:
	safe = "".join(c for c in cstr(tender) if c.isalnum() or c in "-_")
	return os.path.join(folder(), f"BOX-{safe}.release.json")


def _release_state(tender: str) -> dict[str, Any]:
	path = _release_path(tender)
	if not os.path.exists(path):
		return {"confirmations": []}
	with open(path, encoding="utf-8") as fh:
		return json.load(fh)


def confirm_release(*, tender: str, member: str, independent: bool, manifest_digest: str, roster_digest: str, at) -> dict[str, Any]:
	"""TRUST-ADR-001 v0.1 §2 "Joint opening release": one appointed member's
	confirmation against one closed manifest and roster. A member confirming
	again replaces their own earlier confirmation. A test control, not the
	production key threshold."""
	if not _box_closed(tender):
		return {"outcome": "Rejected", "reason": "box_open", "service": NAME, "simulation": True}
	state = _release_state(tender)
	state["confirmations"] = [c for c in state["confirmations"] if c["member"] != member] + [{
		"member": member, "independent": bool(independent), "manifest_digest": manifest_digest, "roster_digest": roster_digest, "at": str(get_datetime(at)),
	}]
	path = _release_path(tender)
	with open(path + ".tmp", "w", encoding="utf-8") as fh:
		json.dump(state, fh, sort_keys=True)
	os.replace(path + ".tmp", path)
	return {"outcome": "Accepted/Verified", "participation_reference": "TBX-REL-" + secrets.token_hex(5).upper(), "service": NAME, "simulation": True}


def reveal(*, tender: str, correlation_id: str, manifest_digest: str, roster_digest: str) -> dict[str, Any]:
	"""Release one sealed package, only after close and only while at least two
	distinct members, one of them independent, have confirmed this exact
	manifest and roster (TRUST-ADR-001 v0.1 §1(5), §2). The custody boundary
	checks this itself; the application check alone is not enough (BOP-CHG-001
	v0.10 §5)."""
	forced = simulation.controls()["reveal_outcome"]
	if forced in ("Unavailable", "Indeterminate"):
		return {"outcome": forced, "service": NAME, "simulation": True}
	if not _box_closed(tender):
		return {"outcome": "Rejected", "reason": "box_open", "service": NAME, "simulation": True}
	valid = [c for c in _release_state(tender)["confirmations"] if c["manifest_digest"] == manifest_digest and c["roster_digest"] == roster_digest]
	if len({c["member"] for c in valid}) < 2 or not any(c["independent"] for c in valid):
		return {"outcome": "Rejected", "reason": "release_not_confirmed", "service": NAME, "simulation": True}
	package = stored_package(correlation_id)
	if package is None:
		return {"outcome": "Rejected", "reason": "not_in_custody", "service": NAME, "simulation": True}
	if forced == "Mismatch":
		package = package + b" "  # a package that no longer matches its sealed digest
	return {"outcome": "Accepted/Verified", "package": package, "service": NAME, "simulation": True}


def release_for_evaluation(*, tender: str, correlation_id: str, completion_reference: str) -> dict[str, Any]:
	"""Release one package opened at a completed opening to Bid Evaluation
	(EVL-CHG-001 v0.4 §5.1, §6 "BOP → Evaluation"; EVL plan D6). The box
	releases only after close and only against the named completion; which
	envelopes that completion opened is checked by the gateway against the
	sealed manifest. A production custody design decides how the opened
	package is kept for evaluation (FU-EVL-11)."""
	if not _box_closed(tender):
		return {"outcome": "Rejected", "reason": "box_open", "service": NAME, "simulation": True}
	if not cstr(completion_reference).strip():
		return {"outcome": "Rejected", "reason": "no_completion", "service": NAME, "simulation": True}
	package = stored_package(correlation_id)
	if package is None:
		return {"outcome": "Rejected", "reason": "not_in_custody", "service": NAME, "simulation": True}
	return {"outcome": "Accepted/Verified", "package": package, "service": NAME, "simulation": True}


def service() -> TestTenderBox | None:
	return TestTenderBox() if simulation.enabled() else None


def remove(correlation_ids: list[str], tenders: list[str] | None = None) -> int:
	"""Fixture and test clean-up: the box's files for these correlations (and
	the close records of these Tenders)."""
	removed = 0
	for tender in tenders or []:
		for path in (_close_path(tender), _release_path(tender)):
			if os.path.exists(path):
				os.remove(path)
				removed += 1
	for correlation_id in correlation_ids:
		for path in _paths(correlation_id):
			if os.path.exists(path):
				os.remove(path)
				removed += 1
	return removed


def stored_package(correlation_id: str) -> bytes | None:
	"""Test-only inspection of what the box holds (the application has no read path)."""
	package, _state = _paths(correlation_id)
	if not os.path.exists(package):
		return None
	with open(package, "rb") as fh:
		return fh.read()
