// REQ-CHG-001 v1.6 §13.1/§13.5 — the shared editor shell: exact header
// (eyebrow, title, status badge, quiet reference line), the left step
// navigation (exact completion text, disabled steps never navigable), and
// the footer's Save draft + step-specific continue action.
import { describe, expect, it } from "vitest";
import { mount } from "@vue/test-utils";
import EditorShell from "./EditorShell.vue";

const STEPS = [
	{ number: 1, label: "Request and drawdown", statusText: "In progress", kind: "active", enabled: true },
	{ number: 2, label: "Equipment items", statusText: "Not started", kind: "not-started", enabled: true },
	{ number: 3, label: "Technical and support", statusText: "Not started", kind: "not-started", enabled: false },
	{ number: 4, label: "Services and acceptance", statusText: "Not started", kind: "not-started", enabled: false },
	{ number: 5, label: "Review and submit", statusText: "8 blockers", kind: "blocked", enabled: false },
];

function make(overrides = {}) {
	return mount(EditorShell, {
		props: {
			title: "Clinical training and deployment laptops for digital health rollout",
			status: "Draft",
			reference: "REQ-MOH-2027-033-001 · PPI-MOH-2027-033 · Version 1",
			steps: STEPS,
			activeStep: 1,
			continueLabel: "Continue to equipment items",
			pending: false,
			...overrides,
		},
		slots: { default: "<div data-testid='step-slot'>step content</div>" },
	});
}

describe("EditorShell — §13.1/§13.5 shared chrome", () => {
	it("renders the exact header: eyebrow, title, status badge and quiet reference line", () => {
		const w = make();
		expect(w.find(".req-eyebrow").text()).toBe("PROCUREMENT REQUISITIONS");
		expect(w.find(".req-editor-title").text()).toBe("Clinical training and deployment laptops for digital health rollout");
		expect(w.find(".kt-status").text()).toBe("Draft");
		expect(w.find(".kt-status").classes()).toContain("is-draft");
		expect(w.find(".req-editor-reference").text()).toBe("REQ-MOH-2027-033-001 · PPI-MOH-2027-033 · Version 1");
	});

	it("renders all five steps with their exact label and status text", () => {
		const w = make();
		const steps = w.findAll(".req-step");
		expect(steps).toHaveLength(5);
		expect(steps[0].find(".req-step-label").text()).toBe("Request and drawdown");
		expect(steps[0].find(".req-step-status").text()).toBe("In progress");
		expect(steps[4].find(".req-step-status").text()).toBe("8 blockers");
	});

	it("marks the active step and disables navigation to a step not yet built", async () => {
		const w = make();
		expect(w.find('[data-testid="req-step-1"]').classes()).toContain("is-active");
		const step3 = w.find('[data-testid="req-step-3"]');
		expect(step3.attributes("disabled")).toBeDefined();
		await step3.trigger("click");
		expect(w.emitted("go-to-step")).toBeUndefined();
	});

	it("emits go-to-step for an enabled step", async () => {
		const w = make();
		await w.find('[data-testid="req-step-2"]').trigger("click");
		expect(w.emitted("go-to-step")[0][0]).toBe(2);
	});

	it("renders the slotted step content", () => {
		const w = make();
		expect(w.find('[data-testid="step-slot"]').text()).toBe("step content");
	});

	it("emits save-draft and continue from the default footer, with the exact continue label", async () => {
		const w = make();
		const buttons = w.findAll(".req-editor-footer button");
		expect(buttons[0].text()).toBe("Save draft");
		expect(buttons[1].text()).toBe("Continue to equipment items");
		await buttons[0].trigger("click");
		expect(w.emitted("save-draft")).toHaveLength(1);
		await buttons[1].trigger("click");
		expect(w.emitted("continue")).toHaveLength(1);
	});

	it("disables the footer buttons while a command is pending", () => {
		const w = make({ pending: true });
		const buttons = w.findAll(".req-editor-footer button");
		expect(buttons[0].attributes("disabled")).toBeDefined();
		expect(buttons[1].attributes("disabled")).toBeDefined();
	});

	it("shows the Request-upstream-correction trigger only when the server permits it, and emits on click", async () => {
		const hidden = make();
		expect(hidden.find('[data-testid="req-upstream-trigger"]').exists()).toBe(false);
		const shown = make({ showUpstreamCorrection: true });
		await shown.find('[data-testid="req-upstream-trigger"]').trigger("click");
		expect(shown.emitted("request-upstream-correction")).toHaveLength(1);
	});

	it("renders a custom footer slot instead of the default Save draft/Continue pair", () => {
		const w = mount(EditorShell, {
			props: { title: "t", steps: STEPS, activeStep: 5, pending: false },
			slots: { default: "<div></div>", footer: "<button data-testid='custom-footer-btn'>Custom</button>" },
		});
		expect(w.find('[data-testid="custom-footer-btn"]').exists()).toBe(true);
		expect(w.findAll(".req-editor-footer button")).toHaveLength(1);
	});
});
