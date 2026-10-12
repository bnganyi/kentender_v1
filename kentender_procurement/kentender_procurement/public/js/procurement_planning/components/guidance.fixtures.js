// PLN-CHG-001 v1.27 §10.1A / §10.6 — `next_step`, `journey`, `budget_fit` and
// `finance_confirmation` payloads for the U07 variants, in the exact shape
// kentender_core.services.next_step returns (server-computed; the screens
// draw them unchanged). Shared by the U07 component and structure specs.
const MARK = { done: "Done", current: "Current", blocked: "Blocked", not_started: "Not started" };
const PLAN_STAGES = [
	["preparation", "Preparation"], ["funding", "Funding confirmation"], ["signature", "Signature"], ["ao", "AO adoption"],
	["statutory", "Cabinet Secretary approval"], ["publication", "Publication"], ["in_force", "In force"],
];

export function planJourney(current, { blocked = false, holder = "", upstream = null, reduced = false } = {}) {
	const index = PLAN_STAGES.findIndex(([code]) => code === current);
	const stages = PLAN_STAGES.map(([code, label], i) => {
		const marker = i < index ? "done" : i === index ? (blocked ? "blocked" : "current") : "not_started";
		return { code, label, marker, marker_label: MARK[marker], holder: i === index ? holder : "" };
	});
	return {
		stages,
		current,
		reduced,
		reduced_parts: { prefix: `Stage ${index + 1} of 7: `, label: PLAN_STAGES[index][1], suffix: holder ? ` — ${holder}` : "" },
		reduced_text: "",
		upstream,
		downstream: null,
	};
}

export const UPSTREAM = { label: "3 departmental requirements included", kind: "focus", target: "requirements" };

export const METHOD_BLOCKED = {
	kind: "your_turn_blocked",
	label: "Your turn, blocked",
	headline: "1 purchase needs a procurement method",
	sentence: "You can request the funding check once a method is chosen.",
	stage: "preparation",
	holder: null,
	since: null,
	blockers: [
		{
			reason_code: "PLN_PLAN_CONTENTS_INCOMPLETE",
			headline: "1 purchase needs a procurement method",
			facts: [],
			fixes: [{ fix_id: "choose_method", label: "Choose a procurement method", kind: "route", target: ["procurement-plan-item", "PPI-MOH-2027-021"], primary: true, responsibility: "Procurement Planner" }],
		},
	],
	fixes: [],
	primary_action: "",
};

export const OVER_BUDGET = {
	...METHOD_BLOCKED,
	headline: "Over budget by KES 2,000,000 on Digital health workforce development",
	sentence: "Purchase costs come from the departments' accepted requirements and cannot be lowered in the plan. You can request the funding check once the line's approved amount covers them.",
	blockers: [
		{
			reason_code: "PLN_PLAN_NOT_AFFORDABLE",
			headline: "Over budget by KES 2,000,000 on Digital health workforce development",
			facts: [{ label: "Requirements on this line", value: "Human Resources Management and Development" }],
			// Owner decision 26 Sep 2026 — the two recovery paths.
			fixes: [
				{ fix_id: "request_budget_revision", label: "Request budget revision from Josphat Mwangi", kind: "command", target: { budget_line: "MOH-BL-HWD-2027" }, primary: true, responsibility: "Budget Officer" },
				{ fix_id: "request_departmental_update", label: "Request departmental plan update from Human Resources Management and Development", kind: "command", target: { budget_line: "MOH-BL-HWD-2027", organisation_unit: "OU-HRMD" }, primary: false, responsibility: "Departmental Author" },
			],
		},
	],
};

export const WAITING_SIGNATURE = {
	kind: "waiting",
	label: "Waiting",
	headline: "Waiting for Charles Mutiso (Head of Procurement Function) to sign and submit",
	sentence: "",
	stage: "signature",
	holder: { role: "Head of Procurement Function", people: ["Charles Mutiso"], display: "Charles Mutiso (Head of Procurement Function)" },
	since: { at: "2026-12-04 07:00:00", display: "4 Dec 2026, 10:00 EAT" },
	blockers: [],
	fixes: [],
	primary_action: "",
};

export const WAITING_BUDGET = {
	...WAITING_SIGNATURE,
	headline: "Waiting for Josphat Mwangi (Budget Officer) to revise the budget line",
	stage: "preparation",
	holder: { role: "Budget Officer", people: ["Josphat Mwangi"], display: "Josphat Mwangi (Budget Officer)" },
	since: { at: "2026-12-15 07:00:00", display: "15 Dec 2026, 10:00 EAT" },
};

