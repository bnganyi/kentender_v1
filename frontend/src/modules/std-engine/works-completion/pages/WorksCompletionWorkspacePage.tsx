/**
 * UI-HARD-0500 — Works completion workspace shell (pack §10, doc §9).
 *
 * Procurement Officer shell: tender context, stage sidebar, main panel, blockers, output impact, action bar.
 */

import { useCallback, useEffect, useState, type ReactElement } from "react";

import { ActionAwareButton, BlockerList } from "../../shared";

import { OutputImpactPanel } from "../components/OutputImpactPanel";

import {
	WORKS_COMPLETION_SIDEBAR_STAGES,
	type WorksCompletionAvailabilityAction,
	type WorksCompletionStageId,
	type WorksCompletionWorkspacePageProps,
} from "./worksCompletionWorkspace.types";

function StageNavButton(props: {
	stageId: WorksCompletionStageId;
	label: string;
	active: boolean;
	onSelect: (id: WorksCompletionStageId) => void;
}): ReactElement {
	const { stageId, label, active, onSelect } = props;
	return (
		<button
			type="button"
			className={`btn btn-block btn-sm ${active ? "btn-primary" : "btn-default"}`}
			style={{ marginBottom: "0.35rem", textAlign: "left" }}
			aria-current={active ? "true" : undefined}
			onClick={() => onSelect(stageId)}
		>
			{label}
		</button>
	);
}

function AvailabilityOrDisabled(props: {
	testId: string;
	label: string;
	action: WorksCompletionAvailabilityAction | null;
}): ReactElement {
	const { testId, label, action } = props;
	if (!action) {
		return (
			<button type="button" className="btn btn-default" disabled data-testid={testId} title="This action is not configured for this workspace.">
				{label}
			</button>
		);
	}
	return (
		<ActionAwareButton
			actionCode={action.actionCode}
			objectType={action.objectType}
			objectCode={action.objectCode}
			label={label}
			variant="secondary"
			buttonTestId={testId}
			availabilityContext={action.availabilityContext}
			onAllowedClick={action.onAllowedClick}
		/>
	);
}

export function WorksCompletionWorkspacePage(props: WorksCompletionWorkspacePageProps): ReactElement {
	const {
		tenderCode,
		tenderTitle,
		packageCode,
		procurementCategory,
		procurementMethod,
		selectedStdTemplate,
		instanceState,
		publicationState,
		blockers = [],
		outputImpactAffectedKinds = [],
		selectedStageId: controlledStage,
		onStageSelect,
		mainPanel,
		saveAction,
		generateOutputsAction,
		runReadinessAction,
	} = props;

	const [internalStage, setInternalStage] = useState<WorksCompletionStageId>("tds");
	const isControlled = controlledStage !== undefined;
	const selectedStage = isControlled ? controlledStage! : internalStage;

	useEffect(() => {
		if (isControlled) {
			return;
		}
		setInternalStage("tds");
	}, [tenderCode, isControlled]);

	const selectStage = useCallback(
		(id: WorksCompletionStageId) => {
			onStageSelect?.(id);
			if (!isControlled) {
				setInternalStage(id);
			}
		},
		[isControlled, onStageSelect],
	);

	const selectedLabel = WORKS_COMPLETION_SIDEBAR_STAGES.find((s) => s.id === selectedStage)?.label ?? selectedStage;

	return (
		<div data-testid="works-completion-page" className="works-completion-workspace-page">
			<header
				data-testid="works-context-header"
				className="panel panel-default"
				style={{ padding: "0.75rem", marginBottom: "0.75rem" }}
			>
				<h2 className="h4" style={{ marginTop: 0 }}>
					Works completion
				</h2>
				<p className="text-muted small" style={{ marginBottom: "0.5rem" }}>
					Complete Works tender content using the stages on the left. Actions below are allowed only when the security service
					says so — not from menu visibility alone.
				</p>
				<dl className="small" style={{ marginBottom: 0 }}>
					<dt>Tender</dt>
					<dd>
						<strong>{tenderTitle}</strong> ({tenderCode})
					</dd>
					<dt>Package code</dt>
					<dd>{packageCode}</dd>
					<dt>Procurement category</dt>
					<dd>{procurementCategory}</dd>
					<dt>Procurement method</dt>
					<dd>{procurementMethod}</dd>
					<dt>Selected STD template</dt>
					<dd>{selectedStdTemplate}</dd>
					<dt>Instance state</dt>
					<dd>{instanceState}</dd>
					<dt>Publication state</dt>
					<dd>{publicationState}</dd>
				</dl>
			</header>

			<div className="row" style={{ marginBottom: "0.75rem" }}>
				<div className="col-md-3">
					<aside
						data-testid="works-progress-sidebar"
						className="panel panel-default"
						style={{ padding: "0.75rem" }}
						aria-label="Completion stages"
					>
						<h4 className="h6" style={{ marginTop: 0 }}>
							Stages
						</h4>
						{WORKS_COMPLETION_SIDEBAR_STAGES.map((s) => (
							<StageNavButton key={s.id} stageId={s.id} label={s.label} active={selectedStage === s.id} onSelect={selectStage} />
						))}
					</aside>
				</div>
				<div className="col-md-9">
					<section data-testid="works-main-panel" className="panel panel-default" style={{ padding: "0.75rem", minHeight: "12rem" }}>
						<h4 className="h6" style={{ marginTop: 0 }}>
							{selectedLabel}
						</h4>
						{mainPanel ?? (
							<p className="text-muted small" style={{ marginBottom: 0 }}>
								Works content for this stage is provided by the host application (forms, grids, uploads). This shell only
								defines layout, navigation, blockers, output impact, and availability-driven actions.
							</p>
						)}
					</section>
				</div>
			</div>

			<section data-testid="works-blockers-panel" className="panel panel-default" style={{ padding: "0.75rem", marginBottom: "0.75rem" }}>
				<h4 className="h6" style={{ marginTop: 0 }}>
					Validation / blockers
				</h4>
				{blockers.length === 0 ? (
					<p className="text-muted small" style={{ marginBottom: 0 }}>
						No validation blockers reported.
					</p>
				) : (
					<BlockerList listDataTestId="works-blocker-sublist" blockers={blockers} emptyHint="None." />
				)}
			</section>

			<section data-testid="works-output-impact-panel" className="panel panel-default" style={{ padding: "0.75rem", marginBottom: "0.75rem" }}>
				<h4 className="h6" style={{ marginTop: 0 }}>
					Output impact
				</h4>
				<OutputImpactPanel affectedKinds={outputImpactAffectedKinds} />
			</section>

			<section className="clearfix" style={{ marginBottom: "1rem" }} aria-label="Save, generate, and readiness actions">
				<ActionAwareButton
					actionCode={saveAction.actionCode}
					objectType={saveAction.objectType}
					objectCode={saveAction.objectCode}
					label="Save"
					variant="primary"
					buttonTestId="works-save-action"
					availabilityContext={saveAction.availabilityContext}
					onAllowedClick={saveAction.onAllowedClick}
				/>{" "}
				<AvailabilityOrDisabled testId="works-generate-outputs-action" label="Generate outputs" action={generateOutputsAction} />{" "}
				<AvailabilityOrDisabled testId="works-run-readiness-action" label="Run readiness" action={runReadinessAction} />
			</section>
		</div>
	);
}
