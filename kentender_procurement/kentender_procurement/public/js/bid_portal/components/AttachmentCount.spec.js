// The evidence column's summary: how many files a row holds, as a paperclip and
// a number, with the names only in a hover; a refused file reads as Rejected;
// nothing is a dash. A very long name can never reach the table's layout.
import { describe, expect, it } from "vitest";
import { mount } from "@vue/test-utils";

import AttachmentCount from "./AttachmentCount.vue";

const render = (props) => mount(AttachmentCount, { props, global: { config: { globalProperties: { __: (s, args = []) => s.replace(/\{(\d+)\}/g, (_, i) => args[i]) } } } });

describe("AttachmentCount", () => {
	it("is a dash when the row holds no file", () => {
		const wrapper = render({ count: 0, names: [] });
		expect(wrapper.text()).toBe("—");
		expect(wrapper.find('[data-testid="bds-attachments"]').exists()).toBe(false);
	});
	it("shows a paperclip and the count, and keeps the names out of the text", () => {
		const long = `${"x".repeat(200)}.pdf`;
		const wrapper = render({ count: 2, names: ["datasheet.pdf", long] });
		const chip = wrapper.get('[data-testid="bds-attachments"]');
		expect(chip.find("svg").exists()).toBe(true);
		expect(chip.get(".bds-attachment-count").text()).toBe("2");
		expect(chip.attributes("aria-label")).toBe("2 files attached"); // the meaning is in the label; the cell holds only the icon and the number
		expect(chip.text()).toBe("2");
		expect(chip.attributes("title")).toBe(`datasheet.pdf, ${long}`);
		expect(wrapper.text()).not.toContain("datasheet.pdf");
	});
	it("says a single file in the singular", () => {
		expect(render({ count: 1, names: ["a.pdf"] }).get('[data-testid="bds-attachments"]').attributes("aria-label")).toBe("1 file attached");
	});
	it("reads a refused file as Rejected, beside the count when the row holds others", () => {
		const both = render({ count: 1, names: ["a.pdf"], rejected: true });
		expect([both.find('[data-testid="bds-attachments"]').exists(), both.get(".kt-status").text()]).toEqual([true, "Rejected"]);
	});
	it("reads a row with only a refused file as Rejected", () => {
		const wrapper = render({ count: 0, names: [], rejected: true });
		expect(wrapper.get(".kt-status").text()).toBe("Rejected");
	});
});
