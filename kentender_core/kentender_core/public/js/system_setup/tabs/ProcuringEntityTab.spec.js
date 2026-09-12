// PLN-CHG-001 v1.18 §10.11 C01 / C01-configured / C01-conflict — the
// Procuring entity tab carries the mandatory statutory route and the county
// flag; a county/type mismatch is shown inline as the artboard's attention
// status, refused by the server before any save.
import { flushPromises, mount } from "@vue/test-utils";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { globalMocks } from "../components/spec_helpers.js";

const api = vi.hoisted(() => ({ configure: vi.fn(), update: vi.fn() }));
vi.mock("../data/siteConfigApi.js", () => ({ siteConfigApi: api }));

import ProcuringEntityTab from "./ProcuringEntityTab.vue";

const ROUTES = ["Cabinet Secretary", "County Executive Committee Member", "Board of Directors", "Council"];

function site(overrides = {}) {
	return {
		configured: true,
		procuring_entity: { pe_name: "Ministry of Health", pe_code: "PE-MOH", pe_type: "National Government Ministry", ppra_registration: "PPRA/PE/2019/0114", timezone: "Africa/Nairobi", statutory_approval_route: "Cabinet Secretary", entity_is_county: false, expected_version: "v1" },
		pe_types: ["National Government Ministry", "County Government"],
		timezones: ["Africa/Nairobi"],
		statutory_approval_routes: ROUTES,
		root_unit: { name: "Ministry of Health", code: "OU-MOH-00001" },
		...overrides,
	};
}

describe("ProcuringEntityTab", () => {
	beforeEach(() => vi.clearAllMocks());

	it("configured: the route select offers exactly the four routes with the help text, and the county checkbox follows the record", () => {
		const wrapper = mount(ProcuringEntityTab, { props: { site: site() }, global: globalMocks() });
		const options = wrapper.findAll('[data-testid="kt-setup-pe-route"] option').map((o) => o.text());
		expect(options).toEqual(ROUTES);
		expect(wrapper.find('[data-testid="kt-setup-pe-route"]').element.value).toBe("Cabinet Secretary");
		expect(wrapper.text()).toContain("Select the authority that approves this entity's Annual Procurement Plan.");
		expect(wrapper.find('[data-testid="kt-setup-pe-county"]').element.checked).toBe(false);
		expect(wrapper.find('[data-testid="kt-setup-pe-code-ro"]').text()).toBe("PE-MOH");
		expect(wrapper.find('[data-testid="kt-setup-pe-submit"]').text()).toBe("Save changes");
		expect(wrapper.find('[data-testid="kt-setup-pe-submit"]').attributes("disabled")).toBeDefined();
	});

	it("first run requires a route before Configure site enables and sends route and county", async () => {
		api.configure.mockResolvedValue({ configured: true });
		const wrapper = mount(ProcuringEntityTab, { props: { site: site({ configured: false, procuring_entity: null, root_unit: null }) }, global: globalMocks() });
		await wrapper.find('[data-testid="kt-setup-pe-code"]').setValue("PE-X");
		await wrapper.find('[data-testid="kt-setup-pe-name"]').setValue("Test Entity");
		await wrapper.find('[data-testid="kt-setup-pe-type"]').setValue("County Government");
		expect(wrapper.find('[data-testid="kt-setup-pe-submit"]').attributes("disabled")).toBeDefined();
		await wrapper.find('[data-testid="kt-setup-pe-route"]').setValue("County Executive Committee Member");
		await wrapper.find('[data-testid="kt-setup-pe-county"]').setValue(true);
		expect(wrapper.find('[data-testid="kt-setup-pe-submit"]').attributes("disabled")).toBeUndefined();
		await wrapper.find('[data-testid="kt-setup-pe-submit"]').trigger("click");
		await flushPromises();
		expect(api.configure.mock.calls[0][0]).toMatchObject({ pe_code: "PE-X", statutory_approval_route: "County Executive Committee Member", entity_is_county: 1 });
	});

	it("a county/type mismatch is shown as the C01-conflict attention status, not the generic error line", async () => {
		api.update.mockRejectedValue(new Error("County applicability does not match the entity details. Review the configuration."));
		const wrapper = mount(ProcuringEntityTab, { props: { site: site() }, global: globalMocks() });
		await wrapper.find('[data-testid="kt-setup-pe-type"]').setValue("County Government");
		await wrapper.find('[data-testid="kt-setup-pe-submit"]').trigger("click");
		await flushPromises();
		expect(api.update.mock.calls[0][0]).toMatchObject({ pe_type: "County Government", entity_is_county: false, statutory_approval_route: "Cabinet Secretary" });
		const conflict = wrapper.find('[data-testid="kt-setup-pe-county-conflict"]');
		expect(conflict.exists()).toBe(true);
		expect(conflict.classes()).toEqual(expect.arrayContaining(["kt-status", "is-attention"]));
		expect(conflict.text()).toBe("County applicability does not match the entity details. Review the configuration.");
		expect(wrapper.find('[data-testid="kt-setup-pe-error"]').exists()).toBe(false);
	});
});
