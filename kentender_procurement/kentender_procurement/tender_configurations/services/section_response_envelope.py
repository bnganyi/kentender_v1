# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Shared section-response envelope for Electronic Bid Submission (no section business rules)."""

from __future__ import annotations

from typing import Any

from frappe.utils import cstr


def normalize_section_response_envelope(
	section_key: str,
	payload: dict[str, Any] | None = None,
	meta: dict[str, Any] | None = None,
) -> dict[str, Any]:
	"""Return ``{ section_key, payload, meta }`` with stable keys."""
	key = cstr(section_key or "").strip()
	body = payload if isinstance(payload, dict) else {}
	meta_out = meta if isinstance(meta, dict) else {}
	return {
		"section_key": key,
		"payload": body,
		"meta": meta_out,
	}


def extract_payload(stored: Any) -> dict[str, Any]:
	"""Accept raw payload dict or envelope and return the payload object."""
	if not isinstance(stored, dict):
		return {}
	if "payload" in stored and ("section_key" in stored or "meta" in stored):
		inner = stored.get("payload")
		return inner if isinstance(inner, dict) else {}
	return stored


def extract_meta(stored: Any) -> dict[str, Any]:
	if not isinstance(stored, dict):
		return {}
	meta = stored.get("meta")
	return meta if isinstance(meta, dict) else {}


def read_section_response(responses: dict[str, Any] | None, section_key: str) -> dict[str, Any]:
	"""Read one section from the responses map as a normalized envelope."""
	key = cstr(section_key or "").strip()
	responses = responses if isinstance(responses, dict) else {}
	stored = responses.get(key)
	if isinstance(stored, dict) and "payload" in stored and (
		"section_key" in stored or "meta" in stored
	):
		return normalize_section_response_envelope(
			cstr(stored.get("section_key") or key),
			stored.get("payload") if isinstance(stored.get("payload"), dict) else {},
			stored.get("meta") if isinstance(stored.get("meta"), dict) else {},
		)
	return normalize_section_response_envelope(
		key, stored if isinstance(stored, dict) else {}, {}
	)


def write_section_response(
	responses: dict[str, Any] | None,
	section_key: str,
	payload: dict[str, Any] | None = None,
	meta: dict[str, Any] | None = None,
	*,
	store_as_envelope: bool = False,
) -> dict[str, Any]:
	"""Write a section into the responses map.

	Default storage remains the bare payload dict (backward compatible with FoT / A2).
	When ``store_as_envelope`` is True, store the full ``{section_key, payload, meta}`` object.
	"""
	key = cstr(section_key or "").strip()
	out = dict(responses) if isinstance(responses, dict) else {}
	envelope = normalize_section_response_envelope(key, payload, meta)
	if store_as_envelope:
		out[key] = envelope
	else:
		# Preserve prior meta keys if callers pass them inside payload; storage is payload-only.
		out[key] = envelope["payload"]
	return out
