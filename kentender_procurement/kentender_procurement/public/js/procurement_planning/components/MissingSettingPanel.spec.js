// PLN-CHG-001 v1.23 §10.16 — MissingSettingPanel component tests (C01–C04).
//
// Three labelled facts in every variant, the purchase where there is one, and
// exactly one of two endings: a working route for a maintainer, or the sentence
// naming who to ask. Never a disabled setup control.
import { describe, expect, it } from "vitest";
import { mount } from "@vue/test-utils";
import MissingSettingPanel from "./MissingSettingPanel.vue";

function panel(overrides = {}) {
	return {
		setting: "Annual Plan approval authority",
		affected_action: "Adopt and submit",
		affected_purchase: "",
		responsible_role: "Administrator or System Manager",
		note: "",
		can_open_setup: true,
		action: "Open System setup",
		href: "/app/system-setup#users-and-responsibilities",
		ask_text: "",
		...overrides,
	};
}

const make = (overrides) => mount(MissingSettingPanel, { props: { panel: panel(overrides) } });

describe("MissingSettingPanel — C01-ROUTE-MISSING", () => {
	it("names the setting, the blocked action and the responsible role", () => {
		const w = make();
		expect(w.find('[data-testid="pln-missing-setting-name"]').text()).toBe("Annual Plan approval authority");
		expect(w.find('[data-testid="pln-missing-setting-action"]').text()).toBe("Adopt and submit");
		expect(w.find('[data-testid="pln-missing-setting-role"]').text()).toBe("Administrator or System Manager");
		// No purchase for a plan-wide setting.
		expect(w.find('[data-testid="pln-missing-setting-purchase"]').exists()).toBe(false);
	});

	it("routes a maintainer to the exact setup section", () => {
		const w = make();
		const link = w.find('[data-testid="pln-open-setup"]');
		expect(link.text()).toBe("Open System setup");
		expect(link.attributes("href")).toBe("/app/system-setup#users-and-responsibilities");
		expect(link.attributes("disabled")).toBeUndefined();
		expect(w.find('[data-testid="pln-ask-administrator"]').exists()).toBe(false);
	});
});

describe("MissingSettingPanel — without setup access", () => {
	it("names who to ask instead of showing a control that cannot be used", () => {
		const w = make({ can_open_setup: false, action: "", href: "", ask_text: "Ask your KenTender administrator to complete this setting." });
		expect(w.find('[data-testid="pln-open-setup"]').exists()).toBe(false);
		expect(w.find('[data-testid="pln-ask-administrator"]').text()).toBe(
			"Ask your KenTender administrator to complete this setting.",
		);
		// Every fact stays, only the control changes.
		expect(w.find('[data-testid="pln-missing-setting-name"]').text()).toBe("Annual Plan approval authority");
	});
});

describe("MissingSettingPanel — C02-DPP-CLOSED", () => {
	it("says what remains permitted", () => {
		const w = make({
			setting: "Departmental plan submissions",
			affected_action: "Submit initial departmental plan",
			note: "Saving a draft and correcting a returned submission are unaffected.",
			href: "/app/system-setup#fiscal-years",
		});
		expect(w.find('[data-testid="pln-missing-setting-note"]').text()).toBe(
			"Saving a draft and correcting a returned submission are unaffected.",
		);
		expect(w.find('[data-testid="pln-open-setup"]').attributes("href")).toBe("/app/system-setup#fiscal-years");
	});
});

describe("MissingSettingPanel — C03 / C04", () => {
	it("names the purchase the rule is missing for", () => {
		const method = make({
			setting: "Applicable procurement method rule",
			affected_action: "Send plan for governance review",
			affected_purchase: "Clinical training and deployment laptops for digital health rollout · PPI-MOH-2027-033",
			href: "/app/system-setup#procurement-settings",
		});
		expect(method.find('[data-testid="pln-missing-setting-purchase"]').text()).toContain("PPI-MOH-2027-033");

		const schedule = make({
			setting: "Applicable procurement schedule",
			affected_action: "Submit annual plan",
			affected_purchase: "National digital health infrastructure upgrade · PPI-MOH-2027-021",
			href: "/app/system-setup#procurement-settings",
		});
		expect(schedule.find('[data-testid="pln-missing-setting-action"]').text()).toBe("Submit annual plan");
		expect(schedule.find('[data-testid="pln-missing-setting-purchase"]').text()).toContain("PPI-MOH-2027-021");
	});
});
