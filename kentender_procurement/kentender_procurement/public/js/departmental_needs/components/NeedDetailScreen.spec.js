// NDS-CHG-001 v1.14 §11.1 / NDS-DES-TERMINAL — NeedDetailScreen.vue's
// decision-provenance block for a declined ("Not taken forward") or
// self-withdrawn ("Withdrawn") terminal Need, ported from NDS
// Artboards.dc.html: exact "Decision reason"/"Decided by"/"Decided at" vs
// "Withdrawn by"/"Withdrawn at" copy. A landmark-only structural gate
// (departmental-needs-fidelity.spec.ts) cannot catch a blank or
// wrong-but-present value, only whether a label is present in order, so this
// asserts the literal rendered strings alongside (never instead of) that
// browser-layer gate.
import { describe, expect, it } from "vitest";
import { mount } from "@vue/test-utils";
import NeedDetailScreen from "./NeedDetailScreen.vue";

const REVISION = {
	title: "Digital health workforce certification programme",
	description: "Professional certification programme for staff supporting national digital health services.",
	expected_operational_result: "Build internal capacity to operate and support national digital health platforms.",
	indicative_quantity: 1,
	unit_label: "Programme",
	required_by_date: "2027-12-31",
	revision_number: 1,
};

describe("NeedDetailScreen — NDS-DES-TERMINAL", () => {
	it("renders NDS-DES-TERMINAL-DECLINE's Decision reason / Decided by / Decided at", () => {
		const wrapper = mount(NeedDetailScreen, {
			props: {
				need: { need_reference: "NDS-MOH-2027-0002", current_state: "Not taken forward" },
				revision: REVISION,
				terminalDecision: {
					reason: "The requirement is already covered by an existing enterprise service for FY 2027/28.",
					actor_label: "Dr Peter Kimani",
					occurred_label: "24 November 2026 at 12:40",
				},
			},
		});
		const block = wrapper.get('[data-testid="nds-terminal-decision"]');
		expect(block.get(".kt-label").text()).toBe("Decision reason");
		expect(block.text()).toContain(
			"The requirement is already covered by an existing enterprise service for FY 2027/28."
		);
		const rows = block.findAll(".kt-meta-row > div");
		expect(rows).toHaveLength(2);
		expect(rows[0].get(".kt-label").text()).toBe("Decided by");
		expect(rows[0].get(".kt-meta-value").text()).toBe("Dr Peter Kimani");
		expect(rows[1].get(".kt-label").text()).toBe("Decided at");
		expect(rows[1].get(".kt-meta-value").text()).toBe("24 November 2026 at 12:40");
	});

	it("renders NDS-DES-TERMINAL-WITHDRAWN's Withdrawn by / Withdrawn at with no Decision reason", () => {
		const wrapper = mount(NeedDetailScreen, {
			props: {
				need: { need_reference: "NDS-MOH-2027-0003", current_state: "Withdrawn" },
				revision: REVISION,
				terminalDecision: {
					reason: "",
					actor_label: "Grace Wanjiku",
					occurred_label: "24 November 2026 at 14:20",
				},
			},
		});
		const block = wrapper.get('[data-testid="nds-terminal-decision"]');
		// No "Decision reason" label at all — §5.1's self-service withdrawal
		// collects no reason, and the artboard itself omits the line entirely
		// rather than showing it blank.
		expect(block.findAll(".kt-label").map((el) => el.text())).toEqual(["Withdrawn by", "Withdrawn at"]);
		const rows = block.findAll(".kt-meta-row > div");
		expect(rows[0].get(".kt-meta-value").text()).toBe("Grace Wanjiku");
		expect(rows[1].get(".kt-meta-value").text()).toBe("24 November 2026 at 14:20");
	});

	it("renders no terminal-decision block for a live (non-terminal) Need", () => {
		const wrapper = mount(NeedDetailScreen, {
			props: {
				need: { need_reference: "NDS-MOH-2027-0001", current_state: "Draft" },
				revision: REVISION,
				terminalDecision: null,
			},
		});
		expect(wrapper.find('[data-testid="nds-terminal-decision"]').exists()).toBe(false);
	});
});

