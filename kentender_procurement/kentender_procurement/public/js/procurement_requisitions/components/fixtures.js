// Board fixture payloads (REQ-CHG-001 v1.11 §16, board v2) shaped exactly as
// the server reads return them, for the component and fidelity specs.
import { ref } from "vue";
import { REQ_CONTEXT } from "../data/context.js";

export const TITLE = "Clinical training and deployment laptops for digital health rollout";
export const REF = "REQ-MOH-2027-033-001";
export const BOTH = "Digital Health; HR Management and Development";

export function context(overrides = {}) {
	const calls = [];
	const ctx = {
		pending: ref(false),
		commandError: ref(null),
		refreshing: ref(false),
		clearError: () => {},
		run: async (label, fn) => {
			calls.push(label);
			return fn("test-key");
		},
		reload: async () => {},
		go: (...args) => calls.push(["go", ...args]),
		goPath: (path) => calls.push(["goPath", path]),
		api: {},
		...overrides,
	};
	return { ctx, calls, global: { provide: { [REQ_CONTEXT]: ctx } } };
}

const READY_ROW = {
	plan_item_id: "PI-0001",
	plan_item_reference: "PPI-MOH-2027-033",
	title: TITLE,
	departments: BOTH,
	available_quantity: "250 Each",
	available_value: "KES 50,000,000.00",
	needed_by: "31 Dec 2027",
	route: "/app/procurement-requisitions/new/PI-0001",
	existing: null,
};

const REGISTER_ROW = {
	requisition: "PR-0001",
	reference: REF,
	title: TITLE,
	plan_item_id: "PI-0001",
	plan_item_reference: "PPI-MOH-2027-033",
	status: "Draft",
	state: "Draft",
	departments: BOTH,
	updated: "1 Mar 2027, 09:45 EAT",
	route: "/app/procurement-requisitions/PR-0001",
};

const FILTERS = {
	statuses: [{ value: "Draft", label: "Draft" }],
	departments: [{ value: "OU-DH", label: "Digital Health" }],
	fiscal_years: [],
};

export function workspace(variant) {
	const base = {
		outcome: "OK",
		mode: "business",
		your_work: [],
		ready_to_start: [READY_ROW],
		register: [],
		register_total: 0,
		counts: { Drafts: 0, Returned: 0, Approvals: 0 },
		filters: FILTERS,
		department_filter_label: "All my departments",
	};
	switch (variant) {
		case "DRAFT":
			return {
				...base,
				ready_to_start: [],
				your_work: [
					{
						requisition: "PR-0001", reference: REF, title: TITLE, task: "Complete request details",
						detail: "Add the laptop request matching the requested quantities.",
						meta: `${REF} · Updated 1 Mar 2027, 09:45 EAT`, action: "Continue", route: REGISTER_ROW.route, kind: "draft",
					},
				],
				register: [REGISTER_ROW],
				counts: { Drafts: 1, Returned: 0, Approvals: 0 },
			};
		case "ACTION":
			return {
				...base,
				ready_to_start: [],
				your_work: [
					{
						requisition: "PR-0001", reference: REF, title: TITLE, task: "Review departmental requisition",
						detail: "Certify that it states both departments’ need and minimum requirements, or return it for correction.",
						meta: `${REF} · Submitted for your decision 8 Mar 2027, 09:00 EAT`, action: "Review",
						route: "/app/procurement-requisitions/department-task/RT-0001", kind: "decision", task_id: "RT-0001",
					},
				],
				counts: { Drafts: 0, Returned: 0, Approvals: 1 },
			};
		case "NONE":
			return { ...base, ready_to_start: [] };
		case "TECHNICAL":
			return {
				...base,
				mode: "technical",
				ready_to_start: [],
				register: [REGISTER_ROW],
				register_total: 1,
				counts: {},
				filters: { ...FILTERS, fiscal_years: [{ value: "2027-2028", label: "FY 2027/28" }] },
				department_filter_label: "All departments",
			};
		default:
			return base;
	}
}

