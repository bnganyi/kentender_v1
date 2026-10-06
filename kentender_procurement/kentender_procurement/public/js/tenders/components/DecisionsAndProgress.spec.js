// Decisions and progress on the published Tender record (OVS-CHG-001 v0.6 §8, §13,
// §15: OVS-AC-003, OVS-AC-010, OVS-AC-011; board views OVS-TPR-01 to 06). One
// block per later stage as its owner discloses it; a header link gives way only
// to a block that carries the same way in; a stage that failed to load says so
// and offers Try again while the others stay usable.
import { describe, expect, it } from "vitest";
import { mount } from "@vue/test-utils";
import { nextTick } from "vue";

import { publishedData } from "./fixtures.js";
import PublishedScreen from "./PublishedScreen.vue";

const opening = { key: "bid-opening", label: "Bid opening", state: "ok", status: "Complete", disclosure: "full", facts: [{ label: "Opening completed", value: "12 Jun 2027, 11:10:30 EAT" }, { label: "Bids opened", value: "4" }],
	outcome: null, reason: "", outstanding: null, notice: "", links: [{ key: "view-record", label: "View opening record", route: ["tenders", "TND-1", "opening"] }] };
const evaluation = { key: "bid-evaluation", label: "Bid evaluation", state: "ok", status: "Report sent", disclosure: "full", facts: [{ label: "Recommendation", value: "Afya Digital Supplies Limited" },
	{ label: "Evaluated total", value: "KES 46,400,000.00" }, { label: "Report sent", value: "16 Jun 2027, 14:07 EAT" }, { label: "Sent to", value: "Charles Mutiso" }],
	outcome: { label: "Outcome", value: "Recommendation" }, reason: "The only bid received meets the published requirements.", outstanding: null, notice: "",
	links: [{ key: "view-record", label: "View evaluation", route: ["tenders", "TND-1", "evaluation"] }, { key: "view-report", label: "View report", route: ["tenders", "TND-1", "evaluation", "report"] }] };
const protectedEvaluation = { ...evaluation, status: "Reviewing", disclosure: "status_only", facts: [{ label: "Committee appointed", value: "11 Jun 2027, 09:00 EAT" }], reason: "", outcome: null,
	notice: "Bid details are shared with you when the committee's report is sent.", links: [evaluation.links[0]] };
const award = { key: "award", label: "Award", state: "ok", status: "Opinion", disclosure: "status_only", facts: [{ label: "Stage", value: "Opinion" }], outcome: null, reason: "",
	outstanding: { text: "Charles Mutiso is preparing the professional opinion.", holder: "Charles Mutiso" }, notice: "", links: [{ key: "view-record", label: "View award", route: ["award", "AWD-1"] }] };
const failed = { key: "bid-evaluation", label: "Bid evaluation", state: "unavailable", error_key: "OVS_STAGE_UNAVAILABLE", message: "We could not load this stage", status: "", disclosure: "status_only",
	facts: [], outcome: null, reason: "", outstanding: null, notice: "", links: [] };
const headerLinks = [{ key: "bid-opening", label: "Bid opening", route: ["tenders", "TND-1", "opening"] }, { key: "bid-evaluation", label: "Bid evaluation", route: ["tenders", "TND-1", "evaluation"] },
	{ key: "award", label: "Award", route: ["award", "AWD-1"] }];

function screen(stages, links = headerLinks) {
	const data = publishedData("HOPF");
	return mount(PublishedScreen, { props: { record: { ...data.record, record_links: links, stage_summaries: stages }, review: data.review || {}, pending: false }, attachTo: document.body });
}

