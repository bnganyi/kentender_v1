from __future__ import annotations

from pathlib import Path

import frappe
from frappe import _

SOURCE_BUILTIN = "BUILTIN_SEED_PACKAGE"
SOURCE_UPLOADED = "UPLOADED_STRUCTURED_PACKAGE"
SOURCE_REGISTRY = "CONNECTED_REGISTRY"

ALLOWED_SOURCES = {SOURCE_BUILTIN, SOURCE_UPLOADED, SOURCE_REGISTRY}
RAW_DISALLOWED_EXTENSIONS = {".pdf", ".doc", ".docx", ".xls", ".xlsx", ".csv"}


def _seed_entry() -> dict[str, str]:
	return {
		"value": "PPRA-WORKS-BLDG-2022-04",
		"label": "PPRA Works — Building and Associated Civil Engineering Works — Rev April 2022",
		"package_type": "Works STD Structured Package",
		"expected_std_category": "WORKS",
		"package_version": "Rev April 2022",
	}


@frappe.whitelist()
def get_std_library_package_sources() -> dict:
	return {
		"ok": True,
		"sources": [
			{
				"value": SOURCE_BUILTIN,
				"label": "Built-in Seed Package",
				"entries": [_seed_entry()],
			},
			{
				"value": SOURCE_UPLOADED,
				"label": "Uploaded Structured Package",
				"entries": [
					{
						"value": "sample_structured_package.zip",
						"label": "sample_structured_package.zip",
						"package_type": "Uploaded Structured Package",
						"expected_std_category": "WORKS",
						"package_version": "Draft Upload",
					}
				],
			},
			{
				"value": SOURCE_REGISTRY,
				"label": "Connected Registry",
				"entries": [
					{
						"value": "registry://ppra/works/building/2022-04",
						"label": "PPRA Registry — Works Building Rev April 2022",
						"package_type": "Registry Structured Package",
						"expected_std_category": "WORKS",
						"package_version": "Rev April 2022",
					}
				],
			},
		],
	}


@frappe.whitelist()
def select_std_library_import_package(
	import_code: str | None = None,
	package_source: str | None = None,
	package_entry: str | None = None,
) -> dict:
	if frappe.session.user in (None, "Guest"):
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	source = str(package_source or "").strip()
	entry = str(package_entry or "").strip()
	if source not in ALLOWED_SOURCES:
		frappe.throw(_("A valid package source is required."))
	if not entry:
		frappe.throw(_("A package file or registry entry is required."))

	if source == SOURCE_UPLOADED:
		ext = Path(entry).suffix.lower()
		if ext in RAW_DISALLOWED_EXTENSIONS:
			frappe.throw(
				_(
					"Raw PDF, Word, or spreadsheet files may be attached as evidence but cannot by themselves create a working STD template. A structured STD package is required."
				)
			)

	metadata = {
		"package_type": "Structured STD Package",
		"expected_std_category": "WORKS",
		"package_version": "Detected",
	}
	if source == SOURCE_BUILTIN and entry == _seed_entry()["value"]:
		metadata = {
			"package_type": _seed_entry()["package_type"],
			"expected_std_category": _seed_entry()["expected_std_category"],
			"package_version": _seed_entry()["package_version"],
		}
	elif source == SOURCE_REGISTRY:
		metadata = {
			"package_type": "Registry Structured Package",
			"expected_std_category": "WORKS",
			"package_version": "Rev April 2022",
		}
	elif source == SOURCE_UPLOADED:
		metadata = {
			"package_type": "Uploaded Structured Package",
			"expected_std_category": "WORKS",
			"package_version": "Draft Upload",
		}

	return {
		"ok": True,
		"import_code": import_code or "STD-IMPORT-DRAFT",
		"selection": {
			"package_source": source,
			"package_entry": entry,
		},
		"metadata": metadata,
	}


