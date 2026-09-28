// BDS-CHG-001 v0.8 §10.17 Evidence rejected: a file the checks refuse shows the
// catalogue state in place — "This file could not be accepted.", the safe
// reason, and Choose another file, which opens the file picker again.
import { afterEach, describe, expect, it, vi } from "vitest";
import { flushPromises, mount } from "@vue/test-utils";
import { ref } from "vue";

import { createCommandRunner } from "../../../../../../kentender_core/kentender_core/public/js/kt_portal/runtime.js";
import FieldControl from "./FieldControl.vue";

const FIELD = { handle: "h-datasheet", kind: "evidence", label: "Product datasheet", help: "", editable: true, visible: true, required: true, value: null, issue: null, evidence: { type: "", minimum: 1, maximum: 1, mandatory: true, files: [] } };
afterEach(() => {
	document.body.innerHTML = "";
});

describe("An evidence field", () => {
	it("shows a refused file as the Evidence rejected state with Choose another file", async () => {
		const upload = vi.fn(async () => ({ ok: false, code: "BDS_EVIDENCE_REJECTED", message: "This file could not be accepted.", errors: { "h-datasheet": "The file failed the malware check." } }));
		const portal = { upload, call: vi.fn(), createCommandRunner };
		const wrapper = mount(FieldControl, { props: { field: FIELD, bid: { reference: "BID-1", record_version: 3 } }, attachTo: document.body, global: { provide: { portal }, config: { globalProperties: { __: globalThis.__ } } } });
		const input = wrapper.get('input[type="file"]');
		Object.defineProperty(input.element, "files", { value: [new File(["x"], "datasheet.pdf", { type: "application/pdf" })] });
		await input.trigger("change");
		await flushPromises();
		const state = wrapper.get('[data-testid="bds-state-evidence-rejected"]');
		expect(state.get("strong").text()).toBe("This file could not be accepted.");
		expect(state.text()).toContain("The file failed the malware check.");
		expect(wrapper.emitted("changed")).toHaveLength(1);
		const click = vi.spyOn(input.element, "click");
		await state.get("button").trigger("click");
		expect(state.get("button").text()).toBe("Choose another file");
		expect(click).toHaveBeenCalled();
	});

	it("keeps a multi-select answer a list and the ports answer structured rows, never flattened (BDS06-AC-009)", async () => {
		const portal = { upload: vi.fn(), call: vi.fn(), createCommandRunner };
		const mountField = (field, modelValue) => mount(FieldControl, { props: { field, modelValue, bid: { reference: "BID-1", record_version: 3 } }, global: { provide: { portal }, config: { globalProperties: { __: globalThis.__ } } } });
		const multi = mountField({ ...FIELD, handle: "h-os", kind: "multi_select", label: "Operating systems", options: ["Windows 11 Pro", "Ubuntu 24.04 LTS"] }, ["Windows 11 Pro"]);
		const boxes = multi.findAll('input[type="checkbox"]');
		expect(boxes.map((b) => b.element.checked)).toEqual([true, false]);
		await boxes[1].setValue(true);
		expect(multi.emitted("update:modelValue").at(-1)).toEqual([["Windows 11 Pro", "Ubuntu 24.04 LTS"]]);
		await boxes[0].setValue(false);
		expect(multi.emitted("update:modelValue").at(-1)).toEqual([[]]);

		const ports = mountField({ ...FIELD, handle: "h-ports", kind: "ports", label: "Ports", options: ["USB-C", "USB-A", "HDMI"] }, [{ port_type: "USB-C", count: 2 }]);
		await ports.get('input[type="number"]').setValue("3");
		expect(ports.emitted("update:modelValue").at(-1)).toEqual([[{ port_type: "USB-C", count: 3 }]]);
		await ports.setProps({ modelValue: [{ port_type: "USB-C", count: 3 }] });
		await ports.get("button").trigger("click");
		expect(ports.emitted("update:modelValue").at(-1)).toEqual([[{ port_type: "USB-C", count: 3 }, { port_type: "USB-C", count: 1 }]]);
		await ports.setProps({ modelValue: [{ port_type: "USB-C", count: 3 }, { port_type: "USB-C", count: 1 }] });
		await ports.findAll("select")[1].setValue("HDMI");
		expect(ports.emitted("update:modelValue").at(-1)).toEqual([[{ port_type: "USB-C", count: 3 }, { port_type: "HDMI", count: 1 }]]);
	});
});

