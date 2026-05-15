/**
 * UI-HARD-0200 — Official STD Library landing (pack §7 + doc §6).
 *
 * Canonical React surface for the hybrid `std-engine` tree; Desk continues to host the primary
 * runtime via `std_library_shell.js`. Keep `data-testid`s aligned with the Desk shell for shared smoke contracts.
 */

import { useMemo, type ReactElement } from "react";

import { ActionAwareButton } from "../../shared";

const TITLE = "Official STD Library";
const SUBTITLE = "Manage official standard tender documents available for tender preparation.";
const GUIDANCE_TEXT =
	"Official STDs are imported as structured packages. Source files are retained as evidence. Active versions are immutable.";
const DETAIL_EMPTY = "Select an STD to view details.";
const EMPTY_LIBRARY = "No official STDs are available.";
const EMPTY_LIBRARY_HINT =
	"Import a structured official STD package before tenders can use standard documents.";

const ACTION = {
	importPackage: "IMPORT_OFFICIAL_STD_PACKAGE",
	registerSource: "REGISTER_SOURCE_DOCUMENT",
	validateLibrary: "VALIDATE_LIBRARY",
} as const;

const SUMMARY_CARDS = [
	{ testid: "std-library-card-active", label: "Active STDs" },
	{ testid: "std-library-card-needs-attention", label: "Needs Attention" },
	{ testid: "std-library-card-ready-review", label: "Ready for Review" },
	{ testid: "std-library-card-superseded", label: "Superseded" },
	{ testid: "std-library-card-package-imports", label: "Package Imports" },
	{ testid: "std-library-card-bundle-issues", label: "Bundle Preview Issues" },
] as const;

export type OfficialStdLibraryPageProps = {
	/** When zero, doc §6.5 empty state is shown in the list region. */
	templateCount?: number;
	onImportClick?: () => void;
	onRegisterSourceClick?: () => void;
	onValidateLibraryClick?: () => void;
};

function defaultImport(): void {
	const g = globalThis as typeof globalThis & { frappe?: { set_route?: (...a: string[]) => void } };
	if (typeof g.frappe?.set_route === "function") {
		g.frappe.set_route("std-engine", "library", "import");
	}
}

export function OfficialStdLibraryPage(props: OfficialStdLibraryPageProps): ReactElement {
	const {
		templateCount = 0,
		onImportClick = defaultImport,
		onRegisterSourceClick = () => {
			const g = globalThis as typeof globalThis & { frappe?: { show_alert?: (o: { message: string }) => void } };
			g.frappe?.show_alert?.({ message: "Register Source Document (STD-LIB-0400)." });
		},
		onValidateLibraryClick = () => {
			const g = globalThis as typeof globalThis & { frappe?: { show_alert?: (o: { message: string }) => void } };
			g.frappe?.show_alert?.({ message: "Validate Library (STD-LIB-0410)." });
		},
	} = props;

	const availabilityContext = useMemo(() => ({}), []);
	const listIsEmpty = templateCount <= 0;

	return (
		<div data-testid="std-library-page" className="std-library-shell">
			<div className="std-library-shell-inner">
				<header className="std-library-region-a">
					<div className="std-library-header-main">
						<h3 data-testid="std-library-header-title">{TITLE}</h3>
						<p data-testid="std-library-header-subtitle" className="std-library-subtitle">
							{SUBTITLE}
						</p>
					</div>
					<div
						className="std-library-header-actions"
						style={{ display: "flex", flexWrap: "wrap", gap: "0.35rem", alignItems: "center" }}
					>
						<ActionAwareButton
							actionCode={ACTION.importPackage}
							objectType="Official STD Library"
							objectCode="HUB"
							label="Import Official STD Package"
							variant="primary"
							buttonTestId="std-library-import-package-button"
							availabilityContext={availabilityContext}
							onAllowedClick={onImportClick}
						/>
						<ActionAwareButton
							actionCode={ACTION.registerSource}
							objectType="Official STD Library"
							objectCode="HUB"
							label="Register Source Document"
							variant="secondary"
							buttonTestId="std-library-register-source-button"
							availabilityContext={availabilityContext}
							onAllowedClick={onRegisterSourceClick}
						/>
						<ActionAwareButton
							actionCode={ACTION.validateLibrary}
							objectType="Official STD Library"
							objectCode="HUB"
							label="Validate Library"
							variant="secondary"
							buttonTestId="std-library-validate-library-button"
							availabilityContext={availabilityContext}
							onAllowedClick={onValidateLibraryClick}
						/>
						<details className="std-library-advanced-route-disclosure">
							<summary data-testid="std-library-advanced-view-toggle" className="std-library-advanced-view-summary">
								Advanced Technical View
							</summary>
							<div className="std-library-advanced-route-body">
								<p className="text-muted small">
									Open the advanced catalogue for authorized technical review. This is not the default library experience.
								</p>
								<button
									type="button"
									className="btn btn-primary btn-sm"
									data-testid="std-library-advanced-catalogue-open"
									onClick={() => {
										const g = globalThis as typeof globalThis & { frappe?: { set_route?: (...a: string[]) => void } };
										g.frappe?.set_route?.("std-engine-advanced");
									}}
								>
									Open advanced catalogue
								</button>
							</div>
						</details>
						<span data-testid="std-library-create-instance-button-absent" aria-hidden="true" className="std-library-prohibited-marker" />
					</div>
				</header>

				<section className="std-library-guidance" data-testid="std-library-guidance-strip">
					{GUIDANCE_TEXT}
				</section>

				<section data-testid="std-library-summary-cards">
					<div
						className="std-library-summary-grid"
						style={{ display: "grid", gridTemplateColumns: "repeat(3, minmax(0, 1fr))", gap: "0.5rem" }}
					>
						{SUMMARY_CARDS.map((c) => (
							<button key={c.testid} type="button" className="btn btn-default" data-testid={c.testid}>
								{c.label}
							</button>
						))}
					</div>
				</section>

				<section className="std-library-search-row" style={{ display: "flex", gap: "0.35rem", flexWrap: "wrap" }}>
					<input
						type="search"
						data-testid="std-library-search-input"
						className="form-control input-sm"
						placeholder="Search official STD library"
						aria-label="Search official STD library"
					/>
					<button type="button" className="btn btn-default btn-sm" data-testid="std-library-filter-button">
						Filters
					</button>
					<button type="button" className="btn btn-default btn-sm" data-testid="std-library-clear-filters">
						Clear Filters
					</button>
				</section>

				<div style={{ display: "flex", flexWrap: "wrap", gap: "1rem" }}>
					<section data-testid="std-library-list" style={{ flex: "1 1 55%", minWidth: "12rem" }}>
						<div data-testid="std-library-list-cards">
							{listIsEmpty ? (
								<div data-testid="std-library-list-empty" className="text-muted">
									<p>{EMPTY_LIBRARY}</p>
									<p>{EMPTY_LIBRARY_HINT}</p>
								</div>
							) : null}
						</div>
					</section>
					<aside data-testid="std-library-detail-panel" style={{ flex: "1 1 35%", minWidth: "12rem" }} className="text-muted">
						{DETAIL_EMPTY}
					</aside>
				</div>
			</div>
		</div>
	);
}
