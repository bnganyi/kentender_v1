// KT-STD-001 v1.8 §2.9 — the shared journey tracker and next-step block draw
// exactly the server's answer: every kind in its own placement, the blocked
// container with one control per fix, the reduced tracker, and nothing at all
// when nothing is supplied (§2.9.3 rule 8).
import { describe, expect, it } from "vitest";
import { mount } from "@vue/test-utils";
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
		const stages = w.findAll(".kt-journey-stage");
		expect(stages).toHaveLength(7);
		expect(stages[0].classes()).toContain("is-blocked");
		expect(stages[0].text()).toBe("PreparationBlocked · Mercy Kilonzo");
		expect(stages[1].text()).toBe("Funding confirmationNot started");
		expect(w.findAll(".kt-journey-holder")).toHaveLength(1);
		expect(w.get("[data-kt=journey]").attributes("aria-label")).toBe("Journey");
	});

	it("draws the reduced one-line form when asked", () => {
		const w = mount(JourneyTracker, { props: { journey: journey({ current: 5, holder: "Amina Hassan", reduced: true }) } });
		expect(w.get("p.kt-journey.is-reduced").text()).toBe("Stage 6 of 7: Publication — Amina Hassan");
		expect(w.get(".kt-journey-current").text()).toBe("Publication");
		expect(w.find(".kt-journey-stage").exists()).toBe(false);
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
		const waiting = { kind: "waiting", label: "Waiting", headline: "Waiting for Amina Hassan (Accounting Officer) to adopt or return the plan", since: { at: "x", display: "7 Dec 2026, 10:00 EAT" }, blockers: [] };
		const head = mount(NextStep, { props: { answer: waiting, placement: "head" } });
		expect(head.get("p.kt-next-step").text()).toBe("Waiting Waiting for Amina Hassan (Accounting Officer) to adopt or return the plan since 7 Dec 2026, 10:00 EAT");
		expect(mount(NextStep, { props: { answer: waiting, placement: "body" } }).find("[data-kt=next-step]").exists()).toBe(false);
		const done = mount(NextStep, { props: { answer: { kind: "done", label: "Done", headline: "Accepted by Mercy Kilonzo on 29 Nov 2026, 15:00 EAT", blockers: [] } } });
		expect(done.get("p.kt-next-step").text()).toBe("Done Accepted by Mercy Kilonzo on 29 Nov 2026, 15:00 EAT");
		expect(done.find(".kt-next-step-since").exists()).toBe(false);
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
