// CFG-CHG-002 v0.11 §10.8 (C03-D / CUX-04) — Check sources against one exact
// version: fixed target, plain result vocabulary, and the completeness rules
// stated before the round trip.
import { flushPromises, mount } from "@vue/test-utils";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { globalMocks } from "./spec_helpers.js";

const api = vi.hoisted(() => ({
	getRegulatoryReferenceVersion: vi.fn(),
	listRegulatoryReferenceVersions: vi.fn(),
	listVerificationHistory: vi.fn(),
	recordReferenceVerification: vi.fn(),
}));
vi.mock("../data/procurementSettingsApi.js", () => ({ procurementSettingsApi: api }));

import SourceCheckScreen from "./SourceCheckScreen.vue";

const VERSION = {
	reference: "rv-1",
	reference_set: "rs-1",
	reference_kind: "Reservation rules",
	version_number: 1,
	effective_from: "2027-07-01",
	effective_until: "2028-06-30",
	source_instrument: "",
	provision: "",
	source_document: "",
	verification_status: "Production verification pending",
};

async function mountScreen(history = []) {
	api.getRegulatoryReferenceVersion.mockResolvedValue(VERSION);
	api.listRegulatoryReferenceVersions.mockResolvedValue([VERSION]);
	api.listVerificationHistory.mockResolvedValue(history);
	const wrapper = mount(SourceCheckScreen, { props: { name: "rv-1" }, global: globalMocks() });
	await flushPromises();
	return wrapper;
}

describe("SourceCheckScreen", () => {
	beforeEach(() => vi.clearAllMocks());

	it("fixes the target and version, and offers the plain result vocabulary", async () => {
		const wrapper = await mountScreen();
		expect(wrapper.find('[data-testid="kt-source-check-rule"]').text()).toBe("Reservation rules");
		expect(wrapper.find('[data-testid="kt-source-check-version"]').text()).toBe("1");
		expect(wrapper.findAll('[data-testid="kt-sc-result"] option').map((o) => o.text())).toEqual([
			"Source check needed",
			"Sources verified",
			"Source check rejected",
		]);
		// The target is a fact, not an input.
		expect(wrapper.find('[data-testid="kt-source-check-rule"]').element.tagName).not.toBe("INPUT");
	});

	it("Sources verified is refused until the three evidence groups are complete", async () => {
		const wrapper = await mountScreen();
		await wrapper.find('[data-testid="kt-sc-result"]').setValue("Verified");
		expect(wrapper.find('[data-testid="kt-sc-evidence-required"]').text()).toContain(
			"Complete the source, applicability and interpretation evidence before recording a verified source check."
		);
		expect(wrapper.find('[data-testid="kt-sc-record"]').attributes("disabled")).toBeDefined();

		await wrapper.find('[data-testid="kt-sc-instrument"]').setValue("Act, 2015 (Revised 2022)");
		await wrapper.find('[data-testid="kt-sc-dates"]').setValue("In force from 2016.");
		await wrapper.find('[data-testid="kt-sc-applicability"]').setValue("Applies from the financial year start.");
		await wrapper.find('[data-testid="kt-sc-interpretation"]').setValue("Confirmed reading.");
		expect(wrapper.find('[data-testid="kt-sc-evidence-required"]').exists()).toBe(false);
		expect(wrapper.find('[data-testid="kt-sc-record"]').attributes("disabled")).toBeUndefined();

		await wrapper.find('[data-testid="kt-sc-record"]').trigger("click");
		await flushPromises();
		expect(api.recordReferenceVerification.mock.calls[0][0]).toMatchObject({
			target_doctype: "Regulatory Reference",
			target_name: "rv-1",
			outcome: "Verified",
		});
	});

	it("the other two outcomes require the unresolved point, and each states its own consequence", async () => {
		const wrapper = await mountScreen();
		expect(wrapper.find('[data-testid="kt-sc-unresolved-required"]').exists()).toBe(true);
		expect(wrapper.find('[data-testid="kt-sc-record"]').attributes("disabled")).toBeDefined();

		await wrapper.find('[data-testid="kt-sc-unresolved"]').setValue("The amended source is not established.");
		expect(wrapper.find('[data-testid="kt-sc-pending-note"]').text()).toContain(
			"This records outstanding work; it does not verify the rule."
		);

		await wrapper.find('[data-testid="kt-sc-result"]').setValue("Rejected");
		expect(wrapper.find('[data-testid="kt-sc-rejected-note"]').text()).toContain(
			"Affected new decisions are blocked; historical evidence is retained."
		);
	});

	it("shows the append-only source-check history, newest as the server ordered it", async () => {
		const wrapper = await mountScreen([
			{ outcome: "Verified", source_check_date: "2026-08-03", recorded_by: "Administrator", change_reason: "Checked." },
			{ outcome: "Pending", source_check_date: "2026-07-01", recorded_by: "Administrator", unresolved_points: "Outstanding." },
		]);
		const rows = wrapper.findAll('[data-testid="kt-sc-history-row"]');
		expect(rows).toHaveLength(2);
		expect(rows[0].text()).toContain("Sources verified");
		expect(rows[1].text()).toContain("Source check needed");
		expect(rows[1].text()).toContain("Outstanding.");
	});
});
