# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""One signature, from the attempt to the proof (CM-CHG-001 v0.8 sections 5.3, 5.17 "Signature outcome uncertain", 7; plan D5, D8).

Every personal proof in Contract Management (the agreement, a certificate, an acceptance report, a certification, a close-out) is a **signing attempt** with the same shape:

1. inside the command, `record` writes the `Recorded` intent atomically with the decision, under a stable operation identity (subject, version, kind, key);
2. after the command commits, `carry_out` calls the trust facade (`kentender_core.services.signing`) with that identity as the correlation, reading the owner first, so a retry of an unknown
   outcome finds the proof and never signs twice;
3. the caller applies the outcome in its own transaction: a **proof** makes the signature; a refusal or an unavailable service keeps the same attempt (`CM_SIGNING`, work saved); an unknown
   reply stays pending and holds a new attempt until it is recovered.

This module owns steps 1 and 2 and the refusal; the caller owns what a proof means."""

from __future__ import annotations

from typing import Any

import frappe

from kentender_contracts.services import intents
from kentender_contracts.services.errors import fail
from kentender_core.services import signing

METHOD = "Signature proof"


def record(case: str, subject: str, version: int, key: str):
	"""The `Recorded` intent for this attempt (the same one on a retry)."""
	return intents.record(case, subject, version, "Signing attempt", key, recovery_owner="Technical operator")


def existing(case: str, subject: str, version: int, key: str) -> str | None:
	return frappe.db.get_value(intents.INTENT, {"operation_identity": intents.identity(case, subject, version, "Signing attempt", key)}, "name")


def lookup(identity: str) -> str | None:
	found = signing.reconcile(identity, consumer="contracts")
	if found.get("known") is True and found.get("outcome") == signing.VERIFIED and found.get("proof_reference"):
		return found["proof_reference"]
	return None


def carry_out(intent: str, *, member: str, target_id: str, target_digest: str, version: int, action: str) -> dict[str, Any]:
	"""Call the facade for this attempt. Returns `{state, reference, outcome, method, detail}`; `state` is the intent's (Succeeded / Reconciled settle it)."""
	seen: dict[str, str] = {}

	def executor(identity: str):
		answer = signing.attest(member=member, target_id=target_id, target_digest=target_digest, minutes_version=str(version), action=action, correlation_id=identity, consumer="contracts")
		seen["outcome"] = answer.get("outcome", "")
		if answer.get("outcome") == signing.VERIFIED and answer.get("proof_reference"):
			seen["method"] = answer.get("method", "")
			return answer["proof_reference"], METHOD
		if answer.get("outcome") in (signing.UNAVAILABLE, signing.REJECTED):
			raise intents.OwnerRefused(f"Signing {answer['outcome'].lower()}.")
		raise RuntimeError("The signing outcome is not known.")

	result = intents.execute(intent, executor, lookup, native_doctype=METHOD)
	return {**result, "outcome": seen.get("outcome", ""), "method": seen.get("method", "")}


def settled(result: dict[str, Any]) -> bool:
	return result["state"] in intents.SETTLED


def unfinished(result: dict[str, Any], **detail) -> None:
	"""The attempt did not produce a proof: refuse with the stable signing error, naming whether the outcome is pending."""
	pending = result["state"] in ("Attempting", "Uncertain", "Recorded")
	fail("CM_SIGNING", pending=pending, state=result["state"], intent=result["intent"], **detail)
