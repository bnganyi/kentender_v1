// A fix the server names must lead somewhere on every bid page it is drawn on
// (BDS-CHG-001 §10.19): a route resolves, a command is left to BidGuidance.
import { describe, expect, it } from "vitest";
import { fixRoute } from "./fixRoute.js";

const REF = "TND-MOH-2027-003";

describe("fixRoute", () => {
	it("resolves a path, a task, a screen and a fix named by id alone", () => {
		expect(fixRoute({ target: "/tenders/T/bid/replace" }, REF)).toBe("/tenders/T/bid/replace");
		expect(fixRoute({ target: { task: "documents" } }, REF)).toBe(`/tenders/${REF}/bid/documents`);
		expect(fixRoute({ target: { screen: "status" } }, REF)).toBe(`/tenders/${REF}/bid/status`);
		expect(fixRoute({ fix_id: "review_bid" }, REF)).toBe(`/tenders/${REF}/bid/review`);
		expect(fixRoute({ fix_id: "continue_bid" }, REF)).toBe(`/tenders/${REF}/bid`);
	});

	it("leaves a command to the guidance block", () => {
		expect(fixRoute({ fix_id: "check_certificate" }, REF)).toBe("");
		expect(fixRoute({ fix_id: "submit_bid" }, REF)).toBe("");
	});
});
