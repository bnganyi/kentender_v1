// An incident's full details are an explicit, audited read that names its purpose (Project Owner, 10 Oct 2026).
import { beforeEach, describe, expect, it, vi } from "vitest";
import { mount } from "@vue/test-utils";
import { nextTick } from "vue";

vi.mock("../data/api.js", () => ({ getIncidentDetails: vi.fn() }));
import { getIncidentDetails } from "../data/api.js";
import IncidentDetails from "./IncidentDetails.vue";

const PURPOSES = ["Investigate the problem", "Record the resolution", "Check the problem as a committee member", "Audit the opening"];
const mountIt = () => mount(IncidentDetails, { props: { tender: "TND-MOH-2027-033", incident: "INC-OPEN-0001-01", purposes: PURPOSES } });
const settle = async () => { for (let i = 0; i < 4; i += 1) await nextTick(); };

describe("IncidentDetails", () => {
	beforeEach(() => getIncidentDetails.mockReset());

	it("reads nothing until a purpose is chosen and the button is pressed, and says the read is recorded", async () => {
		const w = mountIt();
		await settle();
		expect(getIncidentDetails).not.toHaveBeenCalled(); // mounting, polling and refreshing never read
		expect(w.get('[data-testid="bop-incident-show"]').attributes("disabled")).toBeDefined();
		expect(w.text()).toContain("recorded with your name, the time and your purpose");
	});

	it("names the purpose in the request and shows the details, with the envelope only when the server sends it", async () => {
		getIncidentDetails.mockResolvedValue({ ok: true, details: { status: "Open", raised_label: "11:00:05", handled_by: "Opening access support", notification_state: "Delivered", notification_attempts: 2, last_notified_label: "11:02", envelope: "ENV-1", resolution_note: "", resolved_label: "", resolved_by: "" } });
		const w = mountIt();
		await w.get('[data-testid="bop-incident-purpose"]').setValue("Investigate the problem");
		await w.get('[data-testid="bop-incident-show"]').trigger("click");
		await settle();
		expect(getIncidentDetails).toHaveBeenCalledTimes(1);
		expect(getIncidentDetails).toHaveBeenCalledWith("TND-MOH-2027-033", "INC-OPEN-0001-01", "Investigate the problem");
		const text = w.get('[data-testid="bop-incident-detail-table"]').text();
		expect(text).toContain("2 attempts");
		expect(text).toContain("ENV-1");
	});

	it("shows no envelope row when the server withholds it", async () => {
		getIncidentDetails.mockResolvedValue({ ok: true, details: { status: "Open", raised_label: "11:00:05", handled_by: "Opening access support", notification_state: "Delivered", notification_attempts: 1, last_notified_label: "", resolution_note: "", resolved_label: "", resolved_by: "" } });
		const w = mountIt();
		await w.get('[data-testid="bop-incident-purpose"]').setValue("Check the problem as a committee member");
		await w.get('[data-testid="bop-incident-show"]').trigger("click");
		await settle();
		expect(w.get('[data-testid="bop-incident-detail-table"]').text()).not.toContain("Envelope");
	});

	it("keeps the form and says so when the details are refused", async () => {
		getIncidentDetails.mockImplementationOnce(() => new Promise((_, reject) => setTimeout(() => reject(new Error("Not found")), 0)));
		const w = mountIt();
		await w.get('[data-testid="bop-incident-purpose"]').setValue("Audit the opening");
		await w.get('[data-testid="bop-incident-show"]').trigger("click");
		await new Promise((resolve) => setTimeout(resolve, 20));
		await settle();
		expect(w.get('[data-testid="bop-incident-error"]').text()).toBe("These details are not available to you.");
		expect(w.find('[data-testid="bop-incident-detail-table"]').exists()).toBe(false);
	});
});
