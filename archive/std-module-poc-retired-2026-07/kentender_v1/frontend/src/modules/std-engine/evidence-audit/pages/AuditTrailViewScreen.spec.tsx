import "@testing-library/jest-dom/vitest";
import { cleanup, fireEvent, render, screen, within } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { AuditTrailViewScreen } from "./AuditTrailViewScreen";
import type { AuditTrailEventRow, AuditTrailViewScreenProps } from "./auditTrailViewScreen.types";

const sampleRows: AuditTrailEventRow[] = [
	{
		id: "1",
		eventType: "PUBLICATION_READINESS_RUN",
		actor: "officer@moh.go.ke",
		result: "OK",
		objectLabel: "Tender TND-600",
		timestamp: "2026-05-11 09:00",
		timestampIso: "2026-05-11",
		riskLevel: "Low",
	},
	{
		id: "2",
		eventType: "MANUAL_CRITERIA_EDIT_ATTEMPTED",
		actor: "vendor@x.com",
		result: "Denied",
		objectLabel: "Tender TND-600 / DEM",
		timestamp: "2026-05-10 14:22",
		timestampIso: "2026-05-10",
		riskLevel: "Critical",
		deniedAction: true,
	},
	{
		id: "3",
		eventType: "POST_PUBLICATION_EDIT_ATTEMPTED",
		actor: "officer@moh.go.ke",
		result: "Denied",
		objectLabel: "Tender TND-600 / BOQ",
		timestamp: "2026-05-09 11:00",
		timestampIso: "2026-05-09",
		riskLevel: "High",
		deniedAction: true,
	},
];

function minimalProps(overrides: Partial<AuditTrailViewScreenProps> = {}): AuditTrailViewScreenProps {
	return {
		tenderCode: "TND-600",
		rows: sampleRows,
		...overrides,
	};
}

describe("AuditTrailViewScreen (UI-HARD-1310)", () => {
	afterEach(() => {
		cleanup();
	});

	it("exposes pack data-testids", () => {
		render(<AuditTrailViewScreen {...minimalProps()} />);
		expect(screen.getByTestId("audit-trail-page")).toBeInTheDocument();
		expect(screen.getByTestId("audit-filter-event-type")).toBeInTheDocument();
		expect(screen.getByTestId("audit-filter-actor")).toBeInTheDocument();
		expect(screen.getByTestId("audit-filter-denied-only")).toBeInTheDocument();
		expect(screen.getByTestId("audit-event-table")).toBeInTheDocument();
		expect(screen.getAllByTestId("audit-event-row").length).toBe(3);
	});

	it("renders event, actor, result, object, and timestamp per row", () => {
		render(<AuditTrailViewScreen {...minimalProps()} />);
		const table = screen.getByTestId("audit-event-table");
		expect(within(table).getByText("PUBLICATION_READINESS_RUN")).toBeInTheDocument();
		expect(within(table).getAllByText("officer@moh.go.ke").length).toBeGreaterThanOrEqual(1);
		expect(within(table).getAllByText(/Tender TND-600/).length).toBeGreaterThanOrEqual(1);
		expect(within(table).getByText("2026-05-11 09:00")).toBeInTheDocument();
		expect(within(table).getByText("vendor@x.com")).toBeInTheDocument();
	});

	it("marks denied actions with audit-denied-action-row", () => {
		render(<AuditTrailViewScreen {...minimalProps()} />);
		const denied = screen.getAllByTestId("audit-denied-action-row");
		expect(denied.length).toBe(2);
	});

	it("filters rows by event_type (client-side)", () => {
		render(<AuditTrailViewScreen {...minimalProps()} />);
		fireEvent.change(screen.getByTestId("audit-filter-event-type"), { target: { value: "POST_PUBLICATION" } });
		const table = screen.getByTestId("audit-event-table");
		expect(within(table).getByText("POST_PUBLICATION_EDIT_ATTEMPTED")).toBeInTheDocument();
		expect(within(table).queryByText("PUBLICATION_READINESS_RUN")).not.toBeInTheDocument();
	});

	it("shows only denied rows when denied_actions_only is checked", () => {
		render(<AuditTrailViewScreen {...minimalProps()} />);
		fireEvent.click(screen.getByTestId("audit-filter-denied-only"));
		const table = screen.getByTestId("audit-event-table");
		expect(within(table).queryByText("PUBLICATION_READINESS_RUN")).not.toBeInTheDocument();
		expect(within(table).getByText("MANUAL_CRITERIA_EDIT_ATTEMPTED")).toBeInTheDocument();
		expect(within(table).getByText("POST_PUBLICATION_EDIT_ATTEMPTED")).toBeInTheDocument();
	});

	it("notifies parent on filter changes", () => {
		const onFiltersChange = vi.fn();
		render(<AuditTrailViewScreen {...minimalProps({ onFiltersChange })} />);
		fireEvent.change(screen.getByTestId("audit-filter-actor"), { target: { value: "officer" } });
		expect(onFiltersChange).toHaveBeenCalled();
		const last = onFiltersChange.mock.calls.at(-1)?.[0];
		expect(last?.actor).toBe("officer");
	});
});
