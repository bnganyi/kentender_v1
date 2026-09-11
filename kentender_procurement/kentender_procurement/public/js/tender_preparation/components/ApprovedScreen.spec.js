// TPR-DES-06 — approved view: consumption status and server-decided Reopen.
import { describe, expect, it } from "vitest";
import { mount } from "@vue/test-utils";
import ApprovedScreen from "./ApprovedScreen.vue";

function view(overrides = {}) {
	return {
		tender: { tender_reference: "TND-MOH-2099-001", version_number: 2, requirement_title: "Business laptops" },
		notice: "Approved for publication.", approved_by: { name: "Head", at: "15 May 2100, 08:00 EAT" },
		binding: { requisition_content_digest: "d".repeat(64), bundle_digest: "c".repeat(64) },
		publication_handoff: { status: "Ready", consumed_at: "", package_digest: "e".repeat(64) },
		renders: { files: { invitation_pdf_file: "/private/files/inv.pdf", issued_tender_pdf_file: "/private/files/tender.pdf" } },
		mappings: { supplier_response_schema: {}, evaluation_contract: {}, contract_obligations: {} },
		permitted_actions: { can_reopen: true },
		...overrides,
	};
}

describe("ApprovedScreen — TPR-DES-06", () => {
	it("renders the six labelled facts in artboard order, the two renders and the three mappings", () => {
		const w = mount(ApprovedScreen, { props: { view: view() } });
		expect(w.findAll(".kt-label").map((l) => l.text())).toEqual(["Approved by", "Requisition digest", "Template digest", "Package digest", "Publication handoff", "Publication consumption"]);
		expect(w.text()).toContain("Ready · not yet consumed");
		expect(w.find('[data-testid="tpr-consumption-status"]').text()).toBe("Awaiting downstream acknowledgment");
		expect(w.findAll("a.tpr-tag").map((a) => a.attributes("href"))).toEqual(["/private/files/inv.pdf", "/private/files/tender.pdf"]);
		expect(w.findAll(".tpr-tag.is-accent").map((t) => t.text())).toEqual(["Supplier-response schema · complete", "Evaluation contract · complete", "Contract-obligation projection · complete"]);
	});

	it("offers Reopen only when the server permits and shows the consumed instant otherwise", async () => {
		const open = mount(ApprovedScreen, { props: { view: view() } });
		await open.find('[data-testid="tpr-reopen"]').trigger("click");
		expect(open.emitted("reopen")).toBeTruthy();
		const consumed = mount(ApprovedScreen, { props: { view: view({ publication_handoff: { status: "Consumed", consumed_at: "15 May 2100, 08:00 EAT" }, permitted_actions: { can_reopen: false } }) } });
		expect(consumed.find('[data-testid="tpr-reopen"]').exists()).toBe(false);
		expect(consumed.find('[data-testid="tpr-consumption-status"]').text()).toBe("Consumed 15 May 2100, 08:00 EAT");
	});
});
