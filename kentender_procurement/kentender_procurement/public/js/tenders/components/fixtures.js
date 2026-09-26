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

/** TPR-DES-06 — `GetTender` + `GetTenderReview` for the HOPF ("" normal, "SEGREGATION"). */
export function approvalData(variant = "") {
	const blocked = variant === "SEGREGATION";
	const review = reviewData();
	return {
		record: {
			...editorRecord(), screen: "approval",
			tender: { ...TENDER, overall_status: "Awaiting procurement approval" },
			version: { version_number: 2, submitted_by_name: "Brian Wafula", submitted_at_label: "15 Apr 2027, 09:15 EAT" },
			allowed_actions: blocked ? ["view_history"] : ["return_for_correction", "approve_tender_package", "view_history"],
		},
		review: {
			...review,
			allowed_actions: blocked ? ["view_history"] : ["return_for_correction", "approve_tender_package", "view_history"],
			guidance: blocked
				? guidance("D/B/N/N/N", "System Manager", step("waiting", "A System Manager must assign an eligible Head of Procurement Function to decide this Version.", { sentence: "You cannot approve a Tender Version you prepared or submitted." }))
				: guidance("D/C/N/N/N", "Charles Mutiso", step("your_turn", "Decide whether to approve this Tender package.")),
		},
	};
}

/** TPR-DES-07 — `GetTenderPublication` for the AO ("" normal, "SEGREGATION"). */
export function authorisationData(variant = "") {
	const blocked = variant === "SEGREGATION";
	const review = reviewData();
	return {
		outcome: "OK", mode: "site",
		tender: { ...TENDER, overall_status: "Approved" },
		approval_trail: { prepared_by_name: "Brian Wafula", approved_by_name: "Charles Mutiso", approved_at_label: "20 Apr 2027, 10:00 EAT", version_number: 2, package_digest: "a".repeat(64) },
		review: review.review,
		key_facts: [{ label: "Purchase", value: TENDER.title }, ...KEY_FACTS.slice(0, 5), { label: "Tendering period", value: "21 days" }, { label: "Reservation", value: "Youth" }],
		proposed_channels: ["State Portal", "Ministry website", "Notice board", "Two national newspapers"].map((label, i) => ({ channel: `C${i}`, label, how: "HOPF confirmation with evidence", result: "Not started" })),
		sections: review.sections,
		allowed_actions: blocked ? ["view_history"] : ["authorise_publication", "view_history"],
		guidance: blocked
			? guidance("D/D/B/N/N", "System Manager", step("waiting", "A System Manager must assign an eligible Accounting Officer to decide this Version.", { sentence: "You cannot authorise publication of a Tender Version you prepared, submitted or approved as Head of Procurement Function." }))
			: guidance("D/D/C/N/N", "Amina Hassan", step("your_turn", "Authorise publication of the approved Tender package.")),
	};
}

/** TPR-DES-08 — `GetTenderPublication` for the HOPF, 2 of 4 confirmed ("", "INVALID", "CONFLICT"). */
export function publicationData(variant = "") {
	const row = (channel, channel_label, confirmed, online) => ({
		name: `TCC-${channel}`, channel, channel_label, status: confirmed ? "Confirmed" : "Awaiting confirmation", result_label: confirmed ? "Confirmed" : "Awaiting confirmation",
		available_at_label: confirmed ? "15 May 2027, 08:00 EAT" : "", online, dialog_title: channel === "NOTICE_BOARD" ? "Confirm notice-board publication" : channel === "NATIONAL_NEWSPAPERS" ? `Confirm newspaper publication — ${channel_label}` : `Confirm ${channel_label} publication`,
	});
	const invalid = variant === "INVALID";
	const channels = [row("STATE_PORTAL", "State Portal", !invalid, true), row("MINISTRY_WEBSITE", "Ministry website", true, true), row("NOTICE_BOARD", "Notice board", false, false), row("NATIONAL_NEWSPAPERS", "Two national newspapers", false, false)];
	return {
		outcome: "OK", mode: "site",
		tender: { ...TENDER, overall_status: "Publication authorised" },
		publication: { channels, rule_line: "Authorised by Amina Hassan, 15 May 2027, 07:55 EAT · Publication rule PUB-RULE-MOH-OT-2027-01 · 4 required channels, all evidence based." },
		allowed_actions: ["confirm_publication_channel", "view_history"],
		guidance: guidance("D/D/D/C/N", "Charles Mutiso", step("your_turn", "Confirm publication through Notice board and Two national newspapers; 2 of 4 channels are confirmed.")),
		_refusal: invalid ? guidance("D/D/D/B/N", "Charles Mutiso", blockedStep("State Portal evidence could not be accepted.", ["Choose evidence file", "Confirm publication"], "TND_PUBLICATION_EVIDENCE_INVALID")) : variant === "CONFLICT" ? guidance("D/D/D/C/N", "Charles Mutiso", step("your_turn", "Continue with the channels still awaiting confirmation.")) : null,
		_conflict: variant === "CONFLICT" ? channels[0] : null,
	};
}

