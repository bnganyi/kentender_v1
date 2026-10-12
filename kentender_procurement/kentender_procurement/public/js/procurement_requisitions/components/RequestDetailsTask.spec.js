// REQ-CHG-001 v1.15 §13.4 / §13.5 / §14.3 — quantity is typed once, on the item
// rows; the requester enters one estimated total cost for each approved
// requirement. Every finding is said once, in the attention panel; the rows carry
// a marker, and the footer has one status line (v1.17 §13.4A–C).
import { beforeEach, describe, expect, it, vi } from "vitest";
import { flushPromises, mount } from "@vue/test-utils";

import AddItemDialog from "./AddItemDialog.vue";
import RequestDetailsTask from "./RequestDetailsTask.vue";
import { context, editor } from "./fixtures.js";

beforeEach(() => window.sessionStorage.clear());

const text = (w, id) => w.find(`[data-testid="${id}"]`).text();

describe("RequestDetailsTask — Items and Request summary (REQ-DES-03)", () => {
	it("starts empty: no quantity input, no default, no 'Use full available amount', one estimate per requirement", () => {
		const { global } = context();
		const w = mount(RequestDetailsTask, { props: { view: editor() }, global });
		expect(w.find('[data-testid="req-amount-quantity"]').exists()).toBe(false);
		expect(w.find('[data-testid="req-use-full"]').exists()).toBe(false);
		expect(w.text()).not.toContain("Use full available amount");
		const estimates = w.findAll('[data-testid="req-amount-value"]');
		expect(estimates).toHaveLength(2);
		for (const input of estimates) expect(input.element.value).toBe("");
		// the requested quantity is derived, shown read-only
		expect(w.findAll('[data-testid="req-requested-quantity"]').map((c) => c.text())).toEqual(["0 Each", "0 Each"]);
		expect(w.text()).toContain("Add each item and enter its quantity here. You enter a quantity only once.");
		expect(w.text()).toContain("No items added.");
		expect(w.find('[data-testid="req-add-item"]').text()).toBe("Add item");
		expect(text(w, "req-attention-item")).toBe("Add at least one item and enter its estimated total cost.");
		expect(text(w, "req-footer-status")).toBe("Fix what needs attention above to continue.");
		expect(w.find('[data-testid="req-continue"]').attributes("disabled")).toBeDefined();
	});

	it("shows what the items request and what stays available (partial request)", () => {
		const { global } = context();
		const w = mount(RequestDetailsTask, { props: { view: editor("PARTIAL") }, global });
		const row = w.find('[data-testid="req-amount-row"]');
		expect(row.text()).toContain("100 Each");
		expect(row.text()).toContain("20 Each");
		expect(row.text()).toContain("KES 20,000,000.00");
		expect(row.text()).toContain("80 Each · KES 17,000,000.00");
		expect(w.find('[data-testid="req-amount-value"]').element.value).toBe("3,000,000.00");
		expect(w.text()).toContain("Office printers");
		expect(w.text()).toContain("Printer");
		expect(w.text().toLowerCase()).not.toContain("laptop");
		expect(w.find('[data-testid="req-continue"]').attributes("disabled")).toBeUndefined();
	});

	it("says what needs attention once: every finding is listed in one panel, the item carries a marker, the footer a pointer", () => {
		const { global } = context();
		const view = editor("PARTIAL");
		const itemId = view.equipment.rows[0].requisition_item_id;
		view.findings = [
			{ code: "RESTRICTIVE_TERM", severity: "Blocking", task: "request_details", row: { kind: "item", id: itemId }, message: "“Dell” in the item “Office printers” is a brand or restrictive term. Use supplier-neutral wording." },
			{ code: "MISSING_REQUIRED_FIELD", severity: "Blocking", task: "request_details", row: { kind: "field", id: "delivery_location" }, message: "Select the delivery location." },
			{ code: "MISSING_REQUIRED_FIELD", severity: "Blocking", task: "request_details", row: { kind: "field", id: "latest_delivery_date" }, message: "Enter the latest delivery date." },
		];
		view.footer_hints = { ...view.footer_hints, request_details: view.findings[0].message };
		const w = mount(RequestDetailsTask, { props: { view }, global });
		expect(w.find('[data-testid="req-attention-head"]').text()).toBe("3 things need attention");
		const listed = w.findAll('[data-testid="req-attention-item"]').map((e) => e.text());
		expect(listed).toEqual(view.findings.map((f) => f.message)); // the item's own finding is not left out
		expect(w.find('[data-testid="req-equipment-row"]').classes()).toContain("is-flagged");
		expect(w.find('[data-testid="req-item-flag"]').text()).toBe("Needs attention");
		// the message itself is not repeated beside the item or in the footer
		expect(w.text().split("brand or restrictive term")).toHaveLength(2);
		expect(text(w, "req-footer-status")).toBe("Fix what needs attention above to continue.");
		expect(w.find('[data-testid="req-footer-hint"]').exists()).toBe(false);
		expect(w.find('[data-testid="req-more-issues"]').exists()).toBe(false);
	});

	it("keeps a mixed request's items in one block per specification, each with its own Edit shared details", async () => {
		const { global } = context();
		const view = editor("COMPLETE");
		view.equipment = {
			...view.equipment,
			rows: [view.equipment.rows[0], { ...view.equipment.rows[1], item_name: "Dell monitors", equipment_category: "Monitor" }],
			groups: [
				{ group_id: "G1", equipment_category: "Laptop", item_name: "Business laptops", delivery_location: "LOC-1", latest_delivery_date: "2027-09-30", delivery: "Nairobi; 30 Sep 2027", requisition_item_ids: ["RQI-001"] },
				{ group_id: "G2", equipment_category: "Monitor", item_name: "Dell monitors", delivery_location: "LOC-1", latest_delivery_date: "2027-09-30", delivery: "Nairobi; 30 Sep 2027", requisition_item_ids: ["RQI-002"] },
			],
		};
		const w = mount(RequestDetailsTask, { props: { view }, global });
		const groups = w.findAll('[data-testid="req-item-group"]');
		expect(groups).toHaveLength(2);
		expect(groups[0].find('[data-testid="req-group-title"]').text()).toContain("Business laptops");
		expect(groups[1].find('[data-testid="req-group-title"]').text()).toContain("Dell monitors");
		expect(groups[1].findAll('[data-testid="req-equipment-row"]')).toHaveLength(1);
		// the second kind can be renamed and recategorised without touching the first
		await groups[1].find('[data-testid="req-edit-shared"]').trigger("click");
		const dialog = w.findComponent(AddItemDialog);
		expect(dialog.props("group").requisition_item_ids).toEqual(["RQI-002"]);
		expect(dialog.find('[data-testid="req-add-name"]').element.value).toBe("Dell monitors");
		expect(dialog.find('[data-testid="req-shared-scope"]').text()).toContain("1 approved requirement");
	});

	it("formats the estimated total cost for reading when the field loses focus, and leaves it exactly as typed while it is edited", async () => {
		const { global } = context();
		const w = mount(RequestDetailsTask, { props: { view: editor("PARTIAL") }, global });
		const input = w.find('[data-testid="req-amount-value"]');
		await input.setValue("12500000");
		expect(input.element.value).toBe("12500000");
		await input.trigger("blur");
		expect(input.element.value).toBe("12,500,000.00");
		await input.trigger("focus");
		expect(input.element.value).toBe("12,500,000.00");
		await input.setValue("1,2");
		await input.trigger("blur");
		expect(input.element.value).toBe("12.00");
	});

	it("formatting alone is not an unsaved change, and never hides or rounds an amount with too many decimals", async () => {
		const { global } = context();
		const w = mount(RequestDetailsTask, { props: { view: editor("PARTIAL") }, global });
		const input = w.find('[data-testid="req-amount-value"]');
		await input.trigger("blur");
		expect(input.element.value).toBe("3,000,000.00");
		expect(w.find('[data-state="unsaved"]').exists()).toBe(false);
		await input.setValue("20000000.005");
		await input.trigger("blur");
		expect(input.element.value).toBe("20000000.005");
		expect(w.find('[data-state="unsaved"]').exists()).toBe(true);
	});

	it("Save sends only header changes and each editable line's estimate, never a quantity", async () => {
		const saveSummary = vi.fn().mockResolvedValue({ ok: true });
		const { global } = context({ api: { saveSummary } });
		const w = mount(RequestDetailsTask, { props: { view: editor("COMPLETE") }, global });
		const inputs = w.findAll('[data-testid="req-amount-value"]');
		await inputs[0].setValue("3,000,000");
		await w.find('[data-testid="req-save"]').trigger("click");
		await flushPromises();
		expect(saveSummary).toHaveBeenCalledTimes(1);
		const sent = saveSummary.mock.calls[0][0].summary_values;
		expect(sent.drawdown_lines).toEqual([
			{ drawdown_line_id: "RDL-001", requested_value: "3000000" },
			{ drawdown_line_id: "RDL-002", requested_value: "30000000.00" },
		]);
		expect(JSON.stringify(sent)).not.toContain("requested_quantity");
		expect(sent.requirement_title).toBeUndefined();
	});

	it("an unsaved change is marked, and the footer does not speak for it", async () => {
		const { global } = context();
		const w = mount(RequestDetailsTask, { props: { view: editor() }, global });
		expect(w.find('[data-state="unsaved"]').exists()).toBe(false);
		await w.findAll('[data-testid="req-amount-value"]')[0].setValue("3000000");
		// one status line, not two stacked messages
		expect(w.findAll('[data-testid="req-footer-status"]')).toHaveLength(1);
		expect(text(w, "req-footer-status")).toBe("Unsaved changes. Save to check this request.");
		// Continue is the way to save and check it, so it is offered
		expect(w.find('[data-testid="req-continue"]').attributes("disabled")).toBeUndefined();
		// putting the saved text back clears the marker
		await w.findAll('[data-testid="req-amount-value"]')[0].setValue("");
		expect(w.find('[data-state="unsaved"]').exists()).toBe(false);
		expect(text(w, "req-footer-status")).toBe("Fix what needs attention above to continue.");
	});

	it("Continue saves the whole draft and stays, with the saved hint, when the server still blocks", async () => {
		const saveSummary = vi.fn().mockResolvedValue({ ok: true });
		const { global } = context({ api: { saveSummary } });
		const w = mount(RequestDetailsTask, { props: { view: editor() }, global });
		await w.findAll('[data-testid="req-amount-value"]')[0].setValue("3000000");
		await w.find('[data-testid="req-continue"]').trigger("click");
		await flushPromises();
		expect(saveSummary).toHaveBeenCalledTimes(1);
		expect(w.emitted("continue")).toBeUndefined();
	});

	it("Continue moves on when the saved draft has nothing blocking", async () => {
		const saveSummary = vi.fn().mockResolvedValue({ ok: true });
		const { global } = context({ api: { saveSummary } });
		const w = mount(RequestDetailsTask, { props: { view: editor("COMPLETE") }, global });
		await w.find('[data-testid="req-continue"]').trigger("click");
		await flushPromises();
		expect(saveSummary).toHaveBeenCalledTimes(1);
		expect(w.emitted("continue")).toHaveLength(1);
	});

	it("an estimate above the allowance is refused beside its own row and the typed text is kept", async () => {
		const message = "Digital Health can enter at most KES 30,000,000.00 for this requirement; you entered KES 40,000,000.00.";
		const { global, ctx } = context();
		ctx.run = async (label, fn) => {
			try {
				return await fn("key");
			} catch (e) {
				ctx.commandError.value = { label, code: e.code, message: e.message, detail: e.detail };
				return null;
			}
		};
		ctx.api.saveSummary = async () => {
			throw Object.assign(new Error(message), { code: "REQ_ESTIMATE_EXCEEDS_ALLOWANCE", detail: { drawdown_line_id: "RDL-002", entered: "40000000.00", limit: "30000000.00" } });
		};
		const w = mount(RequestDetailsTask, { props: { view: editor("COMPLETE") }, global });
		await w.findAll('[data-testid="req-amount-value"]')[1].setValue("40000000");
		await w.find('[data-testid="req-save"]').trigger("click");
		await flushPromises();
		expect(w.findAll('[data-testid="req-amount-error"]').map((e) => e.text())).toEqual([message]);
		expect(w.findAll('[data-testid="req-amount-value"]')[1].element.value).toBe("40000000");
		// typing something else retires the refusal
		await w.findAll('[data-testid="req-amount-value"]')[1].setValue("30000000");
		expect(w.find('[data-testid="req-amount-error"]').exists()).toBe(false);
	});

	it("marks each approved requirement the server flags, and lists its finding once", () => {
		const view = editor("COMPLETE");
		view.footer_hints = { request_details: "Add the items for Digital Health, or clear its estimated total cost." };
		view.findings = [
			{ code: "SOURCE_INCOMPLETE", severity: "Blocking", task: "request_details", message: "Add the items for Digital Health, or clear its estimated total cost.", row: { kind: "drawdown_line", id: "RDL-002" } },
			{ code: "SOURCE_INCOMPLETE", severity: "Blocking", task: "request_details", message: "Enter the estimated total cost for Human Resources Management and Development.", row: { kind: "drawdown_line", id: "RDL-001" } },
		];
		const { global } = context();
		const w = mount(RequestDetailsTask, { props: { view }, global });
		expect(w.findAll('[data-testid="req-attention-item"]').map((e) => e.text())).toEqual(view.findings.map((f) => f.message));
		expect(w.findAll('[data-testid="req-line-flag"]')).toHaveLength(2);
		expect(w.find('[data-testid="req-amount-finding"]').exists()).toBe(false);
	});

	it("marks a draft carried over from before as Review required", () => {
		const view = editor("COMPLETE");
		view.amounts = [{ ...view.amounts[0], needs_review: true }, view.amounts[1]];
		const { global } = context();
		const w = mount(RequestDetailsTask, { props: { view }, global });
		expect(w.findAll('[data-testid="req-review-required"]')).toHaveLength(1);
	});

	it("contributor: only their own estimate is an input; the other department's row, with its derived quantity, is read-only", () => {
		const { global } = context();
		const w = mount(RequestDetailsTask, { props: { view: editor("CONTRIBUTOR") }, global });
		expect(w.findAll('[data-testid="req-amount-value"]')).toHaveLength(1);
		const rows = w.findAll('[data-testid="req-amount-row"]');
		expect(rows[1].text()).toContain("150 Each");
		expect(rows[1].text()).toContain("KES 30,000,000.00");
		expect(rows[1].text()).toContain("Read-only");
		expect(w.find('[data-testid="req-continue"]').exists()).toBe(false);
	});

	it("Add item opens from the draft on screen, including unsaved edits", async () => {
		const view = editor();
		view.request_information = { ...view.request_information, delivery_location: "", latest_delivery_date: "" };
		const { global } = context();
		const w = mount(RequestDetailsTask, { props: { view }, global, attachTo: document.body });
		// chosen on the page but not saved
		await w.find('[data-testid="req-field-location"]').setValue("LOC-1");
		await w.find("#req-latest").setValue("2027-09-15");
		await w.find('[data-testid="req-add-item"]').trigger("click");
		const dialog = w.findComponent(AddItemDialog);
		expect(dialog.exists()).toBe(true);
		expect(dialog.props("draft")).toMatchObject({ delivery_location: "LOC-1", latest_delivery_date: "2027-09-15" });
		expect(document.querySelector('[data-testid="req-add-location"]').value).toBe("LOC-1");
		expect(document.querySelector("#req-add-latest").value).toBe("2027-09-15");
		// the page keeps what was typed
		expect(w.find('[data-testid="req-field-location"]').element.value).toBe("LOC-1");
		w.unmount();
	});
});

