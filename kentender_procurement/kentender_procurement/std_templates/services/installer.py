# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""`InstallApprovedSTDRelease` (STD-TPL-IMP-001 v1.0 §5, as changed by owner
decision OD5 of 26 Sep 2026).

Deployment-only. The package (a directory or a .zip of the controlled pack)
is copied into an isolated staging directory; paths outside the root,
symbolic links, duplicates and undeclared or missing files are refused;
every asset digest, the bundle digest, the manifest digest, the constituent
digests and the input digest are recalculated; the runtime assets are
validated against the released vocabulary; the renderer adapter must be
registered for the exact profile and version; an owner decision, when
supplied, must name this exact release, bundle and manifest.

Owner decision OD5: "Template release is purely an on and off switch on an
affected site." A release that passes integrity is installed **Available**
with its site switch **On** (or Off when asked); gate results and any owner
decision are recorded evidence only and never block use. Any integrity
failure installs nothing. Private immutable Files and registry rows are
written in one transaction; a failure rolls the rows back and removes the
files already written. The same exact bytes install idempotently; a
different byte under an existing identity fails.
"""

from __future__ import annotations

import json
import os
import shutil
import tempfile
import zipfile
from pathlib import Path
from typing import Any

import frappe
from frappe.utils import now_datetime

from kentender_procurement.std_templates.compiler import assets as release_assets
from kentender_procurement.std_templates.compiler.canonical import sha256_bytes
from kentender_procurement.std_templates.compiler.errors import STDTemplateError, fail
from kentender_procurement.std_templates.release import bundle, gates, manifest as manifest_module
from kentender_procurement.std_templates.renderers import registry

DOCTYPE = "Installed STD Release"
AUDIT_EVENT = "STD Release"
JSON_FIELDS = (
	"supported_use_summary", "rejected_use_summary", "document_summary", "response_summary", "evaluation_summary",
	"contract_summary", "reservation_support", "verification_results", "blockers", "gate_results", "tool_versions",
)


def dump(value: Any) -> str:
	return json.dumps(value, sort_keys=True, ensure_ascii=False)


def load_json(value: Any) -> Any:
	"""Read a JSON projection column (stored as canonical text)."""
	if value is None or value == "":
		return None
	return json.loads(value) if isinstance(value, str) else value


# ---------------------------------------------------------------------------
# staging
# ---------------------------------------------------------------------------


def _stage(package: str, staging: Path) -> Path:
	source = Path(package)
	root = staging / "pack"
	if source.is_file() and source.suffix == ".zip":
		root.mkdir()
		with zipfile.ZipFile(source) as archive:
			names = [n for n in archive.namelist() if not n.endswith("/")]
			prefixes = {n.split("/", 1)[0] for n in names}
			strip = prefixes.pop() + "/" if len(prefixes) == 1 and all("/" in n for n in names) else ""
			seen: set[str] = set()
			for info in archive.infolist():
				if info.is_dir():
					continue
				if (info.external_attr >> 16) & 0o170000 == 0o120000:
					fail("STD_RELEASE_INTEGRITY_FAILED", "The package contains a symbolic link.", identity=info.filename)
				rel = bundle.safe_relative(info.filename[len(strip):] if strip else info.filename)
				if rel in seen:
					fail("STD_RELEASE_INTEGRITY_FAILED", "The package contains a duplicate path.", identity=rel)
				seen.add(rel)
				target = root / rel
				target.parent.mkdir(parents=True, exist_ok=True)
				target.write_bytes(archive.read(info))
	elif source.is_dir():
		for dirpath, dirnames, filenames in os.walk(source, followlinks=False):
			for name in dirnames + filenames:
				if os.path.islink(os.path.join(dirpath, name)):
					fail("STD_RELEASE_INTEGRITY_FAILED", "The package contains a symbolic link.", identity=os.path.relpath(os.path.join(dirpath, name), source))
		shutil.copytree(source, root, symlinks=True, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
	else:
		fail("STD_RELEASE_NOT_FOUND", "The release package does not exist.", identity=str(package))
	return root


# ---------------------------------------------------------------------------
# verification (pure checks on the staged package)
# ---------------------------------------------------------------------------


def verify_package(root: Path) -> dict[str, Any]:
	"""Recalculate and cross-check every digest; return the verified facts.
	Raises `STD_RELEASE_INTEGRITY_FAILED` / `STD_DEFINITION_INVALID` /
	`STD_RENDERER_UNSUPPORTED` on the first failure."""
	manifest_path = root / bundle.MANIFEST_PATH
	if not manifest_path.is_file():
		fail("STD_RELEASE_INTEGRITY_FAILED", "The package has no release manifest.", identity=bundle.MANIFEST_PATH)
	manifest_bytes = manifest_path.read_bytes()
	try:
		manifest = json.loads(manifest_bytes.decode("utf-8"))
	except (UnicodeDecodeError, json.JSONDecodeError):
		fail("STD_RELEASE_INTEGRITY_FAILED", "The release manifest is not valid JSON.", identity=bundle.MANIFEST_PATH)
		raise
	manifest_module.validate_shape(manifest)
	entries = bundle.inventory(root)
	declared = {a["path"]: a for a in manifest["assets"]}
	actual = dict(entries)
	undeclared = sorted(set(actual) - set(declared))
	if undeclared:
		fail("STD_RELEASE_INTEGRITY_FAILED", "The package contains an undeclared file.", identity=undeclared[0])
	missing = sorted(set(declared) - set(actual))
	if missing:
		fail("STD_RELEASE_INTEGRITY_FAILED", "A declared asset is missing from the package.", identity=missing[0])
	for rel, digest in entries:
		row = declared[rel]
		if row["sha256"] != digest:
			fail("STD_RELEASE_INTEGRITY_FAILED", "An asset digest differs from the manifest.", identity=rel)
		if int(row["byte_size"]) != (root / rel).stat().st_size:
			fail("STD_RELEASE_INTEGRITY_FAILED", "An asset size differs from the manifest.", identity=rel)
	if bundle.bundle_digest(entries) != manifest["bundle_digest"]:
		fail("STD_RELEASE_INTEGRITY_FAILED", "The bundle digest differs from the manifest.", identity="bundle_digest")
	if bundle.bundle_digest(bundle.input_entries(entries)) != manifest["input_bundle_digest"]:
		fail("STD_RELEASE_INTEGRITY_FAILED", "The input bundle digest differs from the manifest.", identity="input_bundle_digest")
	for field, rel in (
		("official_source_digest", "01_source/ppra_goods_std_official.pdf"),
		("validation_report_digest", "05_review/validation_report.json"),
		("release_gates_digest", "05_review/release_gates.json"),
		("release_change_report_digest", "05_review/release_change_report.json"),
		("product_profile_digest", release_assets.ASSET_FILES["product_profile"]),
		("response_rules_digest", release_assets.ASSET_FILES["response_rules"]),
		("downstream_rules_digest", release_assets.ASSET_FILES["downstream_rules"]),
		("addendum_identity_rules_digest", release_assets.ASSET_FILES["addendum_identity_rules"]),
	):
		if actual.get(rel) != manifest[field]:
			fail("STD_RELEASE_INTEGRITY_FAILED", f"{field} differs from the asset it names.", identity=field)
	files = {name: (root / rel).read_bytes() for name, rel in release_assets.ASSET_FILES.items()}
	loaded = release_assets.load(files, official_source_digest=manifest["official_source_digest"], bundle_digest=manifest["bundle_digest"])
	env = loaded.envelope
	for key in release_assets.ENVELOPE:
		if key in manifest and manifest[key] != env[key]:
			fail("STD_RELEASE_INTEGRITY_FAILED", f"The manifest {key} differs from the runtime assets.", identity=key)
	if not registry.is_registered(env["renderer_profile_id"], env["supported_renderer_version"]):
		fail("STD_RENDERER_UNSUPPORTED", "No renderer adapter is registered for this release.", identity=f"{env['renderer_profile_id']}@{env['supported_renderer_version']}")
	validation = json.loads((root / "05_review/validation_report.json").read_text(encoding="utf-8"))
	if validation.get("summary", {}).get("blocking"):
		fail("STD_RELEASE_INTEGRITY_FAILED", "The release validator reported a Failed check.", identity="validation_report")
	gate_doc = json.loads((root / "05_review/release_gates.json").read_text(encoding="utf-8"))
	gate_rows = gate_doc["gates"]
	if {g["gate_id"] for g in gate_rows} != set(gates.GATES):
		fail("STD_RELEASE_GATE_INCOMPLETE", "The release gates file does not list every mandatory gate.", identity="release_gates")
	decision = None
	decision_bytes = None
	decision_path = root / bundle.OWNER_DECISION_PATH
	manifest_digest = sha256_bytes(manifest_bytes)
	if decision_path.is_file():
		decision_bytes = decision_path.read_bytes()
		decision = json.loads(decision_bytes.decode("utf-8"))
		problems = manifest_module.validate_owner_decision(decision, manifest, manifest_digest)
		if problems:
			fail("STD_RELEASE_INTEGRITY_FAILED", problems[0], identity=bundle.OWNER_DECISION_PATH)
	review_path = root / bundle.REVIEW_RECORD_PATH
	return {
		"manifest": manifest,
		"manifest_bytes": manifest_bytes,
		"manifest_digest": manifest_digest,
		"entries": entries,
		"assets": loaded,
		"gate_rows": gate_rows,
		"decision": decision,
		"decision_bytes": decision_bytes,
		"review_bytes": review_path.read_bytes() if review_path.is_file() else None,
	}


def _evidence_rows(verified: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
	"""The curation verification rows and blockers, kept as evidence (OD5).
	The live projection replaces the owner-approval row with the site switch
	and derives what blocks use from the switch and integrity."""
	manifest = verified["manifest"]
	return [dict(r) for r in manifest["verification_results"]], [dict(b) for b in manifest["blockers"]]


# ---------------------------------------------------------------------------
# storage
# ---------------------------------------------------------------------------


def _file(release_name: str, rel: str, content: bytes, written: list[str]) -> str:
	doc = frappe.get_doc(
		{
			"doctype": "File",
			"file_name": rel.replace("/", "__"),
			"is_private": 1,
			"attached_to_doctype": DOCTYPE,
			"attached_to_name": release_name,
			"content": content,
		}
	)
	doc.flags.ignore_permissions = True
	doc.insert(ignore_permissions=True)
	written.append(doc.get_full_path())
	return doc.name


def _audit(action: str, name: str, metadata: dict[str, Any]) -> None:
	from kentender_core.services.audit_event_service import log_audit_event

	log_audit_event(event_type=AUDIT_EVENT, entity="STD Templates", document_type=DOCTYPE, document_name=name, action=action, metadata=metadata)


def _existing(manifest: dict[str, Any]) -> dict[str, Any] | None:
	row = frappe.db.get_value(DOCTYPE, manifest["release_id"], ["name", "bundle_digest", "manifest_digest", "lifecycle_status", "owner_decision"], as_dict=True)
	if row:
		return row
	clash = frappe.db.get_value(DOCTYPE, {"template_key": manifest["template_key"], "template_release": manifest["template_release"]}, "name")
	if clash:
		fail("STD_RELEASE_INTEGRITY_FAILED", "Another installed release already uses this template key and release.", identity=clash)
	return None


def install_approved_std_release(package: str, *, installed_by: str, site_switch: str = "On") -> dict[str, Any]:
	"""Install (or idempotently confirm) one exact release package. The caller
	owns the transaction; `install()` below is the deployment entry point."""
	staging = Path(tempfile.mkdtemp(prefix="kt-std-release-"))
	written: list[str] = []
	try:
		root = _stage(package, staging)
		verified = verify_package(root)
		manifest = verified["manifest"]
		if site_switch not in ("On", "Off"):
			raise ValueError("site_switch must be On or Off")
		existing = _existing(manifest)
		now = now_datetime()
		if existing:
			if existing.bundle_digest != manifest["bundle_digest"] or existing.manifest_digest != verified["manifest_digest"]:
				fail("STD_RELEASE_INTEGRITY_FAILED", "A different byte was presented under an existing release identity.", identity=manifest["release_id"])
			doc = frappe.get_doc(DOCTYPE, existing.name)
			recorded = False
			if verified["decision"] and not doc.owner_decision:
				doc.owner_decision = verified["decision"]["decision"]
				doc.owner_approved_by = verified["decision"]["decided_by"]
				doc.owner_approved_at = verified["decision"]["decided_at"]
				doc.owner_decision_record = verified["decision"]["decision_record"]
				doc.owner_decision_file = _file(doc.name, bundle.OWNER_DECISION_PATH, verified["decision_bytes"], written)
				doc.flags.kt_std_bind_decision = True
				doc.save(ignore_permissions=True)
				recorded = True
				_audit("Owner decision recorded", doc.name, {"decision": doc.owner_decision})
			return {"ok": True, "release_id": doc.name, "created": False, "decision_recorded": recorded, "lifecycle_status": doc.lifecycle_status, "site_switch": doc.site_switch, "bundle_digest": doc.bundle_digest, "manifest_digest": doc.manifest_digest}

		rows, blockers = _evidence_rows(verified)
		doc = frappe.get_doc(
			{
				"doctype": DOCTYPE,
				"release_id": manifest["release_id"],
				"template_key": manifest["template_key"],
				"template_release": manifest["template_release"],
				"display_name": manifest["display_name"],
				"lifecycle_status": "Available",
				"site_switch": site_switch,
				"switched_by": installed_by,
				"switched_at": now,
				"product_profile_id": manifest["product_profile_id"],
				"renderer_profile_id": manifest["renderer_profile_id"],
				"supported_renderer_version": manifest["supported_renderer_version"],
				"official_source_title": manifest["official_source_title"],
				"official_source_digest": manifest["official_source_digest"],
				"source_retrieved_at": manifest["source_retrieved_at"],
				"source_checked_by": manifest["source_checked_by"],
				"source_checked_at": manifest["source_checked_at"],
				"source_check_outcome": manifest["source_check_outcome"],
				"bundle_digest": manifest["bundle_digest"],
				"manifest_digest": verified["manifest_digest"],
				"input_bundle_digest": manifest["input_bundle_digest"],
				"validation_report_digest": manifest["validation_report_digest"],
				"release_gates_digest": manifest["release_gates_digest"],
				"release_change_report_digest": manifest["release_change_report_digest"],
				"product_profile_digest": manifest["product_profile_digest"],
				"response_rules_digest": manifest["response_rules_digest"],
				"downstream_rules_digest": manifest["downstream_rules_digest"],
				"addendum_identity_rules_digest": manifest["addendum_identity_rules_digest"],
				"owner_decision": (verified["decision"] or {}).get("decision", ""),
				"owner_approved_by": (verified["decision"] or {}).get("decided_by", ""),
				"owner_approved_at": (verified["decision"] or {}).get("decided_at", ""),
				"owner_decision_record": (verified["decision"] or {}).get("decision_record", ""),
				"installed_by": installed_by,
				"installed_at": now,
				"repository_commit": manifest["repository_commit"],
				"built_by": manifest["built_by"],
				"built_at": manifest["built_at"],
				"integrity_status": "Verified",
				"last_verified_at": now,
				"last_successful_verification_at": now,
				"supported_use_summary": manifest["supported_use"],
				"rejected_use_summary": manifest["rejected_use"],
				"document_summary": manifest["document_summary"],
				"response_summary": manifest["response_summary"],
				"evaluation_summary": manifest["evaluation_summary"],
				"contract_summary": manifest["contract_summary"],
				"reservation_support": manifest["reservation_support"],
				"verification_results": rows,
				"blockers": blockers,
				"gate_results": verified["gate_rows"],
				"tool_versions": manifest["tool_versions"],
			}
		)
		for field in JSON_FIELDS:
			doc.set(field, dump(doc.get(field)))
		doc.flags.kt_std_install = True
		doc.insert(ignore_permissions=True)
		by_path = {a["path"]: a for a in manifest["assets"]}
		asset_rows = []
		for rel, digest in verified["entries"]:
			content = (root / rel).read_bytes()
			file_name = _file(doc.name, rel, content, written)
			asset_rows.append(
				{
					"relative_path": rel,
					"asset_role": by_path[rel]["asset_role"],
					"mime_type": by_path[rel]["mime_type"],
					"byte_size": len(content),
					"sha256_digest": digest,
					"private_file_id": file_name,
				}
			)
		extras = {"manifest_file": _file(doc.name, bundle.MANIFEST_PATH, verified["manifest_bytes"], written)}
		if verified["review_bytes"] is not None:
			extras["review_record_file"] = _file(doc.name, bundle.REVIEW_RECORD_PATH, verified["review_bytes"], written)
		if verified["decision_bytes"] is not None:
			extras["owner_decision_file"] = _file(doc.name, bundle.OWNER_DECISION_PATH, verified["decision_bytes"], written)
		_attach_assets(doc.name, asset_rows, extras)
		_audit(
			"Installed",
			doc.name,
			{"template_key": doc.template_key, "template_release": doc.template_release, "site_switch": site_switch, "bundle_digest": doc.bundle_digest, "manifest_digest": doc.manifest_digest, "assets": len(asset_rows)},
		)
		return {"ok": True, "release_id": doc.name, "created": True, "lifecycle_status": "Available", "site_switch": site_switch, "bundle_digest": doc.bundle_digest, "manifest_digest": doc.manifest_digest, "assets": len(asset_rows)}
	except Exception:
		for path in written:
			try:
				os.remove(path)
			except OSError:
				pass
		raise
	finally:
		shutil.rmtree(staging, ignore_errors=True)


def _attach_assets(name: str, asset_rows: list[dict[str, Any]], extras: dict[str, str]) -> None:
	"""Asset rows and file links complete the same installation transaction
	through the document API (`kt_std_install`)."""
	doc = frappe.get_doc(DOCTYPE, name)
	for row in asset_rows:
		doc.append("assets", row)
	for field, value in extras.items():
		doc.set(field, value)
	doc.flags.kt_std_install = True
	doc.save(ignore_permissions=True)


# ---------------------------------------------------------------------------
# deployment entry point
# ---------------------------------------------------------------------------


def install(package: str, installed_by: str = "", switch: str = "On") -> dict[str, Any]:
	"""`bench --site <site> execute kentender_procurement.std_templates.services.installer.install
	--kwargs "{'package': '<path>', 'installed_by': '<name>', 'switch': 'On'}"`. Commits
	on success; rolls back and records the failed attempt otherwise."""
	actor = installed_by or frappe.session.user or "Administrator"
	try:
		result = install_approved_std_release(package, installed_by=actor, site_switch="Off" if str(switch).lower() == "off" else "On")
		frappe.db.commit()
		print(json.dumps(result, indent=1, default=str))
		return result
	except STDTemplateError as exc:
		frappe.db.rollback()
		_audit("Install failed", "", {"code": exc.code, "identity": exc.identity, "message": exc.message, "package": str(package)})
		frappe.db.commit()
		print(json.dumps({"ok": False, **exc.as_dict()}, indent=1, default=str))
		return {"ok": False, **exc.as_dict()}


#: The controlled release pack for this repository's one Tender format
#: (STD-TPL-001 v0.10 §13; the installer reads the pack directly).
DEFAULT_PACKAGE = Path(__file__).resolve().parents[3].parent / "docs/mvp-1-r1/07_tender_templates/it_equipment_open_v1"
DEFAULT_TEMPLATE_KEY = "IT-EQUIPMENT-OPEN-V1"


def ensure_site_release(*, installed_by: str = "Administrator") -> str:
	"""Seeds and fixtures: make sure this repository's release is installed
	(switched On when newly installed) and usable for a new Tender; returns
	its release id. A release someone switched Off stays Off and stops the
	caller with the command that switches it back on (owner decision OD5)."""
	manifest = json.loads((DEFAULT_PACKAGE / bundle.MANIFEST_PATH).read_text(encoding="utf-8"))
	if not frappe.db.exists(DOCTYPE, manifest["release_id"]):
		install_approved_std_release(str(DEFAULT_PACKAGE), installed_by=installed_by)
	row = frappe.db.get_value(DOCTYPE, manifest["release_id"], ["site_switch", "lifecycle_status", "integrity_status", "display_name", "template_release"], as_dict=True)
	if row.lifecycle_status != "Available" or row.site_switch != "On" or row.integrity_status != "Verified":
		frappe.throw(
			f"{row.display_name} release {row.template_release} cannot be used on this site "
			f"({row.lifecycle_status}, switched {row.site_switch}, integrity {row.integrity_status}). "
			"Switch it on with `make std-release-switch SITE=<site> STATE=On`, or reinstall it."
		)
	_switch_off_others(manifest["template_key"], manifest["release_id"], installed_by)
	return manifest["release_id"]


def _switch_off_others(template_key: str, keep: str, actor: str) -> None:
	"""Two releases of one Tender format switched On stop every new Tender, so a
	newer repository release switches the older ones Off. They stay installed
	and keep serving the Tenders already started on them (owner decision OD5)."""
	from kentender_procurement.std_templates.services import lifecycle

	for name in frappe.get_all(DOCTYPE, filters={"template_key": template_key, "lifecycle_status": "Available", "site_switch": "On", "name": ("!=", keep)}, pluck="name"):
		lifecycle.switch(name, "Off", actor)
