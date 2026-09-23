// NDS-DES-14-MASKED-DETAIL/LOAD-FAILURE/AUTHORITY-CHANGED — literal copy this
// shared component renders, ported class-for-class from NDS Artboards.dc.html.
// The design-fidelity gate's landmark check only sees the heading (an
// unclassed div, not a structural landmark) via a direct text assertion in
// the browser layer; this is the one place the literal string itself is
// pinned so a silent wording drift cannot ship unnoticed.
import { describe, expect, it } from "vitest";
import { mount } from "@vue/test-utils";
import PageNotice from "./PageNotice.vue";

describe("PageNotice — NDS-DES-14-MASKED-DETAIL", () => {
	it("names the record and offers Back to Departmental Needs, no body paragraph", () => {
		const w = mount(PageNotice, {
			props: { heading: "This requirement is not available to you.", actionLabel: "Back to Departmental Needs" },
		});
		expect(w.get('[data-testid="nds-page-notice-heading"]').text()).toBe(
			"This requirement is not available to you.",
		);
		expect(w.get('[data-testid="nds-page-notice-action"]').text()).toBe("Back to Departmental Needs");
		expect(w.find("p").exists()).toBe(false);
	});
});

describe("PageNotice — NDS-DES-14-AUTHORITY-CHANGED", () => {
	it("says permission was withdrawn, not that the record is unavailable", () => {
		const w = mount(PageNotice, {
			props: {
				heading: "You no longer have permission to perform this action.",
				actionLabel: "Back to Departmental Needs",
			},
		});
		expect(w.get('[data-testid="nds-page-notice-heading"]').text()).toBe(
			"You no longer have permission to perform this action.",
		);
		expect(w.get('[data-testid="nds-page-notice-action"]').text()).toBe("Back to Departmental Needs");
	});
});

describe("PageNotice — NDS-DES-14-LOAD-FAILURE (non-workspace routes)", () => {
	it("names the retry action and the exact instruction paragraph", () => {
		const w = mount(PageNotice, {
			props: {
				heading: "Departmental Needs could not be loaded.",
				body: "Try again. If the problem continues, contact support.",
				actionLabel: "Try again",
			},
		});
		expect(w.get('[data-testid="nds-page-notice-heading"]').text()).toBe(
			"Departmental Needs could not be loaded.",
		);
		expect(w.find("p").text()).toBe("Try again. If the problem continues, contact support.");
		expect(w.get('[data-testid="nds-page-notice-action"]').text()).toBe("Try again");
	});

	it("emits `action` when the button is clicked, never navigates on its own", async () => {
		const w = mount(PageNotice, {
			props: { heading: "Departmental Needs could not be loaded.", actionLabel: "Try again" },
		});
		await w.get('[data-testid="nds-page-notice-action"]').trigger("click");
		expect(w.emitted("action")).toHaveLength(1);
	});

	it("renders no action button when none is given", () => {
		const w = mount(PageNotice, { props: { heading: "Departmental Needs could not be loaded." } });
		expect(w.find('[data-testid="nds-page-notice-action"]').exists()).toBe(false);
	});
});
