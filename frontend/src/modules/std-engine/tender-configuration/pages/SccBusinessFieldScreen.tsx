/**
 * UI-HARD-0610 — SCC as grouped contract fields (pack §11, doc §10.2).
 *
 * No editable GCC clause surface; save is SEC-0410–driven.
 */

import type { ChangeEvent, ReactElement } from "react";

import { ActionAwareButton } from "../../shared";

import {
	SCC_BUSINESS_GROUPS,
	SCC_COMPLETION_PERIOD_HELP,
	SCC_FIELD_LABELS,
	type SccBusinessFieldScreenProps,
	type SccFieldKey,
} from "./sccBusinessFieldScreen.types";

function fieldTestId(key: SccFieldKey): string {
	return `scc-field-${key.replace(/_/g, "-")}`;
}

const YES_NO_KEYS = new Set<SccFieldKey>(["advance_payment_allowed", "insurance_required"]);
const INTEGER_KEYS = new Set<SccFieldKey>(["completion_period_days", "defects_liability_period_days"]);
const PERCENT_KEYS = new Set<SccFieldKey>([
	"performance_security_percent",
	"retention_percent",
	"liquidated_damages_percent_per_day",
	"maximum_liquidated_damages_percent",
]);

function SccFieldControl(props: {
	fieldKey: SccFieldKey;
	value: string;
	error: string | undefined;
	onChange: (key: SccFieldKey, value: string) => void;
}): ReactElement {
	const { fieldKey, value, error, onChange } = props;
	const tid = fieldTestId(fieldKey);
	const label = SCC_FIELD_LABELS[fieldKey];

	const onInput = (e: ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
		onChange(fieldKey, e.target.value);
	};

	let control: ReactElement;
	if (YES_NO_KEYS.has(fieldKey)) {
		control = (
			<select id={tid} className="form-control" data-testid={tid} value={value} onChange={onInput} aria-invalid={Boolean(error)}>
				<option value="">—</option>
				<option value="yes">Yes</option>
				<option value="no">No</option>
			</select>
		);
	} else if (INTEGER_KEYS.has(fieldKey)) {
		control = (
			<input
				id={tid}
				type="number"
				className="form-control"
				data-testid={tid}
				value={value}
				onChange={onInput}
				min={0}
				step={1}
				aria-invalid={Boolean(error)}
			/>
		);
	} else if (PERCENT_KEYS.has(fieldKey)) {
		control = (
			<input
				id={tid}
				type="number"
				className="form-control"
				data-testid={tid}
				value={value}
				onChange={onInput}
				min={0}
				max={100}
				step="0.01"
				aria-invalid={Boolean(error)}
			/>
		);
	} else {
		control = (
			<input
				id={tid}
				type="text"
				className="form-control"
				data-testid={tid}
				value={value}
				onChange={onInput}
				autoComplete="off"
				aria-invalid={Boolean(error)}
			/>
		);
	}

	return (
		<div className="form-group" style={{ marginBottom: "0.65rem" }}>
			<label className="control-label" htmlFor={tid}>
				{label}
			</label>
			{control}
			{error ? (
				<p className="text-danger small" role="alert" data-testid={`${tid}-error`} style={{ marginTop: "0.25rem", marginBottom: 0 }}>
					{error}
				</p>
			) : null}
		</div>
	);
}

export function SccBusinessFieldScreen(props: SccBusinessFieldScreenProps): ReactElement {
	const { instanceCode, values, onChange, fieldErrors = {}, saveAction } = props;

	return (
		<div data-testid="scc-screen" className="scc-business-field-screen">
			<header className="page-head" style={{ marginBottom: "1rem" }}>
				<h2>Special Conditions of Contract</h2>
				<p className="text-muted small" style={{ marginBottom: 0 }}>
					<strong>Instance:</strong> {instanceCode}. These are structured contract parameters only. General Conditions of Contract
					(GCC) legal clause text is <strong>not</strong> edited as free text here (doc §10.2).
				</p>
			</header>

			<div className="alert alert-info" data-testid="scc-dcm-carry-forward-note" role="note" style={{ marginBottom: "0.75rem" }}>
				<strong>Contract carry-forward (DCM):</strong> key SCC values you confirm here are carried into the generated{" "}
				<em>Contract Carry-Forward (DCM)</em> output so the signed contract reflects the same numbers and flags — not a separate
				untracked copy. Regenerate outputs after substantive changes, before publication.
			</div>

			{SCC_BUSINESS_GROUPS.map((group) => (
				<section
					key={group.id}
					data-testid={group.sectionTestId}
					className="panel panel-default"
					style={{ padding: "0.75rem", marginBottom: "0.75rem" }}
					aria-labelledby={`${group.sectionTestId}-title`}
				>
					<h4 className="h6" id={`${group.sectionTestId}-title`} style={{ marginTop: 0 }}>
						{group.title}
					</h4>

					{group.id === "completion" ? (
						<p className="text-muted small" data-testid="scc-completion-period-help" style={{ marginBottom: "0.65rem" }}>
							{SCC_COMPLETION_PERIOD_HELP}
						</p>
					) : null}

					{group.id === "dispute" ? (
						<div className="alert alert-warning" data-testid="scc-gcc-not-editable-notice" role="note">
							<strong>GCC content:</strong> general conditions of contract legal clauses are not shown or edited as unstructured
							text on this screen. Use the structured fields above and your organisation&apos;s approved templates / addendum
							workflow.
						</div>
					) : null}

					{group.fieldKeys.map((key) => (
						<SccFieldControl key={key} fieldKey={key} value={values[key] ?? ""} error={fieldErrors[key]} onChange={onChange} />
					))}
				</section>
			))}

			<section style={{ marginTop: "1rem" }} aria-label="Save SCC">
				<ActionAwareButton
					actionCode={saveAction.actionCode}
					objectType={saveAction.objectType}
					objectCode={saveAction.objectCode}
					label="Save SCC"
					variant="primary"
					buttonTestId="scc-save-button"
					availabilityContext={saveAction.availabilityContext}
					onAllowedClick={saveAction.onAllowedClick}
				/>
			</section>
		</div>
	);
}
