import { describe, expect, it } from "vitest";

import { formatMoneyText, plainMoneyText } from "./money";

describe("formatMoneyText — a reading aid that never changes the amount", () => {
	it("groups thousands and shows two decimals", () => {
		expect(formatMoneyText("1000000")).toBe("1,000,000.00");
		expect(formatMoneyText("3000000.00")).toBe("3,000,000.00");
		expect(formatMoneyText("19999999.99")).toBe("19,999,999.99");
		expect(formatMoneyText("0.5")).toBe("0.50");
		expect(formatMoneyText("999")).toBe("999.00");
	});
	it("accepts what it already formatted and what was typed with separators or spaces", () => {
		expect(formatMoneyText("1,000,000.00")).toBe("1,000,000.00");
		expect(formatMoneyText(" 12 500 000 ")).toBe("12,500,000.00");
	});
	it("handles very large exact values without floating point", () => {
		expect(formatMoneyText("12345678901234567890.1")).toBe("12,345,678,901,234,567,890.10");
	});
	it("trims leading zeros but keeps a single zero", () => {
		expect(formatMoneyText("0001500")).toBe("1,500.00");
		expect(formatMoneyText("0")).toBe("0.00");
	});
	it("leaves empty text empty", () => {
		expect(formatMoneyText("")).toBe("");
		expect(formatMoneyText(null)).toBe("");
		expect(formatMoneyText(undefined)).toBe("");
	});
	it("never rounds or hides what it cannot show exactly, so the server's refusal still reads true", () => {
		expect(formatMoneyText("1.005")).toBe("1.005");
		expect(formatMoneyText("20000000.005")).toBe("20000000.005");
		expect(formatMoneyText("12.3.4")).toBe("12.3.4");
		expect(formatMoneyText("abc")).toBe("abc");
		expect(formatMoneyText("-5")).toBe("-5");
		expect(formatMoneyText("2e7")).toBe("2e7");
	});
	it("plainMoneyText gives the comma-free text that is compared and saved", () => {
		expect(plainMoneyText("1,000,000.00")).toBe("1000000.00");
		expect(plainMoneyText(" 5 ")).toBe("5");
		expect(plainMoneyText(null)).toBe("");
	});
});
