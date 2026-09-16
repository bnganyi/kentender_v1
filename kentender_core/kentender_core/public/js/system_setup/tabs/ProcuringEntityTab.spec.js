// CFG-CHG-002 v0.11 §10.2/§11.2 (C01) — the Procuring entity tab carries the
// mandatory statutory route (plain-language label) and an explicit Yes/No
// county choice (never a checkbox); a county/type mismatch is its own
// critical notice, refused by the server before any save. Configured mode
// also carries the Setup record and Plan approval authority sections.
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
		procuring_entity: {
			pe_name: "Ministry of Health",
			pe_code: "PE-MOH",
			pe_type: "National Government Ministry",
			ppra_registration: "PPRA/PE/2019/0114",
			timezone: "Africa/Nairobi",
			statutory_approval_route: "Cabinet Secretary",
			entity_is_county: false,
			configured_by: "Administrator",
			configured_at_label: "29 Jun 2026, 10:10 EAT",
			approval_applicability: { result: "Verification required", reference: "" },
			expected_version: "v1",
		},
		pe_types: ["National Government Ministry", "County Government"],
		timezones: ["Africa/Nairobi"],
		statutory_approval_routes: ROUTES,
		root_unit: { name: "Ministry of Health", code: "PE-MOH" },
		...overrides,
	};
}