export function startPreview(state = "ready") {
	const base = {
		outcome: "OK",
		state: "ready",
		message: "",
		may_start: true,
		plan_item_id: "PI-0001",
		plan_item_reference: "PPI-MOH-2027-033",
		title: TITLE,
		departments: "Digital Health; Human Resources Management and Development",
		available_quantity: "250 Each",
		available_value: "KES 50,000,000.00",
		plan_completion_boundary: "31 Dec 2027",
		requirement_product: "IT Equipment",
		reserved_for: "Youth",
		county_requirement: "",
		reservation_rule: { label: "Applicable verified Youth reservation rule · Version 1", available: true },
		plan_horizon: "Single year",
		failed_check: "",
		submitting_department: "Digital Health",
		combined: true,
		existing: null,
		is_system_manager: false,
	};
	switch (state) {
		case "unsupported":
			return { ...base, state, may_start: false, requirement_product: "Software integration", message: "This approved purchase requires software integration, which this release does not support." };
		case "rule_unavailable":
			return { ...base, state, may_start: false, reservation_rule: { label: "Not ready", available: false }, message: "The applicable reservation rule is not ready for this purchase. Ask your KenTender administrator to complete the rule in System setup." };
		case "reservation_unsupported":
			return { ...base, state, may_start: false, county_requirement: "County residents", message: "This reservation treatment is not supported by the installed IT-equipment Tender format." };
		default:
			return base;
	}
}

const AMOUNTS = [
	{
		drawdown_line_id: "RDL-001", department: "Human Resources Management and Development", requirement: "Business laptops", source_reference: "SRC-MOH-033-001",
		available_quantity: "100 Each", requested_quantity: "100 Each", available_value: "KES 20,000,000.00", requested_value: "KES 20,000,000.00",
		requested_quantity_value: "100", requested_value_value: "20000000.00", remaining_quantity_value: "100", remaining_value_value: "20000000.00", editable: true,
	},
	{
		drawdown_line_id: "RDL-002", department: "Digital Health", requirement: "Business laptops", source_reference: "SRC-MOH-033-002",
		available_quantity: "150 Each", requested_quantity: "150 Each", available_value: "KES 30,000,000.00", requested_value: "KES 30,000,000.00",
		requested_quantity_value: "150", requested_value_value: "30000000.00", remaining_quantity_value: "150", remaining_value_value: "30000000.00", editable: true,
	},
];

const ITEMS = [
	{ requisition_item_id: "RQI-001", drawdown_line_id: "RDL-001", item_name: "Business laptops", equipment_category: "Laptop", department: "Human Resources Management and Development", approved_requirement: "HR Management and Development — SRC-MOH-033-001", quantity: "100 Each", quantity_value: 100, intended_use: "Clinical training for Human Resources Management and Development staff", delivery: "Nairobi; 30 Sep 2027", editable: true },
	{ requisition_item_id: "RQI-002", drawdown_line_id: "RDL-002", item_name: "Business laptops", equipment_category: "Laptop", department: "Digital Health", approved_requirement: "Digital Health — SRC-MOH-033-002", quantity: "150 Each", quantity_value: 150, intended_use: "Field digital-health deployment for Digital Health staff", delivery: "Nairobi; 30 Sep 2027", editable: true },
];

