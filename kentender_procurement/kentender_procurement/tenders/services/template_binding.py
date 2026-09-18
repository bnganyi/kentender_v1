# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""TPR-CHG-001 v0.8 §3 "Installed template release" / §4.1 — bind one
immutable code-owned release (`IT-EQUIPMENT-OPEN-V1` 1.1) when the first
Draft is created, and re-verify it at every later decision. Operational
users cannot edit or choose another release; an unavailable or altered
bundle is `TND_TEMPLATE_UNAVAILABLE` and creates nothing."""

from __future__ import annotations

from typing import Any

from kentender_procurement.tender_templates import loader, registry
from kentender_procurement.tenders.services.errors import fail


def bind() -> dict[str, Any]:
	"""The exact installed release a new Version binds to."""
	resolved = registry.resolve(loader.TEMPLATE_KEY, loader.TEMPLATE_VERSION)
	metadata = loader.metadata()
	return {
		"template_release_id": resolved["registry"],
		"template_key": resolved["template_key"],
		"template_version": resolved["template_version"],
		"display_name": resolved["display_name"],
		"official_source_digest": resolved["official_source_digest"],
		"bundle_digest": resolved["bundle_digest"],
		"official_source_title": metadata.get("official_source_title") or loader.source_record().get("official_title", ""),
		"supported_reservation_categories": list(metadata.get("supported_reservation_categories") or ()),
		"handoff_version": metadata.get("handoff_version"),
	}


def verify(version) -> list[str]:
	"""Problems if the bundle no longer matches the digests this Version bound."""
	try:
		resolved = registry.resolve(loader.TEMPLATE_KEY, loader.TEMPLATE_VERSION)
	except Exception as exc:  # TendersError
		return [f"Template unavailable: {exc}"]
	problems = []
	if resolved["registry"] != version.template_release_id:
		problems.append("The installed template release differs from the one this Version bound.")
	if resolved["bundle_digest"] != version.bundle_digest or resolved["official_source_digest"] != version.official_source_digest:
		problems.append("The installed template release no longer matches the digests this Version bound.")
	return problems


def require_available() -> dict[str, Any]:
	try:
		return bind()
	except Exception as exc:
		if getattr(exc, "code", "") == "TND_TEMPLATE_UNAVAILABLE":
			raise
		fail("TND_TEMPLATE_UNAVAILABLE", detail={"reason": str(exc)})
		return {}  # unreachable
