<!-- Procurement Planning — PLN-CHG-001 v1.12 §10.
     One bundle, several Pages: "procurement-planning" (workspace + task deep
     links), "departmental-procurement-plan", "annual-procurement-plan" and
     "procurement-plan-item". This root reads the full route (page slug
     included) and picks the screen. There is no Procuring Entity anywhere:
     the Financial Year is the one visible filter, and a direct record route
     derives its year from the record (§10). -->
<template>
	<div class="kt-industry kt-pln">
		<div ref="railEl" class="kt-rail-mount"></div>
		<!-- One stable page-ready hook (§16.2): specs wait for
		     [data-testid="pln-shell"][data-loading="false"]. -->
		<div
			class="kt-shell"
			data-testid="pln-shell"
			:data-screen="screen"
			:data-loading="loading ? 'true' : 'false'"
			:data-refreshing="refreshing ? 'true' : 'false'"
		>
			<WorkspaceScreen
				v-if="screen === 'workspace'"
				:loading="loading"
				:error="error"
				:support-ref="supportRef"
				:workspace="workspace"
				:selected-financial-year="financialYear"
				:pending="pending"
				@reload="load"
				@select-financial-year="onSelectFy"
				@reset-financial-year="onResetFy"
				@open-departmental-plan="onOpenDepartmentalPlan"
				@navigate="onNavigate"
				@prepare-update="onPreparePlanUpdate"
			/>

			<template v-else>
				<div v-if="loading" class="kt-card kt-blueprint" style="padding: 24px">
					<i class="kt-corner tl"></i><i class="kt-corner tr"></i>
					<i class="kt-corner bl"></i><i class="kt-corner br"></i>
					<div v-for="row in 3" :key="row" class="pln-skel-row">
						<div class="kt-skel" style="width: 72%"></div>
						<div class="kt-skel" style="width: 52%"></div>
						<div class="kt-skel" style="width: 52%"></div>
						<div class="kt-skel" style="width: 44%"></div>
					</div>
				</div>
				<!-- §9/§11.18 — a masked "not found" (a record that exists but the
				     actor may not read) is a calm, expected state, never the
				     technical-failure panel below: no "Try again", no support
				     reference (reported live 2026-09-11 as a departmental actor's
				     direct link reading as a crash). Shares data-testid="pln-error"
				     with the load-error panel so either state satisfies the one
				     "this record page has an error" locator every spec already uses. -->
				<div v-else-if="notAvailable" class="kt-card kt-blueprint pln-state-card" data-testid="pln-error">
					<i class="kt-corner tl"></i><i class="kt-corner tr"></i>
					<i class="kt-corner bl"></i><i class="kt-corner br"></i>
					<h3>This record isn't available to you</h3>
					<p>It may not exist, or you may not have access to it.</p>
					<button
						type="button" class="kt-btn kt-btn-secondary"
						data-testid="pln-not-found-back"
						@click="frappe.set_route(WORKSPACE_PAGE)"
					>Go to Procurement Planning</button>
				</div>
				<!-- PLN-DES-16 load error — one component for every record page -->
				<div v-else-if="error" class="kt-card kt-blueprint pln-state-card" data-testid="pln-error">
					<i class="kt-corner tl"></i><i class="kt-corner tr"></i>
					<i class="kt-corner bl"></i><i class="kt-corner br"></i>
					<h3>Procurement Planning could not be loaded</h3>
					<p>Try again. If the problem continues, quote the support reference shown below.</p>
					<button type="button" class="kt-btn kt-btn-secondary" @click="load">Try again</button>
					<p class="pln-support-ref">Support reference: {{ supportRef }}</p>
				</div>

				<template v-else-if="screen === 'dpp'">
					<DppPlanScreen
						:plan="dpp"
						:pending="pending"
						:certified="certified"
						:error-summary="errorSummary"
						@update:certified="certified = $event"
						@view-accepted-needs="onViewAcceptedNeeds"
						@add-direct="go(dppReference, 'add-direct')"
						:funding-entry-id="fundingEntryId"
						:funding-editor="editor"
						:funding-budget-line="fundingBudgetLine"
						:funding-amount="fundingAmount"
						@open-entry="onOpenEntry"
						@restore-entry="onRestoreDisposition"
						@open-funding="onOpenFunding"
						@save-funding="onSaveEntryFunding"
						@close-funding="onCloseFunding"
						@exclude-entry="onExcludeEntry"
						@correct-source="onViewAcceptedNeeds"
						@update:funding-budget-line="fundingBudgetLine = $event"
						@update:funding-amount="fundingAmount = $event"
						@back="frappe.set_route(WORKSPACE_PAGE)"
						@save-draft="load({ quiet: true })"
						@submit="onSubmit"
						@create-update="onCreateUpdate"
						@open-task="(route) => frappe.set_route(...route)"
					/>
					<!-- U03-EXCLUDE — the governed exclusion reason, over the
					     plan, for the requirement whose panel is open. -->
					<NotProceedDialog
						v-if="notProceedDialog"
						:pending="pending"
						:error="errorSummary"
						@confirm="onNotProceedConfirm"
						@cancel="notProceedDialog = false"
					/>
				</template>

				<template v-else-if="screen === 'dpp-entry'">
					<DppEntryEditorScreen
						:editor="editor"
						:pending="pending"
						:error-summary="errorSummary"
						@save-direct="onSaveDirect"
						@remove="onRemoveDirect"
						@cancel="go(dppReference)"
					/>
				</template>

				<template v-else-if="screen === 'dpp-review'">
					<DppValidationScreen
						:task="validation"
						:classifications="classifications"
						:pending="pending"
						@set-classification="onClassify"
						@accept="onAccept"
						@return-to-department="returnDialog = true"
						@view-requirement="onViewRequirement"
					/>
					<ReturnIssuesDialog
						v-if="returnDialog"
						:entries="validation.entries || []"
						:pending="pending"
						:error="errorSummary"
						@confirm="onReturnConfirm"
						@cancel="returnDialog = false"
					/>
				</template>

				<!-- PLN-CHG-001 v1.23 §10.5 — the accepted-classification record
				     and its correction panel (U06-ACCEPTED-CLASSIFICATION /
				     U06-CORRECT-CLASSIFICATION). -->
				<template v-else-if="screen === 'dpp-classification'">
					<ClassificationEvidenceScreen
						:evidence="classificationEvidence"
						:panel="classificationPanel"
						:new-type="classificationNewType"
						:reason="classificationReason"
						:error="errorSummary"
						:pending="pending"
						@correct="onOpenClassificationCorrection"
						@cancel="onCancelClassificationCorrection"
						@save="onSaveClassificationCorrection"
						@update:new-type="classificationNewType = $event"
						@update:reason="classificationReason = $event"
					/>
				</template>

				<!-- PLN-CHG-001 v1.23 §10.13 — procurement progress against the
				     plan in force (U14). This replaces the v1.12 "active plan"
				     screen, whose forecast column and cascade dialog the
				     deferred forecast facility removed (PLN23-CHG-001). -->
				<template v-else-if="screen === 'progress'">
					<ProgressScreen
						:progress="progress"
						:pending="pending"
						:error-summary="errorSummary"
						@navigate="onNavigate"
						@view-corrections="onViewCorrections"
						@back="frappe.set_route(PLAN_PAGE, planReference)"
					/>
				</template>

				<!-- §10.15 — the correction requests against one purchase (U16). -->
				<template v-else-if="screen === 'corrections'">
					<CorrectionRequestsScreen
						:task="corrections"
						:open-issue="openIssue"
						:pending="pending"
						:error-summary="errorSummary"
						@open-issue="onOpenIssue"
						@prepare-correction="onPrepareCorrection"
						@record-completed="completeRequest = $event"
						@close-without-change="noChangeRequest = $event"
						@navigate="onNavigate"
						@back="frappe.set_route(PLAN_ITEM_PAGE, planItemId)"
					/>
					<RecordCorrectionDialog
						v-if="completeRequest"
						:request="completeRequest"
						:correcting-plan="corrections.correcting_plan || {}"
						:pending="pending"
						:error="errorSummary"
						@confirm="onRecordCorrectionCompleted"
						@cancel="completeRequest = null"
					/>
					<ReasonDialog
						v-if="noChangeRequest"
						testid="cor-no-change-dialog"
						title="Close without a plan change"
						:intro="`${noChangeRequest.change_required} — requested from ${noChangeRequest.detail.requisition_reference || noChangeRequest.requested_from}.`"
						label="Reason"
						confirm-label="Close request"
						:min-length="20"
						:pending="pending"
						:error="errorSummary"
						@confirm="onCloseWithoutChange"
						@cancel="noChangeRequest = null"
					/>
				</template>

				<template v-else-if="screen === 'publication'">
					<PublicationResultScreen
						:task="publication"
						:pending="pending"
						:error-summary="errorSummary"
						@retry="onRetryPublication"
						@reconcile="onReconcilePublication"
						@record-treasury="treasuryDialog = true"
						@correct-treasury="treasuryDialog = true"
						@request-withdrawal="withdrawalDialog = 'request'"
						@decide-withdrawal="withdrawalDialog = 'decision'"
						@explain-late="lateExplanationDialog = true"
						@navigate="onNavigate"
						@back="publication.plan_reference ? frappe.set_route(PLAN_PAGE, publication.plan_reference) : frappe.set_route(WORKSPACE_PAGE)"
					/>
					<LateExplanationDialog
						v-if="lateExplanationDialog"
						:financial-year-started="publication.late_activation?.financial_year_started_display || ''"
						:activated-at="publication.late_activation?.activated_display || ''"
						:pending="pending"
						:error="errorSummary"
						@confirm="onRecordLateExplanation"
						@cancel="lateExplanationDialog = false"
					/>
					<TreasurySubmissionDialog
						v-if="treasuryDialog"
						:task="publication"
						:pending="pending"
						:error="errorSummary"
						@confirm="onRecordTreasury"
						@cancel="treasuryDialog = false"
					/>
					<WithdrawalDialog
						v-if="withdrawalDialog"
						:task="publication"
						:mode="withdrawalDialog"
						:pending="pending"
						:error="errorSummary"
						@confirm="onWithdrawal"
						@cancel="withdrawalDialog = ''"
					/>
				</template>

				<template v-else-if="screen === 'plan'">
					<!-- PLN-DES-16 — publication was not acknowledged; the Draft is untouched -->
					<div v-if="annualPlan.latest_publication && annualPlan.latest_publication.result === 'Failed'" class="kt-card kt-blueprint pln-state-card" data-testid="pln-publication-failed">
						<i class="kt-corner tl"></i><i class="kt-corner tr"></i>
						<i class="kt-corner bl"></i><i class="kt-corner br"></i>
						<h3>Publication was not acknowledged</h3>
						<p>The approved Plan is unchanged. Retry the same publication when the destination is available.</p>
						<button type="button" class="kt-btn kt-btn-secondary" data-testid="pln-open-publication" @click="onNavigate(annualPlan.latest_publication.route)">Retry publication</button>
					</div>
					<AnnualPlanScreen
						:plan="annualPlan"
						:selected="selectedSources"
						:pending="pending"
						:error-summary="errorSummary"
						@open-form-dialog="formDialog = true"
						@navigate="onNavigate"
						@toggle-source="onToggleSource"
						@view-requirement="onViewPlanRequirement"
						@request-funding="onRequestPlanFunding"
						@submit-consolidated="onSubmitPlanRequested"
						@cancel-update="cancelUpdateDialog = true"
						@open-task="(route) => frappe.set_route(...route)"
						@save-details="onSaveVersionDetails"
					/>
					<CancelUpdateDialog
						v-if="cancelUpdateDialog"
						:pending="pending"
						:error="errorSummary"
						:reason="cancelUpdateReason"
						@update:reason="cancelUpdateReason = $event"
						@confirm="onCancelPlanUpdate"
						@cancel="cancelUpdateDialog = false; cancelUpdateReason = ''"
					/>
					<FormPlanItemsDialog
						v-if="formDialog"
						:entries="selectedSourceRows"
						:pending="pending"
						:error="errorSummary"
						@confirm="onFormConfirm"
						@cancel="formDialog = false"
					/>
					<ReasonDialog
						v-if="splittingDialog"
						testid="pln-splitting-dialog"
						title="Confirm contract splitting review"
						intro="State why the flagged Plan Items are legitimately separate procurements (a preference-scheme unbundling counts). The advisory stays on the readiness card; nothing is aggregated for you."
						label="Confirmation"
						confirm-label="Record confirmation"
						:pending="pending"
						:error="errorSummary"
						@confirm="onConfirmSplitting"
						@cancel="splittingDialog = false"
					/>
					<ReasonDialog
						v-if="lateActivationDialog"
						testid="pln-late-activation-dialog"
						title="Late activation reason"
						intro="The Financial Year has already begun. State why the Plan is being submitted for approval after the start of the year; the reason is kept with the submission."
						label="Late activation reason"
						confirm-label="Submit Plan"
						:pending="pending"
						:error="errorSummary"
						@confirm="onSubmitConsolidatedPlan"
						@cancel="lateActivationDialog = false"
					/>
				</template>

				<template v-else-if="screen === 'plan-item'">
					<PlanItemEditorScreen
						:item="planItem"
						:pending="pending"
						:error-summary="errorSummary"
						@save="onSavePlanItem"
						@remove="dissolveDialog = true"
						@back="onBackToPlan"
						@view-classification="onViewItemClassification"
					/>
					<DissolveItemDialog
						v-if="dissolveDialog"
						:sources="planItem.sources || []"
						:pending="pending"
						:error="errorSummary"
						@confirm="onDissolvePlanItem"
						@cancel="dissolveDialog = false"
					/>
				</template>

				<template v-else-if="screen === 'finance'">
					<FinanceTaskScreen
						:task="financeTask"
						:pending="pending"
						:error-summary="errorSummary"
						@confirm="onConfirmFunding"
						@open-return-dialog="financeReturnDialog = true"
					/>
					<FinanceReturnDialog
						v-if="financeReturnDialog"
						:pending="pending"
						:error="errorSummary"
						@confirm="onReturnFromFinance"
						@cancel="financeReturnDialog = false"
					/>
				</template>

				<template v-else-if="screen === 'governance'">
					<ReviewScreen
						:task="governanceTask"
						:resolution="collectiveResolution"
						:late-reason="lateReason"
						:pending="pending"
						:error-summary="errorSummary"
						@confirm="onGovernanceConfirm"
						@open-return-dialog="governanceReturnDialog = true"
						@back="frappe.set_route(PLAN_PAGE, governanceTask.plan_reference || '')"
						@download-pack="onDownloadReviewPack"
						@view-evidence="onNavigate($event.route)"
						@update:resolution="collectiveResolution = $event"
						@update:late-reason="lateReason = $event"
					/>
					<ReturnPlanDialog
						v-if="governanceReturnDialog"
						:dialog="governanceTask.return_dialog"
						:pending="pending"
						:error="errorSummary"
						@confirm="onGovernanceReturn"
						@cancel="governanceReturnDialog = false"
					/>
				</template>

				<template v-else-if="screen === 'governance-source'">
					<SourceEvidenceScreen
						:evidence="sourceEvidence"
						@navigate="onNavigate"
						@view-newer="onViewNewerRequirement"
						@reload="load"
					/>
				</template>
			</template>
		</div>
	</div>
