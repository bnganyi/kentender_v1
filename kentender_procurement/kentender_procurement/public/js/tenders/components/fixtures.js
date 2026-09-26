// Component fixtures for the Tenders screens (TPR-CHG-001 v0.12 §10.1 /
// §10.17): each builder returns what the server's read returns for that
// board variant, so component, fidelity and guidance tests share one shape.
// Guidance answers mirror kentender_core.services.next_step (answer, journey)
// field for field — the components only ever draw them.

const STAGES = [
	["PREPARE", "Prepare Tender"],
	["HOPF_APPROVAL", "HOPF approval"],
	["AO_AUTHORISATION", "AO publication authorisation"],
	["PUBLICATION", "Confirm publication"],
	["OPEN_MANAGEMENT", "Manage open Tender"],
];
const MARKERS = { D: ["done", "Done"], C: ["current", "Current"], B: ["blocked", "Blocked"], N: ["not_started", "Not started"] };
const KIND_LABELS = { your_turn: "Your turn", your_turn_blocked: "Your turn, blocked", waiting: "Waiting on someone", done: "Done", not_involved: "Not involved" };

/** A Tender journey from the §10.17 marker tuple ("D/D/C/N/N"). */
export function journey(markers, holder = "") {
	const marks = markers.split("/");
	const stages = STAGES.map(([code, label], index) => {
		const [marker, marker_label] = MARKERS[marks[index]];
		return { code, label, marker, marker_label, holder: marker === "current" || marker === "blocked" ? holder : "" };
	});
	const index = marks.findIndex((m) => m === "C" || m === "B");
	const current = index >= 0 ? stages[index] : null;
	return {
		stages,
		current: current ? current.code : "",
		reduced: false,
		reduced_style: "position",
		reduced_parts: current ? { prefix: "", label: current.label + (current.marker === "blocked" ? " (blocked)" : ""), suffix: ` · ${index + 1} of 5` + (holder ? ` · ${holder}` : "") } : null,
		upstream: null,
		downstream: null,
	};
}

/** One next-step answer. */
export function step(kind, headline, extra = {}) {
	return { kind, label: KIND_LABELS[kind], headline, sentence: "", stage: "", holder: null, since: null, blockers: [], fixes: [], primary_action: "", ...extra };
}

/** Your turn, blocked with one blocker and its fixes (labels in order; the first is primary). */
export function blockedStep(headline, fixLabels, reason = "TND_MUST_FIX") {
	const fixes = fixLabels.map((label, index) => ({ label, fix_id: `fix-${index}`, kind: "command", primary: index === 0 }));
	return step("your_turn_blocked", headline, { blockers: [{ reason_code: reason, headline, message: headline, facts: [], fixes }] });
}

export function guidance(markers, holder, answer) {
	return { journey: journey(markers, holder), next_step: answer };
}

const TENDER = {
	name: "TDR-0001", tender_reference: "TND-MOH-2027-033", title: "Supply and delivery of business laptops", requirement_title: "Clinical training and deployment laptops for digital health rollout",
	requisition_reference: "REQ-MOH-2027-033-001", plan_item_id: "PPI-MOH-2027-033", overall_status: "Draft", badge: "Draft", record_version: 3,
};

const REQUIREMENT_TABLES = [
	{ key: "items", columns: [{ label: "Item" }, { label: "Approved requirement" }, { label: "Quantity", num: true }, { label: "Delivery" }], rows: [["Business laptops", "Human Resources Management and Development", "100 Each", "Afya House, Nairobi · 30 Sep 2027"], ["Business laptops", "Digital Health", "150 Each", "Afya House, Nairobi · 30 Sep 2027"]] },
	{ key: "technical", columns: [{ label: "Technical requirement" }, { label: "Value" }], rows: [["Memory", "Minimum 16 GB"], ["Storage capacity", "Minimum 512 GB"]] },
	{ key: "warranty", columns: [{ label: "Warranty and support" }, { label: "Value" }], rows: [["Minimum warranty", "36 months"], ["On-site support required", "Yes"]] },
	{ key: "acceptance", columns: [{ label: "Acceptance check" }, { label: "Pass condition" }, { label: "Evidence" }], rows: [["Quantity", "Delivered quantities equal the authorised schedule", "Inspection record"]] },
];

