/**
 * UI-HARD-1620 — Officer completion UI smoke (pack §21 ticket 1620, doc §21.3).
 *
 * Canonical React surfaces under `std-engine` (Vitest / jsdom). Desk officer POC flows
 * remain in `tests/ui/smoke/procurement/officer-tender-poc-*.spec.ts`.
 */
import "@testing-library/jest-dom/vitest";
import { cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { BoqPreparationScreen } from "../works-completion/pages/BoqPreparationScreen";
import { BOQ_STALENESS_WARNING_PACK } from "../works-completion/pages/boqPreparationScreen.types";
import { DrawingRegisterScreen } from "../works-completion/pages/DrawingRegisterScreen";
import { ConfigureTenderDocumentOverviewPage } from "../tender-configuration/pages/ConfigureTenderDocumentOverviewPage";
import type { TenderConfigOutputRow } from "../tender-configuration/pages/configureTenderDocumentOverview.types";
import { TdsBusinessFieldScreen } from "../tender-configuration/pages/TdsBusinessFieldScreen";

function availabilityOk(action_code: string) {
	return {
		message: {
			success: true,
			actor_user_code: "Administrator",
			action_code,
			allowed: true,
			message: "OK",
			required_permission: null,
			risk_level: "Low",
			requires_confirmation: false,
			audit_on_attempt: false,
		},
	};
}

const sampleOutputs: TenderConfigOutputRow[] = [
	{ kind: "bundle", statusLabel: "Current" },
	{ kind: "dsm", statusLabel: "Current" },
	{ kind: "dom", statusLabel: "Stale" },
	{ kind: "dem", statusLabel: "Missing" },
	{ kind: "dcm", statusLabel: "Current" },
];

const defaultBoqProps = {
	header: {
		currency: "KES",
		pricing_model: "Item rate",
		arithmetic_correction_stage: "Post-opening",
	},
	bills: [{ id: "b1", code: "BILL-1", title: "Civil works" }],
	items: [
		{
			id: "i1",
			item_no: "1.1",
			description: "Excavation",
			item_type: "Works",
			quantity: "120",
			unit: "m3",
			supplier_input_mode: "Rate Only",
			provisional_or_fixed: "Fixed",
		},
	],
	validationMessages: [] as string[],
};

describe("UI-HARD-1620 — UI-SMOKE-OFFICER-* (officer completion)", () => {
	afterEach(() => {
		cleanup();
		vi.unstubAllGlobals();
		vi.restoreAllMocks();
	});

	it("UI-SMOKE-OFFICER-001 — Configure Tender Document opens tender-oriented overview", async () => {
		vi.stubGlobal("frappe", { call: vi.fn(async () => availabilityOk("GENERATE_STD_OUTPUTS")) });
		const { container } = render(
			<ConfigureTenderDocumentOverviewPage
				tenderCode="TND-100"
				tenderTitle="District Health Centre Rehabilitation"
				packageCode="PKG-MOH-2026-001"
				packageTitle="Rehabilitation of District Health Centre"
				selectedStdSummary="PPRA Works — Rev April 2022"
				completionPercent={42}
				outputs={sampleOutputs}
				readinessStatus="Incomplete"
				nextAction={{
					actionCode: "GENERATE_STD_OUTPUTS",
					objectType: "Tender",
					objectCode: "TND-100",
					label: "Regenerate tender outputs",
					onAllowedClick: vi.fn(),
				}}
			/>,
		);
		expect(screen.getByTestId("tender-config-overview-page")).toBeInTheDocument();
		expect(screen.getByTestId("tender-config-context-header")).toBeInTheDocument();
		expect(screen.getByTestId("tender-config-stage-list")).toBeInTheDocument();
		expect(screen.getByRole("heading", { level: 2, name: "Configure Tender Document" })).toBeInTheDocument();
		expect(container.textContent).not.toContain("Edit STD Instance");
		await waitFor(
			() => {
				expect(screen.getByTestId("tender-config-next-action")).toHaveAttribute("title", "OK");
			},
			{ timeout: 5000 },
		);
	});

	it("UI-SMOKE-OFFICER-002 — TDS shown as business fields", () => {
		vi.stubGlobal("frappe", { call: vi.fn(async () => availabilityOk("SAVE")) });
		render(
			<TdsBusinessFieldScreen
				instanceCode="SI-100"
				values={{}}
				onChange={vi.fn()}
				saveAction={{
					actionCode: "EDIT_STD_INSTANCE_PARAMETERS",
					objectType: "StdEngineWorksInstance",
					objectCode: "SI-100",
					onAllowedClick: vi.fn(),
				}}
			/>,
		);
		expect(screen.getByTestId("tds-screen")).toBeInTheDocument();
		expect(screen.getByTestId("tds-group-tender-identity")).toBeInTheDocument();
		expect(screen.getByTestId("tds-group-dates")).toBeInTheDocument();
		expect(screen.getByTestId("tds-group-security")).toBeInTheDocument();
		expect(screen.getByTestId("tds-field-submission-deadline")).toBeInTheDocument();
		expect(screen.getByTestId("tds-field-opening-datetime")).toBeInTheDocument();
	});

	it("UI-SMOKE-OFFICER-003 — ITT clauses not editable", () => {
		vi.stubGlobal("frappe", { call: vi.fn(async () => availabilityOk("SAVE")) });
		render(
			<TdsBusinessFieldScreen
				instanceCode="SI-1"
				values={{}}
				onChange={vi.fn()}
				saveAction={{
					actionCode: "X",
					objectType: "T",
					objectCode: "SI-1",
					onAllowedClick: vi.fn(),
				}}
			/>,
		);
		expect(screen.getByTestId("tds-itt-not-editable-notice")).toBeInTheDocument();
		const submissionSection = screen.getByTestId("tds-group-submission-instructions");
		expect(submissionSection.querySelector("textarea")).toBeNull();
	});

	it("UI-SMOKE-OFFICER-004 — BOQ has no supplier rate input", () => {
		render(<BoqPreparationScreen {...defaultBoqProps} />);
		expect(screen.getByTestId("boq-supplier-rate-field-absent")).toBeInTheDocument();
		const table = screen.getByTestId("boq-items-table");
		const headers = within(table).getAllByRole("columnheader");
		const text = headers.map((h) => h.textContent).join(" ");
		expect(text).not.toMatch(/\bRate\b/i);
		expect(text).not.toMatch(/supplier rate/i);
	});

	it("UI-SMOKE-OFFICER-005 — Drawing upload requires Section VII binding", () => {
		const onAdd = vi.fn();
		render(<DrawingRegisterScreen rows={[]} onAddDrawing={onAdd} />);
		expect(screen.getByTestId("drawing-section-vii-binding")).toBeVisible();
		fireEvent.change(screen.getByTestId("drawing-field-code"), { target: { value: "DWG-02" } });
		fireEvent.change(screen.getByTestId("drawing-field-revision"), { target: { value: "B" } });
		fireEvent.change(screen.getByLabelText(/title/i), { target: { value: "Detail" } });
		fireEvent.change(screen.getByLabelText(/file reference/i), { target: { value: "file.pdf" } });
		fireEvent.change(screen.getByLabelText(/^classification/i), { target: { value: "Internal Only" } });
		fireEvent.change(screen.getByLabelText(/issue status/i), { target: { value: "Draft" } });
		fireEvent.click(screen.getByTestId("drawing-add-row"));
		expect(onAdd).toHaveBeenCalledWith(
			expect.objectContaining({ section_code: "SECTION_VII_DRAWINGS" }),
		);
	});

	it("UI-SMOKE-OFFICER-006 — BOQ change shows output staleness warning", () => {
		const { rerender } = render(<BoqPreparationScreen {...defaultBoqProps} showStalenessWarning={false} />);
		expect(screen.queryByTestId("boq-staleness-warning")).not.toBeInTheDocument();
		rerender(<BoqPreparationScreen {...defaultBoqProps} showStalenessWarning />);
		expect(screen.getByTestId("boq-staleness-warning")).toHaveTextContent(BOQ_STALENESS_WARNING_PACK);
	});
});
