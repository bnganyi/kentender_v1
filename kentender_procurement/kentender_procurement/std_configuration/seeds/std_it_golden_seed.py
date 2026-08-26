# Copyright (c) 2026, KenTender and contributors
"""STD-CHG-001 v1.3 §17.1 — golden package fixture `STD-IT-V1-GOLDEN`.

Creates package `KE-PPRA-IT`, activates its Draft Version 1, and seeds the
§9.15 worked IT Tender instance fixture against it — deterministic, idempotent
(§17.10: "Second run produces no semantic change"), built entirely through the
real domain layer (`frappe.get_doc(...).insert()`, which runs every Phase 1/2
`validate()` guard — the same mechanism a Configurator's own save goes
through) and the real lifecycle engine (`std_lifecycle`), never a raw SQL
write or a shortcut around either.

§17.1's own words: "The fixture must be internally complete and renderable.
It is a deterministic product/test package, not a claim that the short
fixture text reproduces the entire official legal document." Every locked
block, parameter and schema row here is short and representative — proving
the contract, not typing out the real PPRA IT STD's legal prose (that is
§17.2's separate, explicitly out-of-scope-for-this-build production task,
per the user's own confirmed decision, tracker decision log 2026-08-25).
"""

from __future__ import annotations

import frappe

from kentender_procurement.std_configuration.services import std_authorization, std_lifecycle

PACKAGE_CODE = "KE-PPRA-IT"
CONFIGURATOR_EMAIL = "amina.hassan@kentender.example.test"
REVIEWER_EMAIL = "david.mwangi@kentender.example.test"


def ensure_std_it_golden_seed() -> dict:
	if frappe.db.get_value("STD Cfg Package", PACKAGE_CODE, "current_active_version_id"):
		return {"already_seeded": True, "package_code": PACKAGE_CODE}

	std_authorization.ensure_std_configuration_governance_roles()
	configurator = _ensure_actor(CONFIGURATOR_EMAIL, "Amina", "Hassan", std_authorization.ROLE_STD_CONFIGURATOR)
	reviewer = _ensure_actor(REVIEWER_EMAIL, "David", "Mwangi", std_authorization.ROLE_STD_REVIEWER)

	package = _ensure_package()
	draft = std_lifecycle.create_draft(PACKAGE_CODE, "April 2021 edition", actor=configurator)
	source = frappe.get_doc(
		{
			"doctype": "STD Cfg Source Document",
			"reference_doctype": "STD Cfg Draft",
			"reference_name": draft.name,
			"official_title": "Standard Tender Document for Procurement of Information Technology",
			"official_issue_label": "April 2021 edition",
			"file_id": "/files/ppra-it-standard-tender-document.pdf",
		}
	).insert(ignore_permissions=True)
	draft.official_source_file_id = source.name
	draft.save(ignore_permissions=True)

	_seed_sections_and_blocks(draft.name, package.name)
	_seed_parameters(draft.name)
	_seed_requirement_categories(draft.name)
	_seed_schedule(draft.name)
	_seed_inventory(draft.name)
	_seed_price_schemas(draft.name)
	_seed_evaluation_schema(draft.name)
	_seed_forms(draft.name)
	_seed_contract_and_outputs(draft.name)

	task = std_lifecycle.submit_for_review(draft.name, reviewer=reviewer, actor=configurator)
	version = std_lifecycle.activate_package(task.name, actor=reviewer)

	return {
		"already_seeded": False,
		"package_code": PACKAGE_CODE,
		"version_id": version.name,
		"configurator": configurator,
		"reviewer": reviewer,
	}


def _ensure_actor(email: str, first_name: str, last_name: str, role: str) -> str:
	if not frappe.db.exists("User", email):
		frappe.get_doc(
			{
				"doctype": "User",
				"email": email,
				"first_name": first_name,
				"last_name": last_name,
				"enabled": 1,
				"send_welcome_email": 0,
				"roles": [{"role": role}],
			}
		).insert(ignore_permissions=True)
	elif role not in frappe.get_roles(email):
		user = frappe.get_doc("User", email)
		user.append("roles", {"role": role})
		user.save(ignore_permissions=True)
	return email


