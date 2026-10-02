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

	it("starts a ports answer empty: no type chosen and no count, until the bidder gives them", async () => {
		const portal = { upload: vi.fn(), call: vi.fn(), createCommandRunner };
		const field = { ...FIELD, handle: "h-ports", kind: "ports", label: "Required ports", options: ["USB-C", "USB-A", "HDMI"] };
		const ports = mount(FieldControl, { props: { field, modelValue: null, bid: { reference: "BID-1", record_version: 3 } }, global: { provide: { portal }, config: { globalProperties: { __: globalThis.__ } } } });
		expect(ports.get("select").element.value).toBe("");
		expect(ports.get("select").findAll("option")[0].text()).toBe("Select");
		expect(ports.get('input[type="number"]').element.value).toBe("");
		expect(ports.emitted("update:modelValue")).toBeUndefined(); // looking at the field answers nothing
		await ports.get('input[type="number"]').setValue("2");
		expect(ports.emitted("update:modelValue").at(-1)).toEqual([[{ port_type: "", count: 2 }]]);
		await ports.get('input[type="number"]').setValue("");
		expect(ports.emitted("update:modelValue").at(-1)).toEqual([[{ port_type: "", count: null }]]);
	});

	describe("a file's own actions and the field's upload button", () => {
		const evidence = (files, maximum) => ({ ...FIELD, evidence: { ...FIELD.evidence, maximum, files } });
		const ACCEPTED = { id: "EVD-1", name: "guarantee.pdf", status: "Accepted", size_bytes: 10 };
		const REJECTED = { id: "EVD-2", name: "bad.pdf", status: "Rejected", size_bytes: 0, reason: "File failed malware scanning." };
		const mountField = (field, portal = { upload: vi.fn(async () => ({ ok: true })), call: vi.fn(), createCommandRunner }) => ({
			portal,
			wrapper: mount(FieldControl, { props: { field, bid: { reference: "BID-1", record_version: 3 } }, attachTo: document.body, global: { provide: { portal }, config: { globalProperties: { __: globalThis.__ } } } }),
		});
		const labels = (wrapper) => wrapper.findAll("button, a").map((e) => e.text());
		const choose = async (wrapper) => {
			const input = wrapper.get('input[type="file"]');
			Object.defineProperty(input.element, "files", { value: [new File(["x"], "new.pdf", { type: "application/pdf" })], configurable: true });
			await input.trigger("change");
			await flushPromises();
		};

		it("puts View, Replace and Remove against the file, and no separate button where the field takes one file", () => {
			const { wrapper } = mountField(evidence([ACCEPTED], 1));
			expect(labels(wrapper.get('[data-testid="bds-file-EVD-1"]'))).toEqual(["View", "Replace", "Remove"]);
			expect(wrapper.find('[data-testid="bds-upload-h-datasheet"]').exists()).toBe(false);
		});

		it("replaces the named file in one command, never adding a second", async () => {
			const { wrapper, portal } = mountField(evidence([ACCEPTED], 1));
			const click = vi.spyOn(wrapper.get('input[type="file"]').element, "click");
			await wrapper.get('[data-testid="bds-replace-EVD-1"]').trigger("click");
			expect(click).toHaveBeenCalled();
			await choose(wrapper);
			expect(portal.upload).toHaveBeenCalledTimes(1);
			const [method, args] = portal.upload.mock.calls[0];
			expect([method.split(".").pop(), args.evidence_id, args.bid_reference]).toEqual(["replace_bid_evidence", "EVD-1", "BID-1"]);
			expect(args.handle).toBeUndefined();
			expect(wrapper.emitted("changed")).toHaveLength(1);
		});

		it("offers Upload file when empty and Add another file only while the field has room", async () => {
			expect(labels(mountField(evidence([], 1)).wrapper)).toContain("Upload file");
			expect(labels(mountField(evidence([REJECTED], 1)).wrapper)).toContain("Upload file"); // a refused file does not fill the field
			const { wrapper, portal } = mountField(evidence([ACCEPTED], 5));
			expect(labels(wrapper)).toContain("Add another file");
			await choose(wrapper);
			expect(portal.upload.mock.calls[0][0].split(".").pop()).toBe("upload_bid_evidence");
			expect(portal.upload.mock.calls[0][1].handle).toBe("h-datasheet");
			const full = mountField(evidence([ACCEPTED, { ...ACCEPTED, id: "EVD-3" }], 2)).wrapper;
			expect(labels(full).filter((l) => l === "Add another file" || l === "Upload file")).toEqual([]);
		});

		it("a Replace that is cancelled does not turn the next Add another file into a replace", async () => {
			const { wrapper, portal } = mountField(evidence([ACCEPTED], 5));
			await wrapper.get('[data-testid="bds-replace-EVD-1"]').trigger("click"); // the picker is dismissed without a choice
			await wrapper.get('[data-testid="bds-upload-h-datasheet"]').trigger("click");
			await choose(wrapper);
			expect(portal.upload.mock.calls[0][0].split(".").pop()).toBe("upload_bid_evidence");
		});

		it("a refused replacement keeps the old file listed and offers to try again as a replace", async () => {
			const upload = vi.fn(async () => ({ ok: false, code: "BDS_EVIDENCE_REJECTED", message: "This file could not be accepted.", errors: { "h-datasheet": "The file failed the malware check." } }));
			const { wrapper } = mountField(evidence([ACCEPTED], 1), { upload, call: vi.fn(), createCommandRunner });
			await wrapper.get('[data-testid="bds-replace-EVD-1"]').trigger("click");
			await choose(wrapper);
			await wrapper.get('[data-testid="bds-state-evidence-rejected"] button').trigger("click");
			await choose(wrapper);
			expect(upload.mock.calls.map((c) => c[0].split(".").pop())).toEqual(["replace_bid_evidence", "replace_bid_evidence"]);
		});
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
		expect(ports.emitted("update:modelValue").at(-1)).toEqual([[{ port_type: "USB-C", count: 3 }, { port_type: "", count: null }]]); // a new row starts empty
		await ports.setProps({ modelValue: [{ port_type: "USB-C", count: 3 }, { port_type: "", count: null }] });
		await ports.findAll("select")[1].setValue("HDMI");
		expect(ports.emitted("update:modelValue").at(-1)).toEqual([[{ port_type: "USB-C", count: 3 }, { port_type: "HDMI", count: null }]]);
	});
});

