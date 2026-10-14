# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The published seam between the owners of contract source material and Contract Management (CM-CHG-001 v0.8 plan D20, section 19.4).

Award hands Contract Management references to the material it needs (the issued tender and its template release, the accepted tender, the price schedule, the
GCC and SCC, the Form No. 4 source, the notification, the funding lineage, the entity's particulars, the supplier's identity). The material stays with its owner and
stays retrievable and verifiable. Each owner registers a provider on `kt_contract_source_provider`, a callable returning a provider object (or None to decline, for
example outside a simulation environment). A provider answers only the references it owns and returns None for the others.

    describe(*, reference) -> {"reference", "version", "sha256", "media_type", "size", "owner", ...} | None
    fetch(*, reference)    -> {"content": bytes, "digest": sha256 hex} | None

`verify` recomputes the digest of what `fetch` returns against what `describe` said, so a source that changed after it was described fails. Contract Management resolves and
verifies each reference at preparation, copies the bytes and digests into its own manifest, and never imports an owner's code or reads its tables. With no provider a
caller must fail closed (no source, no agreement). A provider that raises is logged and skipped, never taken as a verification. Tests may set
`frappe.flags.kt_contract_source_providers` to a list of provider objects."""

from __future__ import annotations

import hashlib
from typing import Any

import frappe

HOOK = "kt_contract_source_provider"
FUNCTIONS: tuple[str, ...] = ("describe", "fetch")


def providers() -> list[Any]:
	override = frappe.flags.get("kt_contract_source_providers")
	if override is not None:
		return list(override)
	found = []
	for path in frappe.get_hooks(HOOK) or []:
		try:
			provider = frappe.get_attr(path)()
		except Exception:
			frappe.log_error(title=f"Contract source provider failed to load: {path}")
			continue
		if provider is not None:
			found.append(provider)
	return found


def missing_functions(candidate: Any) -> list[str]:
	return [name for name in FUNCTIONS if not callable(getattr(candidate, name, None))]


def _ask(function: str, reference: str) -> dict[str, Any] | None:
	for provider in providers():
		try:
			answer = getattr(provider, function)(reference=reference)
		except Exception:
			frappe.log_error(title=f"Contract source provider {function} failed for {reference}")
			continue
		if answer is not None:
			return answer
	return None


def describe(reference: str) -> dict[str, Any] | None:
	return _ask("describe", reference)


def fetch(reference: str) -> dict[str, Any] | None:
	return _ask("fetch", reference)


def verify(reference: str) -> bool:
	"""True only when the owner describes the reference and the bytes it returns hash to what it described."""
	described, fetched = describe(reference), fetch(reference)
	if not described or not fetched:
		return False
	content = fetched.get("content")
	if not isinstance(content, (bytes, bytearray)):
		return False
	actual = hashlib.sha256(bytes(content)).hexdigest()
	return actual == described.get("sha256") == fetched.get("digest")
