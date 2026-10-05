// The icon component draws the board's own artwork; an area key resolves to that area's icon (ANL §10A.1 rule 7).
import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";
import AnalyticsIcon from "./AnalyticsIcon.vue";
import { ANALYTICS_AREA_ICONS, ANALYTICS_ICONS } from "../analytics_icons.js";

describe("AnalyticsIcon", () => {
	it("draws a named icon on the 24 grid, hidden from assistive technology", () => {
		const svg = mount(AnalyticsIcon, { props: { name: "clock" } }).get("svg");
		expect(svg.classes()).toContain("kt-icon");
		expect(svg.attributes("viewBox")).toBe("0 0 24 24");
		expect(svg.attributes("aria-hidden")).toBe("true");
		expect(svg.html()).toContain("M12 6v6l4 2");
	});

	it("resolves each of the five area keys to a distinct icon", () => {
		const areas = ["needs", "departmental_planning", "annual_planning", "requisitions", "tender_proceedings"];
		expect(Object.keys(ANALYTICS_AREA_ICONS)).toEqual(areas);
		const markups = areas.map((area) => mount(AnalyticsIcon, { props: { name: area } }).get("svg").html());
		expect(new Set(markups).size).toBe(5);
		for (const area of areas) expect(ANALYTICS_ICONS[ANALYTICS_AREA_ICONS[area]]).toBeTruthy();
	});

	it("takes a size class", () => {
		expect(mount(AnalyticsIcon, { props: { name: "info", size: "sm" } }).get("svg").classes()).toContain("is-sm");
	});
});