</template>

<script setup>
import { computed, ref, watch } from "vue";
import { useRouteState } from "../pln_shared/composables/useRouteState.js";
import { usePageRail } from "../pln_shared/composables/usePageRail.js";
import * as api from "./data/planningApi.js";
import WorkspaceScreen from "./components/WorkspaceScreen.vue";
import DppPlanScreen from "./components/DppPlanScreen.vue";
import DppEntryEditorScreen from "./components/DppEntryEditorScreen.vue";
import DppValidationScreen from "./components/DppValidationScreen.vue";
import ClassificationEvidenceScreen from "./components/ClassificationEvidenceScreen.vue";
import ReturnIssuesDialog from "./components/ReturnIssuesDialog.vue";
import NotProceedDialog from "./components/NotProceedDialog.vue";
import AnnualPlanScreen from "./components/AnnualPlanScreen.vue";
import FormPlanItemsDialog from "./components/FormPlanItemsDialog.vue";
import ReasonDialog from "./components/ReasonDialog.vue";
import CancelUpdateDialog from "./components/CancelUpdateDialog.vue";
import DissolveItemDialog from "./components/DissolveItemDialog.vue";
// U11/U12. These three were used in the template but never imported, so the
// governance review has never actually rendered — the v1.18 cycle stopped
// before this slice.
import ReviewScreen from "./components/ReviewScreen.vue";
import ReturnPlanDialog from "./components/ReturnPlanDialog.vue";
import SourceEvidenceScreen from "./components/SourceEvidenceScreen.vue";
import ProgressScreen from "./components/ProgressScreen.vue";
import CorrectionRequestsScreen from "./components/CorrectionRequestsScreen.vue";
import RecordCorrectionDialog from "./components/RecordCorrectionDialog.vue";
import PublicationResultScreen from "./components/PublicationResultScreen.vue";
import LateExplanationDialog from "./components/LateExplanationDialog.vue";
import TreasurySubmissionDialog from "./components/TreasurySubmissionDialog.vue";
import WithdrawalDialog from "./components/WithdrawalDialog.vue";
import PlanItemEditorScreen from "./components/PlanItemEditorScreen.vue";
import FinanceTaskScreen from "./components/FinanceTaskScreen.vue";
import FinanceReturnDialog from "./components/FinanceReturnDialog.vue";
import GovernanceReturnDialog from "./components/GovernanceReturnDialog.vue";

