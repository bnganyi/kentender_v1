// The closed Tender page leads with Bid Opening's own next step for the reader (owner instruction, 10 October 2026):
// the server's published answer is drawn as given, a turn carries one primary button into the opening record, the
// finished Tender row says only that preparation is complete, and "Nothing for you to do here" appears only where true.
import { describe, expect, it } from "vitest";
import { mount } from "@vue/test-utils";
import { nextTick } from "vue";
import PublishedScreen from "./PublishedScreen.vue";

const TENDER = { name: "TDR-1", tender_reference: "TND-MOH-2027-003", title: "Clinical decision-support software licences", badge: "Submission period ended", overall_status: "Submission period ended", published_at_label: "10 Oct 2026, 00:09 EAT", submission_deadline_label: "6 Nov 2026, 11:00 EAT" };
const STAGES = ["Prepare Tender", "HOPF approval", "AO publication authorisation", "Confirm publication", "Manage open Tender"].map((label, i) => ({ code: `s${i}`, label, marker: "done", marker_label: "Done", holder: "" }));
const JOURNEY = (step_first) => ({ stages: STAGES, current: "s4", reduced: false, reduced_style: "position", reduced_text: "", reduced_parts: null, upstream: null, downstream: null, caption: "Tender preparation is complete", step_first });
const answer = (kind, headline, extra = {}) => ({ kind, label: kind, headline, sentence: "", stage: "prepare", holder: null, since: null, blockers: [], fixes: [], primary_action: "", ...extra });
const OPEN = { kind: "route", fix_id: "open_opening_record", label: "Open opening record", responsibility: "Accounting Officer", person: "", target: ["tenders", "TND-MOH-2027-003", "opening"], primary: true };
const TURN = answer("your_turn", "Appoint opening committee", { fixes: [OPEN] });
const DONE = answer("done", "The system closed supplier submission at 6 Nov 2026, 11:00 EAT.", { stage: "open_management" });
const record = (step, first) => ({ tender: TENDER, allowed_actions: [], guidance: { next_step: step, journey: JOURNEY(first) }, stage_summaries: [], record_links: [], documents: [], decisions: [], open_period: {}, review: {} });

async function show(step, first) {
	const w = mount(PublishedScreen, { props: { record: record(step, first), review: {}, pending: false }, attachTo: document.body });
	await nextTick();
	return w;
}

describe("PublishedScreen — submission period ended", () => {
	it("leads with the reader's step, its button, and the opening step above the finished row", async () => {
		const w = await show(TURN, true);
		const region = w.get('[data-testid="kt-guidance"]').element;
		expect(region.children[0].getAttribute("data-kt")).toBe("next-step");
		expect(w.get('[data-kt="next-step"]').text()).toContain("Appoint opening committee");
		const buttons = w.findAll('[data-kt="next-step"] button');
		expect(buttons.map((b) => b.text())).toEqual(["Open opening record"]);
		let fixed = null;
		await w.findComponent({ name: "TenderGuidance" }).vm.$emit("fix", OPEN);
		fixed = w.emitted("fix");
		expect(fixed[0][0].target).toEqual(["tenders", "TND-MOH-2027-003", "opening"]);
		expect(w.get('[data-testid="kt-journey-caption"]').text()).toBe("Tender preparation is complete");
	});

	it("says no business action line at all to a reader who has a step", async () => {
		const w = await show(TURN, true);
		expect(w.find('[data-testid="tnd-no-action"]').exists()).toBe(false);
		expect(w.find('[data-testid="tnd-nothing-to-do"]').exists()).toBe(false);
	});

	it("keeps the status for a reader with no step and says there is nothing to do only then", async () => {
		const w = await show(DONE, false);
		expect(w.get('[data-kt="next-step"]').text()).toContain("The system closed supplier submission");
		expect(w.get('[data-testid="kt-guidance"]').element.children[0].getAttribute("data-kt")).toBe("journey");
		expect(w.find('[data-testid="tnd-no-action"]').exists()).toBe(false);
		expect(w.get('[data-testid="tnd-nothing-to-do"]').text()).toBe("Nothing for you to do here.");
	});

	it("says nothing in the footer to a reader who is waiting; the lead panel names who", async () => {
		const w = await show(answer("waiting", "Waiting for Amina Hassan to appoint the opening committee"), true);
		expect(w.find('[data-testid="tnd-nothing-to-do"]').exists()).toBe(false);
		expect(w.find('[data-testid="tnd-no-action"]').exists()).toBe(false);
	});
});
