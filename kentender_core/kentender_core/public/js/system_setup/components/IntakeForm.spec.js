// CFG-CHG-002 v0.14 §10.4 (C02 #forms, #form-states; tracker CFG14-5B) —
// the focused open/close/deadline form, inline in the year detail (D18), with
// the spec's exact copy and the board's three form-state notices.
import { flushPromises, mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";
import IntakeForm from "./IntakeForm.vue";
import { globalMocks } from "./spec_helpers.js";
import { CFG_VERSION_CONFLICT_MESSAGE } from "../data/format.js";

const row = { fiscal_year: "2027-2028", label: "FY 2027/28", expected_version: "x" };

function mountForm(props) {
	return mount(IntakeForm, { props: { row, ...props }, global: globalMocks(), attachTo: document.body });
}

describe("IntakeForm", () => {
	it("open: the spec's title, a Year fact, the EAT closing time with its helper, a reason, and Open submissions", async () => {
		const wrapper = mountForm({ mode: "open" });
		await flushPromises();
		expect(wrapper.classes()).toContain("card");
		expect(wrapper.find(".kt-intake-title").text()).toBe("Open departmental needs submissions");
		expect(wrapper.find(".kt-meta-row").text()).toBe("YearFY 2027/28");
		expect(wrapper.find('label[for="kt-intake-closes"]').text()).toBe("Close automatically on (EAT)");
		expect(wrapper.text()).toContain("Leave the closing date blank to keep submissions open until you close them.");
		expect(wrapper.find('[data-testid="kt-fy-intake-confirm"]').text()).toBe("Open submissions");
		// Not a modal, and it takes focus on its first field.
		expect(wrapper.find(".dialog").exists()).toBe(false);
		expect(document.activeElement?.getAttribute("data-testid")).toBe("kt-fy-intake-closes");
		wrapper.unmount();
	});

	it("CONFIG-SWAP: opening departmental plans names the year it closes and what stays as it is (§10.4 exact copy)", () => {
		const wrapper = mountForm({ mode: "open", purpose: "plan", replaces: { fiscal_year: "2026-2027", label: "FY 2026/27" } });
		const notice = wrapper.find('[data-testid="kt-fy-intake-replaces"]');
		expect(notice.classes()).toEqual(expect.arrayContaining(["kt-notice", "is-warning"]));
		expect(notice.find(".kt-notice-icon").exists()).toBe(true);
		expect(notice.text()).toBe(
			"This will close departmental plan submissions for FY 2026/27. Departmental needs and disposal plan submissions will stay as they are."
		);
		wrapper.unmount();
	});

	it("close: no deadline input, the activity's own remaining-records sentence, and a plain primary Close submissions", () => {
		for (const [purpose, note] of [
			["needs", "Existing needs remain available under the Departmental Needs rules."],
			["plan", "Existing submissions and permitted updates remain available."],
			["disposal_plan", "Existing records remain available under the Disposal rules."],
		]) {
			const wrapper = mountForm({ mode: "close", purpose });
			expect(wrapper.find('[data-testid="kt-fy-intake-closes"]').exists()).toBe(false);
			expect(wrapper.find('[data-testid="kt-fy-intake-close-note"]').text()).toBe(note);
			const confirm = wrapper.find('[data-testid="kt-fy-intake-confirm"]');
			expect(confirm.text()).toBe("Close submissions");
			expect(confirm.classes()).not.toContain("kt-danger");
			wrapper.unmount();
		}
	});

	it("deadline: Change closing time with Year and Activity facts, prefilled, and Save closing time", () => {
		const wrapper = mountForm({ mode: "deadline", purpose: "plan", row: { ...row, closes_at_local: "2026-11-30T23:59" } });
		expect(wrapper.find(".kt-intake-title").text()).toBe("Change closing time");
		expect(wrapper.find(".kt-meta-row").text()).toBe("YearFY 2027/28ActivityDepartmental plan");
		expect(wrapper.find('[data-testid="kt-fy-intake-closes"]').element.value).toBe("2026-11-30T23:59");
		expect(wrapper.find('[data-testid="kt-fy-intake-confirm"]').text()).toBe("Save closing time");
		wrapper.unmount();
	});

	it("the three form states are their own notices with the board's icons; a stale form offers Review latest settings", async () => {
		const deadline = mountForm({ mode: "open", error: "Enter a closing time later than the current time." });
		expect(deadline.find('[data-testid="kt-fy-intake-deadline-error"]').text()).toBe("Deadline error. Enter a closing time later than the current time.");
		expect(deadline.find('[data-testid="kt-fy-intake-closes"]').attributes("aria-invalid")).toBe("true");
		deadline.unmount();

		const expired = mountForm({ mode: "deadline", error: "Departmental needs submissions closed at 25 Nov 2026, 23:59 EAT." });
		expect(expired.find('[data-testid="kt-fy-intake-expired"]').text()).toBe("Expired. Departmental needs submissions closed at 25 Nov 2026, 23:59 EAT.");
		expired.unmount();

		const stale = mountForm({ mode: "open", error: CFG_VERSION_CONFLICT_MESSAGE });
		const notice = stale.find('[data-testid="kt-fy-intake-stale"]');
		expect(notice.text()).toContain("Stale. These submission settings have changed since you opened them.");
		expect(notice.find(".kt-notice-icon").exists()).toBe(true);
		await stale.find('[data-testid="kt-fy-intake-review"]').trigger("click");
		expect(stale.emitted("refresh")).toBeTruthy();
		stale.unmount();
	});

	it("sends the entered closing time and reason; Escape cancels", async () => {
		const wrapper = mountForm({ mode: "open" });
		await wrapper.find('[data-testid="kt-fy-intake-closes"]').setValue("2026-11-25T23:59");
		await wrapper.find('[data-testid="kt-fy-intake-reason"]').setValue("  Annual needs call.  ");
		await wrapper.find('[data-testid="kt-fy-intake-confirm"]').trigger("click");
		expect(wrapper.emitted("confirm")[0]).toEqual([{ closes_at: "2026-11-25T23:59", reason: "Annual needs call." }]);
		await wrapper.trigger("keydown", { key: "Escape" });
		expect(wrapper.emitted("cancel")).toBeTruthy();
		wrapper.unmount();
	});
});