const WORKSPACE_PAGE = "procurement-planning";
const DPP_PAGE = "departmental-procurement-plan";
const PLAN_PAGE = "annual-procurement-plan";
const PLAN_ITEM_PAGE = "procurement-plan-item";
const { route, epoch } = useRouteState(WORKSPACE_PAGE);
// Last payload per screen identity: a revisited screen renders from here at
// once and refreshes in place; the skeleton is only for a screen never
// loaded in this session.
const cache = kentender_core.desk_page.createScreenCache();

const railEl = ref(null);
const loading = ref(true);
const refreshing = ref(false);
const pending = ref(false);
const error = ref("");
// §9/§11.18 — a masked "unauthorised read" (frappe.DoesNotExistError, HTTP
// 404) is a distinct, calm state from a real load failure; see the template.
const notAvailable = ref(false);
const errorSummary = ref("");
const supportRef = ref("");
const workspace = ref({});
const dpp = ref({});
const editor = ref({});
// §10.4 U03-FUNDING — which requirement's funding panel is open beneath its
// own row, and the department's own unsaved draft of it. The inputs are bound
// to this, never to the server echo (AGENTS.md §6.4).
const fundingEntryId = ref("");
const fundingBudgetLine = ref("");
const fundingAmount = ref("");
const certified = ref(false);
const validation = ref({});
const classifications = ref({});
const classificationEvidence = ref({});
const classificationPanel = ref(null);
const classificationNewType = ref("");
const classificationReason = ref("");
const returnDialog = ref(false);
const notProceedDialog = ref(false);
const annualPlan = ref({});
const planItem = ref({});
const formDialog = ref(false);
// §10.7 — the Planner selects sources on U07 and then chooses how they become
// purchases in U08; the selection lives here so the dialog sees exactly what
// was ticked.
const selectedSources = ref([]);
const cancelUpdateDialog = ref(false);
const dissolveDialog = ref(false);
// §10.10 — a collective body's resolution reference, and the AO's late-start
// explanation, are inputs to the decision itself rather than separate dialogs.
const collectiveResolution = ref("");
const treasuryDialog = ref(false);
const lateExplanationDialog = ref(false);
// §10.12 — "" (closed), "request" (the AO's) or "decision" (the statutory
// authority's). The two are different dialogs for different people.
const withdrawalDialog = ref("");
const lateReason = ref("");
const cancelUpdateReason = ref("");
const splittingDialog = ref(false);
const lateActivationDialog = ref(false);
const financeTask = ref({});
const financeReturnDialog = ref(false);
const governanceTask = ref({});
// §10.11 U12 — one reviewed allocation's own departmental evidence.
const sourceEvidence = ref({});
const governanceReturnDialog = ref(false);
const publication = ref({});
const progress = ref({});
const corrections = ref({});
// Which issue's mechanics the Planner has deliberately opened (§10.15).
const openIssue = ref("");
const completeRequest = ref(null);
const noChangeRequest = ref(null);

