// CFG-CHG-002 v0.14 §9 — System setup's links: `#<tab>`, then within
// Procurement settings `#procurement-settings/{section}/{id}` with optional
// `/versions/{version_id}`, working-day calendars at `/calendars/{id}`, and
// Financial years' year detail at `#fiscal-years/{fy}`.
import { describe, expect, it } from "vitest";
import { buildSetupHash, legacyToRoute, parseSetupHash, routeToLegacy } from "./routes.js";

describe("parseSetupHash", () => {
	it.each([
		["", { tab: "", section: "", id: "", versionId: "", action: "" }],
		["fiscal-years", { tab: "fiscal-years", section: "", id: "", versionId: "", action: "" }],
		["fiscal-years/2027-2028", { tab: "fiscal-years", section: "", id: "2027-2028", versionId: "", action: "" }],
		["organisation-structure/OU-MOH-DHP", { tab: "organisation-structure", section: "", id: "OU-MOH-DHP", versionId: "", action: "" }],
		["users-and-responsibilities/URA-2026-0003", { tab: "users-and-responsibilities", section: "", id: "URA-2026-0003", versionId: "", action: "" }],
		["procurement-settings", { tab: "procurement-settings", section: "", id: "", versionId: "", action: "" }],
		["procurement-settings/procurement-rules", { tab: "procurement-settings", section: "procurement-rules", id: "", versionId: "", action: "" }],
		["procurement-settings/funding-sources/new", { tab: "procurement-settings", section: "funding-sources", id: "", versionId: "", action: "new" }],
		["procurement-settings/procurement-rules/RR-1", { tab: "procurement-settings", section: "procurement-rules", id: "RR-1", versionId: "", action: "" }],
		["procurement-settings/procurement-rules/RR-1/versions/RR-1-V2", { tab: "procurement-settings", section: "procurement-rules", id: "RR-1", versionId: "RR-1-V2", action: "" }],
		["procurement-settings/procurement-rules/RR-1/new-version", { tab: "procurement-settings", section: "procurement-rules", id: "RR-1", versionId: "", action: "new-version" }],
		["procurement-settings/procurement-rules/RR-1/check-sources", { tab: "procurement-settings", section: "procurement-rules", id: "RR-1", versionId: "", action: "check-sources" }],
		["procurement-settings/calendars/Kenya%20public%20holidays", { tab: "procurement-settings", section: "calendars", id: "Kenya public holidays", versionId: "", action: "" }],
	])("%s", (hash, expected) => {
		expect(parseSetupHash(hash)).toEqual(expected);
		expect(parseSetupHash(`#${hash}`)).toEqual(expected);
	});

	it("decodes each segment on its own, so an id containing an encoded slash stays one id", () => {
		expect(parseSetupHash("procurement-settings/funding-sources/A%2FB").id).toBe("A/B");
	});

	it("drops an unknown tab or section rather than guessing", () => {
		expect(parseSetupHash("nonsense/x").tab).toBe("");
		expect(parseSetupHash("procurement-settings/nonsense/x")).toMatchObject({ tab: "procurement-settings", section: "", id: "" });
	});

	it("opens the tab itself for a v0.11 address, never a screen from its old sub-path", () => {
		for (const old of ["rule/RR-1", "new-rule-version/RR-1", "edit-method-rule/MPR-1", "profile/SP-1", "source/FS-1", "calendar/C-1", "check-sources/RR-1-V2"]) {
			expect(parseSetupHash(`procurement-settings/${old}`)).toEqual({ tab: "procurement-settings", section: "", id: "", versionId: "", action: "" });
		}
	});

	it("keeps a malformed escape as typed instead of throwing", () => {
		expect(parseSetupHash("procurement-settings/funding-sources/%E0%A4%A").id).toBe("%E0%A4%A");
	});
});