// NDS-DES-07A NONE/PROCEEDING/EXCLUDED/STILL-ACTIVE/RESTORED — the literal
// "Where this requirement stands" copy a structural (landmark-only) gate
// cannot see, since `.kt-status` is never a checked landmark there.
describe("NeedDetailScreen — NDS-DES-07A Planning-status variants", () => {
	const ACCEPTED_NEED = {
		need_reference: "NDS-MOH-2027-0001",
		current_state: "Accepted for planning",
		current_revision: "NDS-MOH-2027-0001-V1",
		current_accepted_revision: "NDS-MOH-2027-0001-V1",
	};
	const ACCEPTED_REVISION = { ...REVISION, name: "NDS-MOH-2027-0001-V1" };

	function mountAccepted(props) {
		return mount(NeedDetailScreen, {
			props: {
				need: ACCEPTED_NEED,
				acceptedRevision: ACCEPTED_REVISION,
				accessProfile: "owner",
				...props,
			},
		});
	}

	function group(wrapper, label) {
		const groups = wrapper.findAll(".kt-group");
		const match = groups.find((g) => g.get(".kt-label").text() === label);
		if (!match) throw new Error(`no .kt-group labelled ${JSON.stringify(label)}`);
		return match;
	}

	it("NONE — no accepted decision recorded, so no departmental-plan fact at all", () => {
		const w = mountAccepted({ usage: {}, disposition: { recorded: false } });
		// Owner instruction, 23 Sep 2026: until Procurement accepts the
		// departmental plan there is nothing to report, and the old
		// "No accepted departmental decision recorded" line read as if the
		// requirement had gone nowhere — it now sits in a Draft departmental
		// plan that its acceptance started.
		expect(w.findAll(".kt-group").map((g) => g.get(".kt-label").text())).not.toContain("Departmental plan");
		expect(w.text()).not.toContain("No accepted departmental decision recorded");
		expect(group(w, "Current annual plan").text()).toContain("Not included");
		expect(w.find('[data-testid="nds-view-plan-item-inline"]').exists()).toBe(false);
	});

	it("PROCEEDING — included in the departmental plan, not yet in the annual plan", () => {
		const w = mountAccepted({
			usage: { usage: "Not included" },
			disposition: { recorded: true, disposition: "Proceeding" },
		});
		expect(group(w, "Departmental plan").text()).toContain("Included");
		expect(group(w, "Departmental plan").text()).toContain(
			"The accepted departmental plan includes this requirement.",
		);
		expect(group(w, "Current annual plan").text()).toContain("Not included");
	});

	it("EXCLUDED — not included this year, with the department's reason", () => {
		const w = mountAccepted({
			usage: { usage: "Not included" },
			disposition: {
				recorded: true,
				disposition: "Not proceeding",
				reason: "The department will pursue this requirement in a later annual planning cycle.",
			},
		});
		expect(group(w, "Departmental plan").text()).toContain("Not included this year");
		// NDS-DES-07A-EXCLUDED — the reason sits under its own "Reason" label,
		// not folded into an unlabelled sentence.
		const labels = group(w, "Departmental plan").findAll(".kt-label").map((el) => el.text());
		expect(labels).toEqual(["Departmental plan", "Reason"]);
		expect(group(w, "Departmental plan").text()).toContain(
			"The department will pursue this requirement in a later annual planning cycle.",
		);
		expect(w.find('[data-testid="nds-view-plan-item-inline"]').exists()).toBe(false);
	});

	it("STILL-ACTIVE — excluded departmentally but still included in the annual plan, with its own View link", () => {
		const w = mountAccepted({
			usage: { usage: "Fully included", active_plan: "PLN-MOH-2027-001", active_plan_item: "PPI-MOH-2027-021" },
			disposition: {
				recorded: true,
				disposition: "Not proceeding",
				reason: "The department will pursue this requirement in a later annual planning cycle.",
			},
		});
		expect(group(w, "Departmental plan").text()).toContain("Not included this year");
		expect(group(w, "Current annual plan").text()).toContain("Still included");
		const button = w.get('[data-testid="nds-view-plan-item-inline"]');
		expect(button.text()).toBe("View annual plan item");
		expect(group(w, "Current annual plan").find('[data-testid="nds-view-plan-item-inline"]').exists()).toBe(true);
	});

	it("RESTORED — included again departmentally, and still included in the annual plan (not \"still\")", () => {
		const w = mountAccepted({
			usage: { usage: "Fully included", active_plan: "PLN-MOH-2027-001", active_plan_item: "PPI-MOH-2027-021" },
			disposition: { recorded: true, disposition: "Proceeding" },
		});
		expect(group(w, "Departmental plan").text()).toContain("Included");
		expect(group(w, "Current annual plan").text()).toContain("Included");
		expect(group(w, "Current annual plan").text()).not.toContain("Still included");
		expect(w.find('[data-testid="nds-view-plan-item-inline"]').exists()).toBe(true);
	});

	// Owner decision 26 Sep 2026 — a Need accepted after its department's plan
	// was accepted is in no plan until the department creates an update.
	const LATE = {
		position: "Update required",
		department: "Digital Health",
		departmental_plan: "DPP-MOH-02314-2027-001",
		revision_number: 1,
		carried_revision_number: 0,
		can_update: true,
	};

	// NDS-CHG-001 v1.15 §5.5 — who acts, and the one way to the plan, belong
	// to the next step in the guidance region; the fact says only where the
	// need stands.
	const YOUR_TURN_UPDATE_PLAN = {
		kind: "your_turn",
		label: "Your turn",
		headline: "Add this need to Digital Health's departmental plan",
		sentence: "The plan was accepted before this need. Create an update of the plan, fund the need and resubmit.",
		stage: "accepted",
		holder: null,
		since: null,
		blockers: [],
		fixes: [
			{
				fix_id: "update_departmental_plan",
				label: "Update departmental plan",
				kind: "route",
				target: ["departmental-procurement-plan", "DPP-MOH-02314-2027-001"],
				primary: true,
				responsibility: "Departmental Author or Head of User Department",
			},
		],
		primary_action: "",
	};
	const WAITING_DEPARTMENT = {
		...YOUR_TURN_UPDATE_PLAN,
		kind: "waiting",
		label: "Waiting on someone",
		headline: "Waiting for Digital Health to add this need to its departmental plan",
		sentence: "",
		fixes: [],
	};

	it("LATE — not in the plan yet; the next step sends the department to update it", async () => {
		const w = mountAccepted({
			usage: { usage: "Not included" },
			disposition: { recorded: false },
			planPosition: LATE,
			nextStep: YOUR_TURN_UPDATE_PLAN,
		});
		const fact = group(w, "Departmental plan");
		expect(fact.get(".kt-status").text()).toBe("Not in the plan yet");
		expect(fact.text()).toContain("Digital Health's departmental plan was accepted before this need.");
		expect(fact.findAll(".kt-label").map((el) => el.text())).toEqual(["Departmental plan"]);
		expect(fact.find("button").exists()).toBe(false);
		const region = w.get('[data-testid="nds-guidance"]');
		expect(region.text()).toContain("Your turn");
		expect(region.text()).toContain("Add this need to Digital Health's departmental plan");
		const link = region.get('[data-fix="update_departmental_plan"]');
		expect(link.text()).toBe("Update departmental plan");
		await link.trigger("click");
		const [fix] = w.emitted("guidance-fix")[0];
		expect(fix.target).toEqual(["departmental-procurement-plan", "DPP-MOH-02314-2027-001"]);
		// "Create update" on this page updates the need itself; the plan
		// link never borrows that label.
		expect(w.findAll("button").filter((b) => b.text() === "Create update")).toHaveLength(1);
	});

	it("LATE, for a reader who cannot update the plan — waiting on the department, no link", () => {
		const w = mountAccepted({
			usage: {},
			disposition: { recorded: false },
			planPosition: { ...LATE, can_update: false },
			nextStep: WAITING_DEPARTMENT,
		});
		expect(group(w, "Departmental plan").get(".kt-status").text()).toBe("Not in the plan yet");
		const region = w.get('[data-testid="nds-guidance"]');
		expect(region.text()).toContain("Waiting for Digital Health to add this need to its departmental plan");
		expect(region.find('[data-fix="update_departmental_plan"]').exists()).toBe(false);
	});

	it("LATE REVISION — the plan still carries an earlier revision", () => {
		const w = mountAccepted({
			usage: {},
			disposition: { recorded: true, disposition: "Proceeding" },
			planPosition: { ...LATE, revision_number: 2, carried_revision_number: 1 },
		});
		const fact = group(w, "Departmental plan");
		expect(fact.get(".kt-status").text()).toBe("Earlier revision in plan");
		expect(fact.text()).toContain("Digital Health's departmental plan has revision 1 of this need.");
	});

	it("AFTER SUBMISSION — the plan is with Procurement; nothing to do yet", () => {
		const w = mountAccepted({
			usage: {},
			disposition: { recorded: false },
			planPosition: { ...LATE, position: "After current submission", can_update: false },
		});
		const fact = group(w, "Departmental plan");
		expect(fact.get(".kt-status").text()).toBe("Not in the plan yet");
		expect(fact.text()).toContain("Digital Health's departmental plan was submitted before this need was accepted.");
		expect(fact.find("button").exists()).toBe(false);
	});
});