// §10/§12.1 — the Financial Year is a visible filter only; the server
// resolves the remembered preference on a bare load.
const financialYear = ref("");

const pageSlug = computed(() => route.value[0] || WORKSPACE_PAGE);
const segments = computed(() => route.value.slice(1).filter(Boolean));

const dppReference = computed(() =>
	pageSlug.value === DPP_PAGE ? segments.value[0] || "" : ""
);

const planReference = computed(() =>
	pageSlug.value === PLAN_PAGE ? segments.value[0] || "" : ""
);

const planItemId = computed(() =>
	pageSlug.value === PLAN_ITEM_PAGE ? segments.value[0] || "" : ""
);

const screen = computed(() => {
	if (pageSlug.value === DPP_PAGE && dppReference.value) {
		const second = segments.value[1];
		if (second === "add-direct" || second === "entry") return "dpp-entry";
		return "dpp";
	}
	// §10 task deep links live under the workspace page's own prefix.
	if (pageSlug.value === WORKSPACE_PAGE && segments.value[0] === "dpp-review" && segments.value[1]) {
		return "dpp-review";
	}
	if (pageSlug.value === WORKSPACE_PAGE && segments.value[0] === "dpp-classification" && segments.value[1]) {
		return "dpp-classification";
	}
	if (pageSlug.value === WORKSPACE_PAGE && segments.value[0] === "finance" && segments.value[1]) {
		return "finance";
	}
	if (pageSlug.value === WORKSPACE_PAGE && segments.value[0] === "review" && segments.value[1]) {
		// §10.11 — the evidence of one source, within its own review.
		return segments.value[2] === "source" && segments.value[3] ? "governance-source" : "governance";
	}
	if (pageSlug.value === WORKSPACE_PAGE && segments.value[0] === "publication" && segments.value[1]) {
		return "publication";
	}
	if (pageSlug.value === PLAN_PAGE && planReference.value) {
		return segments.value[1] === "progress" ? "progress" : "plan";
	}
	if (pageSlug.value === PLAN_ITEM_PAGE && planItemId.value) {
		return segments.value[1] === "corrections" ? "corrections" : "plan-item";
	}
	return "workspace";
});

const validationTaskId = computed(() =>
	segments.value[0] === "dpp-review" ? segments.value[1] || "" : ""
);

const classificationSubmissionId = computed(() =>
	segments.value[0] === "dpp-classification" ? segments.value[1] || "" : ""
);

const financeTaskId = computed(() =>
	segments.value[0] === "finance" ? segments.value[1] || "" : ""
);

const governanceTaskId = computed(() =>
	segments.value[0] === "review" ? segments.value[1] || "" : ""
);

const sourceKey = computed(() =>
	segments.value[2] === "source" ? segments.value.slice(3).join("/") : ""
);

const publicationId = computed(() =>
	segments.value[0] === "publication" ? segments.value[1] || "" : ""
);

const entryId = computed(() =>
	segments.value[1] === "entry" ? segments.value[2] || "" : ""
);

const screenKey = computed(() => {
	switch (screen.value) {
		case "dpp":
			return `dpp:${dppReference.value}`;
		case "dpp-entry":
			return `dpp-entry:${dppReference.value}:${entryId.value || "new"}`;
		case "dpp-review":
			return `dpp-review:${validationTaskId.value}`;
		case "dpp-classification":
			return `dpp-classification:${classificationSubmissionId.value}`;
		case "plan":
			return `plan:${planReference.value}`;
		case "progress":
			return `progress:${planReference.value}`;
		case "plan-item":
			return `plan-item:${planItemId.value}`;
		case "corrections":
			return `corrections:${planItemId.value}`;
		case "finance":
			return `finance:${financeTaskId.value}`;
		case "governance":
			return `governance:${governanceTaskId.value}`;
		case "governance-source":
			return `governance-source:${governanceTaskId.value}:${sourceKey.value}`;
		case "publication":
			return `publication:${publicationId.value}`;
		default:
			return "workspace";
	}
});

function go(...parts) {
	frappe.set_route(DPP_PAGE, ...parts.filter(Boolean));
}

function onBackToPlan() {
	if (planItem.value.plan_reference) {
		frappe.set_route(PLAN_PAGE, planItem.value.plan_reference);
	} else {
		frappe.set_route(WORKSPACE_PAGE);
	}
}

// RUN-CHG-001 §6.4 — a shared sequence-token utility instead of a
// hand-rolled `let loadSeq = 0` counter, so a slower, older response can
// never overwrite a newer one.
const loadGuard = kentender_core.desk_page.createSequenceGuard();
let inFlightKey = "";

function fetchFor(scr) {
	switch (scr) {
		case "workspace":
			return api.getPlanningWorkspace({ financial_year: financialYear.value || undefined });
		case "dpp":
			return api.getDepartmentalPlan(dppReference.value);
		case "dpp-entry":
			return api.getDppEntryEditor(dppReference.value, entryId.value || undefined);
		case "dpp-review":
			return api.getDppValidationTask(validationTaskId.value);
		case "dpp-classification":
			return api.getAcceptedDppClassification(classificationSubmissionId.value);
		case "plan":
			return api.getAnnualPlan(planReference.value);
		case "progress":
			return api.getProcurementProgress(planReference.value);
		case "plan-item":
			return api.getPlanItem(planItemId.value);
		case "corrections":
			return api.getPlanCorrectionRequests(planItemId.value);
		case "finance":
			return api.getFinanceTask(financeTaskId.value);
		case "governance":
			return api.getPlanGovernanceTask(governanceTaskId.value);
		case "governance-source":
			return api.getSourceEvidence(governanceTaskId.value, sourceKey.value);
		case "publication":
			return api.getPublicationTask(publicationId.value);
		default:
			return Promise.resolve(null);
	}
}

