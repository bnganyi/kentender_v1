// The shared access state: what every module's "You do not have access to ..." screen is built from.
import { describe, expect, it } from "vitest";
import { mount } from "@vue/test-utils";
import AccessDenied from "./AccessDenied.vue";

describe("AccessDenied", () => {
	it("draws the pack's access state: lock spot, heading, then the reason", () => {
		const w = mount(AccessDenied, { props: { heading: "You do not have access to Budget & Funding", text: ["This area needs a Budget Officer."] } });
		expect(w.classes()).toEqual(expect.arrayContaining(["kt-empty", "kt-access"]));
		expect(w.attributes("role")).toBe("alert");
		expect(w.find(".kt-spot.is-neutral .kt-icon").exists()).toBe(true);
		expect(w.get("h2").text()).toBe("You do not have access to Budget & Funding");
		expect(w.findAll("p").map((p) => p.text())).toEqual(["This area needs a Budget Officer."]);
	});

	it("reads a heading written with a full stop the same as one without", () => {
		expect(mount(AccessDenied, { props: { heading: "You do not have access to Tenders." } }).get("h2").text()).toBe("You do not have access to Tenders");
	});

	it("puts the administrator hint in its own paragraph even when a source runs it on", () => {
		const w = mount(AccessDenied, { props: { heading: "h", text: "This area needs one of these responsibilities: A or B. Ask your KenTender administrator to assign one in System setup." } });
		expect(w.findAll("p").map((p) => p.text())).toEqual([
			"This area needs one of these responsibilities: A or B.",
			"Ask your KenTender administrator to assign one in System setup.",
		]);
	});

	it("drops empty text and offers an action only when one is named", async () => {
		const bare = mount(AccessDenied, { props: { heading: "h", text: ["", "  "] } });
		expect(bare.findAll("p")).toHaveLength(0);
		expect(bare.find("button").exists()).toBe(false);
		const withAction = mount(AccessDenied, { props: { heading: "h", actionLabel: "Back to Home" } });
		await withAction.get("button").trigger("click");
		expect(withAction.emitted("action")).toHaveLength(1);
	});
});
