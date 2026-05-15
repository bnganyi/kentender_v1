import "@testing-library/jest-dom/vitest";
import { cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { SEC_API_ACTION_AVAILABILITY_METHOD } from "../../shared/action-availability/constants";
import { ConfigureTenderDocumentOverviewPage } from "./ConfigureTenderDocumentOverviewPage";
import {
	TENDER_CONFIGURE_WORKS_STAGE_LABELS,
	type TenderConfigOutputRow,
} from "./configureTenderDocumentOverview.types";

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

function minimalProps(overrides: Partial<Parameters<typeof ConfigureTenderDocumentOverviewPage>[0]> = {}) {
	return {
		tenderCode: "TND-100",
		tenderTitle: "District Health Centre Rehabilitation",
		packageCode: "PKG-MOH-2026-001",
		packageTitle: "Rehabilitation of District Health Centre",
		selectedStdSummary: "PPRA Works — Building and Associated Civil Engineering Works — Rev April 2022",
		completionPercent: 42,
		outputs: sampleOutputs,
		readinessStatus: "Incomplete" as const,
		nextAction: {
			actionCode: "GENERATE_STD_OUTPUTS",
			objectType: "Tender",
			objectCode: "TND-100",
			label: "Regenerate tender outputs",
			onAllowedClick: vi.fn(),
		},
		...overrides,
	};
}

describe("ConfigureTenderDocumentOverviewPage (UI-HARD-0400)", () => {
	afterEach(() => {
		cleanup();
		vi.unstubAllGlobals();
		vi.restoreAllMocks();
	});

	it("exposes pack data-testids and uses tender-oriented title (not prohibited labels)", () => {
		vi.stubGlobal("frappe", { call: vi.fn(async () => availabilityOk("GENERATE_STD_OUTPUTS")) });
		const { container } = render(<ConfigureTenderDocumentOverviewPage {...minimalProps()} />);
		expect(screen.getByTestId("tender-config-overview-page")).toBeInTheDocument();
		expect(screen.getByTestId("tender-config-context-header")).toBeInTheDocument();
		expect(screen.getByTestId("tender-config-selected-std")).toBeInTheDocument();
		expect(screen.getByTestId("tender-config-stage-list")).toBeInTheDocument();
		expect(screen.getByTestId("tender-config-output-statuses")).toBeInTheDocument();
		expect(screen.getByTestId("tender-config-readiness-status")).toBeInTheDocument();
		expect(screen.getByRole("heading", { level: 2, name: "Configure Tender Document" })).toBeInTheDocument();
		const h2 = screen.getByRole("heading", { level: 2 });
		expect(h2.textContent).not.toContain("Edit STD Instance");
		expect(h2.textContent).not.toContain("Edit Generated Models");
		expect(container.textContent).not.toMatch(/Configure DSM\/DOM\/DEM\/DCM/i);
	});

	it("defaults Works stages to pack labels with Not Started", () => {
		vi.stubGlobal("frappe", { call: vi.fn(async () => availabilityOk("GENERATE_STD_OUTPUTS")) });
		render(<ConfigureTenderDocumentOverviewPage {...minimalProps({ stages: undefined })} />);
		const stageSection = screen.getByTestId("tender-config-stage-list");
		for (const label of TENDER_CONFIGURE_WORKS_STAGE_LABELS) {
			expect(within(stageSection).getByText(label)).toBeInTheDocument();
		}
		expect(within(stageSection).getAllByText("Not Started").length).toBe(TENDER_CONFIGURE_WORKS_STAGE_LABELS.length);
	});

	it("shows output rows with plain names plus acronym hints where required by doc §8.5", () => {
		vi.stubGlobal("frappe", { call: vi.fn(async () => availabilityOk("GENERATE_STD_OUTPUTS")) });
		render(<ConfigureTenderDocumentOverviewPage {...minimalProps()} />);
		const section = screen.getByTestId("tender-config-output-statuses");
		expect(section).toHaveTextContent("Tender document bundle");
		expect(section).toHaveTextContent("Submission Rules (DSM)");
		expect(section).toHaveTextContent("Opening Register (DOM)");
		expect(section).toHaveTextContent("Evaluation Rules (DEM)");
		expect(section).toHaveTextContent("Contract Carry-Forward (DCM)");
		expect(section).toHaveTextContent("Stale");
		expect(section).toHaveTextContent("Missing");
	});

	it("drives next action from ActionAwareButton (SEC-0410)", async () => {
		const call = vi.fn(async (opts: { args?: { action_code?: string } }) =>
			availabilityOk(String(opts.args?.action_code || "")),
		);
		vi.stubGlobal("frappe", { call });
		const onNext = vi.fn();
		render(
			<ConfigureTenderDocumentOverviewPage
				{...minimalProps({
					nextAction: {
						actionCode: "GENERATE_STD_OUTPUTS",
						objectType: "Tender",
						objectCode: "TND-100",
						label: "Regenerate tender outputs",
						onAllowedClick: onNext,
					},
				})}
			/>,
		);
		await waitFor(() => {
			const btn = screen.getByTestId("tender-config-next-action");
			expect(btn).not.toBeDisabled();
		});
		fireEvent.click(screen.getByTestId("tender-config-next-action"));
		await waitFor(() => expect(onNext).toHaveBeenCalled());
		expect(call).toHaveBeenCalledWith(
			expect.objectContaining({
				method: SEC_API_ACTION_AVAILABILITY_METHOD,
				args: expect.objectContaining({
					action_code: "GENERATE_STD_OUTPUTS",
					object_type: "Tender",
					object_code: "TND-100",
				}),
			}),
		);
	});

	it("omits primary CTA when nextAction is null", () => {
		vi.stubGlobal("frappe", { call: vi.fn(async () => availabilityOk("X")) });
		render(<ConfigureTenderDocumentOverviewPage {...minimalProps({ nextAction: null })} />);
		expect(screen.queryByTestId("tender-config-next-action")).not.toBeInTheDocument();
	});
});