const INHERITED = {
	context: { purchase: TENDER.requirement_title, method: "Open Tender", quantity: "250 Each", latest_delivery: "30 Sep 2027", requisition_reference: TENDER.requisition_reference, plan_item_id: TENDER.plan_item_id, reservation_category: "Youth", lotting: "Single lot" },
	items: [],
	requirement_tables: REQUIREMENT_TABLES,
	carried_summary: [
		{ label: "Equipment", text: "Business laptops · 250 Each (100 + 150), Afya House, Nairobi, by 30 Sep 2027" },
		{ label: "Technical", text: "11 mandatory requirements" },
		{ label: "Warranty and support", text: "36 months, on-site, 8-hour response, within Kenya" },
		{ label: "Acceptance", text: "5 checks — quantity, physical condition, required specification, functional test, documents received" },
	],
	reservation_evidence: [{ label: "Youth reservation declaration and evidence", summary: "Suppliers must declare Youth eligibility and provide the published certificate reference, validity and evidence", source: "Required by reservation rule" }],
	internal: { authorised_value: "KES 50,000,000.00", strategic_objective: "Strengthen interoperable national digital health services", plan_horizon: "Single year", note: "For internal review only — not included in supplier documents." },
	counts: { technical_requirements: 11, acceptance_requirements: 5 },
};

const OFFICER_VALUES = {
	tender_title: "Supply and delivery of business laptops", issue_date: "2027-05-15", clarification_deadline: "2027-05-27 17:00:00", submission_deadline: "2027-06-05 11:00:00", tender_validity_days: 120,
	tender_security_amount: 500000, pre_tender_meeting: false, manufacturer_authorisation_required: true, datasheets_required: true, past_experience_required: true, minimum_comparable_contracts: 2,
	experience_period_years: 5, after_sales_evidence_required: true, after_sales_evidence: "Kenya service-centre details and escalation contacts", inspection_location: "Ministry of Health Headquarters, Afya House, Nairobi",
	payment_timing_days: 30, performance_security_required: true, performance_security_percent: 10, delay_damages_per_week_percent: 0.5, maximum_delay_damages_percent: 10, contract_contact_office: "Ministry of Health Procurement Office",
};

/** TPR-DES-03 / TPR-DES-04 (and the DES-13 returned Draft) — `GetTender` for the officer. */
export function editorRecord(variant = "") {
	const meeting = variant === "PHYSICAL" ? { pre_tender_meeting: true, meeting_datetime: "2027-05-22 10:00:00", meeting_mode: "Physical", meeting_venue: "Ministry of Health Headquarters, Afya House, Nairobi" } : variant === "ONLINE" ? { pre_tender_meeting: true, meeting_datetime: "2027-05-22 10:00:00", meeting_mode: "Online", online_joining_information: "Microsoft Teams — https://meet.example.test/tnd-moh-2027-033" } : {};
	const returned = variant === "RETURNED";
	return {
		outcome: "OK", mode: "site", screen: "editor",
		roles: { officer: true, hopf: false, ao: false, auditor: false, technical: false },
		tender: { ...TENDER },
		version: { version_number: returned ? 2 : 1 },
		tasks: { details: "Complete", requirements: "Complete", review: "Not started" },
		officer_values: { ...OFFICER_VALUES, ...meeting },
		options: { delivery_locations: ["Ministry of Health Headquarters, Afya House, Nairobi"], contact_offices: ["Ministry of Health Procurement Office"] },
		catalogue: {},
		evidence_requirements: variant === "EVIDENCE" ? [{ evidence_requirement_id: "EVR-001", label: "Electrical compatibility certificate", evidence_type: "Certificate", proves: "Electrical compatibility — suitable for Kenyan mains supply", mandatory: 1 }] : [],
		evaluation_stages: ["Eligibility", "Technical compliance", "Financial", "Award"],
		inherited: INHERITED,
		returned: returned ? { returned_by: "Charles Mutiso", returned_at: "25 Mar 2027, 14:00 EAT", comment: "Confirm whether manufacturer authorisation is necessary and update the supplier evidence requirement.", affected_task: "requirements" } : null,
		allowed_actions: ["save_draft", "continue", "review_tender", "add_evidence", "preview_documents", "view_history"],
		guidance: guidance("C/N/N/N/N", "Brian Wafula", step("your_turn", "Set the Tender dates, security and meeting details.")),
		task_steps: {
			details: step("your_turn", "Set the Tender dates, security and meeting details."),
			requirements: step("your_turn", returned ? "Address Charles Mutiso's return comment about manufacturer authorisation." : "Set supplier evidence and contract terms."),
		},
	};
}

