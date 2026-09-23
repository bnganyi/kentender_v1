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
});

// NDS-DES-08-DRAFT/SUBMITTED/OTHER-AUTHOR and NDS-DES-11-OPEN-UPDATE — the
// open-successor notice's literal copy and its owner-only action link.
describe("NeedDetailScreen — open successor notice", () => {
	const ACCEPTED_NEED = {
		need_reference: "NDS-MOH-2027-0001",
		current_state: "Accepted for planning",
		current_revision: "NDS-MOH-2027-0001-V2",
		current_accepted_revision: "NDS-MOH-2027-0001-V1",
	};
	const ACCEPTED_REVISION = { ...REVISION, name: "NDS-MOH-2027-0001-V1" };

	it("DRAFT, owner — Update in progress, with a Continue update link and the withdrawal-blocked note", () => {
		const w = mount(NeedDetailScreen, {
			props: {
				need: ACCEPTED_NEED,
				acceptedRevision: ACCEPTED_REVISION,
				revision: { ...REVISION, revision_status: "Draft" },
				accessProfile: "owner",
			},
		});
		expect(w.text()).toContain("Update in progress");
		const button = w.get('[data-testid="nds-open-successor"]');
		expect(button.text()).toBe("Continue update");
		// NDS-DES-11-OPEN-UPDATE's own explanatory sentence for why Request
		// withdrawal is absent from the header while this update is open.
		expect(w.text()).toContain("An update is already in progress. Complete or cancel it before requesting withdrawal.");
	});

	it("SUBMITTED, owner — Your changes are awaiting review, with Submitted at and a View proposed changes link", () => {
		const w = mount(NeedDetailScreen, {
			props: {
				need: ACCEPTED_NEED,
				acceptedRevision: ACCEPTED_REVISION,
				revision: { ...REVISION, revision_status: "Submitted" },
				accessProfile: "owner",
				submittedAt: "2026-12-15 09:45:00",
			},
		});
		expect(w.text()).toContain("Your changes are awaiting review");
		expect(w.text()).toContain("Submitted at");
		const button = w.get('[data-testid="nds-open-successor"]');
		expect(button.text()).toBe("View proposed changes");
	});

	it("SUBMITTED, other reader (NDS-DES-08-OTHER-AUTHOR) — the same fact, with no Submitted-at and no link", () => {
		const w = mount(NeedDetailScreen, {
			props: {
				need: ACCEPTED_NEED,
				acceptedRevision: ACCEPTED_REVISION,
				revision: { ...REVISION, revision_status: "Submitted" },
				accessProfile: "planning",
				submittedAt: "2026-12-15 09:45:00",
			},
		});
		expect(w.text()).toContain("Your changes are awaiting review");
		expect(w.text()).not.toContain("Submitted at");
		expect(w.find('[data-testid="nds-open-successor"]').exists()).toBe(false);
	});
});

// NDS-DES-11-REQUESTED — the withdrawal-already-open headline replaces (not
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

	it("no open withdrawal (NDS-DES-07A-STILL-ACTIVE) — the inline grid warning shows, no top-level notice", () => {
		const w = mount(NeedDetailScreen, { props: { ...STILL_ACTIVE_PROPS, withdrawalOpen: false } });
		expect(w.find('[data-testid="nds-withdrawal-waiting"]').exists()).toBe(false);
		expect(w.text()).toContain("The annual plan has not yet been updated. Withdrawal cannot be approved while");
	});

	it("an open withdrawal (NDS-DES-11-REQUESTED) — the top-level notice shows once, not the inline grid warning too", () => {
		const w = mount(NeedDetailScreen, { props: { ...STILL_ACTIVE_PROPS, withdrawalOpen: true } });
		const notice = w.get('[data-testid="nds-withdrawal-waiting"]');
		expect(notice.text()).toContain("Waiting for a Planning change");
		expect(notice.text()).toContain("The annual plan has not yet been updated. Withdrawal cannot be approved while");
		// Only the one occurrence of the shared sentence — not doubled up.
		const occurrences = w.text().split("The annual plan has not yet been updated").length - 1;
		expect(occurrences).toBe(1);
	});
});