@frappe.whitelist()
def save_std_library_source_evidence(
	import_code: str | None = None,
	source_authority: str | None = None,
	source_title: str | None = None,
	source_revision: str | None = None,
	source_file: str | None = None,
	source_hash: str | None = None,
	prepared_by: str | None = None,
	review_status: str | None = None,
	notes: str | None = None,
) -> dict:
	if frappe.session.user in (None, "Guest"):
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	authority = str(source_authority or "").strip()
	title = str(source_title or "").strip()
	revision = str(source_revision or "").strip()
	evidence_file = str(source_file or "").strip()
	evidence_hash = str(source_hash or "").strip()
	review = str(review_status or "").strip()
	prepared = str(prepared_by or "").strip()
	note_text = str(notes or "").strip()

	if not authority:
		frappe.throw(_("Source Authority is required."))
	if not title:
		frappe.throw(_("Source Document Title is required."))
	if not revision:
		frappe.throw(_("Revision Label is required."))
	if not review:
		frappe.throw(_("Review Status is required."))
	if bool(evidence_file) ^ bool(evidence_hash):
		frappe.throw(_("Source Evidence File and Source Hash must be provided together."))

	return {
		"ok": True,
		"import_code": import_code or "STD-IMPORT-DRAFT",
		"source_evidence": {
			"source_authority": authority,
			"source_title": title,
			"source_revision": revision,
			"source_file": evidence_file or None,
			"source_hash": evidence_hash or None,
			"prepared_by": prepared or None,
			"review_status": review,
			"notes": note_text or None,
		},
	}


@frappe.whitelist()
def get_std_library_detected_structure(import_code: str | None = None) -> dict:
	if frappe.session.user in (None, "Guest"):
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	return {
		"ok": True,
		"import_code": import_code or "STD-IMPORT-DRAFT",
		"summary": {
			"parts_sections": "3 parts, 10 sections detected",
			"locked_legal_text": "ITT and GCC detected",
			"parameters": "48 TDS/SCC parameters detected",
			"forms": "14 tendering forms, 9 contract forms detected",
			"boq_rules": "Works BOQ rules detected",
			"source_mappings": "Bundle, Submission, Opening, Evaluation, Contract mappings detected",
			"readiness_rules": "16 readiness rules detected",
			"works_boq_applicable": True,
		},
		"technical_details": {
			"sections": ["Part I - Instructions", "Part II - Data Sheet", "Part III - Contract"],
			"parameter_groups": ["Eligibility", "Evaluation", "Contract Terms"],
			"form_categories": ["Tendering Forms (14)", "Contract Forms (9)"],
			"mapping_coverage": {
				"bundle": 12,
				"submission": 10,
				"opening": 8,
				"evaluation": 14,
				"contract": 9,
			},
		},
	}


def _validation_payload() -> dict:
	return {
		"result": "Needs Attention",
		"summary": "2 blockers must be resolved before this STD can be reviewed or activated.",
		"categories": [
			{"key": "sections", "label": "Sections", "status": "Passed"},
			{"key": "locked_legal_text", "label": "Locked Legal Text", "status": "Passed"},
			{"key": "parameters", "label": "Parameters", "status": "Needs Attention"},
			{"key": "forms", "label": "Forms", "status": "Passed"},
			{"key": "boq_rules", "label": "BOQ Rules", "status": "Passed"},
			{"key": "source_mappings", "label": "Source Mappings", "status": "Blocked"},
			{"key": "generated_models", "label": "Generated Models", "status": "Needs Attention"},
			{"key": "bundle_rendering", "label": "Bundle Rendering", "status": "Passed"},
		],
		"blockers": [
			{
				"category": "Source Mappings",
				"reason": "Evaluation Rules mapping is incomplete.",
				"fix_path": "Open Advanced Technical View -> Source Mappings.",
				"code": "DEM_MAPPING_MISSING",
			},
			{
				"category": "Generated Models",
				"reason": "Submission requirements model has unresolved mandatory field.",
				"fix_path": "Update source mappings and rerun validation.",
				"code": "DSM_REQUIRED_FIELD_MISSING",
			},
		],
	}


@frappe.whitelist()
def run_std_library_import_validation(import_code: str | None = None) -> dict:
	if frappe.session.user in (None, "Guest"):
		frappe.throw(_("Not permitted"), frappe.PermissionError)
	return {
		"ok": True,
		"import_code": import_code or "STD-IMPORT-DRAFT",
		"validation": _validation_payload(),
	}


@frappe.whitelist()
def get_std_library_import_validation(import_code: str | None = None) -> dict:
	if frappe.session.user in (None, "Guest"):
		frappe.throw(_("Not permitted"), frappe.PermissionError)
	return {
		"ok": True,
		"import_code": import_code or "STD-IMPORT-DRAFT",
		"validation": _validation_payload(),
	}


