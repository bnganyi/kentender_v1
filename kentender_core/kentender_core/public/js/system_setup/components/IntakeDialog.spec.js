// AUTH §18.2 item 22/24 — the open/close intake dialog variants (CFG-DES-05/06).
import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";
import IntakeDialog from "./IntakeDialog.vue";
import { globalMocks } from "./spec_helpers.js";

const row = { fiscal_year: "2027-2028", label: "FY 2027/28", expected_version: "x" };

function mountDialog(props) {
	return mount(IntakeDialog, { props: { row, ...props }, global: globalMocks() });
}

describe("IntakeDialog", () => {
	it("open mode shows the close instant, its help text and no destructive styling", () => {
		const wrapper = mountDialog({ mode: "open" });
		expect(wrapper.find('[data-testid="kt-fy-intake-closes"]').exists()).toBe(true);
		expect(wrapper.text()).toContain("Leave blank to keep submission open until you close it.");
		expect(wrapper.text()).toContain("Departments will be able to create and submit needs for FY 2027/28.");
		expect(wrapper.find('[data-testid="kt-fy-intake-confirm"]').classes()).not.toContain("kt-danger");
	});

	it("the replacement notice appears only when another year is open, naming it", () => {
		const without = mountDialog({ mode: "open" });
		expect(without.find('[data-testid="kt-fy-intake-replaces"]').exists()).toBe(false);

		const withReplace = mountDialog({
			mode: "open",
			replaces: { fiscal_year: "2026-2027", label: "FY 2026/27" },
		});
		const notice = withReplace.find('[data-testid="kt-fy-intake-replaces"]');
		expect(notice.exists()).toBe(true);
		expect(notice.text()).toContain("This will close FY 2026/27");
	});

	it("close mode is destructive, asks for a reason and omits the close instant", () => {
		const wrapper = mountDialog({ mode: "close" });
		expect(wrapper.find('[data-testid="kt-fy-intake-closes"]').exists()).toBe(false);
		expect(wrapper.text()).toContain("Needs already submitted or accepted are unaffected.");
		expect(wrapper.find('[data-testid="kt-fy-intake-confirm"]').classes()).toContain("kt-danger");
	});

	it("confirm emits the trimmed reason, and a close instant only in open mode", async () => {
		const wrapper = mountDialog({ mode: "close" });
		await wrapper.find('[data-testid="kt-fy-intake-reason"]').setValue("  Needs call closed.  ");
		await wrapper.find('[data-testid="kt-fy-intake-confirm"]').trigger("click");
		expect(wrapper.emitted("confirm")[0][0]).toEqual({ closes_at: "", reason: "Needs call closed." });
	});
});