describe("buildSetupHash", () => {
	it("round-trips every parseable shape, encoding ids", () => {
		for (const hash of [
			"fiscal-years",
			"fiscal-years/2027-2028",
			"organisation-structure/OU-MOH-DHP",
			"users-and-responsibilities/URA-2026-0003",
			"procurement-settings/procurement-rules",
			"procurement-settings/funding-sources/new",
			"procurement-settings/procurement-rules/RR-1/versions/RR-1-V2",
			"procurement-settings/schedule-profiles/SP-1/edit",
			"procurement-settings/calendars/Kenya%20public%20holidays",
		]) {
			expect(buildSetupHash(parseSetupHash(hash))).toBe(hash);
		}
	});
});

describe("the current tabs' internal views ⇄ §9 links (until Phase 5 re-ports them)", () => {
	const isMethod = (id) => id.startsWith("MPR-");
	it.each([
		["procurement-settings", "", ""],
		["procurement-settings", "new-source", "procurement-settings/funding-sources/new"],
		["procurement-settings", "source/Government of Kenya", "procurement-settings/funding-sources/Government%20of%20Kenya"],
		["procurement-settings", "new-rule", "procurement-settings/procurement-rules/new"],
		["procurement-settings", "rule/RR-1", "procurement-settings/procurement-rules/RR-1"],
		["procurement-settings", "new-rule-version/RR-1", "procurement-settings/procurement-rules/RR-1/new-version"],
		["procurement-settings", "edit-rule-version/RR-1", "procurement-settings/procurement-rules/RR-1/edit"],
		["procurement-settings", "new-method-version/MPR-1", "procurement-settings/procurement-rules/MPR-1/new-version"],
		["procurement-settings", "edit-method-rule/MPR-1", "procurement-settings/procurement-rules/MPR-1/edit"],
		["procurement-settings", "check-sources/RR-1", "procurement-settings/procurement-rules/RR-1/check-sources"],
		["procurement-settings", "profile/SP-1", "procurement-settings/schedule-profiles/SP-1"],
		["procurement-settings", "new-schedule-version/SP-1", "procurement-settings/schedule-profiles/SP-1/new-version"],
		["procurement-settings", "edit-schedule/SP-1", "procurement-settings/schedule-profiles/SP-1/edit"],
		["procurement-settings", "calendar/CAL-1", "procurement-settings/calendars/CAL-1"],
		["procurement-settings", "new-calendar", "procurement-settings/calendars/new"],
		["procurement-settings", "new-schedule", "procurement-settings/schedule-profiles/new"],
		// C04 — the calendar's board views each have their own link.
		["procurement-settings", "calendar-new-version/CAL-1", "procurement-settings/calendars/CAL-1/new-version"],
		["procurement-settings", "calendar-edit/CAL-1", "procurement-settings/calendars/CAL-1/edit"],
		["procurement-settings", "calendar-check-sources/CAL-1", "procurement-settings/calendars/CAL-1/check-sources"],
		["procurement-settings", "calendar-history/CAL-1", "procurement-settings/calendars/CAL-1/history"],
		["fiscal-years", "year/2027-2028", "fiscal-years/2027-2028"],
	])("%s: %s ⇄ %s", (tab, legacy, hash) => {
		const route = legacyToRoute(tab, legacy);
		expect(buildSetupHash(route)).toBe(hash || tab);
		expect(routeToLegacy(parseSetupHash(hash || tab), { isMethodRule: isMethod })).toBe(legacy);
	});

	it("a section on its own opens the list (the section is scrolled to, not a separate view)", () => {
		expect(routeToLegacy(parseSetupHash("procurement-settings/procurement-rules"))).toBe("");
	});

	it("a rule version link opens that exact version", () => {
		expect(routeToLegacy(parseSetupHash("procurement-settings/procurement-rules/RR-1/versions/RR-1-V2"))).toBe("rule/RR-1-V2");
	});

	it("a bare section name opens the list at that section (Procuring entity's View procurement rules)", () => {
		expect(buildSetupHash(legacyToRoute("procurement-settings", "procurement-rules"))).toBe("procurement-settings/procurement-rules");
	});
});
