// ANL §10A.7 — "Tender invitation timing": 25 / 7 / 7 / 0 / -3 days and one row with no date recorded.
import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";
import FromZeroBars from "./FromZeroBars.vue";
import { INVITATION_TIMING } from "./fixtures.js";

const timing = (props = {}) =>
	mount(FromZeroBars, {
		props: { rows: INVITATION_TIMING, halfRange: 30, earlierLabel: "Earlier", laterLabel: "Later", caption: "Actual invitation date compared with the date approved in the Active Plan.", title: "Tender invitation timing", ...props },
	});
const tracks = (wrapper) => wrapper.findAll(".kt-anl-fromzero-track");

describe("FromZeroBars", () => {
	it("draws later bars to the right of the zero line and earlier bars to the left", () => {
		const bars = tracks(timing()).map((track) => {
			const bar = track.find(".kt-anl-fromzero-bar");
			return bar.exists() ? [bar.classes().includes("is-later") ? "later" : "earlier", bar.element.style.width] : null;
		});
		expect(bars).toEqual([
			["later", "41.67%"],
			["later", "11.67%"],
			["later", "11.67%"],
			["later", "0.6%"],
			["earlier", "5%"],
			null,
		]);
	});

	it("draws no bar for 'No date recorded' and mutes its text", () => {
		const wrapper = timing();
		const last = tracks(wrapper)[5];
		expect(last.find(".kt-anl-fromzero-bar").exists()).toBe(false);
		expect(last.find(".kt-anl-fromzero-zero").exists()).toBe(true);
		const values = wrapper.findAll(".kt-anl-fromzero-value");
		expect(values[5].text()).toBe("No date recorded");
		expect(values[5].classes()).toContain("is-none");
	});

	it("writes a value label on every row, including the one on the approved date", () => {
		expect(timing().findAll(".kt-anl-fromzero-value").map((n) => n.text())).toEqual([
			"25 days after approved date",
			"7 days after approved date",
			"7 days after approved date",
			"On the approved date",
			"3 days before approved date",
			"No date recorded",
		]);
	});

	it("keeps the rows in the order given and states the earlier/later ends and the caption", () => {
		const wrapper = timing();
		expect(wrapper.findAll(".kt-anl-fromzero-label").map((n) => n.text())).toEqual(["Network switches", "Office desks", "Servers", "Monitors", "Printers", "IT peripherals"]);
		expect(wrapper.findAll(".kt-anl-fromzero-ends > span").map((n) => n.text())).toEqual(["Earlier", "Later"]);
		expect(wrapper.get(".kt-anl-caption").text()).toBe("Actual invitation date compared with the date approved in the Active Plan.");
	});

	it("never lets a bar pass the edge of the track", () => {
		const wrapper = timing({ rows: [{ key: "x", label: "X", value: 400, text: "400 days after approved date" }] });
		expect(tracks(wrapper)[0].get(".kt-anl-fromzero-bar").element.style.width).toBe("50%");
	});

	it("exposes the same rows as a hidden table", () => {
		const table = timing().get("table.sr-only");
		expect(table.get("caption").text()).toBe("Tender invitation timing");
		expect(table.findAll("tbody tr").map((tr) => tr.findAll("th,td").map((n) => n.text()))).toEqual([
			["Network switches", "25 days after approved date"],
			["Office desks", "7 days after approved date"],
			["Servers", "7 days after approved date"],
			["Monitors", "On the approved date"],
			["Printers", "3 days before approved date"],
			["IT peripherals", "No date recorded"],
		]);
	});
});