describe("Decisions and progress", () => {
	it("shows one block per stage, with the decision, its reason and a way to the owner's record", async () => {
		const w = screen([opening, evaluation, award]);
		await nextTick();
		const section = w.find('[data-testid="tnd-decisions-progress"]');
		expect(section.find("h2").text()).toBe("Decisions and progress");
		expect(w.findAll(".tnd-stage").map((b) => b.attributes("data-testid"))).toEqual(["tnd-stage-bid-opening", "tnd-stage-bid-evaluation", "tnd-stage-award"]);
		const ev = w.find('[data-testid="tnd-stage-bid-evaluation"]');
		expect(ev.text()).toContain("Afya Digital Supplies Limited");
		expect(ev.text()).toContain("KES 46,400,000.00");
		expect(ev.text()).toContain("The only bid received meets the published requirements.");
		expect(ev.findAll("button").map((b) => b.text())).toEqual(["View record", "View report"]);
		expect(w.find('[data-testid="tnd-stage-award"] [data-testid="tnd-stage-outstanding"]').text()).toBe("Charles Mutiso is preparing the professional opinion.");
		w.unmount();
	});
	it("a status-only stage says why there is nothing more and offers no report", async () => {
		const w = screen([opening, protectedEvaluation]);
		await nextTick();
		const ev = w.find('[data-testid="tnd-stage-bid-evaluation"]');
		expect(ev.attributes("data-disclosure")).toBe("status_only");
		expect(ev.text()).toContain("Bid details are shared with you when the committee's report is sent.");
		expect(ev.text()).not.toContain("Afya");
		expect(ev.findAll("button").map((b) => b.text())).toEqual(["View record"]);
		w.unmount();
	});
	it("replaces a header link only when its stage block carries the same way in", async () => {
		const w = screen([opening, evaluation, award]);
		await nextTick();
		expect(w.findAll("[data-testid^='tnd-link-']")).toHaveLength(0);
		const kept = screen([opening], headerLinks);
		await nextTick();
		expect(kept.findAll("[data-testid^='tnd-link-']").map((b) => b.attributes("data-testid"))).toEqual(["tnd-link-bid-evaluation", "tnd-link-award"]);
		w.unmount();
		kept.unmount();
	});
	it("a stage that failed to load keeps its old link, says so, and offers Try again without disturbing the others", async () => {
		const w = screen([opening, failed, award]);
		await nextTick();
		expect(w.find('[data-testid="tnd-stage-bid-evaluation"]').text()).toContain("We could not load this stage");
		expect(w.findAll("[data-testid^='tnd-link-']").map((b) => b.attributes("data-testid"))).toEqual(["tnd-link-bid-evaluation"]); // equivalent navigation absent: the header link stays
		expect(w.find('[data-testid="tnd-stage-bid-opening"]').text()).toContain("Bids opened");
		await w.find('[data-testid="tnd-stage-retry"]').trigger("click");
		expect(w.emitted("refresh")).toHaveLength(1);
		w.unmount();
	});
	it("opens the owner's record from a block", async () => {
		const w = screen([opening, evaluation, award]);
		await nextTick();
		await w.find('[data-testid="tnd-stage-bid-evaluation-view-report"]').trigger("click");
		expect(w.emitted("open-link")[0][0]).toEqual(["tenders", "TND-1", "evaluation", "report"]);
		w.unmount();
	});
	it("a department reader, who is sent no publication record, still gets the record and the stages", async () => {
		// the server withholds `publication` from a department head; the screen used to fail on it
		const data = publishedData("HOPF");
		const w = mount(PublishedScreen, { props: { record: { ...data.record, publication: null, open_period: null, record_links: [], stage_summaries: [evaluation] }, review: {}, pending: false }, attachTo: document.body });
		await nextTick();
		expect(w.find('[data-testid="tnd-published-facts"]').exists()).toBe(true);
		expect(w.find('[data-testid="tnd-published-facts"]').text()).not.toContain("Publication authorised by");
		expect(w.find('[data-testid="tnd-stage-bid-evaluation"]').text()).toContain("Afya Digital Supplies Limited");
		w.unmount();
	});
	it("draws nothing for a reader to whom no stage is disclosed", async () => {
		const w = screen([], []);
		await nextTick();
		expect(w.find('[data-testid="tnd-decisions-progress"]').exists()).toBe(false);
		w.unmount();
	});
});