const QUESTION = "May the two comparable contracts be from different customers?";
const ANSWER = "Yes. The Tender requires two comparable contracts and does not require both contracts to be from the same customer.";

/** TPR-DES-11 — `GetTenderClarification` for the officer ("" ordinary, "CHANGE" published change, "FAILURE" delivery failure). */
export function clarificationData(variant = "") {
	const failure = variant === "FAILURE";
	const changeAnswer = guidance("D/D/D/D/B", "Brian Wafula", blockedStep("Issue an addendum before sending this answer.", ["Prepare addendum"], "TND_CLARIFICATION_ADDENDUM_REQUIRED"));
	changeAnswer.next_step.sentence = "A clarification cannot change requirements, criteria, dates or supplier obligations on its own.";
	return {
		outcome: "OK",
		tender: { name: "TDR-0001", tender_reference: "TND-MOH-2027-033", overall_status: "Published — open", record_version: 12, clarification_deadline_label: "27 May 2027, 17:00 EAT" },
		clarification: {
			name: "TCQ-0001", candidate_label: "Registered Tender candidate", candidate_name: "Afya Digital Supplies Limited", question: QUESTION, received_at_label: "26 May 2027, 09:00 EAT",
			status: failure ? "Answered" : "Awaiting response", related_addendum_reference: "None", response: failure ? ANSWER : "", response_audience: failure ? "All registered candidates" : "",
			affects_published_tender: false, required_addendum: "", required_addendum_reference: "", responded_by_name: failure ? "Brian Wafula" : "", responded_at_label: failure ? "26 May 2027, 11:00 EAT" : "", record_version: 1,
		},
		notices: failure ? [{ name: "TCN-0009", candidate_registration_id: "ARR-MOH-2027-033-009", destination_snapshot: "procurement@failed-delivery.example", attempt_count: 3, status: "Failed" }] : [],
		audiences: [{ value: "Asker only", label: "Only the supplier who asked" }, { value: "All registered candidates", label: "All registered candidates" }],
		allowed_actions: failure ? ["retry_notice"] : ["send_response", "prepare_addendum"],
		guidance: failure
			? guidance("D/D/D/D/B", "Charles Mutiso", blockedStep("1 candidate notice failed delivery; the Tender remains open.", ["Retry notice"], "TND_NOTICE_DELIVERY_FAILED"))
			: guidance("D/D/D/D/C", "Brian Wafula", step("your_turn", "Send the answer to all registered candidates.")),
		guidance_if_published_change: failure ? null : changeAnswer,
	};
}

