import "@testing-library/jest-dom/vitest";
import { cleanup, render, screen, within } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import { PUBLISHED_STATE_LOCK_MESSAGE } from "./publishedStateSummaryScreen.constants";
import { PublishedStateSummaryScreen } from "./PublishedStateSummaryScreen";
import type { PublishedStateSummaryScreenProps } from "./publishedStateSummaryScreen.types";

function minimalProps(overrides: Partial<PublishedStateSummaryScreenProps> = {}): PublishedStateSummaryScreenProps {
	return {
		tenderCode: "TND-400",
		snapshotCode: "SNAP-MOH-2026-0007",
		bundleVersion: "Bundle v5 (published 2026-05-11)",
		dsmVersion: "DSM v4",
		domVersion: "DOM v4",
		demVersion: "DEM v4",
		dcmVersion: "DCM v2",
		evidencePackageHref: "/desk/tenders/TND-400/evidence",
		evidencePackageLinkLabel: "View sealed evidence package",
		nextLifecycleStep: "Opening session scheduling — assign Opening Officer in Tender Operations.",
		addendumReissueGuidance:
			"Material changes after publication require a formal addendum or a controlled reissue per PPRA guidance; contact Procurement Legal before altering scope or evaluation rules.",
		...overrides,
	};
}

describe("PublishedStateSummaryScreen (UI-HARD-1210)", () => {
	afterEach(() => {
		cleanup();
	});

	it("exposes pack data-testids and exact published lock message", () => {
		render(<PublishedStateSummaryScreen {...minimalProps()} />);
		expect(screen.getByTestId("published-state-summary")).toBeInTheDocument();
		expect(screen.getByTestId("published-snapshot-code")).toHaveTextContent("SNAP-MOH-2026-0007");
		expect(screen.getByTestId("published-output-version-bundle")).toHaveTextContent("Bundle v5");
		expect(screen.getByTestId("published-output-version-dsm")).toHaveTextContent("DSM v4");
		expect(screen.getByTestId("published-output-version-dom")).toHaveTextContent("DOM v4");
		expect(screen.getByTestId("published-output-version-dem")).toHaveTextContent("DEM v4");
		expect(screen.getByTestId("published-output-version-dcm")).toHaveTextContent("DCM v2");
		expect(screen.getByTestId("published-evidence-link")).toHaveAttribute("href", "/desk/tenders/TND-400/evidence");
		expect(screen.getByTestId("published-addendum-guidance")).toHaveTextContent(/addendum or a controlled reissue/i);
		expect(screen.getByRole("status")).toHaveTextContent(/Published/);
		expect(screen.getByText(PUBLISHED_STATE_LOCK_MESSAGE)).toBeInTheDocument();
	});

	it("renders evidence link label from props", () => {
		render(<PublishedStateSummaryScreen {...minimalProps()} />);
		expect(screen.getByTestId("published-evidence-link")).toHaveAccessibleName(/View sealed evidence package/i);
	});

	it("shows exact output version strings per row (pack acceptance)", () => {
		render(
			<PublishedStateSummaryScreen
				{...minimalProps({
					bundleVersion: "B-ONLY",
					dsmVersion: "S-ONLY",
					domVersion: "O-ONLY",
					demVersion: "E-ONLY",
					dcmVersion: "C-ONLY",
				})}
			/>,
		);
		const root = screen.getByTestId("published-state-summary");
		expect(within(root).getByTestId("published-output-version-bundle")).toHaveTextContent("B-ONLY");
		expect(within(root).getByTestId("published-output-version-dsm")).toHaveTextContent("S-ONLY");
		expect(within(root).getByTestId("published-output-version-dom")).toHaveTextContent("O-ONLY");
		expect(within(root).getByTestId("published-output-version-dem")).toHaveTextContent("E-ONLY");
		expect(within(root).getByTestId("published-output-version-dcm")).toHaveTextContent("C-ONLY");
	});

	it("does not offer configuration or publish edit controls", () => {
		render(<PublishedStateSummaryScreen {...minimalProps()} />);
		expect(screen.queryByRole("button", { name: /edit tender|configure document|publish tender|save/i })).not.toBeInTheDocument();
	});
});
