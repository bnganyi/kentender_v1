// KT-STD-001 §3A.2 — page-load states are inline cards, never modals.
import { describe, expect, it } from "vitest";
import { mount } from "@vue/test-utils";
import StateCard from "./StateCard.vue";

describe("StateCard — inline page states", () => {
	it("paints the skeleton while loading and nothing else", () => {
		const w = mount(StateCard, { props: { loading: true, prefix: "tpr-editor" } });
		expect(w.find('[data-testid="tpr-editor-loading"]').exists()).toBe(true);
		expect(w.find('[data-testid="tpr-editor-error"]').exists()).toBe(false);
	});

	it("paints the load error with its support reference and Try again", async () => {
		const w = mount(StateCard, { props: { error: "Internal Server Error", supportRef: "TPR-ERR-1", prefix: "tpr-task" } });
		expect(w.find('[data-testid="tpr-task-error"]').text()).toContain("Tender Preparation could not be loaded.");
		expect(w.text()).toContain("Support reference: TPR-ERR-1");
		await w.find("button").trigger("click");
		expect(w.emitted("reload")).toBeTruthy();
	});

	it("paints §11.3 Tender not found as data with Return to workspace", async () => {
		const w = mount(StateCard, { props: { notFound: true, prefix: "tpr-approved" } });
		expect(w.find('[data-testid="tpr-approved-not-found"]').text()).toContain("Tender not found.");
		await w.find("button").trigger("click");
		expect(w.emitted("home")).toBeTruthy();
	});

	it("paints the server's Forbidden heading and text verbatim", () => {
		const w = mount(StateCard, { props: { forbidden: { heading: "You do not have access to Tender Preparation.", text: "Ask for a responsibility." } } });
		expect(w.find('[data-testid="tpr-forbidden"] h3').text()).toBe("You do not have access to Tender Preparation.");
		expect(w.text()).toContain("Ask for a responsibility.");
	});
});