def _bundle_outline() -> list[dict[str, str]]:
	return [
		{"number": "0", "title": "Invitation to Tender"},
		{"number": "I", "title": "Section I — Instructions to Tenderers"},
		{"number": "II", "title": "Section II — Tender Data Sheet"},
		{"number": "III", "title": "Section III — Evaluation and Qualification Criteria"},
		{"number": "IV", "title": "Section IV — Tendering Forms"},
		{"number": "V", "title": "Section V — Bills of Quantities"},
		{"number": "VI", "title": "Section VI — Specifications"},
		{"number": "VII", "title": "Section VII — Drawings"},
		{"number": "VIII", "title": "Section VIII — General Conditions of Contract"},
		{"number": "IX", "title": "Section IX — Special Conditions of Contract"},
		{"number": "X", "title": "Section X — Contract Forms"},
	]


def _placeholder_rows() -> list[str]:
	return [
		"[To be completed during tender preparation: Submission Deadline]",
		"[To be completed during tender preparation: Employer Name]",
		"[To be completed during tender preparation: BOQ Items and Quantities]",
	]


@frappe.whitelist()
def generate_std_library_bundle_preview(import_code: str | None = None) -> dict:
	if frappe.session.user in (None, "Guest"):
		frappe.throw(_("Not permitted"), frappe.PermissionError)
	return {
		"ok": True,
		"import_code": import_code or "STD-IMPORT-DRAFT",
		"status": "Preview generated",
	}


@frappe.whitelist()
def get_std_library_bundle_preview(import_code: str | None = None) -> dict:
	if frappe.session.user in (None, "Guest"):
		frappe.throw(_("Not permitted"), frappe.PermissionError)
	return {
		"ok": True,
		"import_code": import_code or "STD-IMPORT-DRAFT",
		"outline": _bundle_outline(),
		"sections": [
			{
				"number": row["number"],
				"title": row["title"],
				"preview": f"{row['title']} content preview is available.",
			}
			for row in _bundle_outline()
		],
		"actions": {
			"preview_in_browser": True,
			"download_pdf": True,
			"download_docx": True,
			"view_placeholder_list": True,
		},
		"message": "Bundle preview is ready for review.",
	}


@frappe.whitelist()
def get_std_library_placeholder_list(import_code: str | None = None) -> dict:
	if frappe.session.user in (None, "Guest"):
		frappe.throw(_("Not permitted"), frappe.PermissionError)
	return {
		"ok": True,
		"import_code": import_code or "STD-IMPORT-DRAFT",
		"placeholders": _placeholder_rows(),
	}


def _final_review_summary() -> dict:
	return {
		"std_title": "PPRA Works — Building and Associated Civil Engineering Works",
		"revision": "Rev April 2022",
		"source_authority": "PPRA",
		"source_evidence_status": "Evidence captured",
		"validation_result": "Passed",
		"bundle_preview_status": "Available",
		"generated_model_status": "Ready",
		"warnings": ["Tender preparation placeholders must be completed before issue."],
	}


def _final_review_blockers() -> list[dict[str, str]]:
	return []


def _final_review_actions() -> dict[str, object]:
	return {
		"review_required": True,
		"can_submit_review": True,
		"can_activate": False,
		"submit_denial_code": None,
		"activate_denial_code": "STD_REVIEW_REQUIRED",
		"submit_message": "This package can be submitted for review.",
		"activate_message": "Activation is available after review is completed.",
	}


@frappe.whitelist()
def get_std_library_import_final_review(import_code: str | None = None) -> dict:
	if frappe.session.user in (None, "Guest"):
		frappe.throw(_("Not permitted"), frappe.PermissionError)
	return {
		"ok": True,
		"import_code": import_code or "STD-IMPORT-DRAFT",
		"summary": _final_review_summary(),
		"blockers": _final_review_blockers(),
		"actions": _final_review_actions(),
		"status": "Ready for Review",
		"confirmation_text": {
			"submit": "This will submit the structured STD package for legal or policy review. It will not be available for tenders until approved and activated.",
			"activate": "This will activate the STD version for future tenders. Active versions are immutable.",
		},
	}


