/**
 * UI-HARD-0300 — Release to Tender (pack §8, doc §7).
 *
 * Canonical React surface under `std-engine/tender-configuration`; Desk may host an equivalent route later.
 */

import { useCallback, useEffect, useMemo, useState, type ReactElement } from "react";

import { ActionAwareButton, BlockerList, type StdEngineBlockerItem } from "../../shared";

import type { ReleaseEligibilityStatus, ReleaseStdOption, ReleaseToTenderPageProps } from "./releaseToTender.types";

const RELEASE_ACTION = "RELEASE_PACKAGE_TO_TENDER";

function groupBlockers(blockers: StdEngineBlockerItem[] | undefined): {
	planning: StdEngineBlockerItem[];
	std: StdEngineBlockerItem[];
	permission: StdEngineBlockerItem[];
	released: StdEngineBlockerItem[];
} {
	const planning: StdEngineBlockerItem[] = [];
	const std: StdEngineBlockerItem[] = [];
	const permission: StdEngineBlockerItem[] = [];
	const released: StdEngineBlockerItem[] = [];
	for (const b of blockers || []) {
		const c = String(b.code || "").toUpperCase();
		if (c.startsWith("REL_")) {
			released.push(b);
		} else if (c.startsWith("PERM_") || c.startsWith("SEC_")) {
			permission.push(b);
		} else if (c.startsWith("STD_")) {
			std.push(b);
		} else {
			planning.push(b);
		}
	}
	return { planning, std, permission, released };
}

function eligibilityLabel(status: ReleaseEligibilityStatus): string {
	if (status === "eligible") {
		return "Eligible";
	}
	if (status === "blocked") {
		return "Blocked";
	}
	return "Unknown";
}

