import { describe, expect, it } from "vitest";

import { filterAuditRows } from "./auditTrailFilter";
import type { AuditTrailEventRow, AuditTrailFiltersState } from "./auditTrailViewScreen.types";

const rows: AuditTrailEventRow[] = [
	{
		id: "a",
		eventType: "A",
		actor: "u1",
		result: "OK",
		objectLabel: "Obj",
		timestamp: "2026-05-01",
		timestampIso: "2026-05-01",
		riskLevel: "Low",
	},
	{
		id: "b",
		eventType: "B_DENIED",
		actor: "u2",
		result: "Denied",
		objectLabel: "Obj",
		timestamp: "2026-05-15",
		timestampIso: "2026-05-15",
		riskLevel: "High",
		deniedAction: true,
	},
];

const emptyFilters: AuditTrailFiltersState = {
	event_type: "",
	actor: "",
	object: "",
	result: "",
	risk_level: "",
	date_from: "",
	date_to: "",
	denied_actions_only: false,
};

describe("filterAuditRows", () => {
	it("filters by inclusive ISO date range", () => {
		const f: AuditTrailFiltersState = { ...emptyFilters, date_from: "2026-05-10", date_to: "2026-05-20" };
		expect(filterAuditRows(rows, f).map((r) => r.id)).toEqual(["b"]);
	});

	it("filters by risk_level substring", () => {
		const f: AuditTrailFiltersState = { ...emptyFilters, risk_level: "high" };
		expect(filterAuditRows(rows, f).map((r) => r.id)).toEqual(["b"]);
	});
});
