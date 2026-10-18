// Opening-failure screens (BOP-CHG-001 v0.16 §5.2, §10.7–§10.8): what the opening page shows when a Tender cancellation is recorded, when support has
// recorded a finding, when the Accounting Officer is sent to the Tender decision and when the chair may resume. The server's own captured answers are
// the starting point; each test changes only the facts it is about.
import { afterEach, beforeAll, describe, expect, it, vi } from "vitest";
import { mount } from "@vue/test-utils";
import { nextTick } from "vue";

import CompletedScreen from "./CompletedScreen.vue";
import OpenBidsScreen from "./OpenBidsScreen.vue";
import IncidentFindingForm from "../components/IncidentFindingForm.vue";

const FIXTURES = import.meta.glob("../fixtures/*.json", { eager: true, import: "default" });
const world = (stage, viewer) => JSON.parse(JSON.stringify(FIXTURES[`../fixtures/${stage}.json`][viewer]));
const settle = async () => {
	for (let i = 0; i < 4; i += 1) await nextTick();
};
const screen = (w) => w.get(".kt-page").attributes("data-screen");
const setRoute = vi.fn();

beforeAll(() => {
	globalThis.frappe.session = { user: "pw.req.hopf@example.test" };
	globalThis.frappe.set_route = setRoute;
});
afterEach(() => {
	setRoute.mockReset();
	document.body.innerHTML = "";
});

const CANCEL_PENDING = { state: "Recorded", message: "Cancellation recorded. The opening record is being updated.", reference: "TC-1", outcome: "", decided_label: "10:03", note: "" };
const CANCEL_ENDED = { state: "Ended", message: "This tender was cancelled. Opening ended.", reference: "TC-1", outcome: "Opening not held", decided_label: "10:03", note: "The opening never started. What was recorded stays as it was; bids stay sealed under their existing custody." };

describe("a recorded Tender cancellation", () => {
	it("replaces every ceremony action with one sentence, before the opening record has caught up", async () => {
		const data = world("answered", "chair");
		data.cancellation = CANCEL_PENDING;
		const w = mount(OpenBidsScreen, { props: { data }, attachTo: document.body });
		await settle();
		expect(screen(w)).toBe("open-bids:cancel-pending");
		expect(w.get('[data-testid="bop-cancel-pending"] h2').text()).toBe("Cancellation recorded. The opening record is being updated.");
		expect(w.findAll("button.btn-primary")).toHaveLength(0);
		expect(w.find('[data-testid="bop-open-next"]').exists()).toBe(false);
		expect(w.find('[data-testid="bop-end"]').exists()).toBe(false);
	});

	it("says the opening ended once the terminal outcome is recorded, and names a never-started opening as not held", async () => {
		const data = world("not-held", "ao");
		data.cancellation = CANCEL_ENDED;
		const w = mount(OpenBidsScreen, { props: { data }, attachTo: document.body });
		await settle();
		expect(screen(w)).toBe("open-bids:cancelled");
		expect(w.get('[data-testid="bop-cancelled"] h2').text()).toBe("This tender was cancelled. Opening ended.");
		expect(w.get('[data-testid="bop-cancelled-outcome"]').text()).toBe("Opening not held");
		expect(w.findAll("button.btn-primary")).toHaveLength(0);
	});

	it("keeps an AO-recorded not-held opening on its own screen while no cancellation exists", async () => {
		const w = mount(OpenBidsScreen, { props: { data: world("not-held", "ao") }, attachTo: document.body });
		await settle();
		expect(screen(w)).toBe("open-bids:not-held");
	});
});

describe("the Accounting Officer's route to the Tender decision", () => {
	const aoOnUnresolved = (kind) => {
		const data = world("unresolved", "ao");
		data.decision = { ...data.decision, item: "ODI-0001", tender_reference: data.opening.tender_reference, message: "Opening could not be recovered. The Accounting Officer must review the next step." };
		data.next_step = { ...data.next_step, kind };
		return data;
	};

	it("shows the server's words and goes to the exact decision item as a path segment", async () => {
		const data = aoOnUnresolved("your_turn_blocked");
		const w = mount(OpenBidsScreen, { props: { data }, attachTo: document.body });
		await settle();
		expect(w.get('[data-testid="bop-decision-message"]').text()).toBe("Opening could not be recovered. The Accounting Officer must review the next step.");
		const button = w.get('[data-testid="bop-open-tender-decision"]');
		expect(button.text()).toBe("Review the tender decision");
		await button.trigger("click");
		expect(setRoute).toHaveBeenCalledWith("tenders", data.opening.tender_reference, "cancel", "ODI-0001");
	});

	it("calls the same button the decision itself when nothing stops it", async () => {
		const w = mount(OpenBidsScreen, { props: { data: aoOnUnresolved("your_turn") }, attachTo: document.body });
		await settle();
		expect(w.get('[data-testid="bop-open-tender-decision"]').text()).toBe("Decide on the Tender");
	});

	it("gives the button to the Accounting Officer only", async () => {
		const data = aoOnUnresolved("your_turn_blocked");
		data.viewer = { ...data.viewer, is_accounting_officer: false };
		const w = mount(OpenBidsScreen, { props: { data }, attachTo: document.body });
		await settle();
		expect(w.find('[data-testid="bop-open-tender-decision"]').exists()).toBe(false);
	});
});

