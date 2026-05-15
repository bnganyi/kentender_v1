import { describe, expect, it } from "vitest";

import { isProbableStackTrace, safeUserPrimaryMessage } from "./safeUserMessage";

describe("safeUserMessage", () => {
	it("detects multiline stack traces", () => {
		const stack = `Error: boom
    at Object.handler (file.js:12:3)
    at Module.run (run.js:1:1)`;
		expect(isProbableStackTrace(stack)).toBe(true);
		expect(safeUserPrimaryMessage(stack)).not.toMatch(/at Object\.handler/);
	});

	it("passes through ordinary denial copy", () => {
		const msg = "You cannot publish this tender because approval is not complete.";
		expect(isProbableStackTrace(msg)).toBe(false);
		expect(safeUserPrimaryMessage(msg)).toBe(msg);
	});
});
