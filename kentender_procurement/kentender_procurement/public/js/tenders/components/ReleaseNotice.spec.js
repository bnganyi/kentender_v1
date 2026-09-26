// TPR-CHG-001 v0.11 §10.15 bound-release notice on the Tender record.
import { describe, expect, it } from "vitest";
import { mount } from "@vue/test-utils";

import ReleaseNotice from "./ReleaseNotice.vue";

const WITHDRAWN = {
	state: "Withdrawn", tone: "is-critical", heading: "Tender format withdrawn",
	text: "This Tender cannot continue to publication because release 1.1 was withdrawn. Your work is preserved.",
	std_template_route: ["std-templates", "stdr-1"],
};

describe("ReleaseNotice", () => {
	it("shows the server's heading, text and tone, and View STD Template for a reader", async () => {
		const w = mount(ReleaseNotice, { props: { notice: WITHDRAWN } });
		const notice = w.find('[data-testid="tnd-template-notice"]');
		expect(notice.classes()).toContain("is-critical");
		expect(notice.text()).toContain("Tender format withdrawn");
		expect(notice.text()).toContain("Your work is preserved.");
		await w.find('[data-testid="tnd-template-notice-link"]').trigger("click");
		expect(w.emitted("navigate")[0][0]).toEqual(["std-templates", "stdr-1"]);
	});

	it("offers no link when the server sent no route", () => {
		const w = mount(ReleaseNotice, { props: { notice: { ...WITHDRAWN, std_template_route: [] } } });
		expect(w.find('[data-testid="tnd-template-notice-link"]').exists()).toBe(false);
	});
});