// NDS-DES-08-DRAFT/SUBMITTED/OTHER-AUTHOR and NDS-DES-11-OPEN-UPDATE — v1.15
// §5.5: the open update's turn is the next step; the page keeps only the
// owner's View proposed changes link.
describe("NeedDetailScreen — open successor", () => {
	const ACCEPTED_NEED = {
		need_reference: "NDS-MOH-2027-0001",
		current_state: "Accepted for planning",
		current_revision: "NDS-MOH-2027-0001-V2",
		current_accepted_revision: "NDS-MOH-2027-0001-V1",
	};
	const ACCEPTED_REVISION = { ...REVISION, name: "NDS-MOH-2027-0001-V1" };
	const CONTINUE = {
		kind: "your_turn",
		label: "Your turn",
		headline: "Continue the update and submit it for review",
		sentence: "An update is already in progress. Complete or cancel it before requesting withdrawal.",
		stage: "preparation",
		holder: null,
		since: null,
		blockers: [],
		fixes: [{ fix_id: "continue_update", label: "Continue update", kind: "route", target: ["departmental-needs", "NDS-MOH-2027-0001", "edit"], primary: true, responsibility: "Departmental Author" }],
		primary_action: "",
	};
	const AWAITING = {
		kind: "waiting",
		label: "Waiting on someone",
		headline: "Waiting for Grace Achieng to decide the proposed changes",
		sentence: "",
		stage: "review",
		holder: { name: "Grace Achieng" },
		since: { value: "2026-12-15T06:45:00Z", display: "15 Dec 2026, 09:45 EAT" },
		blockers: [],
		fixes: [],
		primary_action: "",
	};

	it("DRAFT, owner — the next step is Continue update, with the withdrawal-blocked sentence", async () => {
		const w = mount(NeedDetailScreen, {
			props: {
				need: ACCEPTED_NEED,
				acceptedRevision: ACCEPTED_REVISION,
				revision: { ...REVISION, revision_status: "Draft" },
				accessProfile: "owner",
				nextStep: CONTINUE,
			},
		});
		const region = w.get('[data-testid="nds-guidance"]');
		expect(region.text()).toContain("Continue the update and submit it for review");
		// NDS-DES-11-OPEN-UPDATE's own explanatory sentence for why Request
		// withdrawal is absent from the header while this update is open.
		expect(region.text()).toContain("An update is already in progress. Complete or cancel it before requesting withdrawal.");
		expect(w.text().split("An update is already in progress").length - 1).toBe(1);
		await region.get('[data-fix="continue_update"]').trigger("click");
		expect(w.emitted("guidance-fix")[0][0].fix_id).toBe("continue_update");
		expect(w.find('[data-testid="nds-open-successor"]').exists()).toBe(false);
	});

	it("SUBMITTED, owner — waiting on the reviewer, with a View proposed changes link", () => {
		const w = mount(NeedDetailScreen, {
			props: {
				need: ACCEPTED_NEED,
				acceptedRevision: ACCEPTED_REVISION,
				revision: { ...REVISION, revision_status: "Submitted" },
				accessProfile: "owner",
				submittedAt: "2026-12-15 09:45:00",
				nextStep: AWAITING,
			},
		});
		const region = w.get('[data-testid="nds-guidance"]');
		expect(region.text()).toContain("Waiting for Grace Achieng to decide the proposed changes");
		expect(region.text()).toContain("since 15 Dec 2026, 09:45 EAT");
		expect(w.get('[data-testid="nds-open-successor"]').text()).toBe("View proposed changes");
	});

	it("SUBMITTED, other reader (NDS-DES-08-OTHER-AUTHOR) — the same wait, with no link", () => {
		const w = mount(NeedDetailScreen, {
			props: {
				need: ACCEPTED_NEED,
				acceptedRevision: ACCEPTED_REVISION,
				revision: { ...REVISION, revision_status: "Submitted" },
				accessProfile: "planning",
				submittedAt: "2026-12-15 09:45:00",
				nextStep: AWAITING,
			},
		});
		expect(w.get('[data-testid="nds-guidance"]').text()).toContain("Waiting for Grace Achieng to decide the proposed changes");
		expect(w.find('[data-testid="nds-open-successor"]').exists()).toBe(false);
	});
});