export function editor(variant) {
	const base = {
		outcome: "OK", kind: "editor", mode: "editor",
		header: { requisition: "PR-0001", reference: REF, title: TITLE, badge: { label: "Draft", tone: "is-draft" }, description: "Complete the request using the approved purchase shown below.", record_version: 1, version: "RQV-1", version_number: 1, version_record_version: 3 },
		package_record_version: 2, lead_org_unit_id: "OU-DH", lead_department: "Digital Health",
		tasks: [
			{ key: "request_details", label: "Request details", status: "Needs attention" },
			{ key: "requirements", label: "Requirements", status: "Not started" },
			{ key: "review_submit", label: "Review and submit", status: "Not started" },
		],
		footer_hints: { request_details: "Add the laptop request matching the requested quantities.", requirements: "", review_submit: "" },
		returned: null,
		purchase: {
			title: TITLE, departments: BOTH, available: "250 Each · KES 50,000,000.00 available", method: "Open Tender", reserved_for: "Youth", county_requirement: "",
			plan_completion_boundary: "31 Dec 2027", business_need: "Equip clinical training and field deployment staff with a common laptop specification for the national digital health rollout.",
			source_details: [
				{ label: "Plan Item reference", value: "PPI-MOH-2027-033" }, { label: "Estimated completion", value: "24 Sep 2027" }, { label: "Lotting", value: "Single lot" },
				{ label: "Strategic objective", value: "Strengthen interoperable national digital health services · OBJ-MOH-2023-001" },
				{ label: "Reserved for", value: "Youth · Applicable verified Youth reservation rule · Version 1" },
				{ label: "Approved requirements", value: "SRC-MOH-033-001; SRC-MOH-033-002" },
			],
		},
		remaining_original: { shown: false },
		request_information: { requirement_title: TITLE, delivery_location: "LOC-1", latest_delivery_date: "2027-09-30", related_services_required: false, locations: [{ name: "LOC-1", location_name: "Afya House", address: "Ministry of Health Headquarters, Afya House, Nairobi" }] },
		amounts: AMOUNTS,
		equipment: { rows: [], shared_specification: null, add_rows: [{ drawdown_line_id: "RDL-001", department: "Human Resources Management and Development", source_reference: "SRC-MOH-033-001", quantity: 100, unit: "Each", editable: true }, { drawdown_line_id: "RDL-002", department: "Digital Health", source_reference: "SRC-MOH-033-002", quantity: 150, unit: "Each", editable: true }] },
		actions: { save: true, save_label: "Save draft", edit_shared: true, contributor: false },
		catalogue: { categories: ["Laptop", "Desktop computer"] },
	};
	const complete = {
		...base,
		tasks: [{ ...base.tasks[0], status: "Complete" }, { ...base.tasks[1], status: "Needs attention" }, base.tasks[2]],
		footer_hints: { request_details: "" },
		equipment: { rows: ITEMS, add_rows: [], shared_specification: { label: "One shared laptop specification · 2 approved requirements", equipment_category: "Laptop", item_name: "Business laptops", requisition_item_ids: ["RQI-001", "RQI-002"] } },
	};
	switch (variant) {
		case "COMPLETE":
			return complete;
		case "RETURNED":
			return { ...base, header: { ...base.header, badge: { label: "Draft correction", tone: "is-draft" } }, returned: { reason: "Replace the processor wording with a measurable, supplier-neutral minimum.", returned_by: "Dr Peter Kimani", returned_at: "8 Mar 2027, 09:10 EAT", affected_section: "Technical requirements", task: "request_details", section: "" } };
		case "CONTRIBUTOR":
			return {
				...complete, mode: "contributor",
				amounts: [{ ...AMOUNTS[0], editable: true }, { ...AMOUNTS[1], editable: false }],
				actions: { save: true, save_label: "Save my changes", edit_shared: false, contributor: true },
			};
		default:
			return base;
	}
}

