// CFG-CHG-002 v0.11 §10.3/§11.3 (C02) / CFG11-CHG-003–004 — the Financial
// years tab: a read-only Overview naming all three intake activities (the
// new disposal-plan activity included) and a per-year Submission periods
// detail carrying open/close/deadline actions, disable/re-enable and the
// Change history disclosure.
import { flushPromises, mount } from "@vue/test-utils";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { globalMocks } from "../components/spec_helpers.js";

const api = vi.hoisted(() => ({
	listFiscalYears: vi.fn(),
	listFiscalYearIntakeHistory: vi.fn(),
	addFiscalYear: vi.fn(),
	previewFiscalYear: vi.fn(),
	openNeedsSubmission: vi.fn(),
	closeNeedsSubmission: vi.fn(),
	openDppSubmission: vi.fn(),
	closeDppSubmission: vi.fn(),
	openDisposalPlanSubmission: vi.fn(),
	closeDisposalPlanSubmission: vi.fn(),
	updateIntakeCloseInstant: vi.fn(),
	setFiscalYearDisabled: vi.fn(),
}));
vi.mock("../data/siteConfigApi.js", () => ({ siteConfigApi: api }));

import FiscalYearsTab from "./FiscalYearsTab.vue";

function row(overrides = {}) {
	return {
		fiscal_year: "2027-2028",
		label: "FY 2027/28",
		period_label: "1 Jul 2027 – 30 Jun 2028",
		phase: "Upcoming",
		disabled: false,
		reference_count: 0,
		expected_version: "v1",
		needs_submission_open: true,
		needs_submission_closes_at: "2099-11-25 23:59:00",
		needs_submission_closes_label: "25 Nov 2099, 23:59 EAT",
		dpp_submission_open: false,
		dpp_submission_closes_at: "",
		dpp_submission_closes_label: "",
		disposal_plan_submission_open: false,
		disposal_plan_submission_closes_at: "",
		disposal_plan_submission_closes_label: "",
		...overrides,
	};
}

async function mountTab(props = {}, rows = [row()], history = null) {
	api.listFiscalYears.mockResolvedValue({ fiscal_years: rows, count: rows.length });
	api.listFiscalYearIntakeHistory.mockResolvedValue(
		history || { fiscal_year: rows[0]?.fiscal_year, entries: [], count: 0 }
	);
	const wrapper = mount(FiscalYearsTab, { props, global: globalMocks() });
	await flushPromises();
	return wrapper;
}

