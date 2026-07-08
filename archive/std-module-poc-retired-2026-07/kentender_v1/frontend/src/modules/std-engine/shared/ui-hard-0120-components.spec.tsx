import "@testing-library/jest-dom/vitest";
import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import { BlockerList } from "./blockers/BlockerList";
import { ResolutionActionLink } from "./blockers/ResolutionActionLink";
import { DenialNotice } from "./denials/DenialNotice";
import { OutputStatusBadge } from "./status/OutputStatusBadge";
import { ReadinessStatusBadge } from "./status/ReadinessStatusBadge";

describe("UI-HARD-0120 shared components", () => {
	afterEach(() => {
		cleanup();
	});

	it("BlockerList uses pack selectors and resolution links", () => {
		render(
			<BlockerList
				blockers={[
					{
						code: "DEM/STALE",
						message: "Evaluation Rules (DEM) are stale.",
						severity: "critical",
						affectedArea: "Readiness — Evaluation outputs",
						whyItMatters: "Evaluation cannot legally proceed from outdated rules.",
						resolutionAction: "Regenerate outputs, then rerun readiness.",
						affectedSectionHref: "/desk#readiness-eval",
						resolutionHref: "/desk#readiness",
					},
				]}
			/>,
		);

		expect(screen.getByTestId("blocker-list")).toBeInTheDocument();
		expect(screen.getByTestId("blocker-item-DEM_STALE")).toBeInTheDocument();
		expect(screen.getByTestId("resolution-action-link-DEM_STALE-section")).toHaveAttribute("href", "/desk#readiness-eval");
		expect(screen.getByTestId("resolution-action-link-DEM_STALE-resolve")).toHaveAttribute("href", "/desk#readiness");
	});

	it("DenialNotice never renders stack-like primary copy", () => {
		const stack = `Error: failed
    at handler (x.js:1:1)`;
		render(<DenialNotice message={stack} />);
		expect(screen.getByTestId("denial-notice")).not.toHaveTextContent("at handler");
		expect(screen.getByTestId("denial-notice")).not.toHaveTextContent("Error: failed");
	});

	it("DenialNotice hides denial code by default and shows it in audit mode", () => {
		const { rerender } = render(
			<DenialNotice message="You cannot edit this tender because it has been published." denialCode="PUB_IMMUTABLE" />,
		);
		expect(screen.getByTestId("denial-notice")).toHaveTextContent("You cannot edit this tender");
		expect(screen.queryByTestId("denial-notice-technical-code")).not.toBeInTheDocument();

		rerender(
			<DenialNotice
				message="You cannot edit this tender because it has been published."
				denialCode="PUB_IMMUTABLE"
				showDenialCode
			/>,
		);
		expect(screen.getByTestId("denial-notice-technical-code")).toHaveTextContent("PUB_IMMUTABLE");
	});

	it("ReadinessStatusBadge exposes readiness-status-badge", () => {
		render(<ReadinessStatusBadge status="Blocked" />);
		const el = screen.getByTestId("readiness-status-badge");
		expect(el).toHaveTextContent("Blocked");
	});

	it("OutputStatusBadge uses output-status-badge-{outputType} with sanitized type", () => {
		render(<OutputStatusBadge outputType="BOQ/PDF" statusLabel="Stale" />);
		expect(screen.getByTestId("output-status-badge-BOQ_PDF")).toHaveTextContent("Stale");
	});

	it("ResolutionActionLink is standalone", () => {
		render(<ResolutionActionLink code="fix-1" href="/desk#x" label="Fix now" />);
		expect(screen.getByTestId("resolution-action-link-fix-1")).toHaveAttribute("href", "/desk#x");
	});
});
