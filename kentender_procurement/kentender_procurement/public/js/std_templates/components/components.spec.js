// STD Templates component behaviour (STD-TPL-001 v0.10 §11.2–11.4): filters,
// truthful empty states, lifecycle variants, disclosures and the bounded
// Report concern dialog. Server projections are the fixtures; no component
// derives a status, count or permission of its own.
import { describe, expect, it, vi } from "vitest";
import { mount } from "@vue/test-utils";

import ReleaseList from "./ReleaseList.vue";
import ReleaseDetail from "./ReleaseDetail.vue";
import ReportConcernDialog from "./ReportConcernDialog.vue";
import { detailPayload, listPayload } from "./fixtures.js";

const g = { global: { mocks: { __: (s) => s } } };

describe("ReleaseList", () => {
	it("renders one row per installed release with its consequence line", () => {
		const w = mount(ReleaseList, { props: { data: listPayload() }, ...g });
		expect(w.findAll("tbody")).toHaveLength(1);
		expect(w.text()).toContain("This release cannot be used to publish a Tender. Open it to see why.");
		expect(w.find('[data-testid="stdt-clear-filters"]').exists()).toBe(false);
	});

	it("offers Clear filters only while a filter is active", () => {
		const w = mount(ReleaseList, { props: { data: listPayload(), status: "Available" }, ...g });
		expect(w.find('[data-testid="stdt-clear-filters"]').exists()).toBe(true);
	});

	it("emits the chosen status at once and debounces search", async () => {
		vi.useFakeTimers();
		const w = mount(ReleaseList, { props: { data: listPayload() }, ...g });
		await w.find('[data-testid="stdt-filter-status"]').setValue("Withdrawn");
		expect(w.emitted("filter").at(-1)[0]).toEqual({ search: "", status: "Withdrawn" });
		await w.find('[data-testid="stdt-filter-search"]').setValue("IT");
		expect(w.emitted("filter")).toHaveLength(1);
		vi.advanceTimersByTime(400);
		expect(w.emitted("filter").at(-1)[0]).toEqual({ search: "IT", status: "Withdrawn" });
		vi.useRealTimers();
	});

	it("shows the filtered-empty and installed-empty states with the right action", () => {
		const filtered = mount(ReleaseList, { props: { data: listPayload("filtered"), status: "Withdrawn" }, ...g });
		expect(filtered.find('[data-testid="stdt-list-filtered-empty"]').text()).toContain("No STD Templates match these filters.");
		const installed = mount(ReleaseList, { props: { data: listPayload("installed") }, ...g });
		const empty = installed.find('[data-testid="stdt-list-installed-empty"]');
		expect(empty.text()).toContain("Ask whoever manages this site to install a release.");
		expect(empty.find("button").exists()).toBe(false);
	});

	it("shows the read failure with Try again and never stale rows", async () => {
		const w = mount(ReleaseList, { props: { data: listPayload(), failed: true }, ...g });
		expect(w.find('[data-testid="stdt-list-table"]').exists()).toBe(false);
		await w.find('[data-testid="stdt-list-retry"]').trigger("click");
		expect(w.emitted("retry")).toBeTruthy();
	});

	it("never offers an edit, activate, approve, upload or repair action", () => {
		const w = mount(ReleaseList, { props: { data: listPayload() }, ...g });
		expect(w.text()).not.toMatch(/\b(Add|Edit|Activate|Approve|Upload|Replace|Override|Repair)\b/);
	});
});

