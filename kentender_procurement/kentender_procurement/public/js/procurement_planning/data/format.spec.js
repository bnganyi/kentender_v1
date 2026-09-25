import { describe, expect, it } from "vitest";

import { formatDate, formatMoney, formatQuantity } from "./format.js";

describe("formatMoney", () => {
	it("groups thousands and always shows two decimal places", () => {
		expect(formatMoney("1000000.00")).toBe("KES 1,000,000.00");
	});

	it("never routes a decimal string through a float first", () => {
		// "1000000.10" must stay ...10, not collapse to ...1 the way
		// `Number("1000000.10")` formatting would.
		expect(formatMoney("1000000.10")).toBe("KES 1,000,000.10");
	});

	it("pads a whole-number decimal string to two places", () => {
		expect(formatMoney("500000")).toBe("KES 500,000.00");
	});

	it("keeps a negative amount's sign before the currency code", () => {
		expect(formatMoney("-250.50")).toBe("-KES 250.50");
	});

	it("renders a missing amount as zero rather than blank", () => {
		expect(formatMoney("")).toBe("KES 0.00");
		expect(formatMoney(null)).toBe("KES 0.00");
		expect(formatMoney(undefined)).toBe("KES 0.00");
	});
});

describe("formatDate", () => {
	it("renders the artboard's day-month-year form", () => {
		expect(formatDate("2102-04-30")).toBe("30 Apr 2102");
	});

	it("does not zero-pad the day", () => {
		expect(formatDate("2101-09-01")).toBe("1 Sep 2101");
	});

	it("reads a datetime as its date", () => {
		expect(formatDate("2026-11-24 14:00:00")).toBe("24 Nov 2026");
	});

	it("keeps an empty value empty rather than inventing today", () => {
		expect(formatDate("")).toBe("");
		expect(formatDate(null)).toBe("");
		expect(formatDate(undefined)).toBe("");
	});

	it("passes an unparseable value through untouched", () => {
		expect(formatDate("not-a-date")).toBe("not-a-date");
	});
});

describe("formatQuantity", () => {
	it("appends the unit label", () => {
		expect(formatQuantity("1.000", "Each")).toBe("1 Each");
	});

	it("trims trailing zeros from a governed three-decimal quantity", () => {
		expect(formatQuantity("2.500", "Each")).toBe("2.5 Each");
	});

	it("keeps a whole number without a decimal point", () => {
		expect(formatQuantity("300.000", "Each")).toBe("300 Each");
	});

	it("renders a missing quantity as zero", () => {
		expect(formatQuantity("", "Each")).toBe("0 Each");
		expect(formatQuantity(null, "")).toBe("0");
	});
});
