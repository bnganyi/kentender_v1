// C06-Users-Responsibilities.dc.html — the register's behaviour around its
// board-compared structure (system-setup.fidelity.spec): a responsibility
// opens by its own link, a linked one loads without the register, filters
// that match nothing keep the filters, a stale read never overwrites a newer
// one, and focus returns to the control that opened a dialog.
import { flushPromises, mount } from "@vue/test-utils";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { globalMocks } from "../components/spec_helpers.js";

const api = vi.hoisted(() => ({
	listRows: vi.fn(),
	formOptions: vi.fn(async () => ({ responsibilities: [], organisation_units: [], statuses: ["Active"] })),
	searchUsers: vi.fn(async () => []),
	preview: vi.fn(async () => ({ ok: false, problems: [], conflict: null, summary: "" })),
	detail: vi.fn(),
}));
vi.mock("../data/responsibilityApi.js", () => ({ responsibilityApi: api }));

import UserResponsibilitiesTab from "./UserResponsibilitiesTab.vue";

const ROW = {
	assignment: "URA-2026-0003",
	user_full_name: "Julia Njeri",
	user: "julia.njeri@moh.example.test",
	business_role: "Head of User Department",
	scope_label: "Digital Health",
	coverage: "This unit only",
	appointment_type: "Acting",
	period_label: "1 Oct 2026 – 30 Nov 2026",
	status: "Scheduled",
};

beforeEach(() => {
	vi.clearAllMocks();
	api.listRows.mockResolvedValue({ rows: [ROW], total: 1 });
});

describe("UserResponsibilitiesTab", () => {
	it("opens a responsibility by its own link rather than swapping the view in place", async () => {
		const wrapper = mount(UserResponsibilitiesTab, { global: globalMocks() });
		await flushPromises();
		const view = wrapper.find('[data-testid="kt-ura-view-URA-2026-0003"]');
		expect(view.attributes("href")).toBe("#users-and-responsibilities/URA-2026-0003");
		await view.trigger("click");
		expect(wrapper.emitted("open")).toEqual([["URA-2026-0003"]]);
		expect(api.detail).not.toHaveBeenCalled();
	});

	it("loads the linked responsibility and shows it without the register", async () => {
		api.detail.mockResolvedValue({
			...ROW,
			scope_type: "Organisation Unit",
			organisation_unit_path: "Ministry of Health › Digital Health",
			effective_label: "1 Oct 2026, 00:00 EAT – 30 Nov 2026, 23:59 EAT",
			can_edit: true,
			can_revoke: true,
			history: [],
			diagnostics: { required_projection: [], projection_present: false, projection_orphaned: [], coverage: "", overlapping: [], obsolete_rows: {} },
		});
		const wrapper = mount(UserResponsibilitiesTab, { props: { assignmentId: "URA-2026-0003" }, global: globalMocks() });
		await flushPromises();
		expect(api.detail).toHaveBeenCalledWith("URA-2026-0003");
		expect(wrapper.find('[data-testid="kt-ura-detail"] h2').text()).toBe("Julia Njeri — Head of User Department");
		expect(wrapper.find('[data-testid="kt-ura-table"]').exists()).toBe(false);
	});

	it("keeps the filters when they match nothing, so they can be cleared", async () => {
		const wrapper = mount(UserResponsibilitiesTab, { global: globalMocks() });
		await flushPromises();
		api.listRows.mockResolvedValue({ rows: [], total: 0 });
		await wrapper.find('[data-testid="kt-ura-filter-status"]').setValue("Active");
		await flushPromises();
		expect(wrapper.find('[data-testid="kt-ura-no-match"]').exists()).toBe(true);
		expect(wrapper.find('[data-testid="kt-ura-empty"]').exists()).toBe(false);
		await wrapper.find('[data-testid="kt-ura-clear"]').trigger("click");
		expect(api.listRows.mock.calls.at(-1)[0]).toMatchObject({ status: "" });
	});

	it("never lets a stale register read overwrite a newer one", async () => {
		let releaseFirst;
		api.listRows
			.mockImplementationOnce(() => new Promise((resolve) => (releaseFirst = resolve)))
			.mockResolvedValue({ rows: [ROW], total: 1 });
		const wrapper = mount(UserResponsibilitiesTab, { global: globalMocks() });
		await flushPromises();
		// The first read is still pending; the loading state shows the filters'
		// absence, so issue the newer read through the unit link instead.
		await wrapper.setProps({ initialUnit: "OU-MOH-DHI" });
		await flushPromises();
		expect(wrapper.find('[data-testid="kt-ura-row-URA-2026-0003"]').exists()).toBe(true);
		releaseFirst({ rows: [], total: 0 });
		await flushPromises();
		expect(wrapper.find('[data-testid="kt-ura-row-URA-2026-0003"]').exists()).toBe(true);
		expect(wrapper.find('[data-testid="kt-ura-empty"]').exists()).toBe(false);
	});

	it("returns focus to Assign responsibility when the dialog is cancelled", async () => {
		const wrapper = mount(UserResponsibilitiesTab, { global: globalMocks(), attachTo: document.body });
		await flushPromises();
		const open = wrapper.find('[data-testid="kt-ura-assign-open"]');
		open.element.focus();
		await open.trigger("click");
		await flushPromises();
		expect(wrapper.find('[data-testid="kt-ura-assign"]').exists()).toBe(true);
		await wrapper.find('[data-testid="kt-ura-assign"]').trigger("keydown.esc");
		await flushPromises();
		expect(wrapper.find('[data-testid="kt-ura-assign"]').exists()).toBe(false);
		expect(document.activeElement).toBe(wrapper.find('[data-testid="kt-ura-assign-open"]').element);
		wrapper.unmount();
	});
});
