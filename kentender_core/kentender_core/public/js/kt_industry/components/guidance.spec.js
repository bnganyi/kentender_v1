// KT-STD-001 v1.8 §2.9 — the shared journey tracker and next-step block draw
// exactly the server's answer: every kind in its own placement, the blocked
// container with one control per fix, the reduced tracker, and nothing at all
// when nothing is supplied (§2.9.3 rule 8).
import { describe, expect, it } from "vitest";
import { mount } from "@vue/test-utils";
import GuidanceRegion from "./GuidanceRegion.vue";
import JourneyTracker from "./JourneyTracker.vue";
import NextStep from "./NextStep.vue";

const STAGES = [
	["preparation", "Preparation"], ["funding", "Funding confirmation"], ["signature", "Signature"],
	["ao", "AO adoption"], ["statutory", "Cabinet Secretary approval"], ["publication", "Publication"], ["in_force", "In force"],
];

function journey({ current = 0, blocked = false, holder = "", reduced = false, upstream = null } = {}) {
	const stages = STAGES.map(([code, label], i) => {
		const marker = i < current ? "done" : i === current ? (blocked ? "blocked" : "current") : "not_started";
		return { code, label, marker, marker_label: { done: "Done", current: "Current", blocked: "Blocked", not_started: "Not started" }[marker], holder: i === current ? holder : "" };
	});
	return {
		stages,
		current: STAGES[current][0],
		reduced,
		reduced_parts: { prefix: `Stage ${current + 1} of 7: `, label: STAGES[current][1], suffix: holder ? ` — ${holder}` : "" },
		upstream,
		downstream: null,
	};
}

const OVER = {
	kind: "your_turn_blocked",
	label: "Your turn, blocked",
	headline: "Over budget by KES 2,000,000 on Digital health workforce development",
	sentence: "You can request the funding check once every budget line fits. Choose one way to fix it.",
	blockers: [
		{
			reason_code: "PLN_PLAN_NOT_AFFORDABLE",
			headline: "Over budget by KES 2,000,000 on Digital health workforce development",
			facts: [],
			fixes: [
				{ fix_id: "request_budget_revision", label: "Request budget revision from Josphat Mwangi", kind: "command", primary: true },
				{ fix_id: "reduce_purchase", label: "Reduce a purchase", kind: "focus", primary: false },
			],
		},
	],
};

describe("JourneyTracker", () => {
	it("draws one row with a marker per stage and names only the current stage's holder", () => {
		const w = mount(JourneyTracker, { props: { journey: journey({ current: 0, blocked: true, holder: "Mercy Kilonzo" }) } });
		const stages = w.findAll("ol.kt-journey > .kt-journey-stage");
		expect(stages).toHaveLength(7);
		expect(stages[0].classes()).toContain("is-blocked");
		// design-system handoff §3: bar, numbered label, state line
		expect(stages[0].find(".kt-journey-bar").exists()).toBe(true);
		expect(stages[0].get(".kt-journey-num").text()).toBe("1");
		expect(stages[0].get(".kt-journey-state").text()).toBe("Blocked · Mercy Kilonzo");
		expect(stages[1].get(".kt-journey-state").text()).toBe("Not started");
		expect(w.findAll(".kt-journey-state").filter((s) => s.text().includes("Mercy Kilonzo"))).toHaveLength(1);
		expect(w.get("ol.kt-journey").attributes("aria-label")).toBe("Journey");
		expect(stages[0].attributes("aria-current")).toBe("step");
	});

	it("draws the reduced one-line form when asked", () => {
		const w = mount(JourneyTracker, { props: { journey: journey({ current: 5, holder: "Amina Hassan", reduced: true }) } });
		expect(w.get(".kt-journey.is-reduced").text()).toBe("Stage 6 of 7: Publication — Amina Hassan");
		expect(w.get(".kt-journey-current").text()).toBe("Publication");
		expect(w.findAll(".kt-journey-bars > span")).toHaveLength(7);
		expect(w.find(".kt-journey-stage").exists()).toBe(false);
	});

	it("marks done stages with a check and keeps a compact copy for narrow hosts", () => {
		const w = mount(JourneyTracker, { props: { journey: journey({ current: 2, holder: "Josphat Mwangi" }) } });
		expect(w.findAll("ol.kt-journey .kt-journey-state")[0].text()).toBe("✓ Done");
		// the one-line copy the container query shows under 600px
		expect(w.get(".kt-journey-compact .kt-journey-reduced-text").text()).toBe("Stage 3 of 7: Signature — Josphat Mwangi");
		expect(w.findAll(".kt-journey.is-reduced")).toHaveLength(0);
	});

	it("emits the upstream link instead of navigating itself", async () => {
		const upstream = { label: "3 departmental requirements included", kind: "focus", target: "requirements" };
		const w = mount(JourneyTracker, { props: { journey: journey({ upstream }) } });
		await w.get("[data-testid=kt-journey-upstream]").trigger("click");
		expect(w.emitted("link")[0][0]).toEqual(upstream);
	});

	it("draws nothing when no journey is supplied", () => {
		expect(mount(JourneyTracker, { props: { journey: null } }).html()).toBe("<!--v-if-->");
	});
});