function applyLoaded(scr, loaded) {
	switch (scr) {
		case "workspace": {
			workspace.value = loaded;
			const context = loaded.context || {};
			if (context.financial_year) financialYear.value = context.financial_year;
			break;
		}
		case "dpp":
			dpp.value = loaded;
			certified.value = false;
			// A reload closes the funding panel: it was opened against an
			// entry whose state may have moved.
			fundingEntryId.value = "";
			fundingBudgetLine.value = "";
			fundingAmount.value = "";
			break;
		case "dpp-entry":
			editor.value = loaded;
			notProceedDialog.value = false;
			break;
		case "dpp-classification":
			classificationEvidence.value = loaded;
			// A reload closes the panel: it was opened against evidence that
			// may have moved.
			classificationPanel.value = null;
			classificationNewType.value = "";
			classificationReason.value = "";
			break;
		case "dpp-review":
			validation.value = loaded;
			classifications.value = {};
			returnDialog.value = false;
			break;
		case "plan":
			annualPlan.value = loaded;
			selectedSources.value = [];
			formDialog.value = false;
			splittingDialog.value = false;
			lateActivationDialog.value = false;
			break;
		case "progress":
			progress.value = loaded;
			break;
		case "plan-item":
			planItem.value = loaded;
			dissolveDialog.value = false;
			break;
		case "corrections":
			corrections.value = loaded;
			// A reload closes both dialogs and the open detail: they were
			// opened against a request whose state may have moved.
			openIssue.value = "";
			completeRequest.value = null;
			noChangeRequest.value = null;
			break;
		case "finance":
			financeTask.value = loaded;
			financeReturnDialog.value = false;
			break;
		case "governance":
			governanceTask.value = loaded;
			collectiveResolution.value = "";
			lateReason.value = "";
			governanceReturnDialog.value = false;
			break;
		case "governance-source":
			sourceEvidence.value = loaded;
			break;
		case "publication":
			publication.value = loaded;
			treasuryDialog.value = false;
			lateExplanationDialog.value = false;
			withdrawalDialog.value = "";
			break;
	}
}

// The skeleton shows only for a screen with nothing to show yet. A screen
// already loaded this session (Back, Cancel, a save that routes) renders its
// last payload at once and refreshes in place; `quiet` forces the in-place
// path for filter changes and post-action refreshes.
async function load(opts) {
	const scr = screen.value;
	const key = screenKey.value;
	const cached = cache.get(key);
	if (opts && opts.entering && cached) applyLoaded(scr, cached);
	const quiet = !!(opts && opts.quiet === true) || !!cached;
	if (quiet && inFlightKey === key) return;
	const token = loadGuard.next();
	inFlightKey = key;
	if (quiet) refreshing.value = true;
	else loading.value = true;
	error.value = "";
	notAvailable.value = false;
	errorSummary.value = "";
	try {
		const loaded = await fetchFor(scr);
		if (!loadGuard.isCurrent(token)) return;
		cache.set(key, loaded);
		applyLoaded(scr, loaded);
	} catch (e) {
		if (!loadGuard.isCurrent(token)) return;
		if (e.httpStatus === 404) {
			notAvailable.value = true;
		} else {
			error.value = e.message;
			supportRef.value = newSupportRef();
		}
	} finally {
		if (loadGuard.isCurrent(token)) {
			loading.value = false;
			refreshing.value = false;
			inFlightKey = "";
		}
	}
}

function newSupportRef() {
	const now = new Date();
	const pad = (n) => String(n).padStart(2, "0");
	return (
		`PLN-ERR-${now.getFullYear()}${pad(now.getMonth() + 1)}${pad(now.getDate())}` +
		`-${pad(now.getHours())}${pad(now.getMinutes())}`
	);
}

async function persistSelection() {
	try {
		await api.selectPlanningContext({ financial_year: financialYear.value });
	} catch (e) {
		// a refused selection simply does not persist
	}
}

function onSelectFy(value) {
	financialYear.value = value;
	load({ quiet: true }).then(persistSelection);
}

async function onResetFy() {
	try {
		await api.resetPlanningContext();
	} catch (e) {
		// nothing to forget
	}
	financialYear.value = "";
	await load({ quiet: true });
}

async function run(action, fn) {
	if (pending.value) return null;
	pending.value = true;
	errorSummary.value = "";
	try {
		return await fn(api.newIdempotencyKey(action));
	} catch (e) {
		errorSummary.value = e.message;
		return null;
	} finally {
		pending.value = false;
	}
}

async function onOpenDepartmentalPlan(organisationUnit) {
	const result = await run("open-dpp", (key) =>
		api.openDepartmentalPlan({
			organisation_unit: organisationUnit,
			fiscal_year: financialYear.value || (workspace.value.context || {}).financial_year,
			idempotency_key: key,
		})
	);
	if (result) await load({ quiet: true });
}

function onOpenEntry(row) {
	go(dppReference.value, "entry", row.entry_id);
}

// §10.4 U03-FUNDING — the panel opens in place. The editor read supplies the
// eligible budget lines and the requirement's own facts; nothing navigates.
async function onOpenFunding(row) {
	if (fundingEntryId.value === row.entry_id) {
		onCloseFunding();
		return;
	}
	errorSummary.value = "";
	const loaded = await api.getDppEntryEditor(dppReference.value, row.entry_id);
	editor.value = loaded;
	fundingEntryId.value = row.entry_id;
	fundingBudgetLine.value = loaded.entry?.budget_line || "";
	fundingAmount.value = loaded.entry?.indicative_amount ?? "";
}

function onCloseFunding() {
	fundingEntryId.value = "";
	fundingBudgetLine.value = "";
	fundingAmount.value = "";
	errorSummary.value = "";
}

async function onSaveEntryFunding() {
	const result = await run("save-need-funding", async (key) => {
		const r = await api.saveNeedFunding({
			dpp_version: editor.value.dpp_version,
			entry_id: fundingEntryId.value,
			budget_line: fundingBudgetLine.value || undefined,
			indicative_amount: fundingAmount.value || undefined,
			expected_record_version: editor.value.record_version,
			idempotency_key: key,
		});
		await load({ quiet: true });
		return r;
	});
	if (result) onCloseFunding();
}

// U03-EXCLUDE — the exclusion is a governed reason, so it keeps its own
// dialog rather than being a third control in the funding panel.
function onExcludeEntry(row) {
	fundingEntryId.value = row.entry_id;
	notProceedDialog.value = true;
}

function onViewAcceptedNeeds() {
	frappe.set_route("departmental-needs");
}

async function onSubmit() {
	// RUN-CHG-001 — the reload that refreshes record_version must be awaited
	// inside the guarded function, before `run()`'s finally clears `pending`.
	await run("submit-dpp", async (key) => {
		const r = await api.submitDepartmentalPlan({
			dpp_version: dpp.value.version?.name,
			certification_confirmed: certified.value,
			expected_record_version: dpp.value.record_version,
			idempotency_key: key,
		});
		await load({ quiet: true });
		return r;
	});
}

async function onCreateUpdate() {
	// The route stays on the same DPP: the reload now serves the Draft successor.
	await run("create-dpp-update", async (key) => {
		const r = await api.createDepartmentalPlanUpdate({
			departmental_plan: dpp.value.dpp_reference,
			expected_record_version: dpp.value.record_version,
			idempotency_key: key,
		});
		await load({ quiet: true });
		return r;
	});
}