describe("ProcuringEntityTab", () => {
	beforeEach(() => vi.clearAllMocks());

	it("configured: the route select offers exactly the four routes with plain wording, the county radio follows the record, and the timezone reads read-only", () => {
		const wrapper = mount(ProcuringEntityTab, { props: { site: site() }, global: globalMocks() });
		const options = wrapper.findAll('[data-testid="kt-setup-pe-route"] option').map((o) => o.text());
		expect(options).toEqual(ROUTES);
		expect(wrapper.find('[data-testid="kt-setup-pe-route"]').element.value).toBe("Cabinet Secretary");
		expect(wrapper.text()).toContain("Who approves the Annual Procurement Plan?");
		expect(wrapper.find('[data-testid="kt-setup-pe-county-yes"] input').element.checked).toBe(false);
		expect(wrapper.find('[data-testid="kt-setup-pe-county-no"] input').element.checked).toBe(true);
		expect(wrapper.find('[data-testid="kt-setup-pe-tz"]').text()).toBe("Africa/Nairobi");
		expect(wrapper.find('[data-testid="kt-setup-pe-code-ro"]').text()).toBe("PE-MOH");
		expect(wrapper.find('[data-testid="kt-setup-pe-submit"]').text()).toBe("Save changes");
		expect(wrapper.find('[data-testid="kt-setup-pe-submit"]').attributes("disabled")).toBeDefined();
	});

	it("configured: shows the Setup record facts and the Plan approval authority readiness, never a generic Ready badge", () => {
		const wrapper = mount(ProcuringEntityTab, { props: { site: site() }, global: globalMocks() });
		const record = wrapper.find('[data-testid="kt-setup-pe-record"]');
		expect(record.text()).toContain("Administrator");
		expect(record.text()).toContain("29 Jun 2026, 10:10 EAT");
		expect(record.text()).toContain("Ministry of Health");
		expect(record.text()).toContain("PE-MOH");
		const approval = wrapper.find('[data-testid="kt-setup-pe-approval"]');
		const status = wrapper.find('[data-testid="kt-setup-pe-approval-status"]');
		expect(status.text()).toBe("Source check needed");
		expect(status.classes()).toEqual(expect.arrayContaining(["kt-status", "is-attention"]));
		expect(approval.text()).toContain("The approval authority's supporting evidence must be completed before Plan approval.");
		expect(approval.text()).toContain("View procurement rules");
	});

	it("configured with a Verified approval rule shows the live status, and Configuration conflict shows critical", () => {
		const verified = mount(ProcuringEntityTab, {
			props: { site: site({ procuring_entity: { ...site().procuring_entity, approval_applicability: { result: "Verified", reference: "REF-1" } } }) },
			global: globalMocks(),
		});
		expect(verified.find('[data-testid="kt-setup-pe-approval-status"]').classes()).toEqual(expect.arrayContaining(["kt-status", "is-live"]));
		expect(verified.find('[data-testid="kt-setup-pe-approval-status"]').text()).toBe("Sources verified");

		const conflict = mount(ProcuringEntityTab, {
			props: { site: site({ procuring_entity: { ...site().procuring_entity, approval_applicability: { result: "Configuration conflict", reference: "REF-2" } } }) },
			global: globalMocks(),
		});
		expect(conflict.find('[data-testid="kt-setup-pe-approval-status"]').classes()).toEqual(expect.arrayContaining(["kt-status", "is-critical"]));
		expect(conflict.find('[data-testid="kt-setup-pe-approval-status"]').text()).toBe("Configuration conflict");
	});

	it("clicking View procurement rules emits navigate with the procurement-rules section", async () => {
		const wrapper = mount(ProcuringEntityTab, { props: { site: site() }, global: globalMocks() });
		await wrapper.find('[data-testid="kt-setup-pe-approval-link"]').trigger("click");
		expect(wrapper.emitted("navigate")).toEqual([["procurement-rules"]]);
	});

	it("first run: the card itself is titled Configure this site, and Configure site enables only once the route and an explicit county answer are set", async () => {
		const wrapper = mount(ProcuringEntityTab, {
			props: { site: site({ configured: false, procuring_entity: null, root_unit: null }) },
			global: globalMocks(),
		});
		expect(wrapper.find('[data-testid="kt-setup-pe-card"]').find(".kt-card-title").text()).toBe("Configure this site");
		expect(wrapper.text()).toContain("Other four tabs unavailable until this save succeeds.");
		expect(wrapper.find('[data-testid="kt-setup-pe-county-yes"] input').element.checked).toBe(false);
		expect(wrapper.find('[data-testid="kt-setup-pe-county-no"] input').element.checked).toBe(false);

		api.configure.mockResolvedValue({ configured: true });
		await wrapper.find('[data-testid="kt-setup-pe-code"]').setValue("PE-X");
		await wrapper.find('[data-testid="kt-setup-pe-name"]').setValue("Test Entity");
		await wrapper.find('[data-testid="kt-setup-pe-type"]').setValue("County Government");
		await wrapper.find('[data-testid="kt-setup-pe-route"]').setValue("County Executive Committee Member");
		expect(wrapper.find('[data-testid="kt-setup-pe-submit"]').attributes("disabled")).toBeDefined();
		await wrapper.find('[data-testid="kt-setup-pe-county-yes"] input').trigger("change");
		expect(wrapper.find('[data-testid="kt-setup-pe-submit"]').attributes("disabled")).toBeUndefined();
		await wrapper.find('[data-testid="kt-setup-pe-submit"]').trigger("click");
		await flushPromises();
		expect(api.configure.mock.calls[0][0]).toMatchObject({
			pe_code: "PE-X",
			statutory_approval_route: "County Executive Committee Member",
			entity_is_county: 1,
		});
	});

	it("a county/type mismatch is shown as its own critical notice, not folded into the generic error", async () => {
		api.update.mockRejectedValue(new Error("The county answer does not match the entity details."));
		const wrapper = mount(ProcuringEntityTab, { props: { site: site() }, global: globalMocks() });
		await wrapper.find('[data-testid="kt-setup-pe-type"]').setValue("County Government");
		await wrapper.find('[data-testid="kt-setup-pe-submit"]').trigger("click");
		await flushPromises();
		expect(api.update.mock.calls[0][0]).toMatchObject({ pe_type: "County Government", entity_is_county: false, statutory_approval_route: "Cabinet Secretary" });
		const conflict = wrapper.find('[data-testid="kt-setup-pe-county-conflict"]');
		expect(conflict.exists()).toBe(true);
		expect(conflict.classes()).toEqual(expect.arrayContaining(["kt-notice", "is-critical"]));
		expect(conflict.text()).toBe("Conflict. The county answer does not match the entity details.");
		expect(wrapper.find('[data-testid="kt-setup-pe-error"]').exists()).toBe(false);
	});
});