const LINE_DHI = { budget_line: "L1", title: "Digital health infrastructure programme", reference: "MOH-BL-DHI-2027", approved_display: "KES 100,000,000", planned_display: "KES 80,000,000", difference_display: "Within by KES 20,000,000", over: false };
const LINE_HWD = { budget_line: "L2", title: "Digital health workforce development", reference: "MOH-BL-HWD-2027", approved_display: "KES 60,000,000", planned_display: "KES 50,000,000", difference_display: "Within by KES 10,000,000", over: false };

export const FIT_WITHIN = { all_within: true, result: "Within each approved budget line", lines: [LINE_DHI, LINE_HWD] };
export const FIT_OVER = {
	all_within: false,
	result: "Over by KES 2,000,000 on one budget line",
	lines: [LINE_DHI, { ...LINE_HWD, planned_display: "KES 62,000,000", difference_display: "Over by KES 2,000,000", over: true }],
};

export const FINANCE_NOT_REQUESTED = { state: "Not requested", checked_by: "", checked_at: "" };
export const FINANCE_CONFIRMED = { state: "Confirmed", checked_by: "Josphat Mwangi", checked_at: "4 Dec 2026, 10:00 EAT" };

// PLN v1.27 §10.1A.2 — the departmental plan's four-stage journey (U02–U06).
const DPP_STAGES = [["preparation", "Preparation"], ["certification", "Certification"], ["review", "Procurement review"], ["accepted", "Accepted"]];

export function dppJourney(current, { holder = "", complete = false, reduced = false } = {}) {
	const index = complete ? DPP_STAGES.length : DPP_STAGES.findIndex(([code]) => code === current);
	const stages = DPP_STAGES.map(([code, label], i) => {
		const marker = i < index ? "done" : i === index ? "current" : "not_started";
		return { code, label, marker, marker_label: MARK[marker], holder: i === index ? holder : "" };
	});
	const at = Math.min(index, DPP_STAGES.length - 1);
	return {
		stages, current: complete ? "accepted" : current, reduced,
		reduced_parts: { prefix: `Stage ${at + 1} of 4: `, label: DPP_STAGES[at][1], suffix: holder ? ` — ${holder}` : "" },
		reduced_text: "", upstream: null, downstream: null,
	};
}

export const REVIEW_TURN = {
	kind: "your_turn", label: "Your turn",
	headline: "Classify every included requirement, then accept or return the submission",
	sentence: "", stage: "review", holder: null, since: null, blockers: [], fixes: [], primary_action: "review",
};
export const REVIEW_SEGREGATED = {
	kind: "waiting", label: "Waiting",
	headline: "Waiting for Procurement review by another Procurement Planner",
	sentence: "", stage: "review",
	holder: { role: "Procurement Planner", people: ["Mercy Kilonzo"], display: "Mercy Kilonzo (Procurement Planner)" },
	since: { at: "2026-11-25 07:30:00", display: "25 Nov 2026, 10:30 EAT" },
	blockers: [], fixes: [], primary_action: "",
};
export const REVIEW_ACCEPTED = {
	kind: "done", label: "Done", headline: "Accepted by Mercy Kilonzo on 29 Nov 2026, 15:00 EAT",
	sentence: "", stage: "accepted", holder: null, since: null, blockers: [], fixes: [], primary_action: "",
};
export const CLASSIFICATION_PROMPT = {
	one: "Select the requirement type for 1 requirement, then accept",
	many: "Select the requirement type for {count} requirements, then accept",
};

// PLN v1.27 §10.4 — U02–U05 answers.
const TURN = { kind: "your_turn", label: "Your turn", sentence: "", holder: null, since: null, blockers: [], fixes: [] };
export const AUTHOR_DRAFT_TURN = { ...TURN, headline: "Enter funding details for 1 requirement", stage: "preparation", primary_action: "continue" };
export const HOD_TURN = { ...TURN, headline: "Certify and submit the departmental plan", stage: "certification", primary_action: "submit" };
export const CORRECTION_TURN = { ...TURN, headline: "Correct and resubmit the departmental plan", stage: "preparation", primary_action: "resubmit" };
export const CLOSED_BLOCKED = {
	kind: "your_turn_blocked", label: "Your turn, blocked",
	headline: "Initial submissions are closed",
	sentence: "You can keep editing this draft, but it cannot be submitted now.",
	stage: "preparation", holder: null, since: null,
	blockers: [{
		reason_code: "PLN_WINDOW_CLOSED", headline: "Initial submissions are closed", facts: [],
		fixes: [{ fix_id: "ask_administrator", label: "Ask your KenTender administrator to complete this setting.", kind: "text", target: null, primary: false, responsibility: "Technical operator" }],
	}],
	fixes: [], primary_action: "",
};

