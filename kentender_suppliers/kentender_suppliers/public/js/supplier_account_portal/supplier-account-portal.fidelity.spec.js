// Structural fidelity for the supplier Account portal screens against "Bid
// Board v3 - A" (BDS-CHG-001 v0.8 §10.4–10.5), at both frames: each variant is
// mounted with its fixture at 1440 and at 390 (the narrow frame renders the
// boards' labelled cards) and compared container for container with the
// board's `main`; registered departures are the only allowed differences.
// BDS-DES-03-VERIFY is reached the way a person reaches it: Create account.
import { afterEach, describe, expect, it, vi } from "vitest";
import { flushPromises, mount } from "@vue/test-utils";
import { nextTick, ref } from "vue";

import { createCommandRunner, createScreenCache, createSequenceGuard } from "../../../../../kentender_core/kentender_core/public/js/kt_portal/runtime.js";
import { bidSubmissionSkeleton } from "../../../../../tests/ui/fidelity/board.js";
import { compareSkeletons, formatMismatch, skeletonOf } from "../../../../../tests/ui/fidelity/skeleton.js";
import { ACCOUNT_SCREENS, COVERED, DEPARTURES } from "../../../../../tests/ui/fidelity/departures/bid-submission.js";

import { REGISTERED, SCREENS, account } from "./screens/account.fixtures.js";

const BOARD = "docs/mvp-1-r1/12_bid_submission/design/Bid Board v3 - A Public and Account.dc.html";

function portalFor(path) {
	const route = ref({ path, segments: path.split("/").filter(Boolean), query: {} });
	return {
		call: vi.fn(async () => account("VERIFY")), upload: vi.fn(async () => REGISTERED), go: vi.fn(), setTitle: vi.fn(), createSequenceGuard, createCommandRunner, createScreenCache,
		useRoute: () => ({ route, go: vi.fn(), epoch: ref(0) }),
	};
}

afterEach(() => {
	globalThis.__narrow = false;
	document.body.innerHTML = "";
});

describe.each(SCREENS)("$name — $variant at the $frame frame", ({ name, variant, frame, component, props, path, register }) => {
	it("is built out of the board's own elements", async () => {
		globalThis.__narrow = frame === "narrow";
		const wrapper = mount(component, { props, attachTo: document.body, global: { provide: { portal: portalFor(path) }, config: { globalProperties: { __: globalThis.__ } } } });
		await nextTick();
		if (register) {
			await wrapper.get('[data-testid="acc-create"]').trigger("click");
			await flushPromises();
		}
		await nextTick();
		const key = `${name}#${variant}@${frame}`;
		const result = compareSkeletons(bidSubmissionSkeleton(BOARD, variant, { frame }), skeletonOf(wrapper.element), { departures: DEPARTURES[key] || [] });
		const message = formatMismatch(key, result);
		wrapper.unmount();
		expect(message, message).toBe("");
	}, 30_000);
});

describe("the COVERED claim", () => {
	// the screens this spec compares, named here so the registry's COVERED claim points at them
	const COMPARED = ["RegisterScreen", "AccountScreen"];
	it("compares exactly the named screens", () => {
		expect([...new Set(SCREENS.map((s) => s.name))].sort()).toEqual([...COMPARED].sort());
	});
	it("lists exactly the Account variants this spec compares", () => {
		const mine = [...COVERED].filter((key) => ACCOUNT_SCREENS.test(key));
		expect(mine.sort()).toEqual([...new Set(SCREENS.map((s) => `${s.name}#${s.variant}@${s.frame}`))].sort());
	});
});