const TECH = (id, key, label, comparison, display, unit, value, state = "Proposed") => ({ technical_requirement_id: id, characteristic_key: key, label, comparison, display, unit, value, state, applies_to_scope: "All items" });
const TECH_GROUPS = (state) => [
	{ group: "Basic equipment", rows: [TECH("T1", "electrical_compatibility", "Electrical compatibility", "Required", "Yes — suitable for Kenyan mains supply", "—", { value: "Yes" }, state), TECH("T2", "new_unused_equipment", "New and unused equipment", "Required", "Yes", "—", { value: "Yes" }, state)] },
	{
		group: "Performance and storage",
		rows: [
			TECH("T3", "memory", "Memory", "Minimum", "16", "GB", { value: 16 }, state), TECH("T4", "storage_capacity", "Storage capacity", "Minimum", "512", "GB", { value: 512 }, state),
			TECH("T5", "storage_type", "Storage type", "One of", "NVMe SSD", "—", { value: "NVMe SSD" }, state), TECH("T6", "display_size", "Display size", "Minimum", "14.0", "inches", { value: "14.0" }, state),
			TECH("T7", "battery_runtime", "Battery runtime", "Minimum", "8", "hours", { value: "8" }, state), TECH("T8", "processor_requirement", "Processor requirement", "Minimum", "64-bit business-class processor, minimum 10 cores or equivalent benchmark", "—", { value: "64-bit business-class processor, minimum 10 cores or equivalent benchmark" }, state),
			TECH("T9", "operating_system_compatibility", "Operating-system compatibility", "Required", "Approved organisational Windows environment", "—", { value: "Approved organisational Windows environment" }, state),
		],
	},
	{ group: "Connectivity", rows: [TECH("T10", "network_connectivity", "Network connectivity", "Required · every selected capability is required", "Wi-Fi 6 and Bluetooth 5 or later", "—", { values: ["Wi-Fi 6", "Bluetooth 5 or later"] }, state), TECH("T11", "required_ports", "Required ports", "Required", "USB-C ×2; USB-A ×2; HDMI ×1", "—", { ports: [{ port_type: "USB-C", minimum_count: 2 }] }, state)] },
];
const ACC = (id, check, condition, evidence, state) => ({ acceptance_requirement_id: id, check_type: check, applies_to: "All items", applies_to_scope: "All items", pass_condition: condition, evidence, evidence_type: evidence, state });
const ACCEPTANCE = (state) => [
	ACC("A1", "Quantity", "Delivered quantities equal the authorised schedule", "Inspection record", state),
	ACC("A2", "Physical condition", "No visible damage and all listed accessories are present", "Inspection record", state),
	ACC("A3", "Required specification", "Every delivered unit complies with all mandatory technical rows", "Inspection record", state),
	ACC("A4", "Functional test", "Each device powers on and completes the agreed basic functional test", "Test result", state),
	ACC("A5", "Documents received", "Warranty and delivery documents are received and verified", "Certificate", state),
];

export function requirements(variant) {
	const complete = editor("COMPLETE");
	const reviewed = variant === "COMPLETE";
	return {
		...complete,
		tasks: [{ ...complete.tasks[0], status: "Complete" }, { ...complete.tasks[1], status: reviewed ? "Complete" : "Needs attention" }, complete.tasks[2]],
		footer_hints: { request_details: "", requirements: reviewed ? "" : "Review and use the selected standard requirements.", review_submit: "" },
		findings: reviewed ? [] : [{ code: "PACKAGE_REVIEW_REQUIRED", severity: "Blocking", task: "requirements", section: "technical", message: "Review and use the selected standard requirements." }],
		requirements: {
			review_state: reviewed ? "Reviewed" : "Review required", profile_key: "LAPTOP-REQUIREMENTS-V1", profile_version: "1", proposal_digest: "abc", is_laptop_profile: true,
			technical_groups: TECH_GROUPS(reviewed ? "Confirmed" : "Proposed"), acceptance: ACCEPTANCE(reviewed ? "Confirmed" : "Proposed"),
			support: { minimum_warranty_months: 36, onsite_support_required: 1, maximum_support_response_hours: 8, manufacturer_support_required: 1, service_location_constraint: "Within Kenya", support_description: "Supplier to provide escalation and warranty-contact details." },
			services: [], materials: [],
		},
		catalogue: { ...complete.catalogue, service_locations: ["None", "Within Kenya", "At delivery location"], characteristics: [] },
	};
}

