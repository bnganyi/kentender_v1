export type AuditTrailFiltersState = {
	event_type: string;
	actor: string;
	object: string;
	result: string;
	risk_level: string;
	/** Inclusive start `YYYY-MM-DD` (host may map to API query). */
	date_from: string;
	/** Inclusive end `YYYY-MM-DD`. */
	date_to: string;
	denied_actions_only: boolean;
};

export type AuditTrailEventRow = {
	id: string;
	eventType: string;
	actor: string;
	result: string;
	objectLabel: string;
	timestamp: string;
	/** ISO date (e.g. `2026-05-11`) for range filtering; optional. */
	timestampIso?: string;
	riskLevel?: string;
	/** Denied high-risk action attempt (doc §18.3). */
	deniedAction?: boolean;
};

export type AuditTrailViewScreenProps = {
	tenderCode: string;
	/** Full list; screen applies `filters` client-side for desk-style responsiveness until API wires in. */
	rows: AuditTrailEventRow[];
	initialFilters?: Partial<AuditTrailFiltersState>;
	/** Fired whenever a filter control changes (parent may refetch). */
	onFiltersChange?: (filters: AuditTrailFiltersState) => void;
};
