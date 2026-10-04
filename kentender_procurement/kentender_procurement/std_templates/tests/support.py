# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Shared helpers for the STD Templates test modules.

`make_test_package` copies the real release 1.1 candidate pack (without the
103 source page images, to stay small), gives it its own release identity,
optionally mutates it, and re-derives a self-consistent manifest with the
same algorithm the curation tool uses. `purge` removes every row, file and
audit event a test created; this bench has no per-test rollback.
"""

from __future__ import annotations

import json
import os
import shutil
import tempfile
import uuid
from pathlib import Path
from typing import Any, Callable

import frappe

from kentender_procurement.std_templates.compiler import assets as release_assets
from kentender_procurement.std_templates.compiler.canonical import pretty_json, sha256_bytes
from kentender_procurement.std_templates.release import bundle, manifest as manifest_module

APP_DIR = Path(__file__).resolve().parents[3]
PACK = APP_DIR.parent / "docs/mvp-1-r1/07_tender_templates/it_equipment_open_v1"
TEST_RELEASE_PREFIX = "stdr-7e57"


def pack_files() -> dict[str, bytes]:
	return {name: (PACK / rel).read_bytes() for name, rel in release_assets.ASSET_FILES.items()}


def pack_assets() -> release_assets.ReleaseAssets:
	return release_assets.load(
		pack_files(),
		official_source_digest=bundle.file_digest(PACK / "01_source/ppra_goods_std_official.pdf"),
		bundle_digest=bundle.candidate_bundle_digest(PACK),
	)


def moh_projection() -> dict[str, Any]:
	return json.loads((PACK / "04_fixture/moh_input.json").read_text(encoding="utf-8"))


def variant_projection(name: str) -> dict[str, Any]:
	return json.loads((PACK / f"04_fixture/reservation_variants/{name}_input.json").read_text(encoding="utf-8"))


def new_test_release_id() -> str:
	return f"{TEST_RELEASE_PREFIX}-{uuid.uuid4().hex[:4]}-4{uuid.uuid4().hex[:3]}-8{uuid.uuid4().hex[:3]}-{uuid.uuid4().hex[:12]}"


def reseal(root: Path) -> str:
	"""Re-derive the manifest inventory and every digest after a test change;
	returns the new manifest digest."""
	manifest_path = root / bundle.MANIFEST_PATH
	manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
	entries = bundle.inventory(root)
	sizes = {rel: (root / rel).stat().st_size for rel, _ in entries}
	manifest["assets"] = manifest_module.asset_rows(entries, sizes)
	manifest["bundle_digest"] = bundle.bundle_digest(entries)
	manifest["input_bundle_digest"] = bundle.bundle_digest(bundle.input_entries(entries))
	for field, rel in (
		("validation_report_digest", "05_review/validation_report.json"),
		("release_gates_digest", "05_review/release_gates.json"),
		("release_change_report_digest", "05_review/release_change_report.json"),
		("product_profile_digest", release_assets.ASSET_FILES["product_profile"]),
		("response_rules_digest", release_assets.ASSET_FILES["response_rules"]),
		("downstream_rules_digest", release_assets.ASSET_FILES["downstream_rules"]),
		("addendum_identity_rules_digest", release_assets.ASSET_FILES["addendum_identity_rules"]),
	):
		manifest[field] = bundle.file_digest(root / rel)
	manifest_path.write_text(pretty_json(manifest), encoding="utf-8")
	return sha256_bytes(manifest_path.read_bytes())


def make_test_package(
	*,
	release_id: str | None = None,
	template_release: str = "9.9-test",
	mutate: Callable[[Path], None] | None = None,
	decision: str | None = None,
	pass_all_gates: bool = False,
	reseal_after_mutate: bool = True,
) -> tuple[Path, dict[str, Any]]:
	tmp = Path(tempfile.mkdtemp(prefix="kt-std-test-pack-"))
	root = tmp / "it_equipment_open_v1"
	shutil.copytree(PACK, root, ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "pages", "review_record.md", "owner_decision.json"))
	release_id = release_id or new_test_release_id()
	for rel in release_assets.ASSET_FILES.values():
		data = json.loads((root / rel).read_text(encoding="utf-8"))
		data["release_id"] = release_id
		data["template_release"] = template_release
		(root / rel).write_text(pretty_json(data), encoding="utf-8")
	manifest_path = root / bundle.MANIFEST_PATH
	manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
	manifest.update({"release_id": release_id, "template_release": template_release, "display_name": f"IT Equipment Open Tender (test {template_release})"})
	manifest_path.write_text(pretty_json(manifest), encoding="utf-8")
	if pass_all_gates:
		gates_path = root / "05_review/release_gates.json"
		doc = json.loads(gates_path.read_text(encoding="utf-8"))
		for row in doc["gates"]:
			row.update({"result": "Passed", "checked_by": "test", "checked_at": "2026-09-26", "evidence_refs": row["evidence_refs"] or ["test"]})
		gates_path.write_text(pretty_json(doc), encoding="utf-8")
	reseal(root)
	if mutate:
		mutate(root)
		if reseal_after_mutate:
			reseal(root)
	manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
	manifest_digest = sha256_bytes(manifest_path.read_bytes())
	if decision:
		owner = {
			"schema_version": 1,
			"release_id": manifest["release_id"],
			"template_key": manifest["template_key"],
			"template_release": manifest["template_release"],
			"bundle_digest": manifest["bundle_digest"],
			"manifest_digest": manifest_digest,
			"decision": decision,
			"decided_by": "test release owner",
			"decided_at": "2026-09-26",
			"decision_record": "Test decision.",
		}
		(root / bundle.OWNER_DECISION_PATH).write_text(pretty_json(owner), encoding="utf-8")
	return root, {"release_id": release_id, "manifest": manifest, "manifest_digest": manifest_digest, "tmp": tmp}


def purge(release_ids: list[str]) -> None:
	"""Delete test releases, their files, concerns and audit events."""
	for release_id in release_ids:
		if not release_id:
			continue
		for concern in frappe.get_all("STD Template Concern", filters={"release_id": release_id}, pluck="name"):
			doc = frappe.get_doc("STD Template Concern", concern)
			if doc.evidence_file_id and frappe.db.exists("File", doc.evidence_file_id):
				frappe.delete_doc("File", doc.evidence_file_id, force=True, ignore_permissions=True)
			doc.flags.kt_fixture_wipe = True
			doc.delete(ignore_permissions=True, force=True)
			frappe.db.delete("Audit Event", {"document_name": concern})
		for file_name in frappe.get_all("File", filters={"attached_to_doctype": "Installed STD Release", "attached_to_name": release_id}, pluck="name"):
			frappe.delete_doc("File", file_name, force=True, ignore_permissions=True)
		if frappe.db.exists("Installed STD Release", release_id):
			doc = frappe.get_doc("Installed STD Release", release_id)
			doc.flags.kt_fixture_wipe = True
			doc.delete(ignore_permissions=True, force=True)
		frappe.db.delete("Audit Event", {"document_type": "Installed STD Release", "document_name": release_id})
	frappe.db.delete("Audit Event", {"event_type": "STD Release", "document_name": "", "metadata": ["like", "%kt-std-test-pack-%"]})
	frappe.db.commit()


def isolate_switch(testcase, template_key: str = "IT-EQUIPMENT-OPEN-V1", keep: tuple[str, ...] = ()) -> None:
	"""Switch Off every other switched-on release of `template_key` for one
	test, restoring each On in cleanup (this bench has no test rollback, and
	the dev site's own release is normally On)."""
	others = frappe.get_all(
		"Installed STD Release",
		filters={"template_key": template_key, "lifecycle_status": "Available", "site_switch": "On", "name": ["not in", list(keep) or [""]]},
		pluck="name",
	)
	for name in others:
		frappe.db.set_value("Installed STD Release", name, "site_switch", "Off", update_modified=False)
	frappe.db.commit()

	def restore():
		for name in others:
			if frappe.db.exists("Installed STD Release", name):
				frappe.db.set_value("Installed STD Release", name, "site_switch", "On", update_modified=False)
		frappe.db.commit()

	testcase.addCleanup(restore)


def cleanup_tmp(info: dict[str, Any]) -> None:
	shutil.rmtree(info["tmp"], ignore_errors=True)
	os.environ.pop("KT_STD_TEST", None)