// PLN v1.27 §10.9 — U10 answers.
export const FINANCE_TURN = { ...TURN, headline: "Confirm plan funding or return the plan to the planner", stage: "funding", primary_action: "" };
export const FINANCE_RETURN = { ...TURN, headline: "Return the plan to the planner", stage: "funding", primary_action: "return" };
export const REASSESS_TURN = { ...TURN, headline: "Check the current plan against the revised budget", stage: "funding", primary_action: "" };
export const NOT_INVOLVED = { kind: "not_involved", label: "", headline: "", sentence: "", stage: "", holder: null, since: null, blockers: [], fixes: [], primary_action: "" };

// PLN v1.27 §10.10 — U11 answers.
export const AO_TURN = { ...TURN, headline: "Adopt and submit the plan, or return it for correction", stage: "ao", primary_action: "decide" };
export const STALE_EVIDENCE_TURN = { ...TURN, headline: "Return the plan for a new funding check", stage: "ao", primary_action: "return_for_correction" };
export const WAITING_AO = {
	kind: "waiting", label: "Waiting", headline: "Waiting for Amina Hassan (Accounting Officer) to adopt or return the plan",
	sentence: "", stage: "ao",
	holder: { role: "Accounting Officer", people: ["Amina Hassan"], display: "Amina Hassan (Accounting Officer)" },
	since: { at: "2026-12-07 07:00:00", display: "7 Dec 2026, 10:00 EAT" },
	blockers: [], fixes: [], primary_action: "",
};

// PLN v1.31 §10.12 — U13 answers (reduced tracker, stage 6 of 7). The Planner's
// turn replaces the AO's Treasury record, the Head's Publish and the technical
// retry of v1.30.
export const CONFIRM_TURN = { ...TURN, headline: "Confirm plan publication", stage: "publication", primary_action: "confirm_publication" };
export const PREPARE_CORRECTED_TURN = { ...TURN, headline: "Prepare a corrected plan", stage: "publication", primary_action: "" };
export const WAITING_PLANNER = {
	kind: "waiting", label: "Waiting", headline: "Waiting for Mercy Kilonzo (Procurement Planner) to confirm publication",
	sentence: "", stage: "publication",
	holder: { role: "Procurement Planner", people: ["Mercy Kilonzo"], display: "Mercy Kilonzo (Procurement Planner)" },
	since: { at: "2026-12-09 08:00:00", display: "9 Dec 2026, 11:00 EAT" },
	blockers: [], fixes: [], primary_action: "",
};

// §10.16 C01-ROUTE-MISSING — the missing setting as the AO's blocker (D3).
export const ROUTE_PANEL = {
	setting: "Annual Plan approval authority", affected_action: "Adopt and submit", affected_purchase: "",
	responsible_role: "Administrator or System Manager", note: "", lede: "",
	can_open_setup: false, action: "", href: "", ask_text: "Ask your KenTender administrator to complete this setting.",
};
export const AO_ROUTE_BLOCKED = {
	kind: "your_turn_blocked", label: "Your turn, blocked",
	headline: "Annual Plan approval authority is not set up", sentence: "", stage: "ao", holder: null, since: null,
	blockers: [{
		reason_code: "PLN_STATUTORY_ROUTE_UNCONFIGURED", headline: "Annual Plan approval authority is not set up",
		facts: [
			{ label: "Setting", value: "Annual Plan approval authority" },
			{ label: "Affected action", value: "Adopt and submit" },
			{ label: "Responsible role", value: "Administrator or System Manager" },
		],
		fixes: [{ fix_id: "ask_administrator", label: "Ask your KenTender administrator to complete this setting.", kind: "text", target: null, primary: false, responsibility: "Administrator or System Manager" }],
	}],
	fixes: [], primary_action: "",
};
