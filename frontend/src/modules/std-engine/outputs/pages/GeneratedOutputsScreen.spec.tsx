import "@testing-library/jest-dom/vitest";
import { cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { SEC_API_ACTION_AVAILABILITY_METHOD } from "../../shared/action-availability/constants";
import { GENERATED_OUTPUT_CARD_TITLE } from "./generatedOutputsScreen.types";
import { GeneratedOutputsScreen } from "./GeneratedOutputsScreen";

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

const sampleOutputs = {
	bundle: {
		status: "Ready",
		version: "3",
		generatedAt: "2026-05-11T10:00:00Z",
		stale: true,
		sourceSnapshot: "cfg-snap-009",
	},
	dsm: {
		status: "Ready",
		version: "3",
		generatedAt: "2026-05-11T10:01:00Z",
		stale: false,
		sourceSnapshot: null,
	},
} as const;

describe("GeneratedOutputsScreen (UI-HARD-0900)", () => {
	afterEach(() => {
		cleanup();
		vi.unstubAllGlobals();
		vi.restoreAllMocks();
	});

	it("exposes pack data-testids for screen, cards, generate-all, and manual-edit absence marker", () => {
		vi.stubGlobal("frappe", { call: vi.fn(async () => availabilityOk("X")) });
		render(
			<GeneratedOutputsScreen
				contextTitle="Tender TND-1"
				outputs={{}}
				generateAllAction={{
					actionCode: "GENERATE_STD_OUTPUTS",
					objectType: "Tender",
					objectCode: "TND-1",
					onAllowedClick: vi.fn(),
				}}
			/>,
		);
		expect(screen.getByTestId("generated-outputs-screen")).toBeInTheDocument();
		expect(screen.getByTestId("output-card-bundle")).toBeInTheDocument();
		expect(screen.getByTestId("output-card-dsm")).toBeInTheDocument();
		expect(screen.getByTestId("output-card-dom")).toBeInTheDocument();
		expect(screen.getByTestId("output-card-dem")).toBeInTheDocument();
		expect(screen.getByTestId("output-card-dcm")).toBeInTheDocument();
		expect(screen.getByTestId("output-generate-all-button")).toBeInTheDocument();
		expect(screen.getByTestId("output-manual-edit-button-absent")).toBeInTheDocument();
	});

	it("shows plain-language card titles and stale indicator", () => {
		vi.stubGlobal("frappe", { call: vi.fn(async () => availabilityOk("X")) });
		render(
			<GeneratedOutputsScreen
				contextTitle="TND-1"
				outputs={{ ...sampleOutputs }}
				generateAllAction={{ actionCode: "X", objectType: "T", objectCode: "TND-1", onAllowedClick: vi.fn() }}
			/>,
		);
		const bundle = screen.getByTestId("output-card-bundle");
		expect(bundle).toHaveTextContent(GENERATED_OUTPUT_CARD_TITLE.bundle);
		expect(within(bundle).getByText("Stale")).toBeInTheDocument();
		const dsm = screen.getByTestId("output-card-dsm");
		expect(within(dsm).getByText("Current")).toBeInTheDocument();
		expect(bundle).toHaveTextContent("cfg-snap-009");
	});

	it("does not offer manual edit as a control", () => {
		vi.stubGlobal("frappe", { call: vi.fn(async () => availabilityOk("X")) });
		render(
			<GeneratedOutputsScreen
				contextTitle="TND-1"
				outputs={{}}
				generateAllAction={{ actionCode: "X", objectType: "T", objectCode: "TND-1", onAllowedClick: vi.fn() }}
			/>,
		);
		expect(screen.queryByRole("button", { name: /manual edit/i })).toBeNull();
		expect(screen.getByTestId("output-manual-edit-button-absent")).toHaveTextContent("No manual legal edits");
	});

	it("shows traceability only when permission allows", () => {
		vi.stubGlobal("frappe", { call: vi.fn(async () => availabilityOk("X")) });
		const { rerender } = render(
			<GeneratedOutputsScreen
				contextTitle="TND-1"
				outputs={{}}
				generateAllAction={{ actionCode: "X", objectType: "T", objectCode: "TND-1", onAllowedClick: vi.fn() }}
				traceabilityAllowed={false}
				onViewTraceability={vi.fn()}
			/>,
		);
		expect(screen.queryByRole("button", { name: /traceability/i })).toBeNull();
		rerender(
			<GeneratedOutputsScreen
				contextTitle="TND-1"
				outputs={{}}
				generateAllAction={{ actionCode: "X", objectType: "T", objectCode: "TND-1", onAllowedClick: vi.fn() }}
				traceabilityAllowed
				onViewTraceability={vi.fn()}
			/>,
		);
		expect(screen.getAllByRole("button", { name: /view traceability/i }).length).toBeGreaterThan(0);
	});

	it("Generate all uses ActionAwareButton (SEC-0410)", async () => {
		const call = vi.fn(async (opts: { args?: { action_code?: string } }) =>
			availabilityOk(String(opts.args?.action_code || "")),
		);
		vi.stubGlobal("frappe", { call });
		const onGen = vi.fn();
		render(
			<GeneratedOutputsScreen
				contextTitle="TND-1"
				outputs={{}}
				generateAllAction={{
					actionCode: "GENERATE_STD_OUTPUTS",
					objectType: "Tender",
					objectCode: "TND-1",
					onAllowedClick: onGen,
				}}
			/>,
		);
		await waitFor(() => {
			expect(screen.getByTestId("output-generate-all-button")).not.toBeDisabled();
		});
		fireEvent.click(screen.getByTestId("output-generate-all-button"));
		await waitFor(() => expect(onGen).toHaveBeenCalled());
		const hit = call.mock.calls.find(
			(c) => (c[0] as { args?: { action_code?: string } })?.args?.action_code === "GENERATE_STD_OUTPUTS",
		);
		expect(hit?.[0]).toEqual(
			expect.objectContaining({
				method: SEC_API_ACTION_AVAILABILITY_METHOD,
				args: expect.objectContaining({
					action_code: "GENERATE_STD_OUTPUTS",
					object_type: "Tender",
					object_code: "TND-1",
				}),
			}),
		);
	});
});