export function reviewSections() {
	return [
		{
			key: "purpose", title: "Purpose and approved purchase", icon: "target", open: true, compact: false,
			summary: "Clinical training and deployment laptops · Digital Health and HR Management and Development · Open Tender · Reserved for Youth",
			issues: [{ code: "DATE_AFTER_ESTIMATE", severity: "Warning", message: "The requested delivery date is 6 days after the plan’s estimated completion date." }],
			facts: [{ label: "Requirement title", value: TITLE }, { label: "Method", value: "Open Tender" }, { label: "Reserved for", value: "Youth" }],
			narrative: [
				{ label: "Business need", value: "Equip clinical training and field deployment staff with a common laptop specification for the national digital health rollout." },
				{ label: "Strategic objective", value: "Strengthen interoperable national digital health services" },
				{ label: "Expected operational result", value: "Staff can use secure, supported equipment for training and field digital-health work." },
			],
		},
		{ key: "amounts", title: "Amounts requested", icon: "coins", open: false, summary: "2 departments · 250 Each · KES 50,000,000.00", issues: [], rows: [], total_quantity: "250 Each", total_value: "KES 50,000,000.00" },
		{ key: "equipment", title: "Equipment", icon: "monitor", open: false, summary: "2 laptop rows · one shared specification", issues: [], rows: [] },
		{ key: "requirements", title: "Requirements and support", icon: "sliders", open: false, summary: "11 technical requirements · 36-month warranty · support within Kenya", issues: [], groups: [], support: [] },
		{ key: "services", title: "Related services", icon: "wrench", open: false, compact: true, summary: "None requested", empty_text: "None requested", issues: [], rows: [] },
		{ key: "acceptance", title: "Acceptance", icon: "check-square", open: false, summary: "5 delivery checks", issues: [], rows: [] },
		{ key: "supporting_materials", title: "Supporting materials", icon: "paperclip", open: false, compact: true, summary: "None added", empty_text: "None added", issues: [], rows: [] },
	];
}

export function review(variant) {
	const base = requirements("COMPLETE");
	const direct = variant === "DIRECT-HOD";
	return {
		...base,
		tasks: base.tasks.map((t) => (t.key === "review_submit" ? { ...t, status: "Not started" } : { ...t, status: "Complete" })),
		footer_hints: {},
		findings: [],
		review: {
			result: direct ? "Ready to submit to Procurement" : "Ready to send for department approval",
			warnings: [{ code: "DATE_AFTER_ESTIMATE", severity: "Warning", message: "The requested delivery date is 6 days after the plan’s estimated completion date." }],
			dates: [{ label: "Estimated completion", value: "24 Sep 2027" }, { label: "Latest delivery date", value: "30 Sep 2027" }, { label: "Plan completion boundary", value: "31 Dec 2027" }],
			sections: reviewSections(),
		},
		record_details: [{ label: "Requisition", value: REF }],
		actions: direct
			? { save: true, save_label: "Save draft", edit_shared: true, submit_to_procurement: true, withdraw: true, request_planning_correction: true }
			: { save: true, save_label: "Save draft", edit_shared: true, send_for_department_approval: true },
	};
}

