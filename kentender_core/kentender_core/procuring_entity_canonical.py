# Copyright (c) 2026, KenTender and contributors
"""Canonical Procuring Entity references.

WORKS master, Budget, and PP2 packs use **PE-MOH** as the Ministry of Health
procuring entity code. Older DIA/core seeds used **MOH** (same display name,
different DocType row).

Use ``normalize_procuring_entity()`` at write boundaries to migrate legacy
link values. Business rules (budget matching, reservations) must compare exact
docnames after normalization — never treat MOH and PE-MOH as interchangeable
aliases.
"""

from __future__ import annotations

import frappe

# Canonical docname for Ministry of Health (pack: PE-MOH).
CANONICAL_MOH_ENTITY = "PE-MOH"

# Deprecated docname from early core seeds — do not use for new records.
LEGACY_MOH_ENTITY = "MOH"


def normalize_procuring_entity(entity: str | None) -> str | None:
	"""Return the canonical Procuring Entity docname for *entity* when applicable."""
	pe = (entity or "").strip()
	if not pe:
		return None
	if pe == LEGACY_MOH_ENTITY and frappe.db.exists("Procuring Entity", CANONICAL_MOH_ENTITY):
		return CANONICAL_MOH_ENTITY
	return pe


def moh_entity_docname() -> str:
	"""Docname to use when seeding or scoping MOH data."""
	if frappe.db.exists("Procuring Entity", CANONICAL_MOH_ENTITY):
		return CANONICAL_MOH_ENTITY
	if frappe.db.exists("Procuring Entity", LEGACY_MOH_ENTITY):
		return LEGACY_MOH_ENTITY
	return CANONICAL_MOH_ENTITY