@frappe.whitelist()
def submit_std_library_import_review(import_code: str | None = None) -> dict:
	if frappe.session.user in (None, "Guest"):
		frappe.throw(_("Not permitted"), frappe.PermissionError)
	actions = _final_review_actions()
	if not actions.get("can_submit_review"):
		return {
			"ok": False,
			"import_code": import_code or "STD-IMPORT-DRAFT",
			"status": "Submit Blocked",
			"message": "This package cannot be submitted for review yet.",
			"denial_code": actions.get("submit_denial_code") or "STD_SUBMIT_BLOCKED",
		}
	return {
		"ok": True,
		"import_code": import_code or "STD-IMPORT-DRAFT",
		"status": "Submitted for Review",
		"message": "Package submitted for legal or policy review.",
	}


@frappe.whitelist()
def activate_std_library_import(import_code: str | None = None) -> dict:
	if frappe.session.user in (None, "Guest"):
		frappe.throw(_("Not permitted"), frappe.PermissionError)
	actions = _final_review_actions()
	if not actions.get("can_activate"):
		return {
			"ok": False,
			"import_code": import_code or "STD-IMPORT-DRAFT",
			"status": "Activation Blocked",
			"message": "This package cannot be activated yet. Complete governance review first.",
			"denial_code": actions.get("activate_denial_code") or "STD_ACTIVATION_BLOCKED",
		}
	return {
		"ok": True,
		"import_code": import_code or "STD-IMPORT-DRAFT",
		"status": "Activated",
		"message": "STD version activated for future tenders.",
	}


def _library_validation_summary_rows() -> list[dict[str, object]]:
	return [
		{
			"version_code": "KE-PPRA-WORKS-BLDG-2022-04",
			"version": "PPRA Works — Building and Associated Civil Engineering Works (Rev April 2022)",
			"status": "Active",
			"last_validated": "2026-05-08 18:30:00",
			"result": "Passed",
			"blockers": 0,
			"bundle_status": "Available",
		},
		{
			"version_code": "KE-PPRA-WORKS-ROADS-2022-04",
			"version": "PPRA Works — Roads and Bridges (Rev April 2022)",
			"status": "Draft",
			"last_validated": "2026-05-08 18:32:00",
			"result": "Blocked",
			"blockers": 2,
			"bundle_status": "Failed",
		},
	]


@frappe.whitelist()
def get_std_library_validation_summary() -> dict:
	if frappe.session.user in (None, "Guest"):
		frappe.throw(_("Not permitted"), frappe.PermissionError)
	return {
		"ok": True,
		"rows": _library_validation_summary_rows(),
		"message": "Validation summary loaded.",
	}


@frappe.whitelist()
def run_std_library_validation() -> dict:
	if frappe.session.user in (None, "Guest"):
		frappe.throw(_("Not permitted"), frappe.PermissionError)
	return {
		"ok": True,
		"rows": _library_validation_summary_rows(),
		"message": "Validation run completed for eligible STD versions.",
	}


@frappe.whitelist()
def register_std_library_source_document(
	source_document_code: str | None = None,
	source_title: str | None = None,
	source_authority: str | None = None,
	revision_label: str | None = None,
	source_file: str | None = None,
	source_hash: str | None = None,
	notes: str | None = None,
) -> dict:
	if frappe.session.user in (None, "Guest"):
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	code = str(source_document_code or "").strip()
	title = str(source_title or "").strip()
	authority = str(source_authority or "").strip()
	revision = str(revision_label or "").strip()
	file_ref = str(source_file or "").strip()
	hash_value = str(source_hash or "").strip()
	note_text = str(notes or "").strip()

	if not code:
		frappe.throw(_("Source Document Code is required."))
	if not title:
		frappe.throw(_("Source Title is required."))
	if not authority:
		frappe.throw(_("Source Authority is required."))
	if not revision:
		frappe.throw(_("Revision Label is required."))

	return {
		"ok": True,
		"source_document": {
			"source_document_code": code,
			"source_title": title,
			"source_authority": authority,
			"revision_label": revision,
			"source_file": file_ref or None,
			"source_hash": hash_value or None,
			"notes": note_text or None,
			"activation_status": "Not Activated",
		},
		"message": "Source document registered as evidence. This does not make an STD available for tenders.",
	}