export function departmentTask(variant) {
	const submitted = variant === "SUBMITTED";
	return {
		outcome: "OK", kind: "department_task", mode: submitted ? "reader" : "decider",
		header: { requisition: "PR-0001", reference: REF, title: "Review departmental requisition", requirement_title: TITLE, badge: submitted ? { label: "Submitted to Procurement", tone: "is-draft" } : { label: "Awaiting your approval", tone: "is-attention" }, description: "Confirm that the request accurately states the departments’ need and minimum requirements.", record_version: 4 },
		task: { task: "RT-0001", status: submitted ? "Completed" : "Open", record_version: 1 },
		context: [
			{ label: "Result", value: "Ready for departmental submission" }, { label: "Prepared by", value: "Grace Wanjiku" },
			{ label: "Contributing departments", value: "Digital Health; HRMD" }, { label: "Submitting department", value: "Digital Health" },
		],
		question: "Does this requisition accurately state both departments’ need and minimum requirements?",
		certification: "I confirm that this requisition states the departments’ operational need and minimum requirements and may be submitted to Procurement.",
		decision_chain: [
			{ title: "Draft prepared", meta: "1 Mar 2027 · Grace Wanjiku · Digital Health", tone: "is-live" },
			{ title: "Head of User Department approval", meta: "Awaiting your decision", tone: "is-attention" },
			{ title: "Procurement authorisation", meta: "Not yet reached", tone: "is-pending", upcoming: true },
			{ title: "Tender Preparation", meta: "Not started", tone: "is-pending", upcoming: true },
		],
		sections: reviewSections(), findings: [], record_details: [],
		actions: submitted
			? { submit_to_procurement: false, return_for_correction: false, withdraw: true, request_planning_correction: true }
			: { submit_to_procurement: true, return_for_correction: true, withdraw: true, request_planning_correction: true },
		catalogue: { affected_sections: ["Request details", "Technical requirements"] },
		requisition: "PR-0001", root_record_version: 4,
	};
}

const CHECKS = [
	["procurement_category", "Procurement category", "Goods"], ["requirement_type", "Requirement type", "Straightforward off-the-shelf IT equipment"],
	["reservation_category", "Planned designation", "Youth — supported; exact verified rule snapshot bound"], ["county_resident_reservation", "County-residents restriction", "Not applicable"],
	["lotting_indicator", "Lotting indicator", "Single lot"], ["currency", "Currency", "KES"], ["award_package", "Award package", "One"],
	["procurement_method", "Planned method", "Open Tender"], ["plan_horizon", "Plan horizon", "Single year"],
].map(([test, label, result]) => ({ test, label, ok: true, result, failure: "", code: "" }));

export function procurementTask(variant) {
	const technical = variant === "TECHNICAL";
	const shortfall = variant === "BLOCKING-FUNDING";
	const hold = variant === "HOLD";
	const result = shortfall
		? { tone: "is-critical", title: "Cannot authorise — insufficient funding", detail: "" }
		: hold
			? { tone: "is-warning", title: "Authorisation is on hold while Planning reviews a correction request.", detail: "UI-CORR-001 · Open" }
			: { tone: "is-live", title: "Ready to authorise", detail: technical ? "" : "Authorising will reserve KES 50,000,000.00 and allow Tender Preparation to begin." };
	const decider = !technical;
	return {
		outcome: "OK", kind: "procurement_task", mode: decider ? "decider" : "reader",
		header: { requisition: "PR-0001", reference: REF, title: "Authorise requisition", badge: { label: "Submitted to Procurement", tone: "is-draft" }, description: "Review the request, current funding and procurement checks before authorising it." },
		task: { task: "RT-0002", status: "Open", record_version: 1 },
		result, question: "Can this complete requisition lawfully use the approved-plan amount and current funding now?",
		funding: {
			available: true, all_sufficient: !shortfall,
			lines: [shortfall
				? { budget_line: "MOH-BL-HWD-2027", approved: "KES 60,000,000.00", available_now: "KES 40,000,000.00", this_requisition: "KES 50,000,000.00", available_after: "", sufficient: false, shortfall: "KES 10,000,000.00", reserved_share: 100, free_share: 0 }
				: { budget_line: "MOH-BL-HWD-2027", approved: "KES 60,000,000.00", available_now: "KES 60,000,000.00", this_requisition: "KES 50,000,000.00", available_after: "KES 10,000,000.00", sufficient: true, shortfall: "KES 0.00", reserved_share: 83, free_share: 17 }],
			sources: [{ department: "Human Resources Management and Development", requested_value: "KES 20,000,000.00" }, { department: "Digital Health", requested_value: "KES 30,000,000.00" }],
		},
		planning: { status: "Eligible", quantity_available: "250 Each", value_available: "KES 50,000,000.00", hold: hold ? "1 unresolved" : "None unresolved", hold_requests: [] },
		certification: { submitted_by: "Dr Peter Kimani", lead_department: "Digital Health", submitted_at: "8 Mar 2027, 09:00 EAT" },
		change_department: { available: decider, options: [{ value: "OU-HR", label: "Human Resources Management and Development" }, { value: "OU-DH", label: "Digital Health" }], current: "OU-DH" },
		checks: { summary: "9 checks passed", rows: CHECKS, open: false },
		decision_chain: [
			{ title: "Draft prepared", meta: "1 Mar 2027 · Grace Wanjiku · Digital Health", tone: "is-live" },
			{ title: "Certified and submitted by the department", meta: "8 Mar 2027, 09:00 EAT · Dr Peter Kimani", tone: "is-live" },
			{ title: "Procurement authorisation", meta: "Awaiting your decision", tone: "is-attention" },
			{ title: "Tender Preparation", meta: "Not started", tone: "is-pending", upcoming: true },
		],
		sections: reviewSections(), record_details: [],
		statement: "I authorise this requisition. The approved-plan amounts will be used, funding will be reserved and Tender Preparation may begin.",
		confirmation: { quantity: "250 Each", value: "KES 50,000,000.00", budget_line: "MOH-BL-HWD-2027", available_after: "KES 10,000,000.00", text: "The approved-plan amounts will be used, two funding reservations will be created and Tender Preparation may begin." },
		actions: { authorise: decider && !shortfall && !hold, return_to_department: decider, request_planning_correction: decider && !shortfall && !hold, change_submitting_department: decider, refresh: decider, view_planning_request: hold },
		catalogue: { affected_sections: ["Request details"] },
		requisition: "PR-0001", root_record_version: 5,
	};
}