/** TPR-DES-09 — `GetTender` + `GetTenderReview` on a published Tender, per viewer ("HOPF", "AO", "PO", "READER") and variant ("", "NO-ADDENDUM", "ENDED"). */
export function publishedData(role = "HOPF", variant = "") {
	const ended = variant === "ENDED";
	const noAddendum = variant === "NO-ADDENDUM";
	const channels = ["State Portal", "Ministry website", "Notice board", "Two national newspapers"].map((label, i) => ({ name: `TCC-${i}`, channel: `C${i}`, channel_label: label, status: "Confirmed", result_label: "Confirmed", available_at_label: "15 May 2027, 08:00 EAT" }));
	const addendum = { name: "TDA-0001", addendum_reference: "ADD-MOH-2027-033-001", status: "Issued", change_summary: "Delivery point clarified", issued_at_label: "31 May 2027, 09:00 EAT", revised_submission_deadline_label: "12 Jun 2027, 11:00 EAT" };
	const actions = { HOPF: ["prepare_addendum", "recommend_cancellation"], AO: ["cancel_tender"], PO: ["prepare_addendum"], READER: [] }[role];
	const steps = {
		HOPF: ["Charles Mutiso", step("your_turn", "Prepare an addendum or recommend cancellation if the open Tender needs it.", { sentence: "These are available options, not overdue work." })],
		PO: ["Brian Wafula", step("your_turn", "Prepare an addendum if the published Tender needs a non-material correction.", { sentence: "This is an available option, not assigned work." })],
		AO: ["Amina Hassan", step("your_turn", "You can cancel this open Tender on an applicable ground.", { sentence: "This is an available option, not an assigned cancellation review." })],
		READER: ["", step("not_involved", "")],
	}[role];
	return {
		record: {
			outcome: "OK", mode: "site", screen: "published",
			tender: { ...TENDER, overall_status: ended ? "Submission period ended" : "Published — open", badge: ended ? "Submission period ended" : "Published — open", published_at_label: "15 May 2027, 08:00 EAT", submission_deadline_label: noAddendum ? "5 Jun 2027, 11:00 EAT" : "12 Jun 2027, 11:00 EAT" },
			publication: { channels, authorised_by_name: "Amina Hassan", published_at_label: "15 May 2027, 08:00 EAT" },
			open_period: {
				addenda: noAddendum ? [] : [addendum], effective_addenda_count: noAddendum ? 0 : 1, current_addendum: noAddendum ? null : addendum,
				clarifications: [{ name: "TCQ-0001", question: "May the two comparable contracts be from different customers?", related_notice: "None", received_at_label: "26 May 2027, 09:00 EAT", status: "Answered", response_status: "Answered", candidate_notice: "1 of 1 delivered" }],
			},
			documents: [{ kind: "Invitation", digest: "d1" }, { kind: "Complete Tender", digest: "d2" }],
			decisions: [{ decision: "Approved", actor_name: "Charles Mutiso", decided_at_label: "20 Apr 2027, 10:00 EAT", version_number: 2 }, { decision: "Publication authorised", actor_name: "Amina Hassan", decided_at_label: "15 May 2027, 07:55 EAT" }],
			allowed_actions: ended ? ["view_history"] : [...actions, "view_history"],
			guidance: ended ? guidance("D/D/D/D/D", "", step("done", "The system closed supplier submission at 12 Jun 2027, 11:00 EAT.")) : guidance("D/D/D/D/C", steps[0], steps[1]),
		},
		review: { sections: reviewData().sections.map((s) => ({ ...s, open: false, tag: "" })) },
	};
}

