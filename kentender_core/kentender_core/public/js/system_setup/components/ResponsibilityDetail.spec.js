// AUTH §14.4 as amended by the owner on 21 Sep 2026: an assignment that has
// not started yet may be changed; one in force may only be revoked; Expired
// and Revoked are read-only. Both actions appear only because the server's
// detail projection says so, and every change is an append-only history row.
import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";
import { globalMocks } from "./spec_helpers.js";

import ResponsibilityDetail from "./ResponsibilityDetail.vue";

function assignment(overrides = {}) {
	return {
		assignment: "URA-00009",
		user: "peter.kimani@moh.example.test",
		user_full_name: "Dr Peter Kimani",
		business_role: "Head of User Department",
		scope_type: "Organisation Unit",
		organisation_unit: "OU-MOH-00001",
		organisation_unit_path: "Ministry of Health › Digital Health",
		organisation_unit_label: "Digital Health",
		coverage: "This unit only",
		appointment_type: "Permanent",
		authority_reference: "",
		effective_from: "2026-12-01 00:00:00",
		effective_to: "",
		effective_label: "From 1 Dec 2026, 00:00 EAT · No scheduled end",
		status: "Scheduled",
		assigned_by: "Administrator",
		assigned_at_label: "1 Sep 2026, 09:00 EAT",
		revoked_by: "",
		revoked_at_label: "",
		revocation_reason: "",
		can_revoke: true,
		can_edit: true,
		expected_version: "2026-09-21 10:00:00",
		history: [
			{ when: "1 Sep 2026, 09:00 EAT", actor: "Administrator", event: "Responsibility assigned", detail: "" },
		],
		diagnostics: {
			required_projection: ["Head of User Department"],
			projection_present: true,
			projection_missing: [],
			projection_orphaned: [],
			coverage: "This unit only",
			overlapping: [],
			obsolete_rows: {},
		},
		...overrides,
	};
}

function mountDetail(overrides) {
	return mount(ResponsibilityDetail, { props: { assignment: assignment(overrides) }, global: globalMocks() });
}

describe("ResponsibilityDetail", () => {
	it("offers Edit and Revoke for a scheduled assignment, and Edit asks the parent to open the dialog", async () => {
		const wrapper = mountDetail();
		expect(wrapper.find('[data-testid="kt-ura-open-edit"]').text()).toBe("Edit scheduled assignment");
		expect(wrapper.find('[data-testid="kt-ura-open-revoke"]').exists()).toBe(true);
		await wrapper.find('[data-testid="kt-ura-open-edit"]').trigger("click");
		expect(wrapper.emitted("edit")).toHaveLength(1);
	});

	it("offers only Revoke once in force, and nothing once revoked", () => {
		const active = mountDetail({ status: "Active", can_edit: false, can_revoke: true });
		expect(active.find('[data-testid="kt-ura-open-edit"]').exists()).toBe(false);
		expect(active.find('[data-testid="kt-ura-open-revoke"]').exists()).toBe(true);

		const revoked = mountDetail({ status: "Revoked", can_edit: false, can_revoke: false });
		expect(revoked.find('[data-testid="kt-ura-open-edit"]').exists()).toBe(false);
		expect(revoked.find('[data-testid="kt-ura-open-revoke"]').exists()).toBe(false);
		expect(revoked.find(".kt-action-bar").exists()).toBe(false);
	});

	it("renders a change in the administrative history with what moved", () => {
		const wrapper = mountDetail({
			history: [
				{ when: "1 Sep 2026, 09:00 EAT", actor: "Administrator", event: "Responsibility assigned", detail: "" },
				{
					when: "21 Sep 2026, 16:10 EAT",
					actor: "Administrator",
					event: "Scheduled assignment changed",
					detail: "Effective from: 1 Dec 2026, 00:00 EAT → now",
				},
			],
		});
		const rows = wrapper.findAll('[data-testid="kt-ura-history"] tbody tr');
		expect(rows).toHaveLength(2);
		expect(rows[1].text()).toContain("Scheduled assignment changed");
		expect(rows[1].find(".kt-history-detail").text()).toBe("Effective from: 1 Dec 2026, 00:00 EAT → now");
		expect(rows[0].find(".kt-history-detail").exists()).toBe(false);
	});
});
