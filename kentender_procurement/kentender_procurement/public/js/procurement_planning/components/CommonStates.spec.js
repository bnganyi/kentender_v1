// PLN-CHG-001 v1.24 §10.17 — CommonStates component tests (U21-MASKED/
// LOAD-FAILURE and the shared empty-list fragments).
//
// Every kind's exact copy, the loading kinds' live shimmer (not the
// artboard's static placeholder text), and the `action` emit for every kind
// with a button. FORBIDDEN/NO_CONTEXT moved to WorkspaceScreen.vue (its own
// server-supplied §3A.4 copy, not a generic empty state), and the per-screen
// notice-banner states (changed record/authority, unsaved-save-failure,
// uncertain command result, historical read-only) are `.kt-notice` banners
// each screen composes inline — neither is this shared component's kind
// vocabulary any more, so this file previously tested kinds ("forbidden-*",
// "config-missing", "stale-action", "historical-readonly") that do not exist
// on the component at all (found 22 Sep 2026, re-diffing CommonStates.vue
// against the real v1.24 artboards).
import { describe, expect, it } from "vitest";
import { mount } from "@vue/test-utils";
import CommonStates from "./CommonStates.vue";

const KINDS_WITH_ACTION = {
	masked: { heading: "This record is not available to you.", action: "Go to procurement planning" },
	"load-failure": { heading: "Procurement Planning could not be loaded.", action: "Try again" },
	"filtered-empty": { heading: "No requirements match this search.", action: "Clear filters" },
};

const KINDS_WITHOUT_ACTION = {
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

	for (const [kind, { heading, action }] of Object.entries(KINDS_WITH_ACTION)) {
		it(`renders ${kind} with its action and emits on click`, async () => {
			const wrapper = mount(CommonStates, { props: { kind } });
			expect(wrapper.find("h3").text()).toBe(heading);
			const button = wrapper.get("button");
			expect(button.text()).toBe(action);
			await button.trigger("click");
			expect(wrapper.emitted("action")).toHaveLength(1);
		});
	}

	it("carries a support reference on load-failure only when one is supplied", () => {
		const withRef = mount(CommonStates, { props: { kind: "load-failure", supportRef: "PLN-1234" } });
		expect(withRef.text()).toContain("Support reference: PLN-1234");
		const withoutRef = mount(CommonStates, { props: { kind: "load-failure" } });
		expect(withoutRef.text()).not.toContain("Support reference");
	});

	it("renders the loading-workspace kind as a live shimmer, not the artboard's placeholder text", () => {
		const wrapper = mount(CommonStates, { props: { kind: "loading-workspace" } });
		expect(wrapper.find("h3").exists()).toBe(false);
		expect(wrapper.findAll(".kt-skel").length).toBeGreaterThan(0);
		expect(wrapper.find(".pln-sr-only").text()).toBe("Loading procurement planning…");
	});

	it("renders the loading-review kind with its own announced heading", () => {
		const wrapper = mount(CommonStates, { props: { kind: "loading-review" } });
		expect(wrapper.find(".pln-sr-only").text()).toBe("Loading plan review…");
	});

	it("respects a custom loadingRows count", () => {
		const wrapper = mount(CommonStates, { props: { kind: "loading-workspace", loadingRows: 5 } });
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
