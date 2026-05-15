/**
 * UI-HARD-1310 — Audit trail (pack §18 ticket 1310, doc §18.2–18.3).
 *
 * APIs: `GET /api/audit/tenders/{tender_code}/events` — host supplies `rows` / refetch on `onFiltersChange`.
 */

import { useCallback, useMemo, useState, type ChangeEvent, type ReactElement } from "react";

import { filterAuditRows } from "./auditTrailFilter";
import type { AuditTrailEventRow, AuditTrailFiltersState, AuditTrailViewScreenProps } from "./auditTrailViewScreen.types";

const DEFAULT_FILTERS: AuditTrailFiltersState = {
	event_type: "",
	actor: "",
	object: "",
	result: "",
	risk_level: "",
	date_from: "",
	date_to: "",
	denied_actions_only: false,
};

export function AuditTrailViewScreen(props: AuditTrailViewScreenProps): ReactElement {
	const { tenderCode, rows, initialFilters, onFiltersChange } = props;

	const [filters, setFilters] = useState<AuditTrailFiltersState>(() => ({
		...DEFAULT_FILTERS,
		...initialFilters,
	}));

	const emit = useCallback(
		(next: AuditTrailFiltersState) => {
			onFiltersChange?.(next);
		},
		[onFiltersChange],
	);

	const patch = useCallback(
		(partial: Partial<AuditTrailFiltersState>) => {
			setFilters((prev) => {
				const next = { ...prev, ...partial };
				emit(next);
				return next;
			});
		},
		[emit],
	);

	const onText =
		(key: "event_type" | "actor" | "object" | "result" | "risk_level") => (e: ChangeEvent<HTMLInputElement>) => {
			patch({ [key]: e.target.value } as Partial<AuditTrailFiltersState>);
		};

	const onDenied = useCallback(
		(e: ChangeEvent<HTMLInputElement>) => {
			patch({ denied_actions_only: e.target.checked });
		},
		[patch],
	);

	const onDate = (key: "date_from" | "date_to") => (e: ChangeEvent<HTMLInputElement>) => {
		patch({ [key]: e.target.value } as Pick<AuditTrailFiltersState, typeof key>);
	};

	const visibleRows = useMemo(() => filterAuditRows(rows, filters), [rows, filters]);

	return (
		<div data-testid="audit-trail-page" className="std-engine-audit-trail-page">
			<header style={{ marginBottom: "1rem" }}>
				<h1 className="h2">Audit trail</h1>
				<p className="text-muted small">Tender {tenderCode}</p>
			</header>

			<section className="panel panel-default" style={{ padding: "0.75rem", marginBottom: "0.75rem" }} aria-labelledby="audit-filters-heading">
				<h2 id="audit-filters-heading" className="h4">
					Filters
				</h2>
				<p className="text-muted small">
					Pack examples: manual criteria attempted; post-publication edit attempted; unauthorized publication attempted;
					contract override attempted (doc §18.3) — use &quot;Denied actions only&quot; plus text filters.
				</p>
				<div className="row">
					<div className="col-md-4">
						<div className="form-group">
							<label htmlFor="audit-filter-event-type">event_type</label>
							<input
								id="audit-filter-event-type"
								data-testid="audit-filter-event-type"
								className="form-control input-sm"
								value={filters.event_type}
								onChange={onText("event_type")}
							/>
						</div>
					</div>
					<div className="col-md-4">
						<div className="form-group">
							<label htmlFor="audit-filter-actor">actor</label>
							<input
								id="audit-filter-actor"
								data-testid="audit-filter-actor"
								className="form-control input-sm"
								value={filters.actor}
								onChange={onText("actor")}
							/>
						</div>
					</div>
					<div className="col-md-4">
						<div className="form-group">
							<label htmlFor="audit-filter-object">object</label>
							<input
								id="audit-filter-object"
								data-testid="audit-filter-object"
								className="form-control input-sm"
								value={filters.object}
								onChange={onText("object")}
							/>
						</div>
					</div>
				</div>
				<div className="row">
					<div className="col-md-4">
						<div className="form-group">
							<label htmlFor="audit-filter-result">result</label>
							<input
								id="audit-filter-result"
								data-testid="audit-filter-result"
								className="form-control input-sm"
								value={filters.result}
								onChange={onText("result")}
							/>
						</div>
					</div>
					<div className="col-md-4">
						<div className="form-group">
							<label htmlFor="audit-filter-risk-level">risk_level</label>
							<input
								id="audit-filter-risk-level"
								data-testid="audit-filter-risk-level"
								className="form-control input-sm"
								value={filters.risk_level}
								onChange={onText("risk_level")}
								placeholder="e.g. High"
							/>
						</div>
					</div>
					<div className="col-md-4">
						<fieldset data-testid="audit-filter-date-range" className="form-group" style={{ border: 0, padding: 0, margin: 0 }}>
							<legend className="text-muted small" style={{ border: 0, marginBottom: "0.25rem", width: "100%" }}>
								date_range
							</legend>
							<div className="row">
								<div className="col-xs-6">
									<label className="small" htmlFor="audit-filter-date-from">
										from
									</label>
									<input
										id="audit-filter-date-from"
										type="date"
										className="form-control input-sm"
										value={filters.date_from}
										onChange={onDate("date_from")}
									/>
								</div>
								<div className="col-xs-6">
									<label className="small" htmlFor="audit-filter-date-to">
										to
									</label>
									<input
										id="audit-filter-date-to"
										type="date"
										className="form-control input-sm"
										value={filters.date_to}
										onChange={onDate("date_to")}
									/>
								</div>
							</div>
						</fieldset>
					</div>
				</div>
				<div className="checkbox">
					<label>
						<input data-testid="audit-filter-denied-only" type="checkbox" checked={filters.denied_actions_only} onChange={onDenied} />{" "}
						denied_actions_only
					</label>
				</div>
			</section>

			<div className="small text-muted" style={{ marginBottom: "0.35rem" }}>
				Showing {visibleRows.length} of {rows.length} events
			</div>

			<table data-testid="audit-event-table" className="table table-bordered table-condensed">
				<thead>
					<tr>
						<th scope="col">Event</th>
						<th scope="col">Actor</th>
						<th scope="col">Result</th>
						<th scope="col">Object</th>
						<th scope="col">Timestamp</th>
						<th scope="col">Risk</th>
					</tr>
				</thead>
				<tbody>
					{visibleRows.length === 0 ? (
						<tr>
							<td colSpan={6} className="text-muted">
								No rows match the current filters.
							</td>
						</tr>
					) : (
						visibleRows.map((row) => (
							<AuditEventTableRow key={row.id} row={row} />
						))
					)}
				</tbody>
			</table>
		</div>
	);
}

function AuditEventTableRow(props: { row: AuditTrailEventRow }): ReactElement {
	const { row } = props;
	const risk = (row.riskLevel || "").trim() || "—";
	return (
		<tr data-testid="audit-event-row">
			<td>
				{row.deniedAction ? (
					<span data-testid="audit-denied-action-row" className="label label-danger" style={{ marginRight: "0.35rem" }}>
						Denied
					</span>
				) : null}
				{row.eventType}
			</td>
			<td>{row.actor}</td>
			<td>{row.result}</td>
			<td>{row.objectLabel}</td>
			<td>{row.timestamp}</td>
			<td>{risk}</td>
		</tr>
	);
}