export function authorised(variant) {
	const state = variant === "REVOKED" ? "Revoked" : "Authorised";
	const consumed = variant === "CONSUMED";
	const mode = { HOPF: "hopf", AUDITOR: "reader" }[variant] || "officer";
	return {
		outcome: "OK", kind: "authorised", state, mode,
		header: { requisition: "PR-0001", reference: REF, title: TITLE, badge: state === "Revoked" ? { label: "Authorisation revoked", tone: "is-critical" } : { label: "Authorised", tone: "is-live" }, description: state === "Authorised" && !consumed ? "This requisition is authorised and ready for Tender Preparation." : "", tagline: "Open Tender · Reserved for Youth · Single lot", version: "RQV-1", version_number: 1 },
		facts: [
			{ label: "Authorised by", value: "Charles Mutiso" }, { label: "Authorised at", value: "15 Mar 2027, 10:00 EAT" },
			{ label: "Requisition value", value: "KES 50,000,000.00" }, { label: "Tender Preparation", value: consumed ? "Started" : "Not started" },
		],
		consumed: consumed ? { tender: "TND-1", tender_reference: "TND-MOH-2027-033", route: "/app/tenders/TND-1" } : null,
		revoked: state === "Revoked" ? { by: "Charles Mutiso", at: "16 Mar 2027, 10:00 EAT", reason: "The authorised warranty terms must be corrected before tendering.", planning_reversal: "REV-PDR-1", funding_releases: "RSV-1; RSV-2" } : null,
		decision_chain: [{ title: "Draft prepared", meta: "1 Mar 2027", tone: "is-live" }],
		sections: reviewSections().map((s) => ({ ...s, open: false, issues: [] })),
		reservations: [{ reservation: "RSV-MOH-2027-033-001", department: "Human Resources Management and Development", value: "KES 20,000,000.00" }, { reservation: "RSV-MOH-2027-033-002", department: "Digital Health", value: "KES 30,000,000.00" }],
		record_details: [{ label: "Planning drawdown display reference", value: "PDR-MOH-2027-033-001" }],
		actions: {
			continue_to_tender_preparation: mode === "officer" && state === "Authorised" && !consumed, open_tender: consumed,
			revoke: mode === "hopf" && state === "Authorised" && !consumed, start_corrected_draft: false, export: true,
		},
		tender_route: "/app/tenders/new/ARH-1", requisition: "PR-0001", root_record_version: 7,
	};
}