def _ensure_package():
	if frappe.db.exists("STD Cfg Package", PACKAGE_CODE):
		return frappe.get_doc("STD Cfg Package", PACKAGE_CODE)
	return frappe.get_doc(
		{
			"doctype": "STD Cfg Package",
			"package_code": PACKAGE_CODE,
			"official_title": "Standard Tender Document for Procurement of Information Technology",
			"requirement_profile": "Information Technology",
		}
	).insert(ignore_permissions=True)


# --- §15.8 — 13 required Sections, block counts 3,4,5,4,6,4,3,4,3,3,5,4,4 ------

_SECTIONS = [
	("INV", "Tender identity, cover and Invitation to Tender", 1, 1, 3),
	("SEC-I", "Section I — Instructions to Tenderers", 2, 2, 4),
	("SEC-II", "Section II — Tender Data Sheet", 3, 3, 5),
	("SEC-III", "Section III — Evaluation and Qualification Criteria", 4, 4, 4),
	("SEC-IV", "Section IV — Non-price and Price Tendering Forms", 5, 5, 6),
	("SEC-V", "Section V — Requirements of the Information System", 7, 6, 4),
	("SEC-VI", "Section VI — Technical Requirements", 8, 7, 3),
	("SEC-VII", "Section VII — Implementation Schedule", 9, 8, 4),
	("SEC-VIII", "Section VIII — System Inventory Tables", 10, 9, 3),
	("SEC-IX", "Section IX — Background and Informational Materials", 11, 10, 3),
	("GCC", "General Conditions of Contract", 12, 11, 5),
	("SCC", "Special Conditions of Contract", 13, 12, 4),
	("FORMS", "Contract Forms and Appendices", 14, 13, 4),
]


def _seed_sections_and_blocks(draft_name: str, package_id: str) -> None:
	for code, title, coverage_area_number, display_order, block_count in _SECTIONS:
		section = frappe.get_doc(
			{
				"doctype": "STD Cfg Section",
				"package_id": package_id,
				"section_code": code,
				"title": title,
				"coverage_area_number": coverage_area_number,
				"display_order": display_order,
				"is_required": 1,
			}
		).insert(ignore_permissions=True)
		for i in range(block_count):
			if i == 0:
				frappe.get_doc(
					{
						"doctype": "STD Cfg Content Block",
						"reference_doctype": "STD Cfg Draft",
						"reference_name": draft_name,
						"section_id": section.name,
						"block_type": "Locked text",
						"display_order": 1,
						"locked_text": f"{title} — official locked introduction text.",
					}
				).insert(ignore_permissions=True)
			else:
				frappe.get_doc(
					{
						"doctype": "STD Cfg Content Block",
						"reference_doctype": "STD Cfg Draft",
						"reference_name": draft_name,
						"section_id": section.name,
						"block_type": "Generated value",
						"display_order": i + 1,
						"binding_key": f"{code.lower()}.slot_{i}",
					}
				).insert(ignore_permissions=True)

	# §15.11 Bidder Background 5 rows — informational only, Section IX.
	section_ix = frappe.db.get_value("STD Cfg Section", {"package_id": package_id, "section_code": "SEC-IX"})
	next_order = 4
	for topic in ("Existing systems", "Deployment sites", "Current integrations", "Data environment", "Operating constraints"):
		frappe.get_doc(
			{
				"doctype": "STD Cfg Content Block",
				"reference_doctype": "STD Cfg Draft",
				"reference_name": draft_name,
				"section_id": section_ix,
				"block_type": "Generated value",
				"display_order": next_order,
				"binding_key": f"background.{topic.lower().replace(' ', '_')}",
			}
		).insert(ignore_permissions=True)
		next_order += 1


# --- §15.9 — Tender Parameters, 5 groups -----------------------------------------

