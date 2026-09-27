// Structural fidelity for the Bid Submission portal screens against the
// "Bid Board v3" boards (BDS-CHG-001 v0.8 §10), at both frames: each variant
// is mounted with its fixture at 1440 and at 390 (the narrow frame renders
// the boards' labelled cards) and compared container for container with the
// board's `main`; registered departures are the only allowed differences.
import { afterEach, describe, expect, it, vi } from "vitest";
import { mount } from "@vue/test-utils";
import { nextTick, ref } from "vue";

import { createCommandRunner, createScreenCache, createSequenceGuard } from "../../../../../kentender_core/kentender_core/public/js/kt_portal/runtime.js";
import { bidSubmissionSkeleton } from "../../../../../tests/ui/fidelity/board.js";
import { compareSkeletons, formatMismatch, skeletonOf } from "../../../../../tests/ui/fidelity/skeleton.js";
import { ACCOUNT_SCREENS, COVERED, DEPARTURES } from "../../../../../tests/ui/fidelity/departures/bid-submission.js";

import AvailableTendersScreen from "./screens/AvailableTendersScreen.vue";
import { SCREENS as OVERVIEW } from "./screens/TenderOverviewScreen.fixtures.js";
import { SCREENS as MY_BIDS } from "./screens/myBids.fixtures.js";
import { SCREENS as WORKSPACE } from "./screens/workspace.fixtures.js";
import { SCREENS as DOCUMENTS } from "./screens/documents.fixtures.js";
import { SCREENS as COMPANY } from "./screens/company.fixtures.js";

const DESIGN = "docs/mvp-1-r1/12_bid_submission/design";
const A = `${DESIGN}/Bid Board v3 - A Public and Account.dc.html`;
const B = `${DESIGN}/Bid Board v3 - B Workspace and documents.dc.html`;
const C = `${DESIGN}/Bid Board v3 - C Company requirements and price.dc.html`;

function portalFor(path) {
	const route = ref({ path, segments: path.split("/").filter(Boolean), query: {} });
	return {
		call: vi.fn(async () => ({})), go: vi.fn(), setTitle: vi.fn(), createSequenceGuard, createCommandRunner, createScreenCache,
		useRoute: () => ({ route, go: vi.fn(), epoch: ref(0) }),
	};
}

const LIST = {
	rows: [{ reference: "TND-MOH-2027-033", title: "Supply and delivery of business laptops", procuring_entity: "Ministry of Health", method: "Open Tender", reservation: "Youth", submission_deadline_label: "12 Jun 2027, 11:00 EAT", href: "/tenders/TND-MOH-2027-033" }],
	count_text: "1 available Tender", empty_text: "", applied: {}, options: { method: [{ value: "", label: "All methods" }], reservation: [{ value: "", label: "All categories" }], closing: [{ value: "open", label: "Open Tenders" }] },
};
const EMPTY = { ...LIST, rows: [], count_text: "", empty_text: "No Tenders match these filters." };

const SCREENS = [
	...["desktop", "narrow"].flatMap((frame) => [
		{ name: "AvailableTendersScreen", variant: "BDS-DES-01", board: A, frame, component: AvailableTendersScreen, props: { initial: LIST }, path: "/tenders" },
		{ name: "AvailableTendersScreen", variant: "BDS-DES-01-EMPTY", board: A, frame, component: AvailableTendersScreen, props: { initial: EMPTY }, path: "/tenders" },
	]),
	...OVERVIEW.map((s) => ({ ...s, board: A })),
	...MY_BIDS.map((s) => ({ ...s, board: A })),
	...WORKSPACE.map((s) => ({ ...s, board: B })),
	...DOCUMENTS.map((s) => ({ ...s, board: B })),
	...COMPANY.map((s) => ({ ...s, board: C })),
];

afterEach(() => {
	globalThis.__narrow = false;
});

describe.each(SCREENS)("$name — $variant at the $frame frame", ({ name, variant, board, frame, component, props, path }) => {
	it("is built out of the board's own elements", async () => {
		globalThis.__narrow = frame === "narrow";
		const wrapper = mount(component, { props, attachTo: document.body, global: { provide: { portal: portalFor(path) }, config: { globalProperties: { __: globalThis.__ } } } });
		await nextTick();
		await nextTick();
		const key = `${name}#${variant}@${frame}`;
		const result = compareSkeletons(bidSubmissionSkeleton(board, variant, { frame }), skeletonOf(wrapper.element), { departures: DEPARTURES[key] || [] });
		const message = formatMismatch(key, result);
		wrapper.unmount();
		expect(message, message).toBe("");
	}, 30_000);
});

describe("the COVERED claim", () => {
	// the screens this spec compares, named here so the registry's COVERED claim points at them
	const COMPARED = ["AvailableTendersScreen", "TenderOverviewScreen", "MyBidsScreen", "ReceiptHistoryScreen", "BidWorkspaceScreen", "DocumentsTaskScreen", "CompanyTaskScreen"];
	it("compares exactly the named screens", () => {
		expect([...new Set(SCREENS.map((s) => s.name))].sort()).toEqual([...COMPARED].sort());
	});
	it("lists exactly the variants this spec compares", () => {
		// the Account screens are compared by supplier-account-portal.fidelity.spec.js
		const mine = [...COVERED].filter((key) => !ACCOUNT_SCREENS.test(key));
		expect(mine.sort()).toEqual([...new Set(SCREENS.map((s) => `${s.name}#${s.variant}@${s.frame}`))].sort());
	});
});
