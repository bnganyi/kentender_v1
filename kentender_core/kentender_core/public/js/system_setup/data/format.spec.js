// The shared date format for System setup: "24 Nov 2026" (CFG-CHG-002 v0.14
// §10). Newer locale data abbreviates September as "Sept", so the month is
// never left to the runtime's locale tables.
import { describe, expect, it } from "vitest";
import { fmtDate } from "./format.js";

describe("fmtDate", () => {
	it("uses three-letter months for every month, September included", () => {
		expect(fmtDate("2026-09-12")).toBe("12 Sep 2026");
		expect(fmtDate("2026-11-24")).toBe("24 Nov 2026");
		expect(fmtDate("2027-07-01")).toBe("1 Jul 2027");
	});

	it("reads the date part of a server timestamp, and dashes an empty value", () => {
		expect(fmtDate("2026-09-12 10:00:00.123456")).toBe("12 Sep 2026");
		expect(fmtDate("")).toBe("—");
		expect(fmtDate(null)).toBe("—");
	});
});
