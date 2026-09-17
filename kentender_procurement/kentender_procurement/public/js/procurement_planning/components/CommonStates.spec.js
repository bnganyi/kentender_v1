// PLN-CHG-001 v1.18 §10.12 — CommonStates component tests (U21-access/U21-empty).
// Every kind's exact copy, the loading kinds' live shimmer (not the artboard's
// static placeholder text), and the `action` emit for every kind with a button.
import { describe, expect, it } from "vitest";
import { mount } from "@vue/test-utils";
import CommonStates from "./CommonStates.vue";

const KINDS_WITH_ACTION = {
	"record-not-available": "Go to Procurement Planning",
	"load-error": "Try again",
	"config-missing": "Back to Annual Plan",
	"stale-action": "Refresh",
	"empty-search": "Clear filters",
	"historical-readonly": "View current Active Plan",
};

const KINDS_WITHOUT_ACTION = {
	"forbidden-planning": "You do not have access to Procurement Planning",
	"forbidden-system-setup": "You do not have access to System setup",
	"empty-accepted-requirements": "No accepted departmental requirements",
	"empty-validation-queue": "No departmental plans awaiting validation",
	"empty-corrections": "No correction requests",
};

describe("CommonStates", () => {
	for (const [kind, heading] of Object.entries(KINDS_WITHOUT_ACTION)) {
		it(`renders ${kind} with no button`, () => {
			const wrapper = mount(CommonStates, { props: { kind } });
			expect(wrapper.find("h3").text()).toBe(heading);
			expect(wrapper.find("button").exists()).toBe(false);
			expect(wrapper.get(`[data-testid="pln-common-${kind}"]`)).toBeTruthy();
		});
	}

	for (const [kind, actionLabel] of Object.entries(KINDS_WITH_ACTION)) {
		it(`renders ${kind} with its action and emits on click`, async () => {
			const wrapper = mount(CommonStates, { props: { kind } });
			const button = wrapper.get("button");
			expect(button.text()).toBe(actionLabel);
			await button.trigger("click");
			expect(wrapper.emitted("action")).toHaveLength(1);
		});
	}

	it("renders the loading-planning kind as a live shimmer, not the artboard's placeholder text", () => {
		const wrapper = mount(CommonStates, { props: { kind: "loading-planning" } });
		expect(wrapper.find("h3").exists()).toBe(false);
		expect(wrapper.findAll(".kt-skel").length).toBeGreaterThan(0);
		expect(wrapper.find(".pln-sr-only").text()).toBe("Loading Procurement Planning…");
	});

	it("renders the loading-review kind with its own announced heading", () => {
		const wrapper = mount(CommonStates, { props: { kind: "loading-review" } });
		expect(wrapper.find(".pln-sr-only").text()).toBe("Loading Plan review…");
	});

	it("respects a custom loadingRows count", () => {
		const wrapper = mount(CommonStates, { props: { kind: "loading-planning", loadingRows: 5 } });
		expect(wrapper.findAll(".pln-skel-row")).toHaveLength(5);
	});

	it("defaults to 3 skeleton rows", () => {
		const wrapper = mount(CommonStates, { props: { kind: "loading-review" } });
		expect(wrapper.findAll(".pln-skel-row")).toHaveLength(3);
	});

	it("accepts a caller-supplied testid override", () => {
		const wrapper = mount(CommonStates, { props: { kind: "empty-corrections", testid: "pln-item-corrections-empty" } });
		expect(wrapper.find('[data-testid="pln-item-corrections-empty"]').exists()).toBe(true);
	});
});