// PLN-CHG-001 v1.18 §5.1.4 — U03's own overlaid dialog, reached from the
// editor's "Do not proceed this financial year" ghost button.
async function onNotProceedConfirm(reason) {
	// Reached from the funding panel on the plan (the ordinary path) or from
	// the direct-entry editor page; either way it is the same command against
	// the same entry.
	const onPlan = screen.value === "dpp";
	const result = await run("set-need-disposition", async (key) => {
		const r = await api.setNeedPlanningDisposition({
			dpp_version: onPlan ? dpp.value.version?.name : editor.value.dpp_version,
			entry_id: onPlan ? fundingEntryId.value : editor.value.entry?.entry_id,
			disposition: "Do not proceed",
			reason,
			expected_record_version: onPlan ? dpp.value.record_version : editor.value.record_version,
			idempotency_key: key,
		});
		if (onPlan) await load({ quiet: true });
		return r;
	});
	if (!result) return;
	notProceedDialog.value = false;
	if (onPlan) onCloseFunding();
	else go(dppReference.value);
}

// U03-notproceeding — Restore lives on the Plan screen's own not-proceeding
// row, not the editor: no dialog, direct command (the frame draws no overlay).
// U03-EXCLUDED-ROW — the screen emits the row it was clicked on; this takes
// the entry id out of it. Passing the row straight through sent an object
// where the command expects an id, so restoring silently did nothing.
async function onRestoreDisposition(row) {
	const entryId = typeof row === "string" ? row : row?.entry_id;
	if (!entryId) return;
	await run("restore-need-disposition", async (key) => {
		const r = await api.setNeedPlanningDisposition({
			dpp_version: dpp.value.version?.name,
			entry_id: entryId,
			disposition: "Restore",
			expected_record_version: dpp.value.record_version,
			idempotency_key: key,
		});
		await load({ quiet: true });
		return r;
	});
}

async function onSaveDirect(values) {
	const result = await run("save-direct", (key) =>
		api.saveDirectRequirement({
			dpp_version: editor.value.dpp_version,
			entry_values: JSON.stringify(values),
			entry_id: entryId.value || undefined,
			expected_record_version: editor.value.record_version,
			idempotency_key: key,
		})
	);
	if (result) go(dppReference.value);
}

// U04-EDIT — a requirement the department added is the department's own to
// withdraw; it leaves the draft entirely rather than being marked excluded.
async function onRemoveDirect() {
	const result = await run("remove-direct", (key) =>
		api.removeDirectRequirement({
			dpp_version: editor.value.dpp_version,
			entry_id: entryId.value,
			expected_record_version: editor.value.record_version,
			idempotency_key: key,
		})
	);
	if (result) go(dppReference.value);
}

// §5.5.2 / §10.12 — the Accounting Officer records what was sent outside the
// system. A correction supersedes the recorded evidence with a reason; it
// never overwrites it, so the two are separate commands.
async function onRecordTreasury(values) {
	const correcting = Boolean(publication.value.treasury_prior);
	const result = await run("record-treasury", async (key) => {
		const r = correcting
			? await api.correctTreasurySubmissionEvidence({
				prior_evidence: publication.value.treasury_evidence_id,
				reason: values.reason,
				submitted_at: values.submitted_at,
				channel: values.channel,
				destination: values.destination,
				dispatch_reference: values.dispatch_reference,
				supporting_attachment: values.supporting_attachment || "",
				idempotency_key: key,
			})
			: await api.recordTreasurySubmission({
				plan_version: publication.value.version?.reference,
				submitted_at: values.submitted_at,
				channel: values.channel,
				destination: values.destination,
				dispatch_reference: values.dispatch_reference,
				exact_document_confirmed: values.exact_document_confirmed ? 1 : 0,
				supporting_attachment: values.supporting_attachment || "",
				idempotency_key: key,
			});
		await load({ quiet: true });
		return r;
	});
	if (result) treasuryDialog.value = false;
}

// §10.14 — append, never rewrite: the newest recorded explanation is named as
// the one this supersedes, so the earlier reason stays readable beside it.
async function onRecordLateExplanation(reason) {
	const recorded = publication.value.late_activation?.explanations || [];
	const latest = recorded.length ? recorded[recorded.length - 1].id : "";
	const result = await run("record-late-explanation", async (key) => {
		const r = await api.recordLateActivationExplanation({
			plan_version: publication.value.version?.reference,
			reason,
			supersedes: latest,
			idempotency_key: key,
		});
		await load({ quiet: true });
		return r;
	});
	if (result) lateExplanationDialog.value = false;
}

// §5.5.2.4 — the AO asks and the statutory authority decides; the mode the
// dialog was opened in is which of the two this is.
async function onWithdrawal(reason) {
	const deciding = withdrawalDialog.value === "decision";
	const result = await run("plan-withdrawal", async (key) => {
		const r = deciding
			? await api.withdrawApprovedPlanForCorrection({
				task: publication.value.withdrawal_task,
				task_token: publication.value.withdrawal_task_token,
				idempotency_key: key,
			})
			: await api.requestPlanWithdrawal({
				plan_version: publication.value.version?.reference,
				reason,
				idempotency_key: key,
			});
		await load({ quiet: true });
		return r;
	});
	if (result) withdrawalDialog.value = "";
}

async function onReconcilePublication() {
	// §5.5.2.3 — reconciliation reads the authoritative destination result.
	// It never sets success, and an unknown outcome stays unknown.
	const result = await run("reconcile-publication", (key) =>
		api.reconcilePublication({ publication: publication.value.publication, idempotency_key: key })
	);
	if (result) await load({ quiet: true });
}

function onViewItemClassification() {
	// §10.8 — the classification evidence for this purchase's own sources,
	// read-only: nothing on the purchase editor makes it editable.
	const source = (planItem.value.sources || [])[0];
	if (!source || !source.dpp_submission) return;
	frappe.set_route(WORKSPACE_PAGE, "dpp-classification", source.dpp_submission);
}

async function onPreparePlanUpdate() {
	// §5.2.3 / §11.9 — the guarded successor start, not a navigation. The
	// Active predecessor stays in force; this only opens one Draft candidate.
	const planReference = (workspace.value.annual_plan || {}).plan_reference;
	const result = await run("begin-plan-update", (key) =>
		api.beginPlanUpdate({ plan_reference: planReference, idempotency_key: key })
	);
	if (!result) return;
	frappe.set_route(PLAN_PAGE, planReference);
}

async function onCancelPlanUpdate() {
	const result = await run("cancel-plan-update", (key) =>
		api.cancelPlanUpdate({
			plan_reference: annualPlan.value.plan_reference,
			reason: cancelUpdateReason.value,
			expected_record_version: annualPlan.value.record_version,
			idempotency_key: key,
		})
	);
	if (!result) return;
	cancelUpdateDialog.value = false;
	cancelUpdateReason.value = "";
	frappe.set_route(WORKSPACE_PAGE);
}

function onToggleSource(entryId) {
	const current = selectedSources.value;
	selectedSources.value = current.includes(entryId)
		? current.filter((id) => id !== entryId)
		: [...current, entryId];
}

const selectedSourceRows = computed(() =>
	(annualPlan.value.unallocated_sources || []).filter((row) => selectedSources.value.includes(row.entry_id))
);