/** TPR-DES-10 — `GetTenderAddendum`, the board's seven variants. */
export function addendumData(variant = "DRAFT") {
	const material = ["MATERIAL", "MATERIAL-WAIT", "MATERIAL-CLOSED"].includes(variant);
	const status = { HOPF: "Awaiting issue", AWAITING: "Awaiting publication confirmation", ISSUED: "Issued" }[variant] || "Draft";
	const issued = variant === "ISSUED";
	const labels = ["State Portal", "Ministry website", "Notice board", "Two national newspapers"];
	const channels = ["AWAITING", "ISSUED"].includes(variant)
		? labels.map((label, i) => ({ name: `TCC-A${i}`, channel: `C${i}`, channel_label: label, status: issued ? "Confirmed" : "Awaiting confirmation", result_label: issued ? "Confirmed" : "Awaiting confirmation", available_at_label: issued ? "31 May 2027, 09:00 EAT" : "", dialog_title: `Confirm addendum publication — ${label}` }))
		: [];
	const change = material
		? { affected_reference: "Business laptops — Quantity", affected_reference_key: "goods:1:quantity", previous_value: "250 Each", revised_value: "300 Each", reason: "Additional deployment sites require 50 more laptops", change_class: "Non-material correction" }
		: { affected_reference: "Goods and delivery — delivery location", affected_reference_key: "delivery_location", previous_value: "Ministry of Health Headquarters, Afya House, Nairobi", revised_value: "Ministry of Health Headquarters, Afya House, 3rd Floor Procurement Stores, Nairobi", reason: "The published address omitted the internal delivery point", change_class: "Administrative clarification" };
	const actions = {
		DRAFT: ["save_addendum_draft", "submit_addendum_for_issue", "discard_addendum_draft"],
		HOPF: ["return_addendum_for_correction", "issue_addendum"],
		AWAITING: ["confirm_addendum_channel"],
		ISSUED: [],
		MATERIAL: ["save_addendum_draft", "request_cancellation_review", "discard_addendum_draft", "view_cancellation_requirements"],
		"MATERIAL-WAIT": ["view_cancellation_requirements"],
		"MATERIAL-CLOSED": ["discard_addendum_draft", "view_cancellation_requirements"],
	}[variant];
	const g = {
		DRAFT: ["D/D/D/D/C", "Brian Wafula", step("your_turn", "Submit the non-material addendum for issue.")],
		HOPF: ["D/D/D/D/C", "Charles Mutiso", step("your_turn", "Decide whether to issue this addendum.")],
		AWAITING: ["D/D/D/D/C", "Charles Mutiso", step("your_turn", "Confirm publication of ADD-MOH-2027-033-001 through the remaining original channels.")],
		ISSUED: ["D/D/D/D/C", "", step("done", "Charles Mutiso completed addendum publication on 31 May 2027, 09:07 EAT.")],
		MATERIAL: ["D/D/D/D/B", "Brian Wafula", { ...blockedStep("Increasing the business laptops quantity from 250 to 300 cannot be issued as an addendum.", ["Ask Amina Hassan (Accounting Officer) to consider cancellation", "Discard addendum draft"], "TND_ADDENDUM_MATERIAL"), sentence: "Cancel the Tender and start a newly governed Tender if procurement must continue." }],
		"MATERIAL-WAIT": ["D/D/D/D/B", "Amina Hassan", step("waiting", "Accounting Officer Amina Hassan is considering cancellation of TND-MOH-2027-039.")],
		"MATERIAL-CLOSED": ["D/D/D/D/B", "Brian Wafula", blockedStep("The 250-to-300 Each addendum remains unissuable; Amina Hassan closed the cancellation review with a recorded reason.", ["Discard addendum draft"], "TND_ADDENDUM_MATERIAL")],
	}[variant];
	return {
		outcome: "OK", mode: "site",
		tender: { name: "TDR-0001", tender_reference: material ? "TND-MOH-2027-039" : "TND-MOH-2027-033", title: "Supply and delivery of business laptops", overall_status: "Published — open", record_version: 14, current_deadline_label: "5 Jun 2027, 11:00 EAT" },
		addendum: {
			name: "TDA-0001", addendum_number: 1, addendum_reference: material ? "ADD-MOH-2027-039-001" : "ADD-MOH-2027-033-001", status, affected_area: "Goods/delivery schedule", ...change,
			materiality_statement: material ? "" : "Same site; no change to scope, quantity, value or evaluation basis.", deadline_extension_required: !material, revised_submission_deadline: material ? "" : "2027-06-12 11:00:00",
			revised_submission_deadline_label: material ? "" : "12 Jun 2027, 11:00 EAT", issue_decided_by_name: ["AWAITING", "ISSUED"].includes(variant) ? "Charles Mutiso" : "", issue_decided_at_label: ["AWAITING", "ISSUED"].includes(variant) ? "31 May 2027, 08:30 EAT" : "",
			issued_at_label: issued ? "31 May 2027, 09:00 EAT" : "", confirmation_completed_at_label: issued ? "31 May 2027, 09:07 EAT" : "",
			cancellation_review_status: variant === "MATERIAL-WAIT" ? "Requested" : variant === "MATERIAL-CLOSED" ? "Closed" : "", cancellation_review_closed_reason: variant === "MATERIAL-CLOSED" ? "The additional sites will be served by a separate procurement." : "", record_version: 2,
		},
		references: [{ key: "delivery_location", label: "Goods and delivery — delivery location", area: "Goods/delivery schedule", value: "Ministry of Health Headquarters, Afya House, Nairobi", material: false }, { key: "goods:1:quantity", label: "Business laptops — Quantity", area: "Goods/delivery schedule", value: "250 Each", material: true }],
		change_classes: ["Administrative clarification", "Non-material correction", "Submission deadline extension"],
		affected_areas: ["Goods/delivery schedule", "Invitation detail", "Technical requirement", "Submission or opening detail", "Evaluation or contract term", "Other stated location"],
		material, material_text: material ? "This change cannot be made by addendum." : "",
		deadline_rule: { required: true, explanation: "This addendum is being issued within the governed late-amendment period.", current_deadline_label: "5 Jun 2027, 11:00 EAT" },
		channels, original_channels: labels.map((label, i) => ({ channel: `C${i}`, label })),
		editable: variant === "DRAFT" || variant === "MATERIAL", allowed_actions: actions,
		guidance: guidance(g[0], g[1], g[2]),
	};
}