_PARAMETERS = [
	# (key, label, value_type, runtime_owner, required, render_binding, downstream_binding)
	("tender.reference", "Tender reference", "Text", "System derived", 1, "Cover, Invitation, TDS", "Tender Management publication"),
	("tender.title", "Tender title", "Text", "Tender Preparation", 1, "Cover and Invitation", ""),
	("tender.procuring_entity", "Procuring Entity", "Text", "System derived", 1, "All named PE slots", ""),
	("tender.financial_year", "Financial Year", "Text", "System derived", 1, "Tender record", ""),
	("tender.procurement_method", "Procurement method", "Choice", "Tender Preparation", 1, "TDS, evaluation, publication", ""),
	("tender.clarification_deadline", "Clarification deadline", "Datetime", "Tender Preparation", 1, "Section II — Tender Data Sheet", ""),
	("tender.clarification_response_deadline", "Clarification response deadline", "Datetime", "Tender Preparation", 1, "Section II — Tender Data Sheet", ""),
	("tender.pre_tender_meeting_required", "Pre-tender meeting required", "Boolean", "Tender Preparation", 1, "Section II — Tender Data Sheet", ""),
	("tender.pre_tender_meeting_time", "Pre-tender meeting time", "Datetime", "Tender Preparation", 0, "Section II — Tender Data Sheet", ""),
	("tender.submission_deadline", "Submission deadline", "Datetime", "Tender Preparation", 1, "Invitation and TDS", ""),
	("tender.validity_days", "Tender validity", "Duration", "Tender Preparation", 1, "Section II — Tender Data Sheet", "Contract Formation"),
	("tender.language", "Tender language", "Choice", "Tender Preparation", 1, "Section II — Tender Data Sheet", ""),
	("tender.security_amount", "Tender security amount", "Money", "Tender Preparation", 1, "Section II — Tender Data Sheet", "Bidder response"),
	("tender.security_validity_days", "Tender security validity", "Duration", "Tender Preparation", 1, "Section II — Tender Data Sheet", ""),
	("tender.currency", "Tender currency", "Choice", "Tender Preparation", 1, "Section II — Tender Data Sheet", ""),
	("tender.submission_method", "Submission method", "Choice", "Tender Preparation", 1, "Section II — Tender Data Sheet", ""),
]


def _seed_parameters(draft_name: str) -> None:
	owner = {"reference_doctype": "STD Cfg Draft", "reference_name": draft_name}
	for key, label, value_type, runtime_owner, required, render_binding, downstream_binding in _PARAMETERS:
		param = frappe.get_doc(
			{
				"doctype": "STD Cfg Parameter Definition",
				**owner,
				"parameter_key": key,
				"label": label,
				"value_type": value_type,
				"runtime_owner": runtime_owner,
				"required": required,
				"render_binding": render_binding,
				"downstream_binding": downstream_binding,
				"allowed_values": (
					"Open Tender\nRestricted Tender\nDirect Procurement"
					if value_type == "Choice" and key == "tender.procurement_method"
					else "English\nKiswahili"
					if value_type == "Choice" and key == "tender.language"
					else "Kenya Shillings\nUS Dollar"
					if value_type == "Choice" and key == "tender.currency"
					else "Electronic submission through KenTender\nPhysical submission"
					if value_type == "Choice" and key == "tender.submission_method"
					else ""
				),
			}
		).insert(ignore_permissions=True)
		if required:
			frappe.get_doc(
				{
					"doctype": "STD Cfg Output Mapping",
					**owner,
					"source_binding_key": param.parameter_key,
					"owning_area": "PCFG-03",
					"target": "Render",
				}
			).insert(ignore_permissions=True)


# --- §7.8 — 14 governed requirement categories -----------------------------------

_REQUIREMENT_CATEGORIES = [
	"Functional",
	"Architecture",
	"Performance",
	"Security",
	"Integration",
	"Data and migration",
	"Reporting and analytics",
	"Hosting and infrastructure",
	"Training and knowledge transfer",
	"Support and warranty",
	"Testing and acceptance",
	"Accessibility and usability",
	"Business continuity and disaster recovery",
	"Regulatory compliance",
]


