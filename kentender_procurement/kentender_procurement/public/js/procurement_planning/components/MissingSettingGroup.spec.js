// PLN-CHG-001 v1.24 §10.16 — MissingSettingGroup component tests.
//
// One panel is drawn exactly as C03/C04 draw it — no group wrapper. Two or
// more collapse to a summary line, closed by default, that names how many
// there are; opening it reveals every panel, each still telling its own
// setting/purchase/action apart from the others.
import { describe, expect, it } from "vitest";
import { mount } from "@vue/test-utils";
import MissingSettingGroup from "./MissingSettingGroup.vue";

function panel(overrides = {}) {
	return {
		setting: "Applicable procurement method rule",
		affected_action: "Send plan for governance review",
		affected_purchase: "Clinical training laptops for digital health rollout · PPI-MOH-2027-001",
		responsible_role: "Administrator or System Manager",
		note: "",
		lede: "",
		can_open_setup: false,
		action: "",
		href: "",
		ask_text: "Ask your KenTender administrator to complete this setting.",
		...overrides,
	};
}

describe("MissingSettingGroup — a single panel", () => {
	it("renders it directly, with no group wrapper", () => {
		const w = mount(MissingSettingGroup, { props: { panels: [panel()] } });
		expect(w.find('[data-testid="pln-missing-settings-group"]').exists()).toBe(false);
		expect(w.find('[data-testid="pln-missing-setting"]').exists()).toBe(true);
	});

	it("renders nothing for an empty list", () => {
		const w = mount(MissingSettingGroup, { props: { panels: [] } });
		expect(w.find('[data-testid="pln-missing-setting"]').exists()).toBe(false);
		expect(w.find('[data-testid="pln-missing-settings-group"]').exists()).toBe(false);
	});
});

describe("MissingSettingGroup — several panels at once", () => {
	it("collapses to a summary line naming the count, closed by default", () => {
		const w = mount(MissingSettingGroup, {
			props: {
				panels: [
					panel(),
					panel({ setting: "Applicable procurement schedule", affected_action: "Submit annual plan" }),
				],
			},
		});
		const group = w.find('[data-testid="pln-missing-settings-group"]');
		expect(group.exists()).toBe(true);
		expect(group.text()).toContain("2 settings need administrator attention");
		// <details> without `open` starts closed — the browser keeps its body
		// out of view until the Planner asks, which is the point of collapsing.
		expect(group.element.hasAttribute("open")).toBe(false);
		expect(w.findAll('[data-testid="pln-missing-setting"]')).toHaveLength(2);
	});

	it("opening it reveals every panel, each still its own", async () => {
		const w = mount(MissingSettingGroup, {
			props: {
				panels: [
					panel(),
					panel({ setting: "Applicable procurement schedule", affected_action: "Submit annual plan" }),
				],
			},
		});
		// jsdom does not run native <details> toggle behaviour on click, so the
		// open attribute is set directly, matching what a real click does.
		w.find('[data-testid="pln-missing-settings-group"]').element.open = true;
		await w.find('[data-testid="pln-missing-settings-group"]').trigger("toggle");
		const panels = w.findAll('[data-testid="pln-missing-setting"]');
		expect(panels).toHaveLength(2);
		expect(panels[0].text()).toContain("Applicable procurement method rule");
		expect(panels[1].text()).toContain("Applicable procurement schedule");
	});

	it("scales the same way at five", () => {
		const w = mount(MissingSettingGroup, {
			props: { panels: Array.from({ length: 5 }, (_, i) => panel({ affected_purchase: `Purchase ${i}` })) },
		});
		const group = w.find('[data-testid="pln-missing-settings-group"]');
		expect(group.text()).toContain("5 settings need administrator attention");
		expect(group.element.hasAttribute("open")).toBe(false);
		expect(w.findAll('[data-testid="pln-missing-setting"]')).toHaveLength(5);
	});
});
