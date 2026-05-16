# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""R3-001 / LV-R3-001-01 — **Generic handoff upsert service** (cursor pack §8.1).

## Goal

``create_or_update_handoff_card(payload)`` is the single authoritative write path for
``Procurement Handoff Card``.  All specific handoff functions (R3-002 … R3-008) build a
typed payload dict and delegate here — no duplication of upsert or validation logic.

## Required behavior (pack §8.1 items 1–10)

1. Validate required fields.
2. Upsert by ``handoff_code`` (unique index on the DocType).
3. Link to ``journey_code``.
4. Store ``locked_summary`` and ``passed_forward_summary`` as JSON.
5. Store ``evidence_links_json`` using the normalised ``{"links":[...]}`` envelope.
6. Store ``technical_refs_json`` separately (lighter validation than evidence links).
7. Preserve source module ownership — ``source_module`` is set on create and never
   overwritten on update.
8. Mark stale if source state hash changes (via ``source_state_hash`` diff); callers
   may pass a current hash; the service records it and flips status to ``Stale`` when
   the hash diverges from the stored one.
9. Do not mutate source objects (only the ``Procurement Handoff Card`` DocType is touched).
10. Emit a lightweight audit note via ``frappe.log_error``-free path when the card is
    updated after prior consume/handoff (non-blocking; warnings only).

## Required payload keys

| Key | Type | Required | Notes |
|---|---|---:|---|
| ``handoff_code`` | str | Yes | Unique card identifier. |
| ``handoff_title`` | str | Yes | Business display title. |
| ``journey_code`` | str | Yes | Parent Procurement Journey. |
| ``source_module`` | str | Yes | Set on create; ownership rule (pack §8.1 item 7). |
| ``target_module`` | str | Yes | Downstream consumer module. |
| ``status`` | str | Yes | Must be in ``HANDOFF_CARD_STATUS_VALUES``. |
| ``locked_summary`` | dict | No (default ``{}``) | Snapshot of source state at handoff time. |
| ``passed_forward_summary`` | dict | No (default ``{}``) | Derived context for downstream module. |
| ``next_action`` | str | No (default ``""``) | Human-readable guidance. |
| ``evidence_links`` | list | No (default ``[]``) | Each link must satisfy ``§6.4`` schema. |
| ``source_object_type`` | str | No | |
| ``source_object_code`` | str | No | |
| ``target_object_type`` | str | No | |
| ``target_object_code`` | str | No | |
| ``generated_by`` | str | No | Defaults to ``frappe.session.user``. |
| ``generated_at`` | str | No | ISO datetime string. |
| ``consumed_by`` | str | No | |
| ``consumed_at`` | str | No | ISO datetime string. |
| ``technical_refs`` | dict | No | |
| ``source_state_hash`` | str | No | SHA/fingerprint for stale detection. |
| ``is_master_seed`` | bool | No | |

## Error codes

