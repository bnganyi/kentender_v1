# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The installed-release runtime (STD-TPL-IMP-001 v1.0 §§6–8).

Everything here reads the exact installed private Files and re-checks each
file's SHA-256 against its immutable asset row before use, so a changed byte
is `STD_RELEASE_INTEGRITY_FAILED`, never silently rendered. The production
adapter over `CompilePublishedBidDefinition` loads the installed runtime
assets and calls the same pure compiler the curation CLI calls.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

import frappe
from frappe.utils import now_datetime

from kentender_procurement.std_templates.compiler import assets as release_assets
from kentender_procurement.std_templates.compiler import projection as proj
from kentender_procurement.std_templates.compiler.definition import compile_published_bid_definition
from kentender_procurement.std_templates.compiler.errors import fail
from kentender_procurement.std_templates.release import bundle
from kentender_procurement.std_templates.renderers import registry
from kentender_procurement.std_templates.renderers.document import MASTER_PATHS

DOCTYPE = "Installed STD Release"

#: Assets every runtime use needs (the rule files and document masters).
RUNTIME_PATHS: tuple[str, ...] = tuple(release_assets.ASSET_FILES.values()) + tuple(MASTER_PATHS.values())


def release_doc(release_id: str):
	if not release_id or not frappe.db.exists(DOCTYPE, release_id):
		fail("STD_RELEASE_NOT_FOUND", identity=str(release_id or ""))
	return frappe.get_doc(DOCTYPE, release_id)


def _file_bytes(file_name: str) -> bytes:
	from kentender_core.services.file_integrity import read_bytes

	return read_bytes(file_name)  # exact bytes (get_file decodes some binary files)


def asset_bytes(release, relative_path: str) -> bytes:
	"""One installed asset, digest-checked."""
	row = next((a for a in release.assets if a.relative_path == relative_path), None)
	if not row:
		fail("STD_RELEASE_INTEGRITY_FAILED", "The installed release has no such asset.", identity=relative_path)
	try:
		content = _file_bytes(row.private_file_id)
	except Exception:
		_mark_failed(release, f"Asset {relative_path} could not be read.")
		fail("STD_RELEASE_INTEGRITY_FAILED", identity=relative_path)
	if hashlib.sha256(content).hexdigest() != row.sha256_digest:
		_mark_failed(release, f"Asset {relative_path} no longer matches its installed digest.")
		fail("STD_RELEASE_INTEGRITY_FAILED", identity=relative_path)
	return content


def asset_json(release, relative_path: str) -> Any:
	return json.loads(asset_bytes(release, relative_path).decode("utf-8"))


def _mark_failed(release, problem: str) -> None:
	if release.integrity_status == "Failed" and release.integrity_problem == problem:
		return
	release.integrity_status = "Failed"
	release.integrity_problem = problem
	release.last_verified_at = now_datetime()
	release.flags.kt_std_verify = True
	release.save(ignore_permissions=True)
	from kentender_core.services.audit_event_service import log_audit_event

	log_audit_event(event_type="STD Release", entity="STD Templates", document_type=DOCTYPE, document_name=release.name, action="Integrity failed", metadata={"problem": problem})


def verify_integrity(release_id: str, *, scope: str = "runtime") -> dict[str, Any]:
	"""Re-hash installed assets (`runtime` = rule files and masters; `full` =
	every asset plus the bundle digest) and record the result."""
	release = release_doc(release_id)
	rows = release.assets if scope == "full" else [a for a in release.assets if a.relative_path in RUNTIME_PATHS]
	problems: list[str] = []
	for row in rows:
		try:
			content = _file_bytes(row.private_file_id)
		except Exception:
			problems.append(f"Asset {row.relative_path} could not be read.")
			continue
		if hashlib.sha256(content).hexdigest() != row.sha256_digest:
			problems.append(f"Asset {row.relative_path} no longer matches its installed digest.")
	if scope == "full" and not problems:
		if bundle.bundle_digest([(a.relative_path, a.sha256_digest) for a in release.assets]) != release.bundle_digest:
			problems.append("The installed asset inventory no longer reproduces the bundle digest.")
	now = now_datetime()
	release.integrity_status = "Failed" if problems else "Verified"
	release.integrity_problem = "; ".join(problems)
	release.last_verified_at = now
	if not problems:
		release.last_successful_verification_at = now
	release.flags.kt_std_verify = True
	release.save(ignore_permissions=True)
	return {"ok": not problems, "release_id": release.name, "scope": scope, "checked": len(rows), "problems": problems}


