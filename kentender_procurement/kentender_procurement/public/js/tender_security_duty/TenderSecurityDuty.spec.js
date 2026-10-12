// Tender-security intake duty page (Project Owner, 10 Oct 2026): the Head of
// Procurement Function sees officers, why one is not eligible, and the
// assignments — never an intake, a supplier or a bid. Server payloads are the
// fixtures; nothing here decides eligibility.
import { beforeEach, describe, expect, it, vi } from "vitest";
import { flushPromises, mount } from "@vue/test-utils";
import { ref } from "vue";

const api = vi.hoisted(() => ({ getDuty: vi.fn(), assignOfficer: vi.fn(), revokeOfficer: vi.fn(), listConflicts: vi.fn() }));
const route = vi.hoisted(() => ({ hash: null, goHash: null }));
vi.mock("./data/api.js", () => api);
vi.mock("../tnd_shared/composables/usePageRail.js", () => ({ usePageRail: vi.fn() }));
vi.mock("./composables/useRouteState.js", () => ({
	useRouteState: () => {
		route.hash = ref("tender=TND-MOH-2027-002");
		route.goHash = vi.fn((fragment) => (route.hash.value = fragment));
		return { epoch: ref(0), hash: route.hash, goHash: route.goHash };
	},
}));

import TenderSecurityDuty from "./TenderSecurityDuty.vue";

const g = { global: { mocks: { __: (s) => s } } };
const LEAK = /\b(BID-|ARR-|Afya|bid status|Matched|instrument|TSI-)\b/i;
const OFFICERS = {
	found: true, tender_reference: "TND-MOH-2027-002", tender_title: "Laptops",
	officers: [
		{ user: "mercy@x", full_name: "Mercy Kilonzo", responsibilities: ["Procurement Planner"], eligible: true, reason: "", assigned: false, is_head: false },
		{ user: "brian@x", full_name: "Brian Wafula", responsibilities: ["Procurement Officer"], eligible: false, reason: "Brian Wafula is on the opening committee for this Tender, so cannot also take its tender-security intake.", assigned: false, is_head: false },
	],
};
const duty = (rows = []) => ({ outcome: "OK", officers: OFFICERS, assignments: { found: true, tender_reference: "TND-MOH-2027-002", rows } });
const ROW = { assignment: "URA-1", user: "mercy@x", full_name: "Mercy Kilonzo", status: "Active", effective_from: "", effective_to: "", assigned_by: "Charles Mutiso", assigned_at: "2027-06-01 09:00:00", revoked_by: "", revoked_at: "", revocation_reason: "" };

beforeEach(() => {
	vi.clearAllMocks();
	api.listConflicts.mockResolvedValue({ outcome: "OK", rows: [] });
});

describe("TenderSecurityDuty", () => {
	it("lists the officers with the reason one is not eligible, and nothing about a bid", async () => {
		api.getDuty.mockResolvedValue(duty());
		const w = mount(TenderSecurityDuty, g);
		await flushPromises();
		expect(w.findAll('[data-testid="tsd-officer"]')).toHaveLength(2);
		expect(w.get('[data-testid="tsd-reason"]').text()).toContain("is on the opening committee for this Tender");
		expect(w.findAll('[data-testid="tsd-assign"]')).toHaveLength(1);
		expect(w.get('[data-testid="tsd-no-assignments"]').text()).toBe("Nobody holds the intake duty for this Tender.");
		expect(w.text()).not.toMatch(LEAK);
	});

	it("assigns an officer for the Tender with an optional period and reloads", async () => {
		api.getDuty.mockResolvedValueOnce(duty()).mockResolvedValue(duty([ROW]));
		api.assignOfficer.mockResolvedValue({ outcome: "OK", ok: true });
		const w = mount(TenderSecurityDuty, g);
		await flushPromises();
		await w.get('[data-testid="tsd-assign"]').trigger("click");
		await w.get('[data-testid="tsd-d-from"]').setValue("2027-06-01T09:00");
		await w.get('[data-testid="tsd-d-submit"]').trigger("click");
		await flushPromises();
		expect(api.assignOfficer).toHaveBeenCalledWith({ tender_reference: "TND-MOH-2027-002", officer: "mercy@x", effective_from: "2027-06-01 09:00:00", effective_to: "" });
		expect(w.find('[data-testid="tsd-dialog"]').exists()).toBe(false);
		expect(w.get('[data-testid="tsd-done"]').text()).toBe("The intake duty is assigned to Mercy Kilonzo.");
		expect(w.findAll('[data-testid="tsd-assignment"]')).toHaveLength(1);
	});

	it("names a refusal in the dialog and keeps it open", async () => {
		api.getDuty.mockResolvedValue(duty());
		api.assignOfficer.mockResolvedValue({ outcome: "FORBIDDEN", text: "Only the Head of Procurement Function assigns the tender-security intake duty." });
		const w = mount(TenderSecurityDuty, g);
		await flushPromises();
		await w.get('[data-testid="tsd-assign"]').trigger("click");
		await w.get('[data-testid="tsd-d-submit"]').trigger("click");
		await flushPromises();
		expect(w.get('[data-testid="tsd-d-error"]').text()).toContain("Only the Head of Procurement Function assigns");
	});

	it("ends the duty with a reason and says what ending does and does not do", async () => {
		api.getDuty.mockResolvedValue(duty([ROW]));
		api.revokeOfficer.mockResolvedValue({ outcome: "OK", ok: true, revoked: true });
		const w = mount(TenderSecurityDuty, g);
		await flushPromises();
		expect(w.text()).toContain("Someone who has already recorded or viewed this Tender's intake stays ineligible");
		await w.get('[data-testid="tsd-revoke"]').trigger("click");
		await w.get('[data-testid="tsd-d-reason"]').setValue("The duty is no longer needed.");
		await w.get('[data-testid="tsd-d-submit"]').trigger("click");
		await flushPromises();
		expect(api.revokeOfficer).toHaveBeenCalledWith({ assignment: "URA-1", reason: "The duty is no longer needed." });
	});

	it("shows Forbidden as a state for anyone but the Head", async () => {
		api.getDuty.mockResolvedValue({ outcome: "FORBIDDEN", heading: "You do not assign tender-security intake", text: "Only the Head of Procurement Function assigns the tender-security intake duty." });
		const w = mount(TenderSecurityDuty, g);
		await flushPromises();
		expect(w.get('[data-testid="tsd-forbidden"]').text()).toContain("Only the Head of Procurement Function assigns");
		expect(w.find('[data-testid="tsd-assign"]').exists()).toBe(false);
	});

	it("shows the flagged conflicts without any supplier fact", async () => {
		api.getDuty.mockResolvedValue(duty());
		api.listConflicts.mockResolvedValue({ outcome: "OK", rows: [{ name: "c1", tender_reference: "TND-MOH-2027-002", full_name: "Charles Mutiso", conflicting_duty: "Opening committee", basis: "Has recorded intake" }] });
		const w = mount(TenderSecurityDuty, g);
		await flushPromises();
		expect(w.get('[data-testid="tsd-conflict"]').text()).toContain("Opening committee");
		expect(w.text()).toContain("The Accounting Officer resolves a flagged conflict");
	});
});