function onViewPlanRequirement(row) {
	frappe.set_route(DPP_PAGE, row.dpp_reference || "", "entry", row.entry_id);
}

function onClassify({ entry_id: entryId, requirement_type: value }) {
	classifications.value = { ...classifications.value, [entryId]: value };
}

function onViewRequirement(row) {
	frappe.set_route(DPP_PAGE, validation.value.dpp_reference || "", "entry", row.entry_id);
}

// --- §10.5 accepted-classification correction -----------------------------

function onOpenClassificationCorrection(row) {
	classificationPanel.value = row;
	classificationNewType.value = "";
	classificationReason.value = "";
	errorSummary.value = "";
}

function onCancelClassificationCorrection() {
	classificationPanel.value = null;
	classificationNewType.value = "";
	classificationReason.value = "";
	errorSummary.value = "";
}

async function onSaveClassificationCorrection() {
	const row = classificationPanel.value;
	if (!row) return;
	const result = await run("correct-classification", (key) =>
		api.correctAcceptedRequirementClassification({
			dpp_submission: classificationEvidence.value.dpp_submission,
			dpp_entry_id: row.dpp_entry_id,
			// The exact evidence head the Planner was looking at: a concurrent
			// correction must fail rather than silently stack on a newer one.
			expected_evidence_id: row.classification.evidence_id,
			new_requirement_type: classificationNewType.value,
			reason: classificationReason.value,
			idempotency_key: key,
		})
	);
	if (!result) return;
	onCancelClassificationCorrection();
	await load({ quiet: true });
}

async function onAccept() {
	const result = await run("accept-dpp", (key) =>
		api.acceptDepartmentalPlan({
			task: validation.value.task,
			classifications: JSON.stringify(classifications.value),
			task_token: validation.value.task_token,
			idempotency_key: key,
		})
	);
	if (result) frappe.set_route(WORKSPACE_PAGE);
}

async function onReturnConfirm(issues) {
	const result = await run("return-dpp", (key) =>
		api.returnDepartmentalPlan({
			task: validation.value.task,
			issues: JSON.stringify(issues),
			task_token: validation.value.task_token,
			idempotency_key: key,
		})
	);
	if (result) {
		returnDialog.value = false;
		frappe.set_route(WORKSPACE_PAGE);
	}
}

function onNavigate(routeSegments) {
	if (!routeSegments || !routeSegments.length) return;
	frappe.set_route(...routeSegments);
}

async function onFormConfirm({ dppEntries, mode, combinationReason, combinedTitle }) {
	// RUN-CHG-001 — only the in-place branch (multiple items formed, staying
	// on this Plan) needs its reload inside the guarded function; the
	// single-item branch navigates away to a different screen instead.
	const result = await run("form-plan-items", async (key) => {
		const r = await api.formPlanItems({
			plan_version: annualPlan.value.version_reference,
			dpp_entries: JSON.stringify(dppEntries),
			mode,
			// §10.7 — asked at the moment of combining, so the combined
			// purchase is complete the moment it exists.
			combination_reason: combinationReason || "",
			combined_title: combinedTitle || "",
			expected_record_version: annualPlan.value.record_version,
			idempotency_key: key,
		});
		if (!r.single) await load({ quiet: true });
		return r;
	});
	if (result) {
		formDialog.value = false;
		if (result.single) {
			frappe.set_route(PLAN_ITEM_PAGE, result.created_items[0]);
		}
	}
}

async function onSavePlanItem(values) {
	// RUN-CHG-001 — reload inside the guarded function so a command fired the
	// instant the button re-enables reads the fresh record_version.
	await run("save-plan-item", async (key) => {
		const r = await api.savePlanItem({
			plan_item: planItem.value.plan_item_id,
			item_values: JSON.stringify(values),
			expected_record_version: planItem.value.record_version,
			idempotency_key: key,
		});
		await load({ quiet: true });
		return r;
	});
}

async function onDissolvePlanItem() {
	const result = await run("dissolve-plan-item", (key) =>
		api.dissolvePlanItem({
			plan_item: planItem.value.plan_item_id,
			expected_record_version: planItem.value.record_version,
			idempotency_key: key,
		})
	);
	if (result) onBackToPlan();
}

// §5.2 — one plan-level Finance confirmation per Version
async function onRequestPlanFunding() {
	// RUN-CHG-001 — reload inside the guarded function (same-screen command).
	await run("request-plan-funding", async (key) => {
		const r = await api.requestPlanFundingConfirmation({
			plan_version: annualPlan.value.version_reference,
			expected_record_version: annualPlan.value.record_version,
			idempotency_key: key,
		});
		await load({ quiet: true });
		return r;
	});
}

// U07-overview — the Preparation card's own Save draft (SavePlanVersionDetails,
// project_name only; a successor's change_reason is set at BeginPlanUpdate).
async function onSaveVersionDetails(values) {
	await run("save-plan-version-details", async (key) => {
		const r = await api.savePlanVersionDetails({
			plan_version: annualPlan.value.version_reference,
			detail_values: JSON.stringify(values),
			expected_record_version: annualPlan.value.record_version,
			idempotency_key: key,
		});
		await load({ quiet: true });
		return r;
	});
}

async function onConfirmFunding() {
	const result = await run("confirm-plan-funding", (key) =>
		api.confirmPlanFunding({
			task: financeTask.value.task,
			task_token: financeTask.value.task_token,
			idempotency_key: key,
		})
	);
	if (result) frappe.set_route(WORKSPACE_PAGE);
}

async function onReturnFromFinance(reason) {
	const result = await run("return-from-finance", (key) =>
		api.returnFromFinance({
			task: financeTask.value.task,
			reason,
			task_token: financeTask.value.task_token,
			idempotency_key: key,
		})
	);
	if (result) {
		financeReturnDialog.value = false;
		frappe.set_route(WORKSPACE_PAGE);
	}
}

// invariant 27 (O2): once the year has begun the submission carries a reason
function onSubmitPlanRequested() {
	if (annualPlan.value.late_activation_required) {
		lateActivationDialog.value = true;
		return;
	}
	onSubmitConsolidatedPlan("");
}

// invariant 26 (O1)
async function onConfirmSplitting(confirmation) {
	// RUN-CHG-001 — reload inside the guarded function (same-screen command).
	const result = await run("confirm-splitting", async (key) => {
		const r = await api.confirmSplittingAdvisory({
			plan_version: annualPlan.value.version_reference,
			confirmation,
			expected_record_version: annualPlan.value.record_version,
			idempotency_key: key,
		});
		await load({ quiet: true });
		return r;
	});
	if (result) {
		splittingDialog.value = false;
	}
}

