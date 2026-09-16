// CFG-CHG-002 v0.11 §10.5 (C03-A) — funding source name and an explicit
// "Available for new selection" Yes/No choice; server owns the rules.
import { flushPromises, mount } from "@vue/test-utils";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { globalMocks } from "./spec_helpers.js";

const api = vi.hoisted(() => ({ addFundingSource: vi.fn(), updateFundingSource: vi.fn() }));
vi.mock("../data/procurementSettingsApi.js", () => ({ procurementSettingsApi: api }));

import FundingSourceEditor from "./FundingSourceEditor.vue";

describe("FundingSourceEditor", () => {
	beforeEach(() => vi.clearAllMocks());

	it("edits an existing source with the artboard's two fields and saves through the update command", async () => {
		api.updateFundingSource.mockResolvedValue({ name: "Development partner", enabled: false });
		const wrapper = mount(FundingSourceEditor, {
			props: { source: { name: "Development partner", label: "Development partner", enabled: true, referenced: false, expected_version: "v2" } },
			global: globalMocks(),
		});
		expect(wrapper.find(".kt-section-title").text()).toBe("Edit funding source");
		expect(wrapper.find('[data-testid="kt-fs-name"]').element.value).toBe("Development partner");
		expect(wrapper.find('[data-testid="kt-fs-enabled-yes"] input').element.checked).toBe(true);
		expect(wrapper.text()).toContain("Turning this off prevents new selection; existing records keep their funding history.");
		await wrapper.find('[data-testid="kt-fs-enabled-no"] input').trigger("change");
		await wrapper.find('[data-testid="kt-fs-save"]').trigger("click");
		await flushPromises();
		expect(api.updateFundingSource).toHaveBeenCalledWith("Development partner", { label: "Development partner", enabled: false }, "v2");
		expect(wrapper.emitted("saved")).toBeTruthy();
	});

	it("creating uses the add command and a referenced source explains it cannot be renamed", async () => {
		api.addFundingSource.mockResolvedValue({ name: "Donor", created: true });
		const creating = mount(FundingSourceEditor, { props: { creating: true }, global: globalMocks() });
		expect(creating.find(".kt-section-title").text()).toBe("Add funding source");
		expect(creating.find('[data-testid="kt-fs-save"]').text()).toBe("Add funding source");
		expect(creating.find('[data-testid="kt-fs-save"]').attributes("disabled")).toBeDefined();
		await creating.find('[data-testid="kt-fs-name"]').setValue("Donor");
		await creating.find('[data-testid="kt-fs-save"]').trigger("click");
		await flushPromises();
		expect(api.addFundingSource).toHaveBeenCalledWith("Donor");

		const referenced = mount(FundingSourceEditor, {
			props: { source: { name: "Government of Kenya", label: "Government of Kenya", enabled: true, referenced: true, expected_version: "v1" } },
			global: globalMocks(),
		});
		expect(referenced.text()).toContain("referenced by a Budget line and cannot be renamed");
	});

	it("a refused save is shown inline, never a modal", async () => {
		api.updateFundingSource.mockRejectedValue(new Error("This catalogue entry is referenced by existing records and cannot be renamed or removed."));
		const wrapper = mount(FundingSourceEditor, {
			props: { source: { name: "Government of Kenya", label: "Government of Kenya", enabled: true, referenced: true, expected_version: "v1" } },
			global: globalMocks(),
		});
		await wrapper.find('[data-testid="kt-fs-name"]').setValue("GoK");
		await wrapper.find('[data-testid="kt-fs-save"]').trigger("click");
		await flushPromises();
		expect(wrapper.find('[data-testid="kt-fs-error"]').text()).toContain("cannot be renamed");
		expect(wrapper.emitted("saved")).toBeFalsy();
	});

	it("a name that already exists is the exact duplicate defect, with Add refused before submit", async () => {
		const wrapper = mount(FundingSourceEditor, {
			props: {
				creating: true,
				existing: [{ name: "Government of Kenya", label: "Government of Kenya", enabled: true }],
			},
			global: globalMocks(),
		});
		await wrapper.find('[data-testid="kt-fs-name"]').setValue("  government of kenya  ");
		expect(wrapper.find('[data-testid="kt-fs-duplicate"]').text()).toBe(
			"Duplicate. A funding source with this name already exists."
		);
		expect(wrapper.find('[data-testid="kt-fs-save"]').attributes("disabled")).toBeDefined();

		// The source being edited is not its own duplicate.
		const editing = mount(FundingSourceEditor, {
			props: {
				source: { name: "Government of Kenya", label: "Government of Kenya", enabled: true, referenced: false, expected_version: "v1" },
				existing: [{ name: "Government of Kenya", label: "Government of Kenya", enabled: true }],
			},
			global: globalMocks(),
		});
		expect(editing.find('[data-testid="kt-fs-duplicate"]').exists()).toBe(false);
	});

	it("creating an unavailable source disables it through the command that owns availability", async () => {
		api.addFundingSource.mockResolvedValue({ name: "Donor", created: true });
		api.updateFundingSource.mockResolvedValue({ name: "Donor", enabled: false });
		const wrapper = mount(FundingSourceEditor, { props: { creating: true }, global: globalMocks() });
		await wrapper.find('[data-testid="kt-fs-name"]').setValue("Donor");
		await wrapper.find('[data-testid="kt-fs-enabled-no"] input').trigger("change");
		await wrapper.find('[data-testid="kt-fs-save"]').trigger("click");
		await flushPromises();
		expect(api.addFundingSource).toHaveBeenCalledWith("Donor");
		expect(api.updateFundingSource).toHaveBeenCalledWith("Donor", { enabled: false }, "");
	});
});