/** TPR-DES-12 — `GetTenderCancellation`: "BASE" AO decision, "RECOMMEND", "REQUEST" review request, "CANCELLED-HOLDER", "CANCELLED-READER". */
export function cancelData(variant = "BASE") {
	const cancelled = variant.startsWith("CANCELLED");
	const holder = variant === "CANCELLED-HOLDER";
	const obligations = [
		...["State Portal", "Ministry website", "Notice board", "Two national newspapers"].map((label, i) => ({ obligation_id: `NOTICE-C${i}`, obligation_type: "Notice channel", label: `Cancellation notice — ${label}`, due_by: "18 Jun 2027", status: "Due", evidence_reference: "" })),
		{ obligation_id: "PPRA_REPORT", obligation_type: "PPRA report", label: "PPRA report", due_by: "18 Jun 2027", status: "Due", evidence_reference: "" },
		{ obligation_id: "CANDIDATE_NOTICE", obligation_type: "Candidate notice", label: "Candidate notices", due_by: "18 Jun 2027", status: "Recorded", evidence_reference: "No Tender-bound candidates were registered when the Tender was cancelled." },
	];
	const g = {
		BASE: ["D/D/D/D/C", "Amina Hassan", step("your_turn", "Decide whether to cancel this Tender for inadequate budgetary provision.")],
		RECOMMEND: ["D/D/D/D/C", "Amina Hassan", step("your_turn", "Decide whether to cancel this Tender for inadequate budgetary provision.")],
		REQUEST: ["D/D/D/D/C", "Amina Hassan", step("your_turn", "Consider the request to cancel TND-MOH-2027-039 because the proposed quantity increase cannot be issued by addendum.")],
		"CANCELLED-HOLDER": ["D/D/D/D/C", "Brian Wafula", step("your_turn", "Record the outstanding cancellation notices and PPRA report by 18 Jun 2027.")],
		"CANCELLED-READER": ["D/D/D/D/D", "", step("done", "Amina Hassan cancelled this Tender on 4 Jun 2027, 14:00 EAT.")],
	}[variant];
	return {
		outcome: "OK",
		tender: { name: "TDR-0034", tender_reference: variant === "REQUEST" ? "TND-MOH-2027-039" : "TND-MOH-2027-034", title: "Supply and delivery of district clinic printers", overall_status: cancelled ? "Cancelled" : "Published — open", badge: cancelled ? "Cancelled" : "Published — open", record_version: 9 },
		summary: { purchase: "Supply and delivery of district clinic printers", tender: "TND-MOH-2027-034", published_at: "20 May 2027, 08:00 EAT", submission_deadline: "10 Jun 2027, 11:00 EAT", required_channels: "State Portal, Ministry website, Notice board, Two national newspapers", channel_count: 4 },
		grounds: [{ key: "INADEQUATE_BUDGET", label: "Inadequate budgetary provision" }],
		recommendation: variant === "RECOMMEND" ? { by_name: "Charles Mutiso", at_label: "4 Jun 2027, 13:30 EAT", text: "I recommend cancellation because the confirmed budget is insufficient to complete this procurement.", ground: "INADEQUATE_BUDGET" } : null,
		consequences: { ppra_report_due_by: "18 Jun 2027", candidate_notice_due_by: "18 Jun 2027", replacement_text: "Replacement procurement requires new governance." },
		cancellation: cancelled ? { name: "TCX-0001", ground_label: "Inadequate budgetary provision", reason: "The confirmed budget available for this procurement is insufficient to proceed.", decided_by_name: "Amina Hassan", decided_at_label: "4 Jun 2027, 14:00 EAT", obligations } : null,
		compliance: cancelled ? [
			{ key: "record_cancellation_notice_evidence", label: "Cancellation notices", due_by: "18 Jun 2027", status: "Outstanding", detail: "0 of 4 recorded", action: "record_cancellation_notice_evidence", action_label: "Record cancellation notice evidence", obligation_id: "NOTICE-C0" },
			{ key: "record_ppra_report_evidence", label: "PPRA report", due_by: "18 Jun 2027", status: "Outstanding", detail: "", action: "record_ppra_report_evidence", action_label: "Record PPRA report evidence", obligation_id: "PPRA_REPORT" },
		] : [],
		review: variant === "REQUEST" ? { addendum: "TDA-0039", addendum_reference: "ADD-MOH-2027-039-001", requested_by_name: "Brian Wafula", requested_by_role: "Procurement Officer", field: "Business laptops — Quantity", current: "250 Each", proposed: "300 Each", reason: "Additional deployment sites require 50 more laptops" } : null,
		allowed_actions: cancelled ? (holder ? ["record_cancellation_evidence"] : []) : variant === "REQUEST" ? ["cancel_tender", "close_cancellation_review"] : ["cancel_tender"],
		warning_text: "Cancellation is final for this Tender. It does not restore the Requisition or create a replacement Tender.",
		guidance: guidance(g[0], g[1], g[2]),
	};
}