describe("FiscalYearsTab", () => {
	beforeEach(() => vi.clearAllMocks());

	it("overview: all three activities are visible with an Open subtext and a link to Submission periods", async () => {
		const wrapper = await mountTab();
		expect(wrapper.find('[data-testid="kt-fy-needs-2027-2028"]').text()).toContain("Open");
		expect(wrapper.find('[data-testid="kt-fy-needs-2027-2028"]').text()).toContain("Closes at: 25 Nov 2099, 23:59 EAT");
		expect(wrapper.find('[data-testid="kt-fy-dpp-2027-2028"]').text()).toBe("Closed");
		expect(wrapper.find('[data-testid="kt-fy-disposal_plan-2027-2028"]').text()).toBe("Closed");
		expect(wrapper.find('[data-testid="kt-fy-detail-2027-2028"]').text()).toBe("Submission periods");
	});

	it("Include disabled years hides disabled rows until checked", async () => {
		const wrapper = await mountTab({}, [row(), row({ fiscal_year: "2026-2027", label: "FY 2026/27", disabled: true })]);
		expect(wrapper.find('[data-testid="kt-fy-row-2026-2027"]').exists()).toBe(false);
		await wrapper.find('[data-testid="kt-fy-include-disabled"] input').setValue(true);
		expect(wrapper.find('[data-testid="kt-fy-row-2026-2027"]').exists()).toBe(true);
		expect(wrapper.find('[data-testid="kt-fy-row-2026-2027"]').text()).toContain("Disabled");
	});

	it("navigating to a year shows the detail view with all three activities and emits navigate", async () => {
		const wrapper = await mountTab();
		await wrapper.find('[data-testid="kt-fy-detail-2027-2028"]').trigger("click");
		expect(wrapper.emitted("navigate")).toEqual([["year/2027-2028"]]);
	});

	it("detail view: an open activity offers Change closing time and Close submissions; a closed one offers Open submissions", async () => {
		const wrapper = await mountTab({ subpath: "year/2027-2028" });
		const detail = wrapper.find('[data-testid="kt-setup-fy-detail"]');
		expect(detail.exists()).toBe(true);
		expect(wrapper.find('[data-testid="kt-fy-deadline-needs"]').exists()).toBe(true);
		expect(wrapper.find('[data-testid="kt-fy-close-needs"]').exists()).toBe(true);
		expect(wrapper.find('[data-testid="kt-fy-open-dpp"]').exists()).toBe(true);
		expect(wrapper.find('[data-testid="kt-fy-open-disposal_plan"]').exists()).toBe(true);
	});

	it("opening the deadline dialog prefills the current closing instant and saves via updateIntakeCloseInstant", async () => {
		const wrapper = await mountTab({ subpath: "year/2027-2028" });
		await wrapper.find('[data-testid="kt-fy-deadline-needs"]').trigger("click");
		expect(wrapper.find('[data-testid="kt-fy-intake-closes"]').element.value).toBe("2099-11-25T23:59");

		api.updateIntakeCloseInstant.mockResolvedValue({ fiscal_year: "2027-2028", open: true });
		await wrapper.find('[data-testid="kt-fy-intake-reason"]').setValue("Extended.");
		await wrapper.find('[data-testid="kt-fy-intake-confirm"]').trigger("click");
		await flushPromises();
		expect(api.updateIntakeCloseInstant).toHaveBeenCalledWith("needs", "2027-2028", "2099-11-25T23:59", "Extended.", "v1");
	});

	it("opening a closed activity that would replace another open year shows the cross-year notice", async () => {
		const wrapper = await mountTab(
			{ subpath: "year/2027-2028" },
			[row(), row({ fiscal_year: "2026-2027", label: "FY 2026/27", needs_submission_open: false, dpp_submission_open: true, dpp_submission_closes_label: "" })]
		);
		await wrapper.find('[data-testid="kt-fy-open-dpp"]').trigger("click");
		const notice = wrapper.find('[data-testid="kt-fy-intake-replaces"]');
		expect(notice.exists()).toBe(true);
		expect(notice.text()).toContain("FY 2026/27");
	});

	it("closing an activity calls the matching close command with the reason and version", async () => {
		const wrapper = await mountTab({ subpath: "year/2027-2028" });
		await wrapper.find('[data-testid="kt-fy-close-needs"]').trigger("click");
		api.closeNeedsSubmission.mockResolvedValue({ fiscal_year: "2027-2028", open: false });
		await wrapper.find('[data-testid="kt-fy-intake-reason"]').setValue("Call ended.");
		await wrapper.find('[data-testid="kt-fy-intake-confirm"]').trigger("click");
		await flushPromises();
		expect(api.closeNeedsSubmission).toHaveBeenCalledWith("2027-2028", "Call ended.", "v1");
	});

	it("disable is blocked with the exact server-composed reason while an activity is open", async () => {
		const wrapper = await mountTab({ subpath: "year/2027-2028" });
		await wrapper.find('[data-testid="kt-fy-disable-open"]').trigger("click");
		const confirm = wrapper.find('[data-testid="kt-fy-disable-confirm"]');
		expect(confirm.attributes("disabled")).toBeDefined();
		expect(wrapper.text()).toContain("Departmental needs submission is open for this financial year.");
	});

	it("disable succeeds once unblocked, and a disabled year offers Enable financial year instead", async () => {
		const closed = row({ needs_submission_open: false, needs_submission_closes_label: "" });
		const wrapper = await mountTab({ subpath: "year/2027-2028" }, [closed]);
		await wrapper.find('[data-testid="kt-fy-disable-open"]').trigger("click");
		expect(wrapper.find('[data-testid="kt-fy-disable-confirm"]').attributes("disabled")).toBeUndefined();

		api.setFiscalYearDisabled.mockResolvedValue({ fiscal_year: "2027-2028", disabled: true });
		api.listFiscalYears.mockResolvedValue({ fiscal_years: [row({ ...closed, disabled: true })], count: 1 });
		await wrapper.find('[data-testid="kt-fy-disable-confirm"]').trigger("click");
		await flushPromises();
		expect(api.setFiscalYearDisabled).toHaveBeenCalledWith("2027-2028", true, "v1");
		expect(wrapper.find('[data-testid="kt-fy-enable"]').exists()).toBe(true);
	});

	it("the Change history disclosure shows the server's labelled entries once expanded", async () => {
		const wrapper = await mountTab({ subpath: "year/2027-2028" }, [row()], {
			fiscal_year: "2027-2028",
			count: 1,
			entries: [
				{
					activity: "Departmental needs",
					financial_year: "FY 2027/28",
					change: "Open",
					previous_value: "—",
					new_value: "25 Nov 2099, 23:59 EAT",
					reason: "Annual needs call issued.",
					changed_by: "Administrator",
					changed_at: "1 Nov 2099, 08:02 EAT",
				},
			],
		});
		expect(wrapper.find('[data-testid="kt-fy-history-toggle"]').text()).toContain("1 entries");
		await wrapper.find('[data-testid="kt-fy-history-toggle"]').trigger("click");
		const body = wrapper.find('[data-testid="kt-fy-history-body"]');
		expect(body.text()).toContain("Annual needs call issued.");
		expect(body.text()).toContain("Administrator");
	});

	it("adding a year with no accounting company shows the Company not linked defect and disables Add", async () => {
		const wrapper = await mountTab();
		api.previewFiscalYear.mockResolvedValue({
			fiscal_year: "2028-2029",
			label: "FY 2028/29",
			period_label: "1 Jul 2028 – 30 Jun 2029",
			exists: false,
			company_missing: true,
		});
		await wrapper.find('[data-testid="kt-fy-add-open"]').trigger("click");
		await wrapper.find('[data-testid="kt-fy-start-year"]').setValue("2028");
		await flushPromises();
		expect(wrapper.find('[data-testid="kt-fy-company-missing"]').exists()).toBe(true);
		expect(wrapper.find('[data-testid="kt-fy-add-confirm"]').attributes("disabled")).toBeDefined();
	});
});