def installed_assets(release, *, digest_basis: str = "installed") -> release_assets.ReleaseAssets:
	"""The exact installed runtime assets as the compiler's input.
	`digest_basis="input"` binds the input bundle digest instead of the full
	bundle digest — only the golden-vector parity proof uses it (ruling R13)."""
	if release.integrity_status == "Failed":
		fail("STD_RELEASE_INTEGRITY_FAILED", release.integrity_problem or "", identity=release.name)
	files = {name: asset_bytes(release, rel) for name, rel in release_assets.ASSET_FILES.items()}
	return release_assets.load(
		files,
		official_source_digest=release.official_source_digest,
		bundle_digest=release.input_bundle_digest if digest_basis == "input" else release.bundle_digest,
	)


def renderer_capabilities(release) -> dict[str, Any]:
	return registry.bid_workspace_capabilities(release.renderer_profile_id, release.supported_renderer_version)


def compile_published_bid_definition_for(release_id: str, projection: dict[str, Any], *, digest_basis: str = "installed") -> dict[str, Any]:
	"""Production adapter over the shared `CompilePublishedBidDefinition`."""
	release = release_doc(release_id)
	return compile_published_bid_definition(installed_assets(release, digest_basis=digest_basis), projection, renderer_capabilities=renderer_capabilities(release))


def masters(release) -> dict[str, str]:
	return {name: asset_bytes(release, rel).decode("utf-8") for name, rel in MASTER_PATHS.items()}


def document_constants(release) -> dict[str, Any]:
	return asset_json(release, release_assets.ASSET_FILES["product_profile"])["document_constants"]


def render_documents(release_id: str, projection: dict[str, Any], *, with_pdf: bool = False, footer_center: str = "") -> dict[str, Any]:
	"""`RenderSTDDocument` — the Invitation and issued Tender from the exact
	installed masters through the registered adapter (no fallback)."""
	release = release_doc(release_id)
	adapter = registry.document_adapter(release.renderer_profile_id, release.supported_renderer_version)
	context = proj.document_context(projection, document_constants(release))
	release_masters = masters(release)
	out = adapter.render_html(release_masters, context)
	if with_pdf:
		css = release_masters["print.css"]
		out["invitation_pdf"] = adapter.render_pdf(out["invitation_html"], css)
		out["issued_tender_pdf"] = adapter.render_pdf(out["issued_tender_html"], css, footer_center=footer_center)
	return out


def render_context(release_id: str, context: dict[str, Any], *, with_pdf: bool = False, footer_center: str = "") -> dict[str, Any]:
	"""`RenderSTDDocument` for a consumer that already holds the canonical
	render context (Tenders' serializer): the exact installed masters of
	`release_id` through its registered adapter, no fallback."""
	release = release_doc(release_id)
	adapter = registry.document_adapter(release.renderer_profile_id, release.supported_renderer_version)
	release_masters = masters(release)
	out = adapter.render_html(release_masters, context)
	if with_pdf:
		css = release_masters["print.css"]
		out["invitation_pdf"] = adapter.render_pdf(out["invitation_html"], css)
		out["issued_tender_pdf"] = adapter.render_pdf(out["issued_tender_html"], css, footer_center=footer_center)
	return out


def renderer_health(release) -> dict[str, Any]:
	return registry.health(release.renderer_profile_id, release.supported_renderer_version)


def bid_work_status(release_id: str, *, verify: bool = False) -> dict[str, Any]:
	"""The bound release's state for Bid Submission (BDS-CHG-001 v0.8 §4.4.4,
	plan D3/D4). A read, never a gate: it reports lifecycle, site switch and
	integrity/renderer health and leaves the decision to the consumer. The
	recorded integrity result is used unless `verify` re-hashes the runtime
	assets (commands verify; page reads do not write)."""
	if not release_id or not frappe.db.exists(DOCTYPE, release_id):
		return {"release_id": str(release_id or ""), "lifecycle": "Unknown", "site_switch": "", "integrity_ok": False, "renderer_ok": False, "problem": "The bound Tender format is not installed on this site."}
	release = release_doc(release_id)
	if verify:
		result = verify_integrity(release.name, scope="runtime")
		integrity_ok, problem = result["ok"], "; ".join(result["problems"])
	else:
		integrity_ok, problem = release.integrity_status != "Failed", (release.integrity_problem or "") if release.integrity_status == "Failed" else ""
	renderer_ok = bool(renderer_health(release)["ok"])
	if integrity_ok and not renderer_ok:
		problem = f"The renderer {release.renderer_profile_id}@{release.supported_renderer_version} is not available."
	return {"release_id": release.name, "lifecycle": release.lifecycle_status, "site_switch": release.site_switch, "integrity_ok": bool(integrity_ok), "renderer_ok": renderer_ok, "problem": problem}
