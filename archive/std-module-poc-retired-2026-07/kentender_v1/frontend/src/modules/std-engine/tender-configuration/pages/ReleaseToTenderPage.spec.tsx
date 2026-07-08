import "@testing-library/jest-dom/vitest";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { SEC_API_ACTION_AVAILABILITY_METHOD } from "../../shared/action-availability/constants";
import { ReleaseToTenderPage } from "./ReleaseToTenderPage";

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

const stdA = {
	versionCode: "STD-A",
	title: "PPRA Works",
	revision: "Rev April 2022",
	authority: "PPRA",
	profile: "Works profile",
	supportedMethods: ["Open Tender"],
	requiresBoq: true,
	requiresSpecifications: true,
	requiresDrawings: true,
};
const stdB = {
	versionCode: "STD-B",
	title: "Alt STD",
	revision: "Rev 1",
	authority: "KenTender",
	supportedMethods: ["RFQ"],
	requiresBoq: false,
	requiresSpecifications: false,
	requiresDrawings: false,
};

describe("ReleaseToTenderPage (UI-HARD-0300)", () => {
	afterEach(() => {
		cleanup();
		vi.unstubAllGlobals();
		vi.restoreAllMocks();
	});

	it("UI-SMOKE-REL-001 — Approved package shows Release to Tender (canonical React)", async () => {
		vi.stubGlobal("frappe", { call: vi.fn(async () => availabilityOk("RELEASE_PACKAGE_TO_TENDER")) });
		const { container } = render(
			<ReleaseToTenderPage
				packageCode="PKG-MOH-2026-001"
				packageTitle="Rehabilitation of District Health Centre"
				eligibilityStatus="eligible"
				compatibleStdSummary="Compatible STD: PPRA Works — Building and Associated Civil Engineering Works — Rev April 2022"
				stdOptions={[stdA]}
			/>,
		);
		expect(screen.getByTestId("release-to-tender-page")).toBeInTheDocument();
		expect(screen.getByTestId("release-package-summary")).toBeInTheDocument();
		expect(screen.getByTestId("release-eligibility-status")).toHaveTextContent("Eligible");
		expect(screen.getByTestId("release-blocker-list")).toBeInTheDocument();
		expect(screen.getByTestId("release-std-options")).toBeInTheDocument();
		expect(screen.getByTestId("release-selected-std-confirmation")).toBeInTheDocument();
		const releaseBtn = screen.getByTestId("release-action-button");
		expect(releaseBtn).toBeVisible();
		/* `ActionAwareButton` stays in `loading` until `getActionAvailability` resolves (Strict Mode may double-invoke). */
		await waitFor(
			() => {
				expect(screen.getByTestId("release-action-button")).toHaveAttribute("title", "OK");
			},
			{ timeout: 5000 },
		);
		expect(container.textContent).not.toContain("Create STD Instance");
	});

	it("UI-SMOKE-REL-002 — Blocked package shows blockers", () => {
		vi.stubGlobal("frappe", { call: vi.fn(async () => availabilityOk("RELEASE_PACKAGE_TO_TENDER")) });
		render(
			<ReleaseToTenderPage
				packageCode="PKG-1"
				packageTitle="T"
				eligibilityStatus="blocked"
				blockers={[
					{
						code: "PLAN_001",
						message: "Plan not approved.",
						severity: "critical",
						affectedArea: "Planning",
					},
					{
						code: "STD_NO_TEMPLATE",
						message: "No active compatible STD.",
						severity: "critical",
						affectedArea: "STD library",
					},
					{
						code: "PERM_DENIED",
						message: "Missing permission.",
						severity: "warning",
						affectedArea: "Security",
					},
					{
						code: "REL_ALREADY",
						message: "Already released.",
						severity: "info",
						affectedArea: "Package",
					},
				]}
				stdOptions={[stdA]}
			/>,
		);
		expect(screen.getByTestId("release-eligibility-status")).toHaveTextContent("Blocked");
		expect(screen.getByTestId("release-blocker-group-planning")).toBeInTheDocument();
		expect(screen.getByTestId("release-blocker-group-std")).toBeInTheDocument();
		expect(screen.getByTestId("release-blocker-group-permission")).toBeInTheDocument();
		expect(screen.getByTestId("release-blocker-group-released")).toBeInTheDocument();
	});

	it("UI-SMOKE-REL-003 — Multiple STD options require selection", async () => {
		const call = vi.fn(async (opts: { args?: { action_code?: string } }) =>
			availabilityOk(String(opts.args?.action_code || "")),
		);
		vi.stubGlobal("frappe", { call });
		const onRelease = vi.fn();
		render(
			<ReleaseToTenderPage
				packageCode="PKG-1"
				packageTitle="T"
				eligibilityStatus="eligible"
				stdOptions={[stdA, stdB]}
				onReleaseClick={onRelease}
			/>,
		);
		expect(screen.getByTestId("release-action-button")).toBeDisabled();
		fireEvent.click(screen.getByDisplayValue("STD-B"));
		await waitFor(() => {
			const enabled = screen.getByTestId("release-action-button");
			expect(enabled).not.toBeDisabled();
		});
		fireEvent.click(screen.getByTestId("release-action-button"));
		await waitFor(() => expect(onRelease).toHaveBeenCalled());
		expect(call).toHaveBeenCalledWith(
			expect.objectContaining({
				method: SEC_API_ACTION_AVAILABILITY_METHOD,
				args: expect.objectContaining({
					action_code: "RELEASE_PACKAGE_TO_TENDER",
					object_type: "Procurement Package",
					object_code: "PKG-1",
				}),
			}),
		);
	});

	it("UI-SMOKE-REL-004 — Release success shows Tender and STD Instance references", () => {
		vi.stubGlobal("frappe", { call: vi.fn(async () => availabilityOk("X")) });
		render(
			<ReleaseToTenderPage
				packageCode="PKG-1"
				packageTitle="T"
				eligibilityStatus="eligible"
				stdOptions={[stdA]}
				releaseResult={{ tenderCode: "TND-100", stdInstanceCode: "SI-200" }}
			/>,
		);
		const panel = screen.getByTestId("release-success-panel");
		expect(panel).toHaveTextContent("Package released to Tender successfully.");
		expect(panel).toHaveTextContent("TND-100");
		expect(panel).toHaveTextContent("SI-200");
		const link = screen.getByTestId("release-configure-tender-link");
		expect(link).toHaveAttribute("href", "/app/tenders/TND-100/configure-document");
	});
});