describe("ReleaseDetail", () => {
	it("keeps digests and renderer keys out of the default reading path", () => {
		const w = mount(ReleaseDetail, { props: { data: detailPayload() }, ...g });
		expect(w.text()).not.toContain("GOODS-IT-SIMPLE-V1");
		expect(w.find("#stdt-technical-body").exists()).toBe(false);
	});

	it("opens Technical details, coverage and change details through the URL fragment", async () => {
		const w = mount(ReleaseDetail, { props: { data: detailPayload() }, ...g });
		await w.find('[data-testid="stdt-technical"] button').trigger("click");
		expect(w.emitted("hash").at(-1)[0]).toEqual({ tech: "1", __replace: true });
		const open = mount(ReleaseDetail, { props: { data: detailPayload(), hashState: { tech: "1" } }, ...g });
		expect(open.find("#stdt-technical-body").text()).toContain("GOODS-IT-SIMPLE-V1");
		expect(open.find('[data-testid="stdt-technical"] button').attributes("aria-expanded")).toBe("true");
	});

	it("section links set the selected section", async () => {
		const w = mount(ReleaseDetail, { props: { data: detailPayload() }, ...g });
		await w.find('[data-testid="stdt-nav-verification"]').trigger("click");
		expect(w.emitted("hash").at(-1)[0]).toEqual({ section: "verification" });
	});

	it("Available shows no blockers and the site switch On; no approval step exists", () => {
		const w = mount(ReleaseDetail, { props: { data: detailPayload("Available") }, ...g });
		expect(w.find('[data-testid="stdt-blockers"]').text()).toContain("No blockers.");
		expect(w.find('[data-testid="stdt-verification-table"]').text()).toMatch(/Site switch\s*On/);
		expect(w.text()).not.toMatch(/APPROVE EXACT MANIFEST|Owner approval/);
	});

	it("a switched-off release names the switch as its one blocker", () => {
		const w = mount(ReleaseDetail, { props: { data: detailPayload("Unavailable") }, ...g });
		expect(w.find('[data-testid="stdt-blockers"]').text()).toContain("This release is switched off on this site.");
		expect(w.find('[data-testid="stdt-verification-table"]').text()).toMatch(/Site switch\s*Off/);
	});

	it("Superseded names its successor; Withdrawn shows only the facts supplied", () => {
		const s = mount(ReleaseDetail, { props: { data: detailPayload("Superseded") }, ...g });
		expect(s.find('[data-testid="stdt-successor"]').text()).toContain("Release 1.2");
		const w = mount(ReleaseDetail, { props: { data: detailPayload("Withdrawn") }, ...g });
		const facts = w.find('[data-testid="stdt-withdrawal"]').text();
		expect(facts).toContain("Legal defect in the reservation clause.");
		expect(facts).not.toContain("Successor");
	});

	it("a failed verification puts the failed blocker first with its badge", () => {
		const data = detailPayload();
		data.release.failed_verification = true;
		data.blockers = [{ n: 1, text: "Asset 06_runtime/response_rules.json no longer matches its installed digest.", owner: "Controlled template-release owner (bnganyi)", failed: true, gate_id: "GATE-INTEGRITY" }, ...data.blockers];
		data.variant = { earlier_success: "Last successful verification 26 September 2026, 00:09 EAT" };
		const w = mount(ReleaseDetail, { props: { data }, ...g });
		const first = w.find('[data-testid="stdt-blockers"] li');
		expect(first.find(".kt-status.is-critical").text()).toBe("Failed");
		expect(w.find('[data-testid="stdt-earlier-success"]').exists()).toBe(true);
	});

	it("shows the read failure with Back and Try again", async () => {
		const w = mount(ReleaseDetail, { props: { data: {}, failed: true }, ...g });
		expect(w.text()).toContain("STD Template details could not be loaded. Try again.");
		await w.find('[data-testid="stdt-detail-retry"]').trigger("click");
		expect(w.emitted("retry")).toBeTruthy();
	});

	it("Report concern is the only write action", async () => {
		const w = mount(ReleaseDetail, { props: { data: detailPayload() }, ...g });
		await w.find('[data-testid="stdt-report-concern"]').trigger("click");
		expect(w.emitted("report")).toBeTruthy();
		expect(w.text()).not.toMatch(/\b(Edit|Activate|Approve release|Upload|Replace|Override|Repair|Withdraw release|Supersede)\b/);
	});
});

describe("ReportConcernDialog", () => {
	const props = { release: detailPayload().release, categories: detailPayload().concerns.categories };

	it("submits the entered values and the chosen file", async () => {
		const w = mount(ReportConcernDialog, { props, ...g });
		await w.find('[data-testid="stdt-rc-category"]').setValue("Source treatment");
		await w.find('[data-testid="stdt-rc-locator"]').setValue("STD row 184");
		await w.find('[data-testid="stdt-rc-summary"]').setValue("Confirm exclusion reason");
		await w.find('[data-testid="stdt-rc-description"]').setValue("The exclusion reason should name its source basis.");
		await w.find('[data-testid="stdt-rc-submit"]').trigger("click");
		expect(w.emitted("submit")[0][0]).toEqual({
			values: { category: "Source treatment", source_locator: "STD row 184", summary: "Confirm exclusion reason", description: "The exclusion reason should name its source basis." },
			file: null,
		});
	});

	it("shows each field error next to its field and keeps the entered text", async () => {
		const w = mount(ReportConcernDialog, { props: { ...props, errors: { summary: "Enter a summary of at least 5 characters." } }, ...g });
		await w.find('[data-testid="stdt-rc-summary"]').setValue("abc");
		const field = w.find('[data-testid="stdt-rc-summary"]').element.closest(".field");
		expect(field.textContent).toContain("Enter a summary of at least 5 characters.");
		expect(w.find('[data-testid="stdt-rc-summary"]').element.value).toBe("abc");
	});

	it("states that a concern does not change availability, and Escape cancels", async () => {
		const w = mount(ReportConcernDialog, { props, ...g });
		expect(w.text()).toContain("Reporting a concern does not change this release's availability.");
		await w.find('[data-testid="stdt-concern-dialog"]').trigger("keydown", { key: "Escape" });
		expect(w.emitted("cancel")).toBeTruthy();
	});
});
