// The electronic tender-security journey: four separate facts and two explicit
// actions (Project Owner, 10 Oct 2026). An upload is never "verified"; the
// verification source and response time are shown with the result.
import { describe, expect, it } from "vitest";
import { mount } from "@vue/test-utils";

import TenderSecurityStatus from "./TenderSecurityStatus.vue";

const SOURCE = "Test Issuer Service (simulation)";
const electronic = (overrides = {}) => ({
	submission: { state: "Not submitted", text: "You have not submitted your tender security yet.", can_submit: true },
	verification: { state: "Not requested", text: "Not requested.", source: "", responded_at: "", response_ms: null },
	compliance: { state: "Meets", text: "The form, amount and validity match the published requirement." },
	...overrides,
});
const view = (e, props = {}) => mount(TenderSecurityStatus, { props: { electronic: e, ...props }, global: { config: { globalProperties: { __: (s) => s } } } });

describe("TenderSecurityStatus", () => {
	it("shows submission, issuer verification and compliance as three separate facts", () => {
		const w = view(electronic());
		expect(w.get('[data-testid="bds-security-submission"]').text()).toContain("Not submitted");
		expect(w.get('[data-testid="bds-security-verification"]').text()).toContain("Not requested");
		expect(w.get('[data-testid="bds-security-compliance"]').text()).toContain("Meets");
		expect(w.text()).toContain("an upload alone is never treated as verified");
	});
	it("offers Submit tender security only when the details are complete, and never from a closed bid", async () => {
		const ready = view(electronic());
		await ready.get('[data-testid="bds-security-submit"]').trigger("click");
		expect(ready.emitted("submit")).toHaveLength(1);
		expect(view(electronic({ submission: { state: "Not submitted", text: "", can_submit: false } })).get('[data-testid="bds-security-submit"]').attributes("disabled")).toBeDefined();
		expect(view(electronic(), { canEdit: false }).find('[data-testid="bds-security-submit"]').exists()).toBe(false);
	});
	it("shows the verification source, the answer time and the response time beside a result", () => {
		const w = view(electronic({ submission: { state: "Submitted", text: "Submitted 12 Jun 2027, 10:00 EAT.", can_submit: true }, verification: { state: "Confirmed", text: "The issuer confirmed this instrument.", source: SOURCE, responded_at: "12 Jun 2027, 10:00:02 EAT", response_ms: 240 } }));
		const details = w.get('[data-testid="bds-security-verification-details"]').text();
		expect(details).toContain(SOURCE);
		expect(details).toContain("10:00:02");
		expect(details).toContain("240 ms");
		expect(w.find('[data-testid="bds-security-submit"]').exists()).toBe(false);
	});
	it("keeps an unavailable issuer pending and offers to check again", async () => {
		const w = view(electronic({ submission: { state: "Submitted", text: "", can_submit: true }, verification: { state: "Pending", text: "The issuer could not be reached. Verification stays pending; check again later.", last_response: "Unavailable", source: SOURCE, responded_at: "", response_ms: null } }));
		expect(w.get('[data-testid="bds-security-verification"]').text()).toContain("stays pending");
		await w.get('[data-testid="bds-security-check"]').trigger("click");
		expect(w.emitted("check")).toHaveLength(1);
	});
	it("asks to submit again after a mismatch", async () => {
		const w = view(electronic({ submission: { state: "Submitted", text: "", can_submit: true }, verification: { state: "Mismatch", text: "The issuer's record does not match the details you submitted.", source: SOURCE, responded_at: "x", response_ms: 150 } }));
		await w.get('[data-testid="bds-security-submit"]').trigger("click");
		expect(w.emitted("submit")).toHaveLength(1);
		expect(w.get('[data-testid="bds-security-submit"]').text()).toContain("again");
	});
	it("names the issuer's side as \"Issuer verification pending\" and says when security is checked, never \"not matched\"", () => {
		const w = view(electronic({ submission: { state: "Submitted", text: "", can_submit: true }, verification: { state: "Pending", label: "Issuer verification pending", text: "Waiting for the issuer to confirm this instrument.", source: SOURCE, responded_at: "", response_ms: null } }));
		expect(w.get('[data-testid="bds-security-verification"]').text()).toContain("Issuer verification pending");
		expect(w.get('[data-testid="bds-security-after-opening"]').text()).toBe("Security will be checked against your bid after opening.");
		expect(w.text().toLowerCase()).not.toContain("not yet matched");
		const confirmed = view(electronic({ submission: { state: "Submitted", text: "", can_submit: true }, verification: { state: "Confirmed", label: "Issuer verification confirmed", text: "", source: SOURCE, responded_at: "x", response_ms: 1 } }));
		expect(confirmed.find('[data-testid="bds-security-after-opening"]').exists()).toBe(false);
	});
	it("renders nothing for a Tender without a tender security", () => {
		expect(view(null).find('[data-testid="bds-security-status"]').exists()).toBe(false);
	});
});