const SECTIONS = (open) => [
	{ key: "details", title: "Tender details", summary: "Issue 15 May 2027 · submission 5 Jun 2027, 11:00 EAT", tag: "", open: false, blocks: [{ kind: "facts", facts: [{ label: "Tender title", value: "Supply and delivery of business laptops", wide: true }, { label: "Issue date", value: "15 May 2027" }] }] },
	{ key: "requirements", title: "Requirements from the authorised requisition", summary: "2 items · 11 technical requirements · 5 acceptance checks", tag: "", open: false, blocks: [{ kind: "table", title: "Equipment", columns: [{ label: "Item" }], rows: [["Business laptops"]], muted: [] }] },
	{ key: "pricing", title: "Supplier pricing schedule", summary: "1 line", tag: "", open: false, blocks: [{ kind: "table", title: "", columns: [{ label: "Line" }, { label: "Quantity", num: true }, { label: "Unit price" }, { label: "Tax" }, { label: "Total" }], rows: [["Business laptops", "250 Each", "Completed by supplier", "Completed by supplier", "Calculated from supplier response"]], muted: [2, 3, 4] }] },
	{ key: "supplier", title: "Supplier and evaluation requirements", summary: "Manufacturer authorisation, datasheets", tag: open.includes("supplier") ? "1 review note" : "", open: open.includes("supplier"), blocks: [{ kind: "table", title: "", columns: [{ label: "Requirement" }, { label: "Detail" }], rows: [["Manufacturer authorisation", "Yes"]], muted: [] }, { kind: "list", title: "How suppliers will be evaluated", items: ["Eligibility", "Technical compliance", "Financial", "Award"] }] },
	{ key: "contract", title: "Contract terms", summary: "Payment 30 days", tag: open.includes("contract") ? "1 must fix" : "", open: open.includes("contract"), blocks: [{ kind: "facts", facts: [{ label: "Inspection and acceptance location", value: "", wide: true }] }] },
	{ key: "technical", title: "Technical evidence", summary: "Template STD-IT-GOODS-OT-1.1", tag: "", open: false, blocks: [{ kind: "facts", facts: [{ label: "Template", value: "IT Equipment — Open Tender · Version 1.1" }] }] },
];

const KEY_FACTS = [
	{ label: "Requisition", value: TENDER.requisition_reference }, { label: "Quantity", value: "250 Each" }, { label: "Approved value", value: "KES 50,000,000.00" }, { label: "Method", value: "Open Tender" },
	{ label: "Submission deadline", value: "5 Jun 2027, 11:00 EAT" }, { label: "Tender security", value: "KES 500,000.00" }, { label: "Reservation", value: "Youth" }, { label: "Latest delivery", value: "30 Sep 2027" },
];

const NOTE = { finding_code: "TND-RN-001", severity: "Review note", task: "requirements", field: "manufacturer_authorisation_required", message: "Confirm that manufacturer authorisation is proportionate for this purchase.", link_label: "Review supplier requirements" };

/** TPR-DES-05 — `GetTenderReview` for the officer ("" ready, "BLOCKED" needs attention). */
export function reviewData(variant = "") {
	const blocked = variant === "BLOCKED";
	const mustFix = blocked ? [{ finding_code: "TND-MF-001", severity: "Must fix", task: "requirements", field: "inspection_location", message: "Enter the inspection and acceptance location.", link_label: "Review contract terms" }] : [];
	return {
		outcome: "OK", mode: "site",
		tender: { ...TENDER },
		review: { result: blocked ? "Needs attention" : "Ready to submit", findings: [...mustFix, NOTE], must_fix: mustFix, review_notes: [NOTE], must_fix_count: mustFix.length, review_note_count: 1 },
		key_facts: KEY_FACTS,
		sections: SECTIONS(blocked ? ["supplier", "contract"] : ["supplier"]),
		documents: [],
		allowed_actions: blocked ? ["save_draft", "view_history"] : ["save_draft", "submit_for_approval", "view_history"],
		submit_note: "The submitted Version will be locked. Charles Mutiso can return it or approve the package for publication review.",
		guidance: blocked
			? guidance("B/N/N/N/N", "Brian Wafula", blockedStep("Enter the inspection and acceptance location.", ["Review contract terms"]))
			: guidance("C/N/N/N/N", "Brian Wafula", step("your_turn", "Submit this Tender for approval.")),
	};
}

export function reviewRecord() {
	return { ...editorRecord(), tender: { ...TENDER } };
}
