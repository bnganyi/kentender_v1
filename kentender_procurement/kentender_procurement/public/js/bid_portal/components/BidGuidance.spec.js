// The next step's fixes work on every bid page, not only the one that happened
// to implement them (the Check certificate button was dead on the Requirements
// page), and a page with the task stepper does not also draw the formal journey.
import { afterEach, describe, expect, it, vi } from "vitest";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { flushPromises, mount } from "@vue/test-utils";
import { ref } from "vue";

import BidGuidance from "./BidGuidance.vue";

const APP = resolve(process.cwd(), "kentender_procurement/kentender_procurement"); // vitest runs from the repository root
const REF = "TND-MOH-2027-003";
const ANSWER = { kind: "your_turn_blocked", label: "Your turn, blocked", headline: "Obtain a valid digital signature certificate.", blockers: [{ reason_code: "BDS_SIGNATORY_CERTIFICATE_REQUIRED", message: "", headline: "", figures: {}, facts: [], fixes: [{ fix_id: "check_certificate", label: "Check certificate", kind: "command", primary: true }] }], fixes: [], stage: "SIGN_AND_SUBMIT" };
const JOURNEY = { label: "Bid journey", stages: [{ key: "BID_PREPARATION", label: "Prepare bid", state: "done" }, { key: "SIGN_AND_SUBMIT", label: "Sign and submit", state: "blocked" }, { key: "RECEIPT", label: "Receipt", state: "not_started" }] };

function portalFor(call, path = `/tenders/${REF}/bid/requirements`) {
	const route = ref({ path, segments: path.split("/").filter(Boolean), query: {} });
	const go = vi.fn();
	return { call, go, useRoute: () => ({ route, go, epoch: ref(0) }) };
}
function mountWith(props, portal) {
	return mount(BidGuidance, { props: { reference: REF, bidReference: "BID-1", answer: ANSWER, journey: JOURNEY, ...props }, global: { provide: { portal }, config: { globalProperties: { __: (s) => s } }, stubs: { PortalGuidance: { props: ["journey", "answer", "pending"], emits: ["fix"], template: '<div data-testid="guidance" :data-journey="journey ? 1 : 0"><button v-for="f in answer.blockers[0].fixes" :key="f.fix_id" :data-fix="f.fix_id" @click="$emit(\'fix\', f)">{{ f.label }}</button></div>' } } } });
}

afterEach(() => vi.restoreAllMocks());

describe("BidGuidance", () => {
	it("checks the certificate from any bid page, says the result and asks for a re-read", async () => {
		const call = vi.fn(async () => ({ status: "Required", text: "A valid digital signature certificate is required before you can submit." }));
		const wrapper = mountWith({}, portalFor(call));
		await wrapper.get('[data-fix="check_certificate"]').trigger("click");
		await flushPromises();
		expect(call).toHaveBeenCalledWith("kentender_procurement.bid_submission.api.check_certificate", { bid_reference: "BID-1", organisation: "" });
		expect(wrapper.get('[data-testid="bds-certificate-check"]').text()).toBe("A valid digital signature certificate is required before you can submit.");
		expect(wrapper.emitted("reload")).toHaveLength(1);
		expect(wrapper.emitted("fix")).toBeUndefined();
	});

	it("takes Submit bid to the Submit page from another page, and leaves it to the Submit page itself", async () => {
		const answer = { ...ANSWER, blockers: [{ ...ANSWER.blockers[0], fixes: [{ fix_id: "submit_bid", label: "Try confirmation again", kind: "command" }] }] };
		const elsewhere = portalFor(vi.fn());
		await mountWith({ answer }, elsewhere).get('[data-fix="submit_bid"]').trigger("click");
		expect(elsewhere.go).toHaveBeenCalledWith(`/tenders/${REF}/bid/submit`);
		const onSubmit = portalFor(vi.fn(), `/tenders/${REF}/bid/submit`);
		const wrapper = mountWith({ answer }, onSubmit);
		await wrapper.get('[data-fix="submit_bid"]').trigger("click");
		expect(onSubmit.go).not.toHaveBeenCalled();
		expect(wrapper.emitted("fix")[0][0].fix_id).toBe("submit_bid");
	});

	it("opens the support link the page was read with", async () => {
		const assign = vi.fn();
		vi.stubGlobal("location", { assign });
		const answer = { ...ANSWER, blockers: [{ ...ANSWER.blockers[0], fixes: [{ fix_id: "contact_support", label: "Contact support", kind: "route" }] }] };
		await mountWith({ answer, supportHref: "/support" }, portalFor(vi.fn())).get('[data-fix="contact_support"]').trigger("click");
		expect(assign).toHaveBeenCalledWith("/support");
		vi.unstubAllGlobals();
	});

	it("hands a route fix to the screen", async () => {
		const answer = { ...ANSWER, blockers: [{ ...ANSWER.blockers[0], fixes: [{ fix_id: "fix_item:documents", label: "Fix item", kind: "route", target: { task: "documents" } }] }] };
		const wrapper = mountWith({ answer }, portalFor(vi.fn()));
		await wrapper.get('[data-fix="fix_item:documents"]').trigger("click");
		expect(wrapper.emitted("fix")[0][0].target).toEqual({ task: "documents" });
	});

	it("draws the journey only where no task stepper already says where the bidder is", () => {
		expect(mountWith({}, portalFor(vi.fn())).get('[data-testid="guidance"]').attributes("data-journey")).toBe("1");
		expect(mountWith({ tracker: false }, portalFor(vi.fn())).get('[data-testid="guidance"]').attributes("data-journey")).toBe("0");
	});

	it("handles every command fix the server can name", () => {
		const server = readFileSync(resolve(APP, "bid_submission/services/guidance.py"), "utf8");
		const source = readFileSync(resolve(APP, "public/js/bid_portal/components/BidGuidance.vue"), "utf8");
		const commands = [...server.matchAll(/kind=ns\.FIX_COMMAND, fix_id="([a-z_]+)"/g)].map((m) => m[1]);
		expect(commands.length).toBeGreaterThan(0);
		for (const id of commands) expect(source, `${id} is a command the server names; BidGuidance must do it`).toContain(`"${id}"`);
	});
});
