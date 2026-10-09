// A Planning refusal names its code and the fields it is about (`errors.fail`, PLN v1.31). They ride on the
// server message log; the wrapper must hand them to the screen, or the page can only show a generic sentence.
import { afterEach, describe, expect, it, vi } from "vitest";

import { frappeCall } from "../../pln_shared/frappeCall.js";

function refusal(structured, message = "Public plan URL: Enter the address of the published plan, starting with http:// or https://.") {
	const entry = JSON.stringify({ message, title: "PLN_TREASURY_EVIDENCE_REQUIRED", indicator: "red", ...(structured ? { kt_pln: structured } : {}) });
	return { status: 417, statusText: "EXPECTATION FAILED", responseJSON: { _server_messages: JSON.stringify([entry]), exception: "x.ProcurementPlanningError: ignored" } };
}

function stubFrappe(xhr) {
	globalThis.__ = (text) => text;
	globalThis.frappe = { call: vi.fn().mockRejectedValue(xhr), msgprint: () => {} };
}

afterEach(() => {
	delete globalThis.frappe;
	delete globalThis.__;
});

describe("frappeCall", () => {
	it("hands the screen the refusal's code and its per-field detail along with the message", async () => {
		stubFrappe(refusal({ code: "PLN_TREASURY_EVIDENCE_REQUIRED", detail: { fields: { public_plan_url: "Enter the address of the published plan, starting with http:// or https://." } } }));
		const error = await frappeCall("x.y", {}).catch((e) => e);
		expect(error.message).toContain("Public plan URL");
		expect(error.code).toBe("PLN_TREASURY_EVIDENCE_REQUIRED");
		expect(error.detail.fields.public_plan_url).toContain("http:// or https://");
		expect(error.httpStatus).toBe(417);
	});

	it("gives an empty detail, never undefined, when the refusal carried none", async () => {
		stubFrappe(refusal(null, "This review has changed. Refresh before deciding."));
		const error = await frappeCall("x.y", {}).catch((e) => e);
		expect(error.message).toBe("This review has changed. Refresh before deciding.");
		expect(error.code).toBe("");
		expect(error.detail).toEqual({});
	});
});