export function stopped(variant) {
	const status = { RESOLVED: "Resolved", CLOSED: "Closed without change", PROGRESS: "In progress" }[variant] || "Open";
	const labels = { Open: ["Awaiting Planning correction", "is-attention"], "In progress": ["Planning correction in progress", "is-attention"], Resolved: ["Planning correction completed", "is-live"], "Closed without change": ["Planning request closed without change", "is-pending"] };
	const terminal = status === "Resolved" || status === "Closed without change";
	return {
		outcome: "OK", kind: "stopped", status, status_label: labels[status][0], status_tone: labels[status][1],
		header: { requisition: "PR-0001", reference: REF, title: TITLE, badge: { label: labels[status][0], tone: labels[status][1] }, description: "Planning is reviewing an approved-plan issue. This requisition is preserved and cannot be edited or resumed." },
		request: { reference: "UI-CORR-001", status: `UI-CORR-001 · ${status === "Open" ? "Open" : status}`, plan_item: "PPI-MOH-2027-033", reason: "The approved source allocation refers to the wrong Budget Line. Please review the departmental funding specification through the governed Planning correction process.", requested_by: "Dr Peter Kimani", requested_at: "10 Mar 2027, 09:00 EAT", started: "" },
		outcome_text: terminal ? "Resolved by Mercy Kilonzo." : "", unchanged_notice: status === "Closed without change" ? "The approved Planning facts have not changed. This requisition will not restart." : "",
		unavailable: variant === "UNAVAILABLE", other_unresolved: variant === "ANOTHER" ? [{ reference: "UI-CORR-002", status: "Open" }] : [],
		hold_notice: variant === "ANOTHER" ? "Authorisation remains on hold: 1 Planning request is still unresolved." : "",
		correction_chain: [
			{ title: "Requisition submitted to Procurement", meta: "8 Mar 2027 · Dr Peter Kimani", tone: "is-live" },
			{ title: "Planning correction requested · work stopped", meta: "10 Mar 2027, 09:00 EAT · UI-CORR-001", tone: "is-critical" },
			{ title: "Planning review", meta: "Awaiting Procurement Planner", tone: "is-attention" },
			{ title: "Outcome recorded", meta: "This requisition will not reopen automatically", tone: "is-pending", upcoming: true },
		],
		sections: [], record_details: [],
		fresh_start: terminal ? { heading: "Start a new requisition?", text: "Use the Active corrected Planning facts shown. Earlier decisions and funding reservations will not be copied.", facts: [{ label: "Stopped requisition", value: REF }, { label: "Current Plan", value: "PLN-MOH-2027-001" }, { label: "Current Plan Version", value: "Version 2" }, { label: "Current eligibility", value: "Eligible" }], blocked_message: "" } : null,
		actions: { view_planning_request: true, open_planning_task: false, start_new_requisition: terminal, try_again: variant === "UNAVAILABLE", export: false },
		planning_route: "/app/procurement-planning/correction/UI-CORR-001", requisition: "PR-0001", root_record_version: 6,
	};
}

export function versionReview() {
	return {
		outcome: "OK", kind: "version",
		header: { requisition: "PR-0001", reference: REF, title: TITLE, badge: { label: "Returned", tone: "is-critical" }, version: "RQV-1", version_number: 1 },
		decision: { by: "Dr Peter Kimani", at: "8 Mar 2027, 09:10 EAT", reason: "Replace the processor wording with a measurable, supplier-neutral minimum.", affected_section: "Technical requirements", decision: "Return for correction" },
		current_draft_route: "/app/procurement-requisitions/PR-0001", sections: [], record_details: [], actions: { export: true }, requisition: "PR-0001",
	};
}