describe("the chair on a paused bid", () => {
	const chairWith = (finding) => {
		const data = world("unresolved", "chair");
		data.ceremony.pause.incident = { ...data.ceremony.pause.incident, current_finding: finding };
		return data;
	};

	it("is told a bid that could not be recovered cannot be retried", async () => {
		const w = mount(OpenBidsScreen, { props: { data: chairWith("Cannot recover") }, attachTo: document.body });
		await settle();
		expect(w.get('[data-testid="bop-problem-status"]').text()).toBe("Could not be recovered");
		expect(w.get('[data-testid="bop-not-recovered"]').text()).toBe("Opening could not be recovered. The Accounting Officer must review the next step.");
		expect(w.find('[data-testid="bop-retry"]').exists()).toBe(false);
	});

	it("reads a Recovered finding as recovered", async () => {
		const data = chairWith("Recovered");
		data.ceremony.pause.incident.resolved_at = "2027-06-05 11:05:00";
		const w = mount(OpenBidsScreen, { props: { data }, attachTo: document.body });
		await settle();
		expect(w.get('[data-testid="bop-problem-status"]').text()).toContain("Recovered");
	});

	it("offers Resume only when the server says the pause waits for the chair, and sends ResumeOpening", async () => {
		const data = world("member-left", "chair");
		data.next_step = { ...data.next_step, kind: "your_turn", primary_action: "resume", headline: "Resume the opening" };
		const w = mount(OpenBidsScreen, { props: { data }, attachTo: document.body });
		await settle();
		await w.get('[data-testid="bop-resume"]').trigger("click");
		expect(w.emitted("command")[0][0]).toEqual({ method: "resume_opening", args: {} });
		const without = mount(OpenBidsScreen, { props: { data: world("member-left", "chair") }, attachTo: document.body });
		await settle();
		expect(without.find('[data-testid="bop-resume"]').exists()).toBe(false);
	});
});

describe("support's finding", () => {
	const incident = { incident_id: "INC-OPEN-0001-01", current_finding: "Unresolved", incident_revision: 2 };

	it("needs a choice and a reason before anything is sent", async () => {
		const w = mount(IncidentFindingForm, { props: { incident }, attachTo: document.body });
		await w.get('[data-testid="bop-finding-submit"]').trigger("click");
		expect(w.get('[data-testid="bop-finding-error"]').text()).toBe("Choose what you found.");
		await w.get('[data-testid="bop-finding-select"]').setValue("Recovered");
		await w.get('[data-testid="bop-finding-submit"]').trigger("click");
		expect(w.get('[data-testid="bop-finding-error"]').text()).toBe("Record what you found.");
		expect(w.emitted("record")).toBeUndefined();
	});

	it("sends the finding against the incident revision it was shown, then clears the form", async () => {
		const w = mount(IncidentFindingForm, { props: { incident }, attachTo: document.body });
		await w.get('[data-testid="bop-finding-select"]').setValue("Cannot recover");
		await w.get('[data-testid="bop-finding-reason"]').setValue("  The package cannot be rendered.  ");
		await w.get('[data-testid="bop-finding-evidence"]').setValue("CHK-1");
		await w.get('[data-testid="bop-finding-submit"]').trigger("click");
		expect(w.emitted("record")[0][0]).toEqual({ incident: "INC-OPEN-0001-01", finding: "Cannot recover", reason: "The package cannot be rendered.", evidence_refs: "CHK-1", expected_revision: 2 });
		expect(w.get('[data-testid="bop-finding-reason"]').element.value).toBe("");
	});
});

describe("support's own page", () => {
	it("lists the incidents with their current finding and carries one finding form each, for support only", async () => {
		const data = world("complete", "admin");
		data.viewer = { ...data.viewer, technical: true, is_support: true, can_read_incident_details: true, incident_purposes: ["Record the resolution"] };
		data.incidents = [{ incident_id: "INC-OPEN-0001-01", type: "Package unreadable", notification_state: "Delivered", notified_label: "11:00", current_finding: "Unresolved", incident_revision: 1 }];
		const w = mount(CompletedScreen, { props: { data }, attachTo: document.body });
		await settle();
		expect(w.get('[data-testid="bop-support-incident-INC-OPEN-0001-01"]').text()).toContain("Unresolved");
		expect(w.find('[data-testid="bop-finding-form-INC-OPEN-0001-01"]').exists()).toBe(true);
		data.viewer.is_support = false;
		const other = mount(CompletedScreen, { props: { data }, attachTo: document.body });
		await settle();
		expect(other.find('[data-testid="bop-finding-form-INC-OPEN-0001-01"]').exists()).toBe(false);
	});
});