// NDS-DES-11-REQUESTED — v1.15 §5.5: an open withdrawal waiting for a
// Planning change is the next step's sentence, and it replaces (not
// duplicates) the inline STILL-ACTIVE warning inside the Planning-status grid.
describe("NeedDetailScreen — withdrawal waiting for a Planning change", () => {
	const ACCEPTED_NEED = {
		need_reference: "NDS-MOH-2027-0001",
		current_state: "Accepted for planning",
		current_revision: "NDS-MOH-2027-0001-V1",
		current_accepted_revision: "NDS-MOH-2027-0001-V1",
	};
	const ACCEPTED_REVISION = { ...REVISION, name: "NDS-MOH-2027-0001-V1" };
	const STILL_ACTIVE_PROPS = {
		need: ACCEPTED_NEED,
		acceptedRevision: ACCEPTED_REVISION,
		accessProfile: "owner",
		usage: { usage: "Fully included", active_plan: "PLN-MOH-2027-001", active_plan_item: "PPI-MOH-2027-021" },
		disposition: { recorded: true, disposition: "Not proceeding", reason: "A later cycle." },
	};
	const WAITING_PLANNING = {
		kind: "waiting",
		label: "Waiting on someone",
		headline: "Waiting for a Planning change",
		sentence: "The annual plan has not yet been updated. Withdrawal cannot be approved while this requirement remains included.",
		stage: "accepted",
		holder: { name: "Procurement Planner" },
		since: null,
		blockers: [],
		fixes: [],
		primary_action: "",
	};

	it("no open withdrawal (NDS-DES-07A-STILL-ACTIVE) — the inline grid warning shows", () => {
		const w = mount(NeedDetailScreen, { props: { ...STILL_ACTIVE_PROPS, withdrawalOpen: false } });
		expect(w.text()).toContain("The annual plan has not yet been updated. Withdrawal cannot be approved while");
	});

	it("an open withdrawal (NDS-DES-11-REQUESTED) — the next step says it once, not the inline grid warning too", () => {
		const w = mount(NeedDetailScreen, { props: { ...STILL_ACTIVE_PROPS, withdrawalOpen: true, nextStep: WAITING_PLANNING } });
		const region = w.get('[data-testid="nds-guidance"]');
		expect(region.text()).toContain("Waiting for a Planning change");
		expect(region.text()).toContain("The annual plan has not yet been updated. Withdrawal cannot be approved while");
		// Only the one occurrence of the shared sentence — not doubled up.
		const occurrences = w.text().split("The annual plan has not yet been updated").length - 1;
		expect(occurrences).toBe(1);
	});
});
