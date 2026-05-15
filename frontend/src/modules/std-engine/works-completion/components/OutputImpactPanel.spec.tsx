import "@testing-library/jest-dom/vitest";
import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import { OutputImpactPanel } from "./OutputImpactPanel";

describe("OutputImpactPanel (UI-HARD-0510)", () => {
	afterEach(() => {
		cleanup();
	});

	it("exposes output-impact-panel and per-kind item data-testids with pack plain labels", () => {
		render(<OutputImpactPanel affectedKinds={["bundle", "dsm", "dom", "dem", "dcm"]} />);
		expect(screen.getByTestId("output-impact-panel")).toBeInTheDocument();
		expect(screen.getByTestId("output-impact-item-bundle")).toHaveTextContent("Tender Document Bundle");
		expect(screen.getByTestId("output-impact-item-dsm")).toHaveTextContent("Submission Rules (DSM)");
		expect(screen.getByTestId("output-impact-item-dom")).toHaveTextContent("Opening Register (DOM)");
		expect(screen.getByTestId("output-impact-item-dem")).toHaveTextContent("Evaluation Rules (DEM)");
		expect(screen.getByTestId("output-impact-item-dcm")).toHaveTextContent("Contract Carry-Forward (DCM)");
	});

	it("uses pack example lead-in by default", () => {
		render(<OutputImpactPanel affectedKinds={["bundle"]} />);
		expect(screen.getByTestId("output-impact-panel")).toHaveTextContent("Changing this value will require regeneration of:");
	});

	it("dedupes kinds while preserving first-seen order", () => {
		render(<OutputImpactPanel affectedKinds={["dsm", "bundle", "dsm", "dom", "bundle"]} />);
		const panel = screen.getByTestId("output-impact-panel");
		const items = panel.querySelectorAll("li[data-testid]");
		expect(items).toHaveLength(3);
		expect(items[0]).toHaveAttribute("data-testid", "output-impact-item-dsm");
		expect(items[1]).toHaveAttribute("data-testid", "output-impact-item-bundle");
		expect(items[2]).toHaveAttribute("data-testid", "output-impact-item-dom");
	});

	it("shows guidance when no kinds are affected", () => {
		render(<OutputImpactPanel affectedKinds={[]} />);
		expect(screen.getByTestId("output-impact-panel")).toBeInTheDocument();
		expect(screen.queryByTestId("output-impact-item-bundle")).not.toBeInTheDocument();
		expect(screen.getByTestId("output-impact-panel")).toHaveTextContent("No affected outputs are listed");
	});

	it("allows custom lead-in and suppresses explanation when null", () => {
		render(<OutputImpactPanel affectedKinds={["dem"]} leadIn="If you save this change:" explanation={null} />);
		const panel = screen.getByTestId("output-impact-panel");
		expect(panel).toHaveTextContent("If you save this change:");
		expect(panel).not.toHaveTextContent("Regeneration refreshes");
	});
});