async function onSubmitConsolidatedPlan(lateActivationReason) {
	const command = annualPlan.value.is_correction ? "submit-corrected" : "submit-consolidated";
	const apiCall = annualPlan.value.is_correction ? api.submitCorrectedPlan : api.submitConsolidatedPlan;
	const result = await run(command, (key) =>
		apiCall({
			plan_version: annualPlan.value.version_reference,
			expected_record_version: annualPlan.value.record_version,
			idempotency_key: key,
			...(lateActivationReason ? { late_activation_reason: lateActivationReason } : {}),
		})
	);
	if (result) {
		lateActivationDialog.value = false;
		frappe.set_route(WORKSPACE_PAGE, "review", result.task);
	}
}

// PLN-CHG-001 v1.23 §10.13 / §10.15 — progress and correction requests.

// §10.11 U12-NEWER-SOURCE — the newer requirement is the department's record,
// not this plan's; it opens where that department keeps it, and the reviewed
// evidence behind it is left exactly as it was.
function onViewNewerRequirement() {
	const reference = sourceEvidence.value.departmental_plan_reference;
	if (reference) frappe.set_route(DPP_PAGE, reference);
}

function onViewCorrections(planItemId) {
	frappe.set_route(PLAN_ITEM_PAGE, planItemId, "corrections");
}

// The mechanics of one issue open only when the Planner asks for them; the
// required change is what the table leads with (PLN22-AC-011).
function onOpenIssue(request) {
	openIssue.value = openIssue.value === request ? "" : request;
}

// §7.2 StartPlanItemCorrection — Open becomes In progress. The hold stays in
// force: starting is not resolving, and this command never edits the item.
async function onPrepareCorrection(row) {
	const result = await run("start-correction", async (key) => {
		const r = await api.startPlanItemCorrection({
			correction_request: row.request,
			expected_record_version: row.record_version,
			idempotency_key: key,
		});
		await load({ quiet: true });
		return r;
	});
	if (result) openIssue.value = row.request;
}

// §7.2 ResolvePlanItemCorrectionRequest — recorded against the exact Active
// version; the server refuses anything that is not Active.
async function onRecordCorrectionCompleted() {
	const row = completeRequest.value;
	if (!row) return;
	const result = await run("resolve-correction", async (key) => {
		const r = await api.resolvePlanItemCorrectionRequest({
			correction_request: row.request,
			correcting_plan_version: corrections.value.correcting_plan?.correcting_plan_version,
			expected_record_version: row.record_version,
			idempotency_key: key,
		});
		await load({ quiet: true });
		return r;
	});
	if (result) completeRequest.value = null;
}

// §7.2 ClosePlanItemCorrectionWithoutChange — a reasoned no-change outcome.
// It resolves this request only, and revives nothing downstream.
async function onCloseWithoutChange(reason) {
	const row = noChangeRequest.value;
	if (!row) return;
	const result = await run("close-correction", async (key) => {
		const r = await api.closePlanItemCorrectionWithoutChange({
			correction_request: row.request,
			reason,
			expected_record_version: row.record_version,
			idempotency_key: key,
		});
		await load({ quiet: true });
		return r;
	});
	if (result) noChangeRequest.value = null;
}

async function onRetryPublication() {
	const result = await run("retry-publication", (key) =>
		api.retryPublication({ publication: publication.value.publication, idempotency_key: key })
	);
	if (!result) return;
	// a retry is a new attempt record; the route follows it (§12.11)
	if (result.publication && result.publication !== publication.value.publication) {
		frappe.set_route(WORKSPACE_PAGE, "publication", result.publication);
	} else {
		await load({ quiet: true });
	}
}

async function onBeginUpdate() {
	const result = await run("begin-plan-update", (key) =>
		api.beginPlanUpdate({
			plan_reference: planReference.value,
			idempotency_key: key,
		})
	);
	if (result) await load({ quiet: true });
}

async function onGovernanceConfirm() {
	const command = governanceTask.value.stage === "Accounting Officer adoption" ? "adopt" : "approve";
	const result = await run(command, (key) =>
		command === "adopt"
			? api.adoptAndSubmitPlan({
					task: governanceTask.value.task,
					task_token: governanceTask.value.task_token,
					// §10.10 U11-LATE-ADOPTION — the AO's own explanation, given
					// on the review rather than in a separate dialog.
					late_activation_reason: lateReason.value || undefined,
					idempotency_key: key,
				})
			: api.approveAnnualPlan({
					task: governanceTask.value.task,
					task_token: governanceTask.value.task_token,
					// Required only for a collective body; the server checks it.
					resolution_reference: collectiveResolution.value || undefined,
					idempotency_key: key,
				})
	);
	if (result) frappe.set_route(WORKSPACE_PAGE);
}

function onDownloadReviewPack() {
	// §11.1 — the exact authorised reviewed snapshot, and never a
	// prerequisite to deciding.
	window.open(
		`/api/method/kentender_procurement.procurement_planning.api.download_review_pack`
		+ `?task=${encodeURIComponent(governanceTask.value.task || "")}`,
		"_blank",
	);
}

async function onGovernanceReturn(reason) {
	const result = await run("return-plan-version", (key) =>
		api.returnPlanVersion({
			task: governanceTask.value.task,
			reason,
			task_token: governanceTask.value.task_token,
			idempotency_key: key,
		})
	);
	if (result) {
		governanceReturnDialog.value = false;
		frappe.set_route(WORKSPACE_PAGE);
	}
}

watch([pageSlug, segments], () => load({ entering: true }), { immediate: true, deep: true });
// The page came back into view on the same route: revalidate what is shown.
watch(epoch, () => {
	if (cache.has(screenKey.value)) load({ quiet: true });
});

const railTrail = computed(() => {
	const trail = [
		{ label: __("Home"), route: ["Workspaces", "Procurement Home"] },
		{ label: "Procurement Planning", route: [WORKSPACE_PAGE] },
	];
	if (screen.value === "dpp-review") {
		trail.push({ label: "DPP review" });
	}
	if (screen.value === "finance") {
		trail.push({ label: "Finance" });
	}
	if (screen.value === "governance") {
		trail.push({ label: "Review" });
	}
	if (screen.value === "publication") {
		trail.push({ label: "Publication" });
	}
	if (dppReference.value) {
		trail.push({ label: dppReference.value, route: [DPP_PAGE, dppReference.value] });
		if (screen.value === "dpp-entry") {
			trail.push({
				label:
					segments.value[1] === "add-direct"
						? "Add direct requirement"
						: (editor.value.entry || {}).need_reference_line?.split(" · ")[0] ||
						  entryId.value,
			});
		}
	}
	if (planReference.value) {
		trail.push({ label: planReference.value, route: [PLAN_PAGE, planReference.value] });
	}
	if (screen.value === "plan-item" && planItemId.value) {
		if (!planReference.value && planItem.value.plan_reference) {
			trail.push({
				label: planItem.value.plan_reference,
				route: [PLAN_PAGE, planItem.value.plan_reference],
			});
		}
		trail.push({ label: planItemId.value });
	}
	return trail;
});

// §10 — no Procuring Entity switcher anywhere in Planning
usePageRail(railEl, railTrail, { showPeSwitcher: false });
</script>
