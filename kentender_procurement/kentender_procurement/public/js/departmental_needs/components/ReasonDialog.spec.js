// NDS-CHG-001 v1.14 §11.12/§11.13 — ReasonDialog.vue component tests for
// NDS-DES-13's RETURN-INITIAL/RETURN-UPDATE/DECLINE-INITIAL/DECLINE-UPDATE/
// DECLINE-WITHDRAWAL dialogs, ported from NDS Artboards.dc.html: exact
// title/subject/meta/field-label/button copy — a landmark-only structural
// gate (departmental-needs-fidelity.spec.ts) cannot catch a blank or
// wrong-but-present value, only whether a label is present in order, so this
// asserts the literal rendered strings alongside (never instead of) that
// browser-layer gate.
import { describe, expect, it } from "vitest";
import { mount } from "@vue/test-utils";
import ReasonDialog from "./ReasonDialog.vue";

describe("ReasonDialog", () => {
	it("renders NDS-DES-13-RETURN-INITIAL's exact title, subject, meta and field copy", () => {
		const wrapper = mount(ReasonDialog, {
			props: {
				title: "What needs to change?",
				subject: "Clinical training laptops for digital health rollout",
				meta: [
					{ label: "Reference", value: "NDS-MOH-2027-0003" },
					{ label: "Revision", value: "1" },
				],
				fieldLabel: "Correction required",
				confirmLabel: "Return for correction",
				modelValue: "",
			},
		});
		expect(wrapper.get(".dialog-title").text()).toBe("What needs to change?");
		expect(wrapper.get(".kt-dialog-body p").text()).toBe("Clinical training laptops for digital health rollout");
		const rows = wrapper.findAll(".kt-meta-row > div");
		expect(rows).toHaveLength(2);
		expect(rows[0].get(".kt-label").text()).toBe("Reference");
		expect(rows[0].get(".kt-meta-value").text()).toBe("NDS-MOH-2027-0003");
		expect(rows[1].get(".kt-label").text()).toBe("Revision");
		expect(rows[1].get(".kt-meta-value").text()).toBe("1");
		expect(wrapper.get("label").text()).toBe("Correction required");
		expect(wrapper.get('[data-testid="nds-dialog-confirm"]').text()).toContain("Return for correction");
	});

	it("renders NDS-DES-13-DECLINE-WITHDRAWAL's 'Accepted revision' meta label and reason field", () => {
		const wrapper = mount(ReasonDialog, {
			props: {
				title: "Decline withdrawal",
				subject: "National digital health infrastructure upgrade",
				meta: [
					{ label: "Reference", value: "NDS-MOH-2027-0001" },
					{ label: "Accepted revision", value: "1" },
				],
				fieldLabel: "Reason",
				confirmLabel: "Decline withdrawal",
				destructive: true,
				modelValue: "",
			},
		});
		const rows = wrapper.findAll(".kt-meta-row > div");
		expect(rows[1].get(".kt-label").text()).toBe("Accepted revision");
		expect(wrapper.get("label").text()).toBe("Reason");
		expect(wrapper.get('[data-testid="nds-dialog-confirm"]').classes()).toContain("btn-destructive");
	});

	it("falls back to the single-line subjectMeta when no meta rows are given (NDS-DES-11)", () => {
		// Regression check: NDS-DES-11's request-withdrawal dialog is out of
		// this task's scope and still passes a pre-joined `subjectMeta` string,
		// never `meta` — the `meta` addition must not change its rendering.
		const wrapper = mount(ReasonDialog, {
			props: {
				title: "Request withdrawal",
				subject: "National digital health infrastructure upgrade",
				subjectMeta: "NDS-MOH-2027-0001 · Accepted revision 1",
				fieldLabel: "Reason for withdrawal",
				confirmLabel: "Request withdrawal",
				modelValue: "",
			},
		});
		expect(wrapper.find(".kt-meta-row").exists()).toBe(false);
		expect(wrapper.get(".kt-dialog-body > .kt-label").text()).toBe("NDS-MOH-2027-0001 · Accepted revision 1");
	});

	it("emits confirm/cancel from their own buttons", async () => {
		const wrapper = mount(ReasonDialog, {
			props: {
				title: "Do not take forward",
				fieldLabel: "Why are you declining this requirement?",
				confirmLabel: "Do not take forward",
				modelValue: "",
			},
		});
		await wrapper.get('[data-testid="nds-dialog-cancel"]').trigger("click");
		expect(wrapper.emitted("cancel")).toHaveLength(1);
		await wrapper.get('[data-testid="nds-dialog-confirm"]').trigger("click");
		expect(wrapper.emitted("confirm")).toHaveLength(1);
	});
});
