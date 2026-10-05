// NDS-CHG-001 v1.14 §11.13 — ConfirmDialog.vue component tests for
// NDS-DES-13's WITHDRAW-DRAFT/CANCEL-UPDATE/APPROVE-WITHDRAWAL
// confirmations, ported from NDS Artboards.dc.html: exact title/subject/
// meta/message/button copy — a landmark-only structural gate
// (departmental-needs-fidelity.spec.ts) cannot catch a blank or
// wrong-but-present value, only whether a label is present in order, so this
// asserts the literal rendered strings alongside (never instead of) that
// browser-layer gate.
import { describe, expect, it } from "vitest";
import { mount } from "@vue/test-utils";
import ConfirmDialog from "./ConfirmDialog.vue";

describe("ConfirmDialog", () => {
	it("renders NDS-DES-13-WITHDRAW-DRAFT's exact title, subject, meta and message", () => {
		const wrapper = mount(ConfirmDialog, {
			props: {
				title: "Withdraw this need?",
				subject: "Clinical training laptops for digital health rollout",
				meta: [
					{ label: "Reference", value: "NDS-MOH-2027-0003" },
					{ label: "Revision", value: "2" },
				],
				message: "This withdraws the unaccepted requirement. Earlier submissions and decisions remain in history.",
				confirmLabel: "Withdraw need",
				destructive: true,
			},
		});
		expect(wrapper.get(".dialog-title").text()).toBe("Withdraw this need?");
		expect(wrapper.get(".kt-dialog-body > p").text()).toBe("Clinical training laptops for digital health rollout");
		const rows = wrapper.findAll(".kt-meta-row > div");
		expect(rows).toHaveLength(2);
		expect(rows[0].get(".kt-label").text()).toBe("Reference");
		expect(rows[0].get(".kt-meta-value").text()).toBe("NDS-MOH-2027-0003");
		expect(rows[1].get(".kt-label").text()).toBe("Revision");
		expect(rows[1].get(".kt-meta-value").text()).toBe("2");
		expect(wrapper.text()).toContain(
			"This withdraws the unaccepted requirement. Earlier submissions and decisions remain in history."
		);
		expect(wrapper.get('[data-testid="nds-dialog-confirm"]').text()).toContain("Withdraw need");
		expect(wrapper.get('[data-testid="nds-dialog-confirm"]').classes()).toContain("btn-destructive");
	});

	it("renders NDS-DES-13-CANCEL-UPDATE's 'Proposed revision' meta label", () => {
		const wrapper = mount(ConfirmDialog, {
			props: {
				title: "Cancel these proposed changes?",
				subject: "National digital health infrastructure upgrade",
				meta: [
					{ label: "Reference", value: "NDS-MOH-2027-0001" },
					{ label: "Proposed revision", value: "2" },
				],
				message: "The previously accepted requirement will remain in effect.",
				confirmLabel: "Cancel update",
				destructive: true,
			},
		});
		const rows = wrapper.findAll(".kt-meta-row > div");
		expect(rows[1].get(".kt-label").text()).toBe("Proposed revision");
	});

	it("renders NDS-DES-13-APPROVE-WITHDRAWAL's 'Accepted revision' meta label with primary (non-destructive) styling", () => {
		const wrapper = mount(ConfirmDialog, {
			props: {
				title: "Approve withdrawal?",
				subject: "National digital health infrastructure upgrade",
				meta: [
					{ label: "Reference", value: "NDS-MOH-2027-0001" },
					{ label: "Accepted revision", value: "1" },
				],
				message: "This withdraws the accepted requirement. Earlier decisions remain in history.",
				confirmLabel: "Approve withdrawal",
			},
		});
		const rows = wrapper.findAll(".kt-meta-row > div");
		expect(rows[1].get(".kt-label").text()).toBe("Accepted revision");
		expect(wrapper.get('[data-testid="nds-dialog-confirm"]').classes()).not.toContain("btn-destructive");
	});

	it("renders no meta row when none is given (e.g. the NDS-DES-06/09 Accept confirmation)", () => {
		const wrapper = mount(ConfirmDialog, {
			props: {
				title: "Accept for planning",
				subject: "NDS-MOH-2027-0002 · Revision 1",
				message:
					"Acceptance makes this revision available to Procurement Planning. It does not approve expenditure or create procurement authority.",
				confirmLabel: "Accept for planning",
			},
		});
		expect(wrapper.find(".kt-meta-row").exists()).toBe(false);
	});

	it("emits confirm/cancel from their own buttons", async () => {
		const wrapper = mount(ConfirmDialog, {
			props: { title: "Withdraw this need?", message: "This withdraws the unaccepted requirement.", confirmLabel: "Withdraw need" },
		});
		await wrapper.get('[data-testid="nds-dialog-cancel"]').trigger("click");
		expect(wrapper.emitted("cancel")).toHaveLength(1);
		await wrapper.get('[data-testid="nds-dialog-confirm"]').trigger("click");
		expect(wrapper.emitted("confirm")).toHaveLength(1);
	});
});
