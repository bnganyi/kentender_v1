// PLN-CHG-001 v1.18 §7.2 — LateExplanationHistory component tests
// (U21-late-explanation-history). Read-only, newest first, no date editor.
import { describe, expect, it } from "vitest";
import { mount } from "@vue/test-utils";
import LateExplanationHistory from "./LateExplanationHistory.vue";

const FACTS = { initialVersion: 1, financialYearStarted: "1 Jul 2027", activatedAt: "2 Jul 2027, 09:00 EAT" };

describe("LateExplanationHistory", () => {
	it("renders a single explanation with no Superseded badge", () => {
		const wrapper = mount(LateExplanationHistory, {
			props: {
				...FACTS,
				entries: [{ name: "e1", reason: "Late acknowledgement.", actor: "Amina Hassan", recordedAt: "2 Jul 2027, 09:05 EAT" }],
			},
		});
		expect(wrapper.text()).toContain("Late acknowledgement.");
		expect(wrapper.text()).toContain("Amina Hassan");
		expect(wrapper.find('[data-testid="pln-late-explanation-superseded"]').exists()).toBe(false);
		expect(wrapper.get(".pln-fact-val").text()).toBe("1");
	});

	it("shows the most recent entry first and marks earlier ones Superseded", () => {
		const wrapper = mount(LateExplanationHistory, {
			props: {
				...FACTS,
				entries: [
					{ name: "e1", reason: "First reason.", actor: "Amina Hassan", recordedAt: "2 Jul 2027, 09:05 EAT" },
					{ name: "e2", reason: "Corrected reason.", actor: "Amina Hassan", recordedAt: "3 Jul 2027, 10:00 EAT" },
				],
			},
		});
		const cards = wrapper.findAll('[data-testid="pln-late-explanation-history"] > *');
		expect(cards[0].text()).toContain("Corrected reason.");
		expect(cards[1].text()).toContain("First reason.");
		expect(cards[1].find('[data-testid="pln-late-explanation-superseded"]').exists()).toBe(true);
		expect(cards[0].find('[data-testid="pln-late-explanation-superseded"]').exists()).toBe(false);
	});

	it("has no input or textarea anywhere — no retroactive date editor", () => {
		const wrapper = mount(LateExplanationHistory, {
			props: { ...FACTS, entries: [{ name: "e1", reason: "x", actor: "y", recordedAt: "z" }] },
		});
		expect(wrapper.find("input").exists()).toBe(false);
		expect(wrapper.find("textarea").exists()).toBe(false);
		expect(wrapper.find("button").exists()).toBe(false);
	});
});
