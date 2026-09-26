# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Release selection and lifecycle enforcement for consumers (STD-TPL-IMP-001
v1.0 §9; TPR-CHG-001 v0.11 §5.3; owner rulings R3, R12; owner decision OD5).

| Purpose            | Available, On | Available, Off            | Superseded                      | Withdrawn |
|--------------------|---------------|---------------------------|---------------------------------|-----------|
| new_binding        | yes           | STD_RELEASE_NOT_AVAILABLE | STD_RELEASE_NOT_AVAILABLE       | STD_RELEASE_NOT_AVAILABLE |
| continue / publish | yes           | yes, while integrity + renderer | yes, while integrity + renderer | STD_RELEASE_WITHDRAWN |
| read_published     | yes           | yes                       | yes                             | yes (with the withdrawal notice) |

OD5: the site switch decides whether a new Tender may start on a release;
switching it Off never strands a Tender already started on it. Every
non-read purpose re-verifies the installed runtime assets and the renderer
adapter. Nothing here ever rebinds a Tender to another release.
"""

from __future__ import annotations

from typing import Any

import frappe

from kentender_procurement.std_templates.compiler import compatibility as compat
from kentender_procurement.std_templates.compiler.errors import fail
from kentender_procurement.std_templates.services import runtime

DOCTYPE = "Installed STD Release"
PURPOSES = ("new_binding", "continue", "publication", "read_published")


def binding_facts(release) -> dict[str, Any]:
	return {
		"template_release_id": release.name,
		"template_key": release.template_key,
		"template_release": release.template_release,
		"display_name": release.display_name,
		"product_profile_id": release.product_profile_id,
		"renderer_profile_id": release.renderer_profile_id,
		"supported_renderer_version": release.supported_renderer_version,
		"official_source_digest": release.official_source_digest,
		"bundle_digest": release.bundle_digest,
		"lifecycle_status": release.lifecycle_status,
		"site_switch": release.site_switch,
	}


def available_release(template_key: str):
	"""The one switched-on Available release of a template family for a new
	Tender."""
	names = frappe.get_all(
		DOCTYPE,
		filters={"template_key": template_key, "lifecycle_status": "Available", "site_switch": "On", "integrity_status": "Verified"},
		pluck="name",
		order_by="installed_at desc",
	)
	if not names:
		fail("STD_RELEASE_NOT_AVAILABLE", identity=template_key)
	if len(names) > 1:
		fail("STD_RELEASE_NOT_AVAILABLE", "More than one release of this Tender format is switched on; switch one off or supersede it.", identity=template_key)
	return runtime.release_doc(names[0])


def require(release_id: str, purpose: str) -> dict[str, Any]:
	"""Enforce the lifecycle matrix above; returns the binding facts plus any
	notice the consumer must show."""
	if purpose not in PURPOSES:
		raise ValueError(purpose)
	release = runtime.release_doc(release_id)
	status = release.lifecycle_status
	notice = ""
	if purpose == "read_published":
		if status == "Withdrawn":
			notice = "This Tender format was withdrawn after publication. The published documents and Bid definition are unchanged and remain the record."
		elif status == "Superseded":
			notice = "A newer release of this Tender format exists; this Tender keeps the release it was published with."
		return {**binding_facts(release), "notice": notice}
	if purpose == "new_binding" and (status != "Available" or release.site_switch != "On"):
		fail("STD_RELEASE_NOT_AVAILABLE", identity=release.name)
	if status == "Withdrawn":
		fail("STD_RELEASE_WITHDRAWN", identity=release.name)
	result = runtime.verify_integrity(release.name, scope="runtime")
	if not result["ok"]:
		fail("STD_RELEASE_INTEGRITY_FAILED", "; ".join(result["problems"]), identity=release.name)
	health = runtime.renderer_health(release)
	if not health["ok"]:
		fail("STD_RENDERER_UNSUPPORTED", identity=f"{release.renderer_profile_id}@{release.supported_renderer_version}", detail={"health": health})
	if status == "Superseded":
		notice = "This Tender format has been superseded. This Tender may continue on it while its integrity and renderer checks pass; new Tenders use the current release."
	return {**binding_facts(release), "notice": notice}


def check_compatibility(release_id: str, facts: dict[str, Any]) -> dict[str, Any]:
	"""`CheckSTDReleaseCompatibility` — deterministic supported/rejected
	result for an authorised Requisition or Tender input."""
	release = runtime.release_doc(release_id)
	profile = runtime.asset_json(release, "06_runtime/product_profile.json")
	checks = compat.evaluate(profile, facts)
	failed = compat.first_failure(checks)
	return {"supported": failed is None, "checks": checks, "first_failure": failed, "template_release_id": release.name}
