// CFG-CHG-002 v0.14 §10.5 (C03A #add/#edit/#duplicate; tracker CFG14-5C) —
// the funding-source dialog: a name and an explicit "Available for new
// selection" Yes/No choice; the server owns the rules.
import { flushPromises, mount } from "@vue/test-utils";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { globalMocks } from "./spec_helpers.js";

const api = vi.hoisted(() => ({ addFundingSource: vi.fn(), updateFundingSource: vi.fn() }));
vi.mock("../data/procurementSettingsApi.js", () => ({ procurementSettingsApi: api }));

import FundingSourceDialog from "./FundingSourceDialog.vue";

describe("FundingSourceDialog", () => {
	beforeEach(() => vi.clearAllMocks());

	it("edits an existing source with the artboard's two fields and saves through the update command", async () => {
		api.updateFundingSource.mockResolvedValue({ name: "Development partner", enabled: false });
		const wrapper = mount(FundingSourceDialog, {
			props: { source: { name: "Development partner", label: "Development partner", enabled: true, referenced: false, expected_version: "v2" } },
			global: globalMocks(),
		});
		expect(wrapper.find(".kt-dialog-title").text()).toBe("Edit funding source");
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
		const creating = mount(FundingSourceDialog, { props: { creating: true }, global: globalMocks() });
		expect(creating.find(".kt-dialog-title").text()).toBe("Add funding source");
		expect(creating.find('[data-testid="kt-fs-save"]').text()).toBe("Add funding source");
		expect(creating.find('[data-testid="kt-fs-save"]').attributes("disabled")).toBeDefined();
		await creating.find('[data-testid="kt-fs-name"]').setValue("Donor");
		await creating.find('[data-testid="kt-fs-save"]').trigger("click");
		await flushPromises();
		expect(api.addFundingSource).toHaveBeenCalledWith("Donor");

		const referenced = mount(FundingSourceDialog, {
			props: { source: { name: "Government of Kenya", label: "Government of Kenya", enabled: true, referenced: true, expected_version: "v1" } },
			global: globalMocks(),
		});
		// A referenced source's name is not offered for editing; its
		// availability still is, and takes the focus.
		expect(referenced.find('[data-testid="kt-fs-locked"]').text()).toBe("This source is referenced by a Budget line and cannot be renamed.");
		expect(referenced.find('[data-testid="kt-fs-name"]').attributes("disabled")).toBeDefined();
	});

	it("is a modal dialog that takes focus on its first field and closes on Escape", async () => {
		const wrapper = mount(FundingSourceDialog, { props: { creating: true }, global: globalMocks(), attachTo: document.body });
		await flushPromises();
		const dialog = wrapper.find('[role="dialog"]');
		expect(dialog.attributes("aria-modal")).toBe("true");
		expect(dialog.attributes("aria-label")).toBe("Add funding source");
		expect(document.activeElement?.getAttribute("data-testid")).toBe("kt-fs-name");
		await dialog.trigger("keydown", { key: "Escape" });
		expect(wrapper.emitted("cancel")).toBeTruthy();
		wrapper.unmount();

		const locked = mount(FundingSourceDialog, {
			props: { source: { name: "GoK", label: "Government of Kenya", enabled: true, referenced: true, expected_version: "v1" } },
			global: globalMocks(),
			attachTo: document.body,
		});
		await flushPromises();
		expect(document.activeElement?.closest('[data-testid="kt-fs-enabled-yes"]')).toBeTruthy();
		locked.unmount();
	});

	it("a refused save is shown inline as a notice, never a Frappe pop-up", async () => {
		// The list said unreferenced; a Budget line took it since (the server decides).
		api.updateFundingSource.mockRejectedValue(new Error("This catalogue entry is referenced by existing records and cannot be renamed or removed."));
		const wrapper = mount(FundingSourceDialog, {
			props: { source: { name: "Government of Kenya", label: "Government of Kenya", enabled: true, referenced: false, expected_version: "v1" } },
			global: globalMocks(),
		});
		await wrapper.find('[data-testid="kt-fs-name"]').setValue("GoK");
		await wrapper.find('[data-testid="kt-fs-save"]').trigger("click");
		await flushPromises();
		const notice = wrapper.find('[data-testid="kt-fs-error"]');
		expect(notice.classes()).toEqual(expect.arrayContaining(["kt-notice", "is-critical"]));
		expect(notice.text()).toContain("cannot be renamed");
		expect(wrapper.emitted("saved")).toBeFalsy();
	});

	it("a name that already exists is the exact duplicate defect, with Add refused before submit", async () => {
		const wrapper = mount(FundingSourceDialog, {
			props: {
				creating: true,
				existing: [{ name: "Government of Kenya", label: "Government of Kenya", enabled: true }],
			},
			global: globalMocks(),
		});
		await wrapper.find('[data-testid="kt-fs-name"]').setValue("  government of kenya  ");
		const duplicate = wrapper.find('[data-testid="kt-fs-duplicate"]');
		expect(duplicate.text()).toBe("Duplicate. A funding source with this name already exists.");
		expect(duplicate.find(".kt-notice-icon").exists()).toBe(true);
		expect(wrapper.find('[data-testid="kt-fs-name"]').attributes("aria-invalid")).toBe("true");
		expect(wrapper.find('[data-testid="kt-fs-save"]').attributes("disabled")).toBeDefined();

		// The source being edited is not its own duplicate.
		const editing = mount(FundingSourceDialog, {
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
		const wrapper = mount(FundingSourceDialog, { props: { creating: true }, global: globalMocks() });
		await wrapper.find('[data-testid="kt-fs-name"]').setValue("Donor");
		await wrapper.find('[data-testid="kt-fs-enabled-no"] input').trigger("change");
		await wrapper.find('[data-testid="kt-fs-save"]').trigger("click");
		await flushPromises();
		expect(api.addFundingSource).toHaveBeenCalledWith("Donor");
		expect(api.updateFundingSource).toHaveBeenCalledWith("Donor", { enabled: false }, "");
	});
});