def _seed_requirement_categories(draft_name: str) -> None:
	owner = {"reference_doctype": "STD Cfg Draft", "reference_name": draft_name}
	for order, category in enumerate(_REQUIREMENT_CATEGORIES, start=1):
		frappe.get_doc(
			{
				"doctype": "STD Cfg Requirement Schema",
				**owner,
				"category": category,
				"display_order": order,
				"allowed_response_types": "Compliance choice\nText\nNumeric\nChoice\nStructured table",
				"evidence_mode": "Product documentation and configured demonstration",
				"acceptance_mode": "Independent test evidence and configured acceptance script",
				"vendor_neutrality_trigger": 1 if category == "Integration" else 0,
				"vendor_neutrality_note": (
					"Vendor-neutrality trigger includes named cloud platforms and requires reviewer attention."
					if category == "Integration"
					else ""
				),
				"render_binding": "Sections V and VI",
				"bidder_response_binding": "Technical compliance response",
				"evaluation_binding": "Requirement evaluation input",
				"contract_carry_forward_binding": "Accepted supplier obligation",
			}
		).insert(ignore_permissions=True)


# --- §9.15.D — 5 implementation-schedule milestones ------------------------------

_SCHEDULE = [
	("inception", "Inception", "Approved inception report and detailed work plan", "14 days from commencement", "Project team availability", "Inception report approved by the Project Manager."),
	("solution_design", "Solution design", "Approved solution and integration design", "35 days from commencement", "Access to current-system documentation", "Design review completed with no Blocking finding."),
	("configuration_integration", "Configuration and integration", "Configured solution and completed interfaces", "90 days from commencement", "Test credentials and interface access", "System and integration tests passed."),
	("training_migration", "Training and migration", "Trained users and accepted migrated data", "120 days from commencement", "Cleansed source data and nominated trainees", "Training records and migration reconciliation accepted."),
	("go_live", "Go-live and operational acceptance", "Production service and operational acceptance certificate", "150 days from commencement", "Production infrastructure and authorised users", "Thirty-day stabilisation period completed and acceptance certificate issued."),
]


def _seed_schedule(draft_name: str) -> None:
	owner = {"reference_doctype": "STD Cfg Draft", "reference_name": draft_name}
	for order, (key, title, deliverable, rule, dependency, checkpoint) in enumerate(_SCHEDULE, start=1):
		frappe.get_doc(
			{
				"doctype": "STD Cfg Schedule Schema",
				**owner,
				"milestone_key": f"schedule.{key}",
				"title": title,
				"display_order": order,
				"required_deliverable": deliverable,
				"completion_rule": rule,
				"dependency_description": dependency,
				"acceptance_checkpoint": checkpoint,
				"render_binding": "Section VII — Implementation Schedule",
				"contract_binding": "Contract Formation schedule",
			}
		).insert(ignore_permissions=True)


# --- §15.11 — 8 System Inventory categories --------------------------------------

_INVENTORY = [
	("Hardware", "Required"),
	("Software", "Required"),
	("Licence", "Required"),
	("Service", "Required"),
	("Training", "Required"),
	("Support", "Required"),
	("Hosting", "Optional"),
	("Integration", "Required"),
]


def _seed_inventory(draft_name: str) -> None:
	owner = {"reference_doctype": "STD Cfg Draft", "reference_name": draft_name}
	schedule_link = frappe.db.get_value(
		"STD Cfg Schedule Schema", {"reference_doctype": "STD Cfg Draft", "reference_name": draft_name}, "name"
	)
	requirement_link = frappe.db.get_value(
		"STD Cfg Requirement Schema", {"reference_doctype": "STD Cfg Draft", "reference_name": draft_name}, "name"
	)
	for category, policy in _INVENTORY:
		frappe.get_doc(
			{
				"doctype": "STD Cfg Inventory Schema",
				**owner,
				"category": category,
				"price_schedule_link_policy": policy,
				"requirement_link": requirement_link,
				"schedule_link": schedule_link,
				"render_binding": "Section VIII — System Inventory Tables",
			}
		).insert(ignore_permissions=True)


# --- §7.11 — 4 IT price-table families -------------------------------------------

_PRICE_SCHEMAS = [
	"Software and infrastructure",
	"Implementation services",
	"Training",
	"Recurrent support",
]


def _seed_price_schemas(draft_name: str) -> None:
	owner = {"reference_doctype": "STD Cfg Draft", "reference_name": draft_name}
	for family in _PRICE_SCHEMAS:
		frappe.get_doc(
			{
				"doctype": "STD Cfg Price Schema",
				**owner,
				"family": family,
				"line_description": "Approved scope line description",
				"quantity_unit_source": "Approved scope",
				"currency_rule": "Kenya Shillings, single currency",
				"tax_treatment": "VAT and applicable duties, bidder-declared",
				"bidder_price_fields": "Unit price\nTax amount",
				"calculation": "Quantity × Unit price + Tax amount",
				"evaluated_total_binding": "Sum of all four price schedules",
			}
		).insert(ignore_permissions=True)


