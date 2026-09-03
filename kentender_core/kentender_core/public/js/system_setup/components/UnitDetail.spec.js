// AUTH §18.2 item 22 — the selected-unit panel renders only the actions the
// server allowed (§9.2), never a client-side status rule.
import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";
import UnitDetail from "./UnitDetail.vue";
import { globalMocks } from "./spec_helpers.js";

function unit(overrides = {}) {
	return {
		id: "OU-MOH-00001",
		code: "OU-MOH-00001",
		name: "Digital Health",
		is_root: false,
		status: "Active",
		path: ["Ministry of Health", "Digital Health"],
		descendant_count: 0,
		active_assignments: 0,
		expected_version: "x",
		actions: { add_child: true, rename: true, deactivate: true, reactivate: false },
		...overrides,
	};
}

function mountDetail(overrides) {
	return mount(UnitDetail, { props: { unit: unit(overrides) }, global: globalMocks() });
}

describe("UnitDetail", () => {
	it("renders the AUTH-DES-01 labelled rows: name, code, path, included units", () => {
		const wrapper = mountDetail();
		expect(wrapper.text()).toContain("Unit name");
		expect(wrapper.text()).toContain("Digital Health");
		expect(wrapper.text()).toContain("OU-MOH-00001");
		expect(wrapper.text()).toContain("Ministry of Health › Digital Health");
		expect(wrapper.text()).toContain("No descendants");
	});

	it("included units count descendants as the artboard states them", () => {
		expect(mountDetail({ descendant_count: 1 }).text()).toContain("1 descendant");
		expect(mountDetail({ descendant_count: 3 }).text()).toContain("3 descendants");
	});

	it("buttons follow the server actions map exactly", () => {
		const wrapper = mountDetail({
			actions: { add_child: false, rename: false, deactivate: false, reactivate: true },
		});
		expect(wrapper.find('[data-testid="kt-ou-add"]').exists()).toBe(false);
		expect(wrapper.find('[data-testid="kt-ou-rename"]').exists()).toBe(false);
		expect(wrapper.find('[data-testid="kt-ou-deactivate"]').exists()).toBe(false);
		expect(wrapper.find('[data-testid="kt-ou-reactivate"]').exists()).toBe(true);
	});

	it("the affected-responsibilities link appears only with active assignments", () => {
		expect(mountDetail().find('[data-testid="kt-ou-affected"]').exists()).toBe(false);
		const wrapper = mountDetail({ active_assignments: 2 });
		expect(wrapper.find('[data-testid="kt-ou-affected"]').text()).toContain("View 2 affected responsibilities");
	});

	it("never exposes nested-set internals", () => {
		const html = mountDetail().html();
		for (const banned of ["lft", "rgt", "old_parent", "procuring_entity"]) {
			expect(html).not.toContain(banned);
		}
	});
});
