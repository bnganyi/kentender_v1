/**
 * UI-HARD-0800 — BOQ preparation (pack §13, doc §13).
 *
 * No supplier rate entry in tender preparation; quantity owner and supplier input mode surfaced per pack acceptance.
 */

import type { ChangeEvent, ReactElement } from "react";

import {
	BOQ_RATE_PREPARATION_WARNING_PACK,
	BOQ_STALENESS_WARNING_PACK,
	type BoqHeaderValues,
	type BoqPreparationScreenProps,
} from "./boqPreparationScreen.types";

const HEADER_EDITABLE: (keyof BoqHeaderValues)[] = ["currency", "pricing_model", "arithmetic_correction_stage"];

function HeaderField(props: {
	field: keyof BoqHeaderValues;
	label: string;
	value: string;
	onChange?: (field: keyof BoqHeaderValues, value: string) => void;
}): ReactElement {
	const { field, label, value, onChange } = props;
	const id = `boq-header-${String(field)}`;
	return (
		<div className="form-group col-md-4">
			<label className="control-label" htmlFor={id}>
				{label}
			</label>
			<input
				id={id}
				type="text"
				className="form-control"
				value={value}
				onChange={(e: ChangeEvent<HTMLInputElement>) => onChange?.(field, e.target.value)}
				autoComplete="off"
			/>
		</div>
	);
}

export function BoqPreparationScreen(props: BoqPreparationScreenProps): ReactElement {
	const { header, bills, items, validationMessages, showStalenessWarning = false, onHeaderFieldChange, onImportClick, onExportClick } =
		props;

	const quantityOwner = header.quantity_owner?.trim() || "Procuring Entity";
	const supplierInputMode = header.supplier_input_mode?.trim() || "Rate Only";

	return (
		<div data-testid="boq-screen" className="boq-preparation-screen">
			<header className="page-head" style={{ marginBottom: "1rem" }}>
				<h2>Bill of Quantities (preparation)</h2>
				<p className="text-muted small" style={{ marginBottom: 0 }}>
					The procuring entity controls item structure and quantities. Supplier rates are not captured here (doc §13.1).
				</p>
			</header>

			{showStalenessWarning ? (
				<div data-testid="boq-staleness-warning" className="alert alert-warning" role="alert" style={{ marginBottom: "0.75rem" }}>
					{BOQ_STALENESS_WARNING_PACK}
				</div>
			) : null}

			<section data-testid="boq-header" className="panel panel-default" style={{ padding: "0.75rem", marginBottom: "0.75rem" }}>
				<h4 className="h6" style={{ marginTop: 0 }}>
					BOQ header
				</h4>
				<div className="row">
					{HEADER_EDITABLE.map((field) => (
						<HeaderField
							key={field}
							field={field}
							label={
								field === "currency"
									? "Currency"
									: field === "pricing_model"
										? "Pricing model"
										: "Arithmetic correction stage"
							}
							value={String(header[field] ?? "")}
							onChange={onHeaderFieldChange}
						/>
					))}
				</div>
				<div className="row" style={{ marginTop: "0.35rem" }}>
					<div className="col-md-6">
						<p className="small" style={{ marginBottom: "0.25rem" }}>
							<strong>Quantity owner</strong>
						</p>
						<p className="form-control-static" style={{ marginBottom: 0 }}>
							<span className="label label-primary">{quantityOwner}</span>
						</p>
					</div>
					<div className="col-md-6">
						<p className="small" style={{ marginBottom: "0.25rem" }}>
							<strong>Supplier input mode</strong>
						</p>
						<p className="form-control-static" style={{ marginBottom: 0 }}>
							<span className="label label-default">{supplierInputMode}</span>
						</p>
					</div>
				</div>
			</section>

			<section data-testid="boq-bills-list" className="panel panel-default" style={{ padding: "0.75rem", marginBottom: "0.75rem" }}>
				<h4 className="h6" style={{ marginTop: 0 }}>
					Bills
				</h4>
				{bills.length === 0 ? (
					<p className="text-muted small" style={{ marginBottom: 0 }}>
						No bills yet. Import a structured BOQ or add bills from your host flow.
					</p>
				) : (
					<ul className="list-unstyled small" style={{ marginBottom: 0 }}>
						{bills.map((b) => (
							<li key={b.id} style={{ marginBottom: "0.35rem" }}>
								<strong>{b.code}</strong> — {b.title}
							</li>
						))}
					</ul>
				)}
			</section>

			<section style={{ marginBottom: "0.75rem" }}>
				<div
					data-testid="boq-supplier-rate-field-absent"
					className="alert alert-info small"
					role="status"
					style={{ marginBottom: "0.5rem" }}
					aria-label="Supplier rate fields are not present on this preparation screen"
				>
					<strong>No supplier rate columns:</strong> fields such as <code>rate</code>, <code>supplier_rate</code>,{" "}
					<code>bidder_rate</code>, and <code>amount_entered_by_supplier</code> are not rendered during tender preparation (pack
					prohibited list).
				</div>
				<div className="table-responsive">
					<table data-testid="boq-items-table" className="table table-bordered table-condensed">
						<thead>
							<tr>
								<th scope="col">Item No.</th>
								<th scope="col">Description</th>
								<th scope="col">Unit</th>
								<th scope="col">Quantity</th>
								<th scope="col">Item Type</th>
								<th scope="col">Supplier Input Mode</th>
								<th scope="col">Provisional / Fixed Amount</th>
							</tr>
						</thead>
						<tbody>
							{items.length === 0 ? (
								<tr>
									<td colSpan={7} className="text-muted small">
										No BOQ lines loaded.
									</td>
								</tr>
							) : (
								items.map((r) => (
									<tr key={r.id}>
										<td>{r.item_no}</td>
										<td>{r.description}</td>
										<td>{r.unit}</td>
										<td>{r.quantity}</td>
										<td>{r.item_type}</td>
										<td>{r.supplier_input_mode}</td>
										<td>{r.provisional_or_fixed}</td>
									</tr>
								))
							)}
						</tbody>
					</table>
				</div>
			</section>

			<section data-testid="boq-validation-summary" className="panel panel-default" style={{ padding: "0.75rem", marginBottom: "0.75rem" }}>
				<h4 className="h6" style={{ marginTop: 0 }}>
					Validation summary
				</h4>
				<p className="small text-muted" style={{ marginBottom: "0.5rem" }}>
					{BOQ_RATE_PREPARATION_WARNING_PACK}
				</p>
				{validationMessages.length === 0 ? (
					<p className="small" style={{ marginBottom: 0 }}>
						No structured validation errors. Import must still be validated server-side before acceptance (doc §13.5).
					</p>
				) : (
					<ul className="small text-danger" style={{ marginBottom: 0 }}>
						{validationMessages.map((m) => (
							<li key={m}>{m}</li>
						))}
					</ul>
				)}
			</section>

			<section aria-label="Import and export controls" style={{ marginBottom: "1rem" }}>
				<button type="button" className="btn btn-primary" data-testid="boq-import-button" onClick={() => onImportClick?.()}>
					Import BOQ
				</button>{" "}
				<button type="button" className="btn btn-default" onClick={() => onExportClick?.()}>
					Export BOQ
				</button>
			</section>
		</div>
	);
}