# --- §9.11 — 4 evaluation stages, §15.13 criterion structures --------------------

_EVALUATION_CRITERIA = [
	# (stage, key, structure, treatment, response_source, evidence_source, weight, failure_effect)
	("Preliminary responsiveness", "preliminary_responsiveness", "Preliminary responsiveness check", "Pass/Fail", "Tender Form completeness", "Submission checklist", None, "Fails preliminary evaluation"),
	("Technical evaluation", "mandatory_compliance", "Mandatory requirement compliance", "Pass/Fail", "Requirement response", "Requirement evidence", None, "Fails technical evaluation"),
	("Technical evaluation", "technical_response_quality", "Technical response quality", "Scored", "Narrative response", "Configured evidence", 40, "Scored against technical threshold"),
	("Technical evaluation", "demonstration_result", "Demonstration result", "Pass/Fail or scored", "Demonstration record", "Demonstration evidence", 30, "Scored or fails per package rule"),
	("Technical evaluation", "key_personnel_capability", "Key personnel capability", "Scored", "Personnel Form", "Personnel evidence", 20, "Scored against technical threshold"),
	("Technical evaluation", "relevant_experience", "Relevant experience", "Pass/Fail or scored", "Specific Experience Form", "Contract evidence", 10, "Scored or fails per package rule"),
	("Financial evaluation", "evaluated_price", "Evaluated price comparison", "Calculated financial result", "Price schedule totals", "Bidder price submission", None, "Determines financial ranking"),
	("Post-qualification", "post_qualification_check", "Post-qualification confirmation", "Pass/Fail", "Qualification evidence", "Post-qualification documentation", None, "Fails post-qualification"),
]


def _seed_evaluation_schema(draft_name: str) -> None:
	owner = {"reference_doctype": "STD Cfg Draft", "reference_name": draft_name}
	for order, (stage, key, structure, treatment, response_source, evidence_source, weight, failure_effect) in enumerate(
		_EVALUATION_CRITERIA, start=1
	):
		frappe.get_doc(
			{
				"doctype": "STD Cfg Evaluation Schema",
				**owner,
				"stage": stage,
				"criterion_key": f"eval.{key}",
				"criterion_structure": structure,
				"display_order": order,
				"treatment": treatment,
				"response_source": response_source,
				"evidence_source": evidence_source,
				"weight": weight,
				"failure_effect": failure_effect,
			}
		).insert(ignore_permissions=True)


# --- §7.13 — 18 governed IT forms, §15.14 activation ------------------------------

_ALWAYS_FORMS = [
	"Form of Tender",
	"Tenderer Information Form",
	"Confidential Business Questionnaire",
	"Certificate of Independent Tender Determination",
	"Self-Declaration",
	"Fraud and Corruption",
	"Beneficial Ownership",
]

_CONDITIONAL_FORMS = [
	"Joint Venture Member Information Form",
	"Historical Non-performance and Pending Litigation",
	"General Experience",
	"Specific Experience",
	"Current Contract Commitments",
	"Financial Situation",
	"Average Annual Turnover",
	"Financial Resources",
	"Personnel Capability",
	"Intellectual Property",
	"Conformance of Information System Materials",
]

_SPECIFIC_EXPERIENCE_FIELDS = [
	("Client organisation", "Text", 1),
	("Contract title", "Text", 1),
	("Contract value", "Money", 1),
	("Start date", "Date", 1),
	("Completion date", "Date", 1),
	("Evidence", "File evidence", 1),
]


