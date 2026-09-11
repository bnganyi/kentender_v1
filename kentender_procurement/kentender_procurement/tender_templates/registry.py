# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""TPR-CHG-001 v0.6 §6.3 / STD-TPL-IMP-001 §12 — the read-only
`Supported Tender Template` registry.

`install()` is the one writer (idempotent; wired into `after_migrate`): it
verifies the bundle and official-source digests, then creates or updates the
single registry row for `IT-EQUIPMENT-OPEN-V1 / 1.1`, marking it available
for new Tenders only when every check passes (TPR-AC-032/033). `resolve()`
re-verifies the live bundle on every call, so a bundle altered after
installation is refused for a new binding (SMOKE-14) even before the next
migrate rewrites the row. No Desk action edits the row (TPR-AC-034; the
doctype has no write DocPerm and its controller refuses saves without the
installer flag).
"""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import now_datetime

from kentender_procurement.tender_templates import loader

AVAILABLE = "Available for new Tenders"
UNAVAILABLE = "Unavailable"
HISTORICAL = "Historical only"

REGISTRY_DOCTYPE = "Supported Tender Template"


def registry_name(template_key: str = loader.TEMPLATE_KEY, template_version: str = loader.TEMPLATE_VERSION) -> str:
	return f"{template_key}-{template_version}"


def install(*, bundle_root: str = loader.DEFAULT_BUNDLE_ROOT, commit: bool = False) -> dict[str, Any]:
	"""Create or update the one registry row from the code-owned bundle."""
	meta = loader.metadata(bundle_root)
	source = loader.source_record(bundle_root)
	verification = loader.verify(bundle_root)
	name = registry_name(meta["template_key"], meta["template_version"])
	values = {
		"template_key": meta["template_key"],
		"template_version": meta["template_version"],
		"display_name": meta["display_name"],
		"supported_category": meta.get("supported_category", ""),
		"supported_method": meta.get("supported_method", ""),
		"official_source_title": source.get("official_title", ""),
		"official_source_digest": source.get("sha256", ""),
		"bundle_digest": verification.bundle_digest,
		"availability": AVAILABLE if verification.ok else UNAVAILABLE,
		"last_verified_at": now_datetime(),
		"verification_note": verification.summary(),
	}
	created = False
	if frappe.db.exists(REGISTRY_DOCTYPE, name):
		doc = frappe.get_doc(REGISTRY_DOCTYPE, name)
		changed = any((doc.get(k) or "") != (v or "") for k, v in values.items() if k not in ("last_verified_at",))
		for k, v in values.items():
			doc.set(k, v)
		doc.flags.kt_template_install = True
		doc.save(ignore_permissions=True)
	else:
		doc = frappe.get_doc({"doctype": REGISTRY_DOCTYPE, "installed_at": now_datetime(), **values})
		doc.flags.kt_template_install = True
		doc.insert(ignore_permissions=True)
		created = True
		changed = True
	if commit:
		frappe.db.commit()
	return {"ok": verification.ok, "name": doc.name, "created": created, "changed": changed, "availability": doc.availability, "bundle_digest": verification.bundle_digest, "note": verification.summary()}


def after_migrate() -> None:
	"""Idempotent hook: two migrates leave exactly one row (TPR-AC-032)."""
	if frappe.db.exists("DocType", REGISTRY_DOCTYPE):
		install()


def resolve(template_key: str = loader.TEMPLATE_KEY, template_version: str = loader.TEMPLATE_VERSION, *, bundle_root: str = loader.DEFAULT_BUNDLE_ROOT) -> dict[str, Any]:
	"""The exact installed release a new Tender binds to — or
	`TPR_TEMPLATE_UNAVAILABLE`, creating nothing (§11.3)."""
	from kentender_procurement.tender_preparation.services.errors import fail

	name = registry_name(template_key, template_version)
	row = frappe.db.get_value(REGISTRY_DOCTYPE, name, ["name", "availability", "bundle_digest", "official_source_digest", "display_name"], as_dict=True)
	if not row or row.availability != AVAILABLE:
		fail("TPR_TEMPLATE_UNAVAILABLE", detail={"template": name, "availability": row.availability if row else "not installed"})
	verification = loader.verify(bundle_root)
	if not verification.ok or verification.bundle_digest != row.bundle_digest or verification.source_digest != row.official_source_digest:
		fail("TPR_TEMPLATE_UNAVAILABLE", "The installed template bundle no longer matches its registered digests.", detail={"template": name, "problems": verification.summary()})
	return {
		"registry": row.name, "template_key": template_key, "template_version": template_version, "display_name": row.display_name,
		"official_source_digest": row.official_source_digest, "bundle_digest": row.bundle_digest,
	}
