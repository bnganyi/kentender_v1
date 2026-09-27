// BDS-CHG-001 v0.8 §10.17 BDS-DES-16: every common state against its cell on
// board E ("Bid Board v3 - E Desk and common states", both frames). Headings
// and actions are the board's words verbatim; a message is too, unless the
// board cell is an instruction to the builder (recorded as `board_message`,
// with the live wording in `message`). Every state renders from the one
// catalogue the server also reads.
import { afterEach, describe, expect, it } from "vitest";
import { mount } from "@vue/test-utils";

import { bidSubmissionStateCells } from "../../../../../tests/ui/fidelity/board.js";
import catalogue from "../../../bid_submission/common_states.json";
import CommonState from "./components/CommonState.vue";

const E = "docs/mvp-1-r1/12_bid_submission/design/Bid Board v3 - E Desk and common states.dc.html";
// The §10.1 fixture facts the board's literal messages name.
const FIGURES = {
	organisation: "Afya Digital Supplies Limited", correlation_id: "COR-BDS-2027-033-01", support_reference: "SUP-BDS-2027-033-01",
	deadline: "12 Jun 2027, 11:00 EAT", current_time: "12 Jun 2027, 11:00:01 EAT", rejection_reference: "TBX-REJECT-033-01", receipt_reference: "RCPT-MOH-2027-033-002", reason: "",
};
const fill = (text) => text.replace(/\{(\w+)\}/g, (_m, name) => FIGURES[name] ?? "");
const byLabel = Object.fromEntries(catalogue.states.map((entry) => [entry.label, entry]));

afterEach(() => {
	document.body.innerHTML = "";
});

describe.each(["desktop", "narrow"])("BDS-DES-16 at the %s frame", (frame) => {
	const cells = bidSubmissionStateCells(E, "BDS-DES-16", { frame });

	it("has one catalogue state for every cell and one cell for every §10.17 state", () => {
		expect(cells.map((c) => c.label).sort()).toEqual(catalogue.states.filter((e) => !e.added).map((e) => e.label).sort());
	});

	it.each(cells.map((c) => [c.label, c]))("%s says what the board says", (_label, cell) => {
		const entry = byLabel[cell.label];
		expect(entry.heading).toBe(cell.heading);
		expect(entry.action).toBe(cell.action);
		if (entry.board_message) expect(entry.board_message).toBe(cell.message);
		else expect(fill(entry.message)).toBe(cell.message);
	});
});

describe("every catalogue state renders from the catalogue", () => {
	it.each(catalogue.states.map((e) => [e.key, e]))("%s, as a page and in place", (key, entry) => {
		for (const inline of [false, true]) {
			const wrapper = mount(CommonState, { props: { state: key, figures: FIGURES, inline }, attachTo: document.body, global: { config: { globalProperties: { __: globalThis.__ } } } });
			const state = wrapper.get(`[data-testid="bds-state-${key}"]`);
			expect(state.text()).toContain(entry.heading);
			expect(state.text()).toContain(fill(entry.message));
			expect(state.get("button").text()).toBe(entry.action);
			wrapper.unmount();
		}
	});

	it("uses a state's retry action only when the server permits one", () => {
		const wrapper = mount(CommonState, { props: { state: "custody-rejected", figures: FIGURES, retry: true }, global: { config: { globalProperties: { __: globalThis.__ } } } });
		expect(wrapper.get("button").text()).toBe("Try confirmation again");
	});
});
