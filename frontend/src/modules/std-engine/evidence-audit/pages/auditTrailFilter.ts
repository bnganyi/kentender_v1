import type { AuditTrailEventRow, AuditTrailFiltersState } from "./auditTrailViewScreen.types";

function includes(hay: string, needle: string): boolean {
	const n = needle.trim().toLowerCase();
	if (!n) {
		return true;
	}
	return hay.toLowerCase().includes(n);
}

function parseIsoDay(value: string): string | null {
	const v = value.trim();
	if (!v) {
		return null;
	}
	if (!/^\d{4}-\d{2}-\d{2}$/.test(v)) {
		return null;
	}
	return v;
}

function rowDay(row: AuditTrailEventRow): string {
	const iso = (row.timestampIso || "").trim();
	if (iso.length >= 10) {
		return iso.slice(0, 10);
	}
	const m = /(\d{4}-\d{2}-\d{2})/.exec(row.timestamp);
	return m ? m[1] : "";
}

/** Client-side filter (pack: filters work; host can replace with GET …/events results). */
export function filterAuditRows(rows: AuditTrailEventRow[], f: AuditTrailFiltersState): AuditTrailEventRow[] {
	const from = parseIsoDay(f.date_from);
	const to = parseIsoDay(f.date_to);

	return rows.filter((row) => {
		if (f.denied_actions_only && !row.deniedAction) {
			return false;
		}
		if (!includes(row.eventType, f.event_type)) {
			return false;
		}
		if (!includes(row.actor, f.actor)) {
			return false;
		}
		if (!includes(row.objectLabel, f.object)) {
			return false;
		}
		if (!includes(row.result, f.result)) {
			return false;
		}
		const rl = (row.riskLevel || "").trim();
		if (f.risk_level.trim() && !includes(rl, f.risk_level)) {
			return false;
		}
		const day = rowDay(row);
		if (from && day && day < from) {
			return false;
		}
		if (to && day && day > to) {
			return false;
		}
		return true;
	});
}