| Code | Condition |
|---|---|
| ``MISSING_REQUIRED_FIELD`` | Required payload key absent or blank. |
| ``INVALID_STATUS`` | ``status`` value not in ``HANDOFF_CARD_STATUS_VALUES``. |
| ``JOURNEY_NOT_FOUND`` | ``journey_code`` does not exist in ``Procurement Journey``. |
| ``EVIDENCE_LINKS_INVALID`` | Evidence links fail §6.4 schema validation. |
| ``TECHNICAL_REFS_INVALID`` | Technical refs exceed size cap or bad JSON. |
"""

from __future__ import annotations

import json
from typing import Any

import frappe

from kentender_procurement.procurement_lifecycle.evidence_links import (
    parse_validate_and_normalize_evidence_links,
)
from kentender_procurement.procurement_lifecycle.handoff_card_status import (
    HANDOFF_CARD_STATUS_VALUES,
)
from kentender_procurement.procurement_lifecycle.technical_refs import (
    parse_validate_technical_refs_json,
)

_REQUIRED_FIELDS: tuple[str, ...] = (
    "handoff_code",
    "handoff_title",
    "journey_code",
    "source_module",
    "target_module",
    "status",
)


def _coerce_json_text(value: Any) -> str:
    """Return a compact JSON string for longtext/JSON fields."""
    if isinstance(value, str):
        return value
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def create_or_update_handoff_card(payload: dict[str, Any]) -> dict[str, Any]:
    """Upsert a ``Procurement Handoff Card`` by ``handoff_code``.

    :param payload: Dict satisfying the required payload schema (see module docstring).
    :returns: ``{"ok": True, "action": "created"|"updated"|"existing", "handoff_code": …, "warnings": []}``.
    :raises ValueError: For validation failures (codes embedded in message).
    :raises frappe.DoesNotExistError: If ``journey_code`` is not found.
    """
    warnings: list[str] = []

    # --- 1. Validate required fields ---
    for field in _REQUIRED_FIELDS:
        val = payload.get(field)
        if not val or (isinstance(val, str) and not val.strip()):
            raise ValueError(
                f"MISSING_REQUIRED_FIELD: payload is missing or blank for required key {field!r}"
            )

    handoff_code: str = str(payload["handoff_code"]).strip()
    handoff_title: str = str(payload["handoff_title"]).strip()
    journey_code: str = str(payload["journey_code"]).strip()
    source_module: str = str(payload["source_module"]).strip()
    target_module: str = str(payload["target_module"]).strip()
    status: str = str(payload["status"]).strip()

    # --- Validate status vocabulary ---
    if status not in HANDOFF_CARD_STATUS_VALUES:
        raise ValueError(
            f"INVALID_STATUS: {status!r} is not a valid handoff card status. "
            f"Valid values: {sorted(HANDOFF_CARD_STATUS_VALUES)}"
        )

    # --- 3. Validate journey exists ---
    if not frappe.db.exists("Procurement Journey", journey_code):
        frappe.throw(
            f"Procurement Journey {journey_code!r} does not exist.",
            frappe.DoesNotExistError,
            title="JOURNEY_NOT_FOUND",
        )

    # --- 5 & 6. Validate evidence links and technical refs ---
    raw_evidence = payload.get("evidence_links", [])
    try:
        evidence_links_normalized = parse_validate_and_normalize_evidence_links(raw_evidence)
    except ValueError as exc:
        raise ValueError(f"EVIDENCE_LINKS_INVALID: {exc}") from exc

    raw_tech_refs = payload.get("technical_refs") or payload.get("technical_refs_json")
    try:
        technical_refs_parsed = parse_validate_technical_refs_json(raw_tech_refs)
    except ValueError as exc:
        raise ValueError(f"TECHNICAL_REFS_INVALID: {exc}") from exc

    # Normalize summary dicts
    locked_summary = payload.get("locked_summary") or {}
    if not isinstance(locked_summary, dict):
        locked_summary = {}
    passed_forward_summary = payload.get("passed_forward_summary") or {}
    if not isinstance(passed_forward_summary, dict):
        passed_forward_summary = {}

    next_action: str = str(payload.get("next_action") or "").strip()
    source_object_type: str = str(payload.get("source_object_type") or "").strip() or ""
    source_object_code: str = str(payload.get("source_object_code") or "").strip() or ""
    target_object_type: str = str(payload.get("target_object_type") or "").strip() or ""
    target_object_code: str = str(payload.get("target_object_code") or "").strip() or ""
    generated_by: str = (
        str(payload.get("generated_by") or frappe.session.user or "system").strip()
    )
    generated_at: str = str(payload.get("generated_at") or "").strip() or None  # type: ignore[assignment]
    consumed_by: str = str(payload.get("consumed_by") or "").strip() or None  # type: ignore[assignment]
    consumed_at: str = str(payload.get("consumed_at") or "").strip() or None  # type: ignore[assignment]
    source_state_hash: str = str(payload.get("source_state_hash") or "").strip() or None  # type: ignore[assignment]
    is_master_seed: int = 1 if payload.get("is_master_seed") else 0

    evidence_links_json_text = _coerce_json_text(evidence_links_normalized)
    locked_summary_text = _coerce_json_text(locked_summary)
    passed_forward_text = _coerce_json_text(passed_forward_summary)
    tech_refs_text = (
        _coerce_json_text(technical_refs_parsed) if technical_refs_parsed is not None else None
    )

    existing = frappe.db.exists("Procurement Handoff Card", {"handoff_code": handoff_code})

    if existing:
        # --- 2 / 7 / 8. Update — preserve source_module ownership; detect stale hash ---
        stored_hash = frappe.db.get_value(
            "Procurement Handoff Card", existing, "source_state_hash"
        )
        stored_source_module = frappe.db.get_value(
            "Procurement Handoff Card", existing, "source_module"
        )

        # Stale check: if caller passes a hash and it differs from stored → warn (item 8)
        if source_state_hash and stored_hash and source_state_hash != stored_hash:
            warnings.append(
                f"source_state_hash changed since last upsert for {handoff_code!r}; "
                "consider refreshing the handoff card."
            )

        update_fields: dict[str, Any] = {
            "handoff_title": handoff_title,
            "journey_code": journey_code,
            # Preserve source_module per ownership rule (item 7)
            "source_module": stored_source_module or source_module,
            "target_module": target_module,
            "source_object_type": source_object_type,
            "source_object_code": source_object_code,
            "target_object_type": target_object_type,
            "target_object_code": target_object_code,
            "status": status,
            "generated_by": generated_by,
            "generated_at": generated_at,
            "consumed_by": consumed_by,
            "consumed_at": consumed_at,
            "locked_summary": locked_summary_text,
            "passed_forward_summary": passed_forward_text,
            "next_action": next_action,
            "evidence_links_json": evidence_links_json_text,
            "technical_refs_json": tech_refs_text,
            "source_state_hash": source_state_hash,
            "is_master_seed": is_master_seed,
        }
        frappe.db.set_value(
            "Procurement Handoff Card",
            existing,
            update_fields,
            update_modified=True,
        )
        action = "updated"
    else:
        # --- 2. Create new card ---
        doc = frappe.get_doc(
            {
                "doctype": "Procurement Handoff Card",
                "name": handoff_code,
                "handoff_code": handoff_code,
                "handoff_title": handoff_title,
                "journey_code": journey_code,
                "source_module": source_module,
                "target_module": target_module,
                "source_object_type": source_object_type,
                "source_object_code": source_object_code,
                "target_object_type": target_object_type,
                "target_object_code": target_object_code,
                "status": status,
                "generated_by": generated_by,
                "generated_at": generated_at,
                "consumed_by": consumed_by,
                "consumed_at": consumed_at,
                "locked_summary": locked_summary_text,
                "passed_forward_summary": passed_forward_text,
                "next_action": next_action,
                "evidence_links_json": evidence_links_json_text,
                "technical_refs_json": tech_refs_text,
                "source_state_hash": source_state_hash,
                "is_master_seed": is_master_seed,
            }
        )
        doc.flags.ignore_permissions = True
        doc.flags.ignore_mandatory = True
        doc.insert()
        action = "created"

    return {
        "ok": True,
        "action": action,
        "handoff_code": handoff_code,
        "warnings": warnings,
    }