export function ReleaseToTenderPage(props: ReleaseToTenderPageProps): ReactElement {
	const {
		packageCode,
		packageTitle,
		summaryLines = [],
		eligibilityStatus,
		compatibleStdSummary,
		blockers = [],
		stdOptions,
		selectedStdVersionCode: controlledSelected,
		onSelectedStdChange,
		releaseResult = null,
		releaseAvailabilityContext,
		onReleaseClick,
	} = props;

	const grouped = useMemo(() => groupBlockers(blockers), [blockers]);

	const [internalSelected, setInternalSelected] = useState<string>(() => {
		if (stdOptions.length === 1) {
			return stdOptions[0].versionCode;
		}
		return "";
	});

	useEffect(() => {
		if (stdOptions.length === 1) {
			const only = stdOptions[0].versionCode;
			setInternalSelected(only);
			onSelectedStdChange?.(only);
		} else if (stdOptions.length === 0) {
			setInternalSelected("");
		}
	}, [stdOptions, onSelectedStdChange]);

	const selectedStdVersionCode = controlledSelected ?? internalSelected;

	const setSelected = useCallback(
		(code: string) => {
			if (onSelectedStdChange) {
				onSelectedStdChange(code);
			} else {
				setInternalSelected(code);
			}
		},
		[onSelectedStdChange],
	);

	const selectedOption = useMemo(
		() => stdOptions.find((o) => o.versionCode === selectedStdVersionCode) || null,
		[stdOptions, selectedStdVersionCode],
	);

	const canAttemptRelease =
		stdOptions.length > 0 && (stdOptions.length === 1 || Boolean(selectedStdVersionCode.trim()));

	const availabilityContext = useMemo(() => {
		const base = { ...(releaseAvailabilityContext || {}) };
		if (selectedStdVersionCode) {
			(base as Record<string, unknown>).selected_std_version_code = selectedStdVersionCode;
		}
		return base;
	}, [releaseAvailabilityContext, selectedStdVersionCode]);

	const showBlockerGroups =
		grouped.planning.length +
			grouped.std.length +
			grouped.permission.length +
			grouped.released.length >
		0;

	return (
		<div data-testid="release-to-tender-page" className="release-to-tender-page">
			<header className="page-head" style={{ marginBottom: "1rem" }}>
				<h2>Release to Tender</h2>
				<p className="text-muted" data-testid="release-package-header-line">
					<strong>Package:</strong> {packageCode} — {packageTitle}
				</p>
			</header>

			<section data-testid="release-package-summary" className="panel panel-default" style={{ padding: "0.75rem", marginBottom: "0.75rem" }}>
				<h4 className="h6">Package summary</h4>
				<dl className="small" style={{ marginBottom: 0 }}>
					{summaryLines.length === 0 ? (
						<>
							<dt>Package code</dt>
							<dd>{packageCode}</dd>
							<dt>Title</dt>
							<dd>{packageTitle}</dd>
						</>
					) : (
						summaryLines.map((row) => (
							<div key={row.label}>
								<dt>{row.label}</dt>
								<dd>{row.value}</dd>
							</div>
						))
					)}
				</dl>
			</section>

			<section
				data-testid="release-eligibility-status"
				className={`alert ${eligibilityStatus === "eligible" ? "alert-success" : eligibilityStatus === "blocked" ? "alert-danger" : "alert-info"}`}
				role="status"
			>
				<strong>Eligibility:</strong> {eligibilityLabel(eligibilityStatus)}
				{compatibleStdSummary ? (
					<>
						<br />
						<span className="small">{compatibleStdSummary}</span>
					</>
				) : null}
			</section>

			<section data-testid="release-blocker-list" style={{ marginTop: "0.75rem", marginBottom: "0.75rem" }}>
				{showBlockerGroups ? (
					<>
						{grouped.planning.length ? (
							<div className="release-blocker-group" data-testid="release-blocker-group-planning">
								<h5 className="h6">Planning blockers</h5>
								<BlockerList listDataTestId="release-blocker-sublist-planning" blockers={grouped.planning} emptyHint="None." />
							</div>
						) : null}
						{grouped.std.length ? (
							<div className="release-blocker-group" data-testid="release-blocker-group-std">
								<h5 className="h6">STD eligibility blockers</h5>
								<BlockerList listDataTestId="release-blocker-sublist-std" blockers={grouped.std} emptyHint="None." />
							</div>
						) : null}
						{grouped.permission.length ? (
							<div className="release-blocker-group" data-testid="release-blocker-group-permission">
								<h5 className="h6">Permission blockers</h5>
								<BlockerList listDataTestId="release-blocker-sublist-permission" blockers={grouped.permission} emptyHint="None." />
							</div>
						) : null}
						{grouped.released.length ? (
							<div className="release-blocker-group" data-testid="release-blocker-group-released">
								<h5 className="h6">Already released</h5>
								<BlockerList listDataTestId="release-blocker-sublist-released" blockers={grouped.released} emptyHint="None." />
							</div>
						) : null}
					</>
				) : (
					<p className="text-muted small" style={{ marginBottom: 0 }}>
						No blockers reported for this release check.
					</p>
				)}
			</section>

			<section data-testid="release-std-options" style={{ marginBottom: "0.75rem" }} role="radiogroup" aria-label="Eligible STD options">
				<h4 className="h6">STD option</h4>
				{stdOptions.length === 0 ? (
					<p className="text-muted small">No eligible STD templates were returned for this package.</p>
				) : (
					stdOptions.map((o) => (
						<label
							key={o.versionCode}
							className="release-std-option-row"
							style={{ display: "block", marginBottom: "0.35rem" }}
						>
							<input
								type="radio"
								name="release-std-option"
								value={o.versionCode}
								checked={selectedStdVersionCode === o.versionCode}
								onChange={() => setSelected(o.versionCode)}
							/>{" "}
							<strong>{o.title}</strong>{" "}
							<span className="text-muted small">
								({o.revision} · {o.authority}
								{o.profile ? ` · ${o.profile}` : ""})
							</span>
							<div className="text-muted small" style={{ marginLeft: "1.35rem" }}>
								Methods: {o.supportedMethods.length ? o.supportedMethods.join(", ") : "—"}
								{" · "}
								Requires BOQ: {o.requiresBoq ? "Yes" : "No"}, specifications: {o.requiresSpecifications ? "Yes" : "No"}, drawings:{" "}
								{o.requiresDrawings ? "Yes" : "No"}
							</div>
						</label>
					))
				)}
			</section>

			<section data-testid="release-selected-std-confirmation" className="panel panel-default" style={{ padding: "0.75rem", marginBottom: "0.75rem" }}>
				<h4 className="h6">Selected STD confirmation</h4>
				{selectedOption ? (
					<p className="small" style={{ marginBottom: 0 }}>
						<strong>{selectedOption.title}</strong> — {selectedOption.revision} ({selectedOption.authority})
					</p>
				) : (
					<p className="text-muted small" style={{ marginBottom: 0 }}>
						{stdOptions.length > 1 ? "Select an STD option above before releasing." : "No STD selected."}
					</p>
				)}
			</section>

			<section data-testid="release-action-section" style={{ marginBottom: "0.75rem" }}>
				{canAttemptRelease ? (
					<ActionAwareButton
						actionCode={RELEASE_ACTION}
						objectType="Procurement Package"
						objectCode={packageCode}
						label="Release to Tender"
						variant="primary"
						buttonTestId="release-action-button"
						availabilityContext={availabilityContext}
						onAllowedClick={() => {
							onReleaseClick?.();
						}}
					/>
				) : (
					<button type="button" className="btn btn-primary" disabled data-testid="release-action-button" title="Select an eligible STD option first.">
						Release to Tender
					</button>
				)}
			</section>

			{releaseResult ? (
				<section data-testid="release-success-panel" className="alert alert-success" role="status">
					<p>
						<strong>Package released to Tender successfully.</strong>
					</p>
					<p className="small" style={{ marginBottom: "0.35rem" }}>
						Tender: {releaseResult.tenderCode}
					</p>
					<p className="small" style={{ marginBottom: "0.35rem" }}>
						STD Instance: {releaseResult.stdInstanceCode}
					</p>
					<p className="small" style={{ marginBottom: "0.35rem" }}>
						Next step: Configure Tender Document.
					</p>
					<p style={{ marginBottom: 0 }}>
						<a
							data-testid="release-configure-tender-link"
							className="btn btn-xs btn-default"
							href={`/app/tenders/${encodeURIComponent(releaseResult.tenderCode)}/configure-document`}
						>
							Configure Tender Document
						</a>
					</p>
				</section>
			) : null}
		</div>
	);
}
