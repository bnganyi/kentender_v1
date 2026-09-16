// CFG-CHG-002 v0.11 §10.3/§11.3 (C02 "forms") / CFG11-CHG-004 — one focused
// open/close/deadline form, its title and consequence copy composed from a
// shared activity-label vocabulary across all three intake purposes.
import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";
import IntakeDialog from "./IntakeDialog.vue";
import { globalMocks } from "./spec_helpers.js";
import { CFG_VERSION_CONFLICT_MESSAGE } from "../data/format.js";

const row = { fiscal_year: "2027-2028", label: "FY 2027/28", expected_version: "x" };

function mountDialog(props) {
	return mount(IntakeDialog, { props: { row, ...props }, global: globalMocks() });
}

describe("IntakeDialog", () => {
	it("open mode shows the close instant, its help text and no destructive styling", () => {
		const wrapper = mountDialog({ mode: "open" });
		expect(wrapper.find(".kt-dialog-title").text()).toBe("Open departmental needs submissions");
		expect(wrapper.find('[data-testid="kt-fy-intake-closes"]').exists()).toBe(true);
		expect(wrapper.text()).toContain("Leave blank to keep submissions open until you close them.");
		expect(wrapper.find('[data-testid="kt-fy-intake-confirm"]').classes()).not.toContain("kt-danger");
		expect(wrapper.find('[data-testid="kt-fy-intake-confirm"]').text()).toBe("Open submissions");
	});

	it("the replacement notice appears only when another year is open, naming it and what stays untouched", () => {
		const without = mountDialog({ mode: "open" });
		expect(without.find('[data-testid="kt-fy-intake-replaces"]').exists()).toBe(false);

		const withReplace = mountDialog({
			mode: "open",
			replaces: { fiscal_year: "2026-2027", label: "FY 2026/27" },
		});
		const notice = withReplace.find('[data-testid="kt-fy-intake-replaces"]');
		expect(notice.exists()).toBe(true);
		expect(notice.text()).toContain("This will close FY 2026/27");
		expect(notice.text()).toContain(
			"This will close departmental needs submissions for FY 2026/27. Departmental plan and Disposal plan submissions will stay as they are."
		);
	});

	it("close mode is destructive, asks for a reason, omits the close instant and names what remains available", () => {
		const wrapper = mountDialog({ mode: "close" });
		expect(wrapper.find(".kt-dialog-title").text()).toBe("Close departmental needs submissions");
		expect(wrapper.find('[data-testid="kt-fy-intake-closes"]').exists()).toBe(false);
		expect(wrapper.text()).toContain("Existing needs remain available under the Departmental Needs rules.");
		expect(wrapper.find('[data-testid="kt-fy-intake-confirm"]').classes()).toContain("kt-danger");
		expect(wrapper.find('[data-testid="kt-fy-intake-confirm"]').text()).toBe("Close submissions");
	});

	it("deadline mode shows the year and activity, prefills the current instant and saves in place", () => {
		const wrapper = mountDialog({
			mode: "deadline",
			purpose: "plan",
			row: { ...row, closes_at_local: "2026-11-30T23:59" },
		});
		expect(wrapper.find(".kt-dialog-title").text()).toBe("Change closing time");
		expect(wrapper.text()).toContain("Departmental plan");
		expect(wrapper.find('[data-testid="kt-fy-intake-closes"]').element.value).toBe("2026-11-30T23:59");
		expect(wrapper.find('[data-testid="kt-fy-intake-confirm"]').text()).toBe("Save closing time");
		expect(wrapper.find('[data-testid="kt-fy-intake-confirm"]').classes()).not.toContain("kt-danger");
	});

	it("the plan and disposal-plan purposes carry their own composed copy and the same controls", () => {
		const plan = mountDialog({ mode: "close", purpose: "plan" });
		expect(plan.find('[data-testid="kt-fy-intake"]').attributes("data-purpose")).toBe("plan");
		expect(plan.find(".kt-dialog-title").text()).toBe("Close departmental plan submissions");
		expect(plan.text()).toContain("Existing submissions and permitted updates remain available.");

		const disposal = mountDialog({ mode: "open", purpose: "disposal_plan" });
		expect(disposal.find(".kt-dialog-title").text()).toBe("Open disposal plan submissions");
	});

	it("confirm emits the trimmed reason, and a close instant only outside close mode", async () => {
		const wrapper = mountDialog({ mode: "close" });
		await wrapper.find('[data-testid="kt-fy-intake-reason"]').setValue("  Needs call closed.  ");
		await wrapper.find('[data-testid="kt-fy-intake-confirm"]').trigger("click");
		expect(wrapper.emitted("confirm")[0][0]).toEqual({ closes_at: "", reason: "Needs call closed." });
	});

	it("a stale control token shows the recoverable notice instead of the generic error, and Review latest settings emits refresh", async () => {
		const wrapper = mountDialog({ mode: "close", error: CFG_VERSION_CONFLICT_MESSAGE });
		const stale = wrapper.find('[data-testid="kt-fy-intake-stale"]');
		expect(stale.exists()).toBe(true);
		expect(stale.text()).toContain("These submission settings have changed since you opened them.");
		expect(wrapper.find(".kt-inline-error").exists()).toBe(false);
		await stale.find("a").trigger("click");
		expect(wrapper.emitted("refresh")).toBeTruthy();
	});

	it("a non-stale error shows the generic inline error, not the stale notice", () => {
		const wrapper = mountDialog({ mode: "close", error: "Something else went wrong." });
		expect(wrapper.find('[data-testid="kt-fy-intake-stale"]').exists()).toBe(false);
		expect(wrapper.find(".kt-inline-error").text()).toBe("Something else went wrong.");
	});
});
