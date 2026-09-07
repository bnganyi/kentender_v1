// REQ-DES-06's "Add supporting material" dialog (§5.10). The file picker
// itself is `frappe.ui.FileUploader` (the same precedent
// BudgetVersionEditorScreen.vue already uses for a real OS file-open
// dialog) — stubbed here since only the metadata form and the submitted
// payload shape are this component's own behaviour to verify.
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { mount } from "@vue/test-utils";
import MaterialDialog from "./MaterialDialog.vue";

const EDITOR = {
	package: {
		technical_requirements: [{ technical_requirement_id: "TECH-001", characteristic_key: "memory" }],
		related_services: [{ service_requirement_id: "SVC-001", service_type: "Installation" }],
		acceptance_requirements: [{ acceptance_requirement_id: "ACC-001", check_type: "Quantity" }],
	},
	catalogue: {
		supporting_material_types: ["Photograph", "Other supporting material"],
		characteristics: [{ key: "memory", label: "Memory" }],
	},
};

function make() {
	return mount(MaterialDialog, { props: { editor: EDITOR, pending: false, error: "" } });
}

function stubFileUploader(fileDoc = { name: "FILE001", file_name: "site-photo.jpg" }) {
	global.frappe = { ui: { FileUploader: vi.fn().mockImplementation((opts) => opts.on_success(fileDoc)) } };
}

describe("MaterialDialog — REQ-DES-06", () => {
	beforeEach(() => stubFileUploader());
	afterEach(() => {
		delete global.frappe;
	});

	it("rejects submission with no file chosen", async () => {
		const w = make();
		await w.find("#mat-title").setValue("Site photograph");
		await w.find("#mat-type").setValue("Photograph");
		await w.find("#mat-purpose").setValue("Shows the delivery-site layout for context.");
		await w.find('[data-testid="req-material-dialog-confirm"]').trigger("click");
		expect(w.emitted("confirm")).toBeFalsy();
		expect(w.text()).toContain("A file is required.");
	});

	it("opens the file uploader and shows the chosen file's name", async () => {
		const w = make();
		await w.find(".req-file-picker button").trigger("click");
		expect(w.find('[data-testid="req-material-filename"]').text()).toBe("site-photo.jpg");
	});

	it("submits Informational treatment with an empty linked_requirement_ids_json", async () => {
		const w = make();
		await w.find(".req-file-picker button").trigger("click");
		await w.find("#mat-title").setValue("Site photograph");
		await w.find("#mat-type").setValue("Photograph");
		await w.find("#mat-purpose").setValue("Shows the delivery-site layout for context.");
		await w.find('[data-testid="req-material-dialog-confirm"]').trigger("click");
		const payload = w.emitted("confirm")[0][0];
		expect(payload.file).toBe("FILE001");
		expect(payload.treatment).toBe("Informational");
		expect(payload.linked_requirement_ids_json).toBe("[]");
	});

	it("requires at least one linked requirement when treatment is Forms part of requirement", async () => {
		const w = make();
		await w.find(".req-file-picker button").trigger("click");
		await w.find("#mat-title").setValue("Compliance certificate");
		await w.find("#mat-type").setValue("Photograph");
		await w.find("#mat-purpose").setValue("Evidence supporting the memory characteristic.");
		const forms = w.findAll('input[type="radio"]')[1];
		await forms.setValue(true);
		await w.find('[data-testid="req-material-dialog-confirm"]').trigger("click");
		expect(w.emitted("confirm")).toBeFalsy();
		expect(w.text()).toContain("At least one linked structured row is required.");
		await w.find('.req-check-list input[type="checkbox"]').setValue(true);
		await w.find('[data-testid="req-material-dialog-confirm"]').trigger("click");
		const payload = w.emitted("confirm")[0][0];
		expect(JSON.parse(payload.linked_requirement_ids_json)).toEqual(["TECH-001"]);
	});

	it("requires other_document_type only when type is Other supporting material", async () => {
		const w = make();
		await w.find(".req-file-picker button").trigger("click");
		await w.find("#mat-title").setValue("Custom document");
		await w.find("#mat-type").setValue("Other supporting material");
		await w.find("#mat-purpose").setValue("A document type not otherwise listed.");
		await w.find('[data-testid="req-material-dialog-confirm"]').trigger("click");
		expect(w.emitted("confirm")).toBeFalsy();
		await w.find("#mat-other-type").setValue("Compliance letter");
		await w.find('[data-testid="req-material-dialog-confirm"]').trigger("click");
		expect(w.emitted("confirm")).toBeTruthy();
	});
});
