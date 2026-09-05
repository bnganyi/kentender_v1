// PLN-CHG-001 v1.12 §15 — PublicationResultScreen component tests (D14).
// PLN-DES-13: read-only approved Version, destination, attempt, result and
// acknowledgement; the retry only for a technical user on a failed attempt.
import { describe, expect, it } from "vitest";
import { mount } from "@vue/test-utils";
import PublicationResultScreen from "./PublicationResultScreen.vue";

const TASK = {
	outcome: "OK",
	publication: "PUB-1",
	publication_reference: "PUB-MOH-2027-001",
	header: { eyebrow: "ANNUAL PLAN PUBLICATION", title: "Publication result", reference_line: "PLN-MOH-2027-001 · Version 1", badge: "Publication pending", badge_kind: "attention" },
	plan_reference: "PLN-MOH-2027-001",
	approved_plan: { financial_year: "FY 2027/28", plan_items: 1, value_display: "KES 80,000,000", statutory_approval_line: "Responsible Cabinet Secretary · 9 Dec 2026, 11:00 EAT" },
	destination: { id: "MOH-APP-SANDBOX-v1", title: "KenTender Annual Plan Publication Sandbox" },
	configuration: "MOH-APP-SANDBOX-v1",
	attempt_number: 1,
	result: "Pending",
	attempted_display: "9 Dec 2026, 11:00 EAT",
	acknowledged_display: "",
	result_display: "Awaiting acknowledgement",
	acknowledgement_reference: "Not received",
	quiet_notice: "Publication is an automatic system action after statutory approval. It runs without a business-role control.",
	can_retry: false,
};

function make(task = TASK) {
	return mount(PublicationResultScreen, { props: { task, pending: false, errorSummary: "" } });
}

describe("PublicationResultScreen — PLN-DES-13", () => {
	it("renders the header, the Approved Plan card and the Publication card read-only", () => {
		const w = make();
		expect(w.find(".kt-page-kicker").text()).toBe("ANNUAL PLAN PUBLICATION");
		expect(w.find(".kt-page-title").text()).toBe("Publication result");
		expect(w.find('[data-testid="pub-badge"]').text()).toBe("Publication pending");
		expect(w.find('[data-testid="pub-approved-plan"]').findAll("label").map((l) => l.text())).toEqual(["Financial Year", "Plan Items", "Approved value", "Statutory approval"]);
		expect(w.find('[data-testid="pub-publication"]').findAll("label").map((l) => l.text())).toEqual(["Destination", "Configuration", "Latest attempt", "Result", "Acknowledgement reference"]);
		expect(w.find('[data-testid="pub-result"]').text()).toBe("Awaiting acknowledgement");
		expect(w.find('[data-testid="pub-reference"]').text()).toBe("Not received");
		expect(w.find('[data-testid="pub-quiet-notice"]').text()).toBe(TASK.quiet_notice);
		expect(w.findAll("input, textarea, select")).toHaveLength(0);
		expect(w.text()).not.toContain("Publish");
		expect(w.find('[data-testid="pub-retry"]').exists()).toBe(false);
	});

	it("shows the failed state with the retry only for a technical user (§11.15)", async () => {
		const failed = { ...TASK, result: "Failed", result_display: "Not acknowledged", header: { ...TASK.header, badge: "Publication failed", badge_kind: "critical" } };
		const reader = make(failed);
		expect(reader.find('[data-testid="pub-failed"] h3').text()).toBe("Publication was not acknowledged");
		expect(reader.find('[data-testid="pub-retry"]').exists()).toBe(false);
		const technical = make({ ...failed, can_retry: true });
		const retry = technical.find('[data-testid="pub-retry"]');
		expect(retry.text()).toBe("Retry exact approved payload");
		await retry.trigger("click");
		expect(technical.emitted("retry")).toHaveLength(1);
	});

	it("an acknowledged publication reads its reference and no failed card", () => {
		const w = make({ ...TASK, result: "Acknowledged", result_display: "Acknowledged", acknowledgement_reference: "APP-ACK-2026-001", header: { ...TASK.header, badge: "Acknowledged", badge_kind: "live" } });
		expect(w.find('[data-testid="pub-badge"]').classes()).toContain("is-live");
		expect(w.find('[data-testid="pub-reference"]').text()).toBe("APP-ACK-2026-001");
		expect(w.find('[data-testid="pub-failed"]').exists()).toBe(false);
	});
});