def _seed_forms(draft_name: str) -> None:
	owner = {"reference_doctype": "STD Cfg Draft", "reference_name": draft_name}
	for form_name in _ALWAYS_FORMS + _CONDITIONAL_FORMS:
		is_always = form_name in _ALWAYS_FORMS
		form = frappe.get_doc(
			{
				"doctype": "STD Cfg Form Schema",
				**owner,
				"form_key": f"form.{form_name.lower().replace(' ', '_')}",
				"form_name": form_name,
				"activation": "Always" if is_always else "Conditional",
				"activation_condition": "" if is_always else "Applicable per procurement method or bidder structure",
				"render_location": "Section IV — Non-price Tendering Forms",
				"evidence_rule": "As declared on the form" if is_always else "Configured evidence per condition",
			}
		)
		if form_name == "Specific Experience":
			for field_label, field_type, required in _SPECIFIC_EXPERIENCE_FIELDS:
				form.append("fields", {"field_label": field_label, "field_type": field_type, "required": required})
		else:
			# Every form gets at least one field-level entry — §7.13: "A form
			# required for evaluation must expose field-level data; it cannot
			# be only a downloadable template" (Phase 6's STD_FORM_OPAQUE_UPLOAD).
			form.append("fields", {"field_label": "Declaration statement", "field_type": "Long Text", "required": 1})
		form.insert(ignore_permissions=True)


# --- §15.15 — 12 contract values, 4 contract forms, 3 post-award mappings -------

_CONTRACT_VALUES = [
	("Performance security", "Tender Preparation", "Required", "SCC and Contract Formation"),
	("Advance-payment security", "Tender Preparation", "Conditional", "SCC and Contract Formation"),
	("Payment milestones", "Tender Preparation", "Required", "SCC and contract schedule"),
	("Operational acceptance", "Requirement and schedule data", "Required", "SCC and acceptance certificate"),
	("Warranty period", "Tender Preparation", "Required", "SCC and contract"),
	("Support period", "Tender Preparation", "Required", "SCC and contract"),
	("Intellectual-property treatment", "Tender Preparation", "Required", "SCC and contract"),
	("Software licence categories", "IT Requirements", "Conditional", "Contract appendix"),
	("Confidentiality", "Package default plus Tender value", "Required", "SCC and contract"),
	("Insurance", "Tender Preparation", "Conditional", "SCC and contract"),
	("Liability limit", "Tender Preparation", "Required", "SCC and contract"),
	("Dispute resolution", "Tender Preparation", "Required", "SCC and contract"),
]

_POST_AWARD_MAPPINGS = [
	"Change Order Form",
	"Acceptance Certificate",
	"Contract Amendment Form",
]


def _seed_contract_and_outputs(draft_name: str) -> None:
	owner = {"reference_doctype": "STD Cfg Draft", "reference_name": draft_name}
	for value_category, supplied_by, required_treatment, output in _CONTRACT_VALUES:
		frappe.get_doc(
			{
				"doctype": "STD Cfg Contract Schema",
				**owner,
				"value_category": value_category,
				"supplied_by": supplied_by,
				"required_treatment": required_treatment,
				"condition": "" if required_treatment == "Required" else "Applicable per approved contract terms",
				"scc_binding": f"SCC — {value_category}",
				"contract_binding": output,
			}
		).insert(ignore_permissions=True)

	# §15.15 "Post-award 3 tab" — mapped to Contract Management, not exposed as
	# a Tender configuration step (§7.13 item 16 / §9.13), and not a "contract
	# value" in §15.15's own 12-item sense (that field is a closed Select enum
	# of exactly those 12 — these post-award forms don't belong in it).
	# Represented as Content Blocks under the Contract Forms section instead,
	# each carrying a binding_key naming its Contract Management destination —
	# this is what the Contract Management manifest builder's own documented
	# proxy (contract_binding-bearing Contract Schema rows) does NOT cover, a
	# real, smaller, second gap worth naming rather than silently working
	# around with an invalid enum value.
	forms_section = frappe.db.get_value("STD Cfg Section", {"package_id": frappe.db.get_value("STD Cfg Draft", draft_name, "package_id"), "section_code": "FORMS"})
	for i, form_name in enumerate(_POST_AWARD_MAPPINGS, start=1):
		frappe.get_doc(
			{
				"doctype": "STD Cfg Content Block",
				**owner,
				"section_id": forms_section,
				"block_type": "Contract value",
				"display_order": 100 + i,
				"binding_key": f"contract_management.{form_name.lower().replace(' ', '_')}",
			}
		).insert(ignore_permissions=True)
