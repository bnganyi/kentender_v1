// A guard that the per-app copies of the record picker's host wrapper have not drifted (AGENTS.md
// section 6.12): a bundle cannot import another app's wrapper (section 6.6), so the file is copied, and
// a copy that is edited alone is how two modules would come to draw or report the picker differently.
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";

describe("per-app copies", () => {
	const roots = [
		"kentender_procurement/kentender_procurement",
		"kentender_budget/kentender_budget",
		"kentender_strategy/kentender_strategy",
		"kentender_core/kentender_core",
		"kentender_contracts/kentender_contracts",
	];
	it.each(["RecordPickerHost.vue"])("%s is identical in every app", (file) => {
		const read = (root) => readFileSync(resolve(process.cwd(), root, "public/js/record_picker_shared", file), "utf8");
		const [first, ...rest] = roots.map(read);
		for (const other of rest) expect(other).toBe(first);
	});
});
