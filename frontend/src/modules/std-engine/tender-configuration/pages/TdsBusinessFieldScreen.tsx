/**
 * UI-HARD-0600 — TDS as grouped business fields (pack §11, doc §10.1).
 *
 * No editable ITT clause surface; save is SEC-0410–driven.
 */

import type { ChangeEvent, ReactElement } from "react";

import { ActionAwareButton } from "../../shared";

import {
	TDS_BUSINESS_GROUPS,
	TDS_FIELD_LABELS,
	type TdsBusinessFieldScreenProps,
	type TdsFieldKey,
} from "./tdsBusinessFieldScreen.types";

function fieldTestId(key: TdsFieldKey): string {
	return `tds-field-${key.replace(/_/g, "-")}`;
}

const YES_NO_KEYS = new Set<TdsFieldKey>(["tender_security_required", "site_visit_required", "pre_tender_meeting_required"]);
const NUMBER_KEYS = new Set<TdsFieldKey>(["bid_validity_days", "tender_security_amount"]);
const DATETIME_KEYS = new Set<TdsFieldKey>(["submission_deadline", "opening_datetime", "clarification_deadline", "site_visit_datetime"]);

function TdsFieldControl(props: {
	fieldKey: TdsFieldKey;
	value: string;
	error: string | undefined;
	onChange: (key: TdsFieldKey, value: string) => void;
}): ReactElement {
	const { fieldKey, value, error, onChange } = props;
	const tid = fieldTestId(fieldKey);
	const label = TDS_FIELD_LABELS[fieldKey];

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
	} else if (NUMBER_KEYS.has(fieldKey)) {
		control = (
			<input
				id={tid}
				type="number"
				className="form-control"
				data-testid={tid}
				value={value}
				onChange={onInput}
				min={0}
				step={fieldKey === "bid_validity_days" ? 1 : "any"}
				aria-invalid={Boolean(error)}
			/>
		);
	} else if (DATETIME_KEYS.has(fieldKey)) {
		control = (
			<input
				id={tid}
				type="datetime-local"
				className="form-control"
				data-testid={tid}
				value={value}
				onChange={onInput}
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

export function TdsBusinessFieldScreen(props: TdsBusinessFieldScreenProps): ReactElement {
	const { instanceCode, values, onChange, fieldErrors = {}, saveAction } = props;

	return (
		<div data-testid="tds-screen" className="tds-business-field-screen">
			<header className="page-head" style={{ marginBottom: "1rem" }}>
				<h2>Tender Data Sheet</h2>
				<p className="text-muted small" style={{ marginBottom: 0 }}>
					<strong>Instance:</strong> {instanceCode}. Business fields are grouped below. Invitation-to-tender (ITT) legal clauses are{" "}
					<strong>not</strong> edited as free text here (doc §10.1).
				</p>
			</header>

			{TDS_BUSINESS_GROUPS.map((group) => (
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

					{group.id === "submission" ? (
						<div className="alert alert-warning" data-testid="tds-itt-not-editable-notice" role="note">
							<strong>ITT content:</strong> tender invitation legal clauses are not shown or edited as unstructured text on this
							screen. Use structured fields and your organisation&apos;s approved templates workflow.
						</div>
					) : null}

					{group.id === "complaints" ? (
						<p className="text-muted small" style={{ marginBottom: 0 }}>
							Complaints and review processes follow your organisation&apos;s standard channels. Do not paste full ITT or GCC legal
							clause text into free-text fields here.
						</p>
					) : null}

					{group.fieldKeys.map((key) => (
						<TdsFieldControl key={key} fieldKey={key} value={values[key] ?? ""} error={fieldErrors[key]} onChange={onChange} />
					))}
				</section>
			))}

			<section style={{ marginTop: "1rem" }} aria-label="Save TDS">
				<ActionAwareButton
					actionCode={saveAction.actionCode}
					objectType={saveAction.objectType}
					objectCode={saveAction.objectCode}
					label="Save TDS"
					variant="primary"
					buttonTestId="tds-save-button"
					availabilityContext={saveAction.availabilityContext}
					onAllowedClick={saveAction.onAllowedClick}
				/>
			</section>
		</div>
	);
}
