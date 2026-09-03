import { describe, expect, it } from "vitest";

import { formatDate, formatInstant, quantityWithUnit, versionKicker } from "./format.js";

/**
 * NDS-906 — the presentation helpers, unit-tested.
 *
 * Every case below is a real defect this module has already produced. Phase 7
 * shipped `1 Programme` and `31 August 2027` where the NDS-DES artboards say
 * `1 programme` and `31 Aug 2027`, and both survived a full Python suite and a
 * page that rendered without a single console error — because nothing about
 * them is an error. They are wrong strings, which only a comparison against the
 * artboard catches.
 *
 * These are plain functions with no Vue or frappe dependency, so they are
 * tested here rather than through a component harness. What the components do
 * *with* them — which fields appear, which controls a role is offered — is
 * asserted in the browser layer against the real server, where the answer
 * depends on permissions rather than props.
 */

describe("formatDate", () => {
	it("renders the artboard's day-month-year form", () => {
		// NDS-DES-01's required-by column, exactly as drawn.
		expect(formatDate("2027-08-31")).toBe("31 Aug 2027");
	});

	it("does not zero-pad the day", () => {
		expect(formatDate("2027-09-01")).toBe("1 Sep 2027");
	});

	it("reads a datetime as its date", () => {
		expect(formatDate("2026-11-24 14:00:00")).toBe("24 Nov 2026");
	});

	it("keeps an empty value empty rather than inventing today", () => {
		// A missing required-by must render blank; a fallback to "now" would
		// silently claim a date the requester never entered.
		expect(formatDate("")).toBe("");
		expect(formatDate(null)).toBe("");
		expect(formatDate(undefined)).toBe("");
	});

	it("passes an unparseable value through untouched", () => {
		expect(formatDate("not-a-date")).toBe("not-a-date");
	});
});

describe("formatInstant", () => {
	it("renders the artboard's instant form with the site timezone", () => {
		// §12.8 — displayed in Africa/Nairobi while stored instants stay UTC.
		expect(formatInstant("2026-11-24 14:00:00")).toBe("24 Nov 2026, 14:00 EAT");
	});

	it("falls back to the date alone when there is no time part", () => {
		expect(formatInstant("2026-11-24")).toBe("24 Nov 2026");
	});

	it("keeps an empty value empty", () => {
		expect(formatInstant("")).toBe("");
	});
});

describe("quantityWithUnit", () => {
	it("lowercases the governed unit label", () => {
		// The catalogue stores "Programme"; the artboards read "1 programme".
		expect(quantityWithUnit({ indicative_quantity: 1, unit_label: "Programme" })).toBe(
			"1 programme",
		);
	});

	it("renders a plural quantity unchanged", () => {
		expect(quantityWithUnit({ indicative_quantity: 300, unit_label: "Each" })).toBe("300 each");
	});

	it("keeps a fractional quantity as entered", () => {
		// §4.3 allows three decimals; rounding here would misreport the Need.
		expect(quantityWithUnit({ indicative_quantity: 2.5, unit_label: "Each" })).toBe("2.5 each");
	});

	it("falls back to the unit code when no label was resolved", () => {
		expect(quantityWithUnit({ indicative_quantity: 4, unit: "UNIT-EACH" })).toBe("4 unit-each");
	});

	it("renders nothing for a missing or zero quantity", () => {
		expect(quantityWithUnit({ indicative_quantity: 0, unit_label: "Each" })).toBe("");
		expect(quantityWithUnit({})).toBe("");
		expect(quantityWithUnit(null)).toBe("");
	});
});

describe("versionKicker", () => {
	it("joins reference and version in upper case", () => {
		expect(versionKicker("NDS-MOH-2027-0001", { version_number: 1 })).toBe(
			"NDS-MOH-2027-0001 · VERSION 1",
		);
	});

	it("prefixes the record kind when one is given", () => {
		expect(versionKicker("NDS-MOH-2027-0001", { version_number: 2 }, "Accepted need")).toBe(
			"ACCEPTED NEED · NDS-MOH-2027-0001 · VERSION 2",
		);
	});

	it("omits the version segment before the record has one", () => {
		// A new Need has no version until first save (§12.3), so the kicker must
		// not read "VERSION undefined".
		expect(versionKicker("NDS-MOH-2027-0001", {})).toBe("NDS-MOH-2027-0001");
		expect(versionKicker("", {})).toBe("");
	});
});