describe("AddItemDialog (REQ-DES-04)", () => {
	function open(view, draft) {
		const { global, ctx } = context();
		ctx.run = async (label, fn) => {
			try {
				return await fn("key");
			} catch (e) {
				ctx.commandError.value = { label, code: e.code, message: e.message, detail: e.detail };
				return null;
			}
		};
		return { ctx, w: mount(AddItemDialog, { props: { view, draft }, global, attachTo: document.body }) };
	}
	const q = (id) => Array.from(document.querySelectorAll(`[data-testid="${id}"]`));

	it("is category-neutral, with nothing prefilled: no category, empty quantities, the room as the hint", () => {
		const { w } = open(editor(), {});
		expect(document.body.textContent).toContain("Add item");
		expect(document.body.textContent).toContain("Enter the shared item details once, then enter the quantity and intended use for each department.");
		expect(document.body.textContent).toContain("The standard requirements for the chosen category will be ready for review in the next task.");
		expect(document.body.textContent.toLowerCase()).not.toContain("laptop request");
		expect(document.querySelector('[data-testid="req-add-category"]').value).toBe("");
		expect(q("req-add-quantity").map((i) => i.value)).toEqual(["", ""]);
		expect(q("req-add-quantity").map((i) => i.placeholder)).toEqual(["100", "150"]);
		expect(q("req-add-confirm")[0].disabled).toBe(true);
		expect(q("req-add-confirm")[0].textContent).toBe("Add 2 items");
		w.unmount();
	});

	it("starts its location and date from the draft on screen, falling back to the saved values", () => {
		const view = editor();
		view.request_information = { ...view.request_information, locations: [...view.request_information.locations, { name: "LOC-2", location_name: "Annex", address: "Ministry of Health Annex, Nairobi" }] };
		const a = open(view, { delivery_location: "LOC-2", latest_delivery_date: "2027-09-01" });
		expect(document.querySelector('[data-testid="req-add-location"]').value).toBe("LOC-2");
		expect(document.querySelector("#req-add-latest").value).toBe("2027-09-01");
		a.w.unmount();
		const b = open(view, {});
		expect(document.querySelector('[data-testid="req-add-location"]').value).toBe("LOC-1");
		expect(document.querySelector("#req-add-latest").value).toBe("2027-09-30");
		b.w.unmount();
	});

	it("sends the typed quantity once, and binds the limit sentence to its row", async () => {
		const sentence = "Digital Health can request at most 150 Each for this requirement; you entered 160.";
		const addSameSpecificationItems = vi.fn().mockRejectedValue(Object.assign(new Error(sentence), { code: "REQ_QUANTITY_EXCEEDS_AVAILABLE", detail: { rows: { "RDL-002": sentence } } }));
		const { w, ctx } = open(editor(), {});
		ctx.api.addSameSpecificationItems = addSameSpecificationItems;
		const set = async (el, value) => {
			el.value = value;
			el.dispatchEvent(new Event(el.tagName === "SELECT" ? "change" : "input"));
			await flushPromises();
		};
		await set(document.querySelector('[data-testid="req-add-category"]'), "Printer");
		await set(document.querySelector('[data-testid="req-add-name"]'), "Office printers");
		const quantities = q("req-add-quantity");
		const uses = q("req-add-use");
		await set(quantities[0], "20");
		await set(uses[0], "Printing for the HR office");
		await set(quantities[1], "160");
		await set(uses[1], "Printing for the digital health team");
		expect(q("req-add-confirm")[0].disabled).toBe(false);
		q("req-add-confirm")[0].click();
		await flushPromises();
		expect(addSameSpecificationItems).toHaveBeenCalledTimes(1);
		const sent = addSameSpecificationItems.mock.calls[0][0];
		expect(sent.item_rows.map((r) => [r.drawdown_line_id, r.quantity])).toEqual([["RDL-001", "20"], ["RDL-002", "160"]]);
		expect(sent.shared_values).toMatchObject({ equipment_category: "Printer", item_name: "Office printers", delivery_location: "LOC-1" });
		// said once, beside the Digital Health row; nothing else is lost
		expect(q("req-add-row-error").map((e) => e.textContent)).toEqual([sentence]);
		expect(document.querySelector('[data-testid="req-add-mismatch"]')).toBeNull();
		expect(quantities[1].value).toBe("160");
		expect(q("req-add-confirm")[0].disabled).toBe(true);
		w.unmount();
	});
});