describe("NextStep", () => {
	it("draws Your turn, Waiting and Done as one line in the header placement only", () => {
		const waiting = { kind: "waiting", label: "Waiting on someone", headline: "Waiting for Amina Hassan (Accounting Officer) to adopt or return the plan", since: { at: "x", display: "7 Dec 2026, 10:00 EAT" }, blockers: [] };
		const head = mount(NextStep, { props: { answer: waiting, placement: "head" } });
		const line = head.get("div.kt-next-step.is-waiting");
		expect(line.get(".kt-next-step-label").text()).toBe("Waiting on someone");
		expect(line.get(".kt-next-step-headline").text()).toBe("Waiting for Amina Hassan (Accounting Officer) to adopt or return the plan since 7 Dec 2026, 10:00 EAT");
		expect(mount(NextStep, { props: { answer: waiting, placement: "body" } }).find("[data-kt=next-step]").exists()).toBe(false);
		const done = mount(NextStep, { props: { answer: { kind: "done", label: "Done", headline: "Accepted by Mercy Kilonzo on 29 Nov 2026, 15:00 EAT", blockers: [] } } });
		expect(done.get("div.kt-next-step.is-done .kt-next-step-headline").text()).toBe("Accepted by Mercy Kilonzo on 29 Nov 2026, 15:00 EAT");
		expect(done.find(".kt-next-step-since").exists()).toBe(false);
	});

	it("draws Scheduled as a compact line with the neutral rule and no action (KT-STD-001 v1.10 §2.9.1)", () => {
		const answer = { kind: "timed", label: "Scheduled", headline: "Submissions close automatically at 12 Jun 2027, 11:00 EAT.", sentence: "", stage: "open",
			holder: { role: "System", people: [], display: "System" }, since: null, blockers: [], fixes: [], primary_action: "" };
		const w = mount(NextStep, { props: { answer, placement: "region" } });
		const line = w.find('[data-kt="next-step"]');
		expect(line.classes()).toContain("is-waiting");
		expect(line.find(".kt-next-step-label").text()).toBe("Scheduled");
		expect(line.find(".kt-next-step-headline").text()).toBe("Submissions close automatically at 12 Jun 2027, 11:00 EAT.");
		expect(w.findAll("button")).toHaveLength(0);
	});

	it("draws Your turn with its accent rule and one optional sentence", () => {
		const turn = { kind: "your_turn", label: "Your turn", headline: "Prepare an addendum or recommend cancellation if the open Tender needs it.", sentence: "These are available options, not overdue work.", blockers: [], fixes: [] };
		const w = mount(NextStep, { props: { answer: turn, placement: "region" } });
		expect(w.get("div.kt-next-step.is-turn .kt-next-step-sentence").text()).toBe("These are available options, not overdue work.");
		expect(w.find("button").exists()).toBe(false);
	});

	it("never repeats a since fact the headline already states", () => {
		const waiting = { kind: "waiting", label: "Waiting on someone", headline: "Grace Wanjiku, Departmental Author, is correcting the requisition since 21 Apr 2027, 09:00 EAT.", since: { at: "x", display: "21 Apr 2027, 09:00 EAT" }, blockers: [] };
		const w = mount(NextStep, { props: { answer: waiting, placement: "region" } });
		expect(w.find(".kt-next-step-since").exists()).toBe(false);
		expect(w.get(".kt-next-step-headline").text()).toBe("Grace Wanjiku, Departmental Author, is correcting the requisition since 21 Apr 2027, 09:00 EAT.");
	});

	it("draws the blocked kind as the one container, in the body placement, with one control per fix", async () => {
		const w = mount(NextStep, { props: { answer: OVER, placement: "body" } });
		const block = w.get("div.kt-notice.is-warning.kt-next-step-block");
		expect(block.find(".kt-notice-icon").exists()).toBe(true);
		expect(block.get(".kt-next-step-block-headline").text()).toBe("Over budget by KES 2,000,000 on Digital health workforce development");
		const buttons = block.findAll("button");
		expect(buttons.map((b) => b.text())).toEqual(["Request budget revision from Josphat Mwangi", "Reduce a purchase"]);
		expect(buttons[0].classes()).toContain("kt-btn-primary");
		expect(buttons[1].classes()).toContain("kt-btn-secondary");
		await buttons[0].trigger("click");
		expect(w.emitted("fix")[0][0].fix_id).toBe("request_budget_revision");
		expect(mount(NextStep, { props: { answer: OVER, placement: "head" } }).find("[data-kt=next-step]").exists()).toBe(false);
	});

	it("disables fix controls while a command is pending", () => {
		const w = mount(NextStep, { props: { answer: OVER, placement: "body", pending: true } });
		expect(w.findAll("button").every((b) => b.attributes("disabled") !== undefined)).toBe(true);
	});

	it("states a setting blocker's facts and a text-only recovery with no button", () => {
		const setting = {
			...OVER,
			headline: "Annual Plan approval authority is not set up",
			sentence: "",
			blockers: [{
				reason_code: "PLN_STATUTORY_ROUTE_UNCONFIGURED",
				headline: "Annual Plan approval authority is not set up",
				facts: [{ label: "Setting", value: "Annual Plan approval authority" }, { label: "Affected action", value: "Adopt and submit" }, { label: "Responsible role", value: "Administrator or System Manager" }],
				fixes: [{ fix_id: "ask_admin", label: "Ask your KenTender administrator to complete this setting.", kind: "text" }],
			}],
		};
		const w = mount(NextStep, { props: { answer: setting, placement: "body" } });
		expect(w.findAll(".kt-next-step-facts .kt-label").map((l) => l.text())).toEqual(["Setting", "Affected action", "Responsible role"]);
		expect(w.find("button").exists()).toBe(false);
		expect(w.get(".kt-next-step-fix-text").text()).toBe("Ask your KenTender administrator to complete this setting.");
	});

	it("lists several blockers on their own lines under a count headline", () => {
		const two = {
			...OVER,
			headline: "2 things stop this plan going to Finance",
			blockers: [
				OVER.blockers[0],
				{ reason_code: "PLN_PLAN_CONTENTS_INCOMPLETE", headline: "1 purchase needs a procurement method", facts: [], fixes: [{ fix_id: "choose_method", label: "Choose a procurement method", kind: "route" }] },
			],
		};
		const w = mount(NextStep, { props: { answer: two, placement: "body" } });
		expect(w.findAll(".kt-next-step-blockers > li").map((li) => li.attributes("data-reason"))).toEqual(["PLN_PLAN_NOT_AFFORDABLE", "PLN_PLAN_CONTENTS_INCOMPLETE"]);
		expect(w.findAll("button")).toHaveLength(3);
	});

	it("keeps each blocker's facts when several blockers are listed", () => {
		// A declined budget revision is stated as facts on the over-budget
		// blocker; a second blocker must not hide it (found live 25 Sep 2026).
		const declined = {
			reason_code: "PLN_PLAN_NOT_AFFORDABLE", headline: "Over budget by KES 2,000,000 on Digital health workforce development",
			facts: [{ label: "Budget revision", value: "Declined by Josphat Mwangi on 25 Sep 2026, 23:51 EAT" }, { label: "Reason", value: "No further allocation this year." }],
			fixes: [],
		};
		const method = { reason_code: "PLN_PLAN_CONTENTS_INCOMPLETE", headline: "Choose a procurement method for Clinical laptops", facts: [], fixes: [] };
		const w = mount(NextStep, { props: { answer: { kind: "your_turn_blocked", label: "Your turn, blocked", headline: "2 issues stop this plan going to Finance", blockers: [declined, method] }, placement: "body" } });
		const row = w.find('[data-reason="PLN_PLAN_NOT_AFFORDABLE"]');
		expect(row.text()).toContain("Declined by Josphat Mwangi on 25 Sep 2026, 23:51 EAT");
		expect(row.text()).toContain("No further allocation this year.");
		expect(w.find('[data-reason="PLN_PLAN_CONTENTS_INCOMPLETE"] .kt-next-step-blocker-facts').exists()).toBe(false);
	});

	it("puts a Your-turn route fix on the line itself, so a turn held on another page has a way there", async () => {
		// Found live 25 Sep 2026: a Budget Officer reading the plan was told
		// it was their turn with nothing to press.
		const open = { fix_id: "open_budget_revision_request", label: "Open the request in Budget & Funding", kind: "route", target: ["budget-funding"] };
		const turn = { kind: "your_turn", label: "Your turn", headline: "Revise Digital health workforce development for the plan update", blockers: [], fixes: [open] };
		const w = mount(NextStep, { props: { answer: turn, placement: "head" } });
		const link = w.find("[data-kt=next-step] [data-fix=open_budget_revision_request]");
		expect(link.text()).toBe("Open the request in Budget & Funding");
		await link.trigger("click");
		expect(w.emitted("fix")[0][0]).toEqual(open);
		// A waiting line never carries a control, and a turn without a route
		// fix draws only its words.
		expect(mount(NextStep, { props: { answer: { ...turn, kind: "waiting", label: "Waiting" }, placement: "head" } }).find("[data-fix]").exists()).toBe(false);
		expect(mount(NextStep, { props: { answer: { ...turn, fixes: [] }, placement: "head" } }).find("[data-fix]").exists()).toBe(false);
	});

	it("draws nothing for Not involved or an absent answer", () => {
		expect(mount(NextStep, { props: { answer: { kind: "not_involved", label: "", headline: "", blockers: [] } } }).find("[data-kt]").exists()).toBe(false);
		expect(mount(NextStep, { props: { answer: null } }).find("[data-kt]").exists()).toBe(false);
	});
});

describe("GuidanceRegion", () => {
	it("draws the tracker above the next step in one region, and the blocked kind in the same region", () => {
		const w = mount(GuidanceRegion, { props: { journey: journey({ current: 1, holder: "Charles Mutiso" }), answer: OVER, label: "Tender journey" } });
		const region = w.get("section.kt-guidance");
		expect(region.get("ol.kt-journey").attributes("aria-label")).toBe("Tender journey");
		expect(region.get("[data-kt=next-step]").classes()).toContain("kt-notice");
	});

	it("draws nothing for a Not involved reader with no tracker", () => {
		expect(mount(GuidanceRegion, { props: { journey: null, answer: { kind: "not_involved", label: "", headline: "" } } }).html()).toBe("<!--v-if-->");
	});
});
