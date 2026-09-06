// AUTH §18.2 items 20/22 — the assign dialog's field variants come only from
// the selected registry role's scope and appointment (§14.3), and the primary
// button stays disabled with a visible reason until the server preview is ok.
// The Responsibility and Organisation Unit controls are the AUTH-DES-04
// listboxes (role beside its scope tag, unit as its full path).
import { flushPromises, mount } from "@vue/test-utils";
import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("../data/responsibilityApi.js", () => ({
	responsibilityApi: {
		searchUsers: vi.fn(async () => [{ id: "grace.wanjiku@moh.example.test", label: "Grace Wanjiku" }]),
		preview: vi.fn(async () => ({
			ok: false,
			problems: [{ field: "user", message: "Select a user." }],
			conflict: null,
			summary: "",
			summary_parts: null,
			descendant_count: 0,
			included_units: [],
		})),
	},
}));

import AssignDialog from "./AssignDialog.vue";
import { responsibilityApi } from "../data/responsibilityApi.js";
import { globalMocks } from "./spec_helpers.js";

const RESPONSIBILITIES = [
	{ business_role: "Departmental Author", scope_type: "Organisation Unit", requires_organisation_unit: true },
	{ business_role: "Procurement Planner", scope_type: "Site-wide", requires_organisation_unit: false },
];
const UNITS = [
	{ id: "OU-MOH-00001", label: "Digital Health", path_label: "Ministry of Health › Digital Health", parent: "" },
];

function mountDialog() {
	return mount(AssignDialog, {
		props: { responsibilities: RESPONSIBILITIES, organisationUnits: UNITS },
		global: globalMocks(),
	});
}

async function pickRole(wrapper, role) {
	await wrapper.find('[data-testid="kt-ura-role"]').trigger("click");
	await wrapper.find(`[data-testid="kt-ura-role-option-${role}"]`).trigger("click");
	await flushPromises();
}

beforeEach(() => {
	vi.clearAllMocks();
});

describe("AssignDialog", () => {
	it("shows the Organisation Unit control only for an OU-scoped role", async () => {
		const wrapper = mountDialog();
		await flushPromises();
		expect(wrapper.find('[data-testid="kt-ura-ou"]').exists()).toBe(false);

		await pickRole(wrapper, "Departmental Author");
		expect(wrapper.find('[data-testid="kt-ura-ou"]').exists()).toBe(true);

		await pickRole(wrapper, "Procurement Planner");
		expect(wrapper.find('[data-testid="kt-ura-ou"]').exists()).toBe(false);
	});

	it("renders the role beside its scope tag and units as their full path", async () => {
		const wrapper = mountDialog();
		await pickRole(wrapper, "Departmental Author");
		const roleControl = wrapper.find('[data-testid="kt-ura-role"]');
		expect(roleControl.text()).toContain("Departmental Author");
		expect(roleControl.find(".kt-tag").text()).toBe("Organisation Unit");

		await wrapper.find('[data-testid="kt-ura-ou-toggle"]').trigger("click");
		expect(wrapper.find('[data-testid="kt-ura-ou-option-OU-MOH-00001"]').text()).toContain(
			"Ministry of Health › Digital Health"
		);
	});

	it("shows Effective to and Authority reference only for Acting", async () => {
		const wrapper = mountDialog();
		await flushPromises();
		expect(wrapper.find('[data-testid="kt-ura-to"]').exists()).toBe(false);
		expect(wrapper.find('[data-testid="kt-ura-authority"]').exists()).toBe(false);

		await wrapper.find('[data-testid="kt-ura-appointment-acting"]').setValue(true);
		expect(wrapper.find('[data-testid="kt-ura-to"]').exists()).toBe(true);
		expect(wrapper.find('[data-testid="kt-ura-authority"]').exists()).toBe(true);
	});

	it("never renders a Procuring Entity, Fiscal Year or capability control", async () => {
		const wrapper = mountDialog();
		await flushPromises();
		const html = wrapper.html();
		expect(html).not.toContain("Procuring Entity");
		expect(html).not.toContain("Fiscal Year");
		expect(html).not.toContain("capability");
	});

	it("keeps the primary disabled with a visible reason until the preview is ok", async () => {
		const wrapper = mountDialog();
		await flushPromises();
		await pickRole(wrapper, "Procurement Planner");
		expect(wrapper.find('[data-testid="kt-ura-assign-confirm"]').attributes("disabled")).toBeDefined();
		expect(wrapper.find(".kt-blocked").text()).toContain("Complete every required field to continue");
	});

	it("renders the labelled server summary with bolded role and scope, the descendant note and the exclusive-office conflict verbatim", async () => {
		responsibilityApi.preview.mockResolvedValue({
			ok: false,
			problems: [],
			conflict: {
				assignment: "URA-00002",
				kind: "exclusive_office",
				heading: "This office is already held",
				message: "Dr Peter Kimani holds this responsibility for this scope until 30 Nov 2026.",
			},
			summary: "Julia Njeri will be Head of User Department for Digital Health from now with no scheduled end.",
			summary_parts: {
				user: "Julia Njeri",
				role: "Head of User Department",
				scope: "Digital Health",
				period: "from now with no scheduled end",
			},
			descendant_count: 1,
			included_units: ["Digital Health"],
		});
		const wrapper = mountDialog();
		await pickRole(wrapper, "Departmental Author");
		const summary = wrapper.find('[data-testid="kt-ura-summary"]');
		expect(summary.find(".kt-label").text()).toBe("Responsibility summary");
		const bolded = summary.findAll("strong").map((node) => node.text());
		expect(bolded).toContain("Head of User Department");
		expect(bolded).toContain("Digital Health");
		expect(summary.text()).toContain("This includes 1 subordinate organisation unit.");
		const conflict = wrapper.find('[data-testid="kt-ura-conflict"]');
		expect(conflict.text()).toContain("This office is already held");
		expect(conflict.text()).toContain("Dr Peter Kimani");
		expect(wrapper.find(".kt-blocked").text()).toContain("Resolve the conflicting assignment to continue");
	});
});
