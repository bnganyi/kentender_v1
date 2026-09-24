import { beforeEach, describe, expect, it, vi } from "vitest";
import { flushPromises, mount } from "@vue/test-utils";

import RequirementsTask from "./RequirementsTask.vue";
import { context, requirements } from "./fixtures.js";

beforeEach(() => window.sessionStorage.clear());

describe("RequirementsTask (REQ-DES-05)", () => {
	it("Review required: the issue leads, Use selected sends the whole visible selection once", async () => {
		const applyPackage = vi.fn().mockResolvedValue({ ok: true });
		const { global } = context({ api: { applyPackage } });
		const w = mount(RequirementsTask, { props: { view: requirements() }, global });
		expect(w.find('[data-testid="req-requirements-issue"]').text()).toBe("Review the standard laptop requirements before continuing.");
		expect(w.find('[data-testid="req-review-state"]').text()).toBe("Review required");
		expect(w.findAll('[data-testid="req-technical-row"]')).toHaveLength(11);
		expect(w.findAll('[data-testid="req-acceptance-row"]')).toHaveLength(5);
		expect(w.find('[data-testid="req-continue"]').attributes("disabled")).toBeDefined();
		// clearing a suggestion keeps the row visible and unselects it
		await w.findAll('[data-testid="req-technical-clear"]')[4].trigger("click");
		expect(w.findAll("tr.is-cleared")).toHaveLength(1);
		await w.find('[data-testid="req-use-selected"]').trigger("click");
		await flushPromises();
		expect(applyPackage).toHaveBeenCalledTimes(1);
		const sent = applyPackage.mock.calls[0][0];
		expect(sent.technical_rows).toHaveLength(11);
		expect(sent.technical_rows.filter((r) => !r.selected).map((r) => r.characteristic_key)).toEqual(["storage_type"]);
		expect(sent.acceptance_rows).toHaveLength(5);
		expect(sent).toMatchObject({ profile_key: "LAPTOP-REQUIREMENTS-V1", proposal_digest: "abc", expected_record_version: 2 });
		expect(sent.support_values.minimum_warranty_months).toBe("36");
		expect(sent.technical_rows.find((r) => r.characteristic_key === "network_connectivity").value).toEqual(["Wi-Fi 6", "Bluetooth 5 or later"]);
	});

	it("clearing every acceptance check disables Use selected requirements", async () => {
		const { global } = context();
		const w = mount(RequirementsTask, { props: { view: requirements() }, global });
		for (const button of w.findAll('[data-testid="req-acceptance-clear"]')) await button.trigger("click");
		expect(w.find('[data-testid="req-use-selected"]').attributes("disabled")).toBeDefined();
	});

	it("Reviewed: no issue, no Use column, Edit/Remove per row, Continue to review enabled", () => {
		const { global } = context();
		const w = mount(RequirementsTask, { props: { view: requirements("COMPLETE") }, global });
		expect(w.find('[data-testid="req-requirements-issue"]').exists()).toBe(false);
		expect(w.find('[data-testid="req-review-state"]').text()).toBe("Reviewed");
		expect(w.text()).not.toContain("Review required");
		expect(w.find('[data-testid="req-technical-remove"]').exists()).toBe(true);
		expect(w.find('[data-testid="req-technical-clear"]').exists()).toBe(false);
		expect(w.find('[data-testid="req-use-selected"]').exists()).toBe(false);
		expect(w.find('[data-testid="req-continue"]').attributes("disabled")).toBeUndefined();
	});

	it("a refused warranty is bound to its field and every other value is kept", async () => {
		const { global, ctx } = context();
		const w = mount(RequirementsTask, { props: { view: requirements() }, global });
		await w.find('[data-testid="req-support-warranty"]').setValue("");
		ctx.commandError.value = { label: "apply-package", code: "REQ_CONTROL_INVALID", message: "Enter the minimum warranty in months.", detail: { fields: { minimum_warranty_months: "Enter the minimum warranty in months." } } };
		await flushPromises();
		expect(w.find(".req-field-error").text()).toBe("Enter the minimum warranty in months.");
		expect(w.find('[data-testid="req-package-error"]').exists()).toBe(false);
		expect(w.findAll('[data-testid="req-technical-row"]')).toHaveLength(11);
	});
});
