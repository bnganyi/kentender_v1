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
		>
			<WorkspaceScreen
				v-if="screen === 'workspace'"
				:loading="loading"
				:error="error"
				:support-ref="supportRef"
				:workspace="workspace"
				:pending="pending"
				@reload="load"
				@select-financial-year="onSelectFy"
				@reset-financial-year="onResetFy"
				@open-departmental-plan="onOpenDepartmentalPlan"
				@navigate="onNavigate"
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
						@open-entry="onOpenEntry"
						@back="frappe.set_route(WORKSPACE_PAGE)"
						@save-draft="load({ quiet: true })"
						@submit="onSubmit"
					/>
				</template>

				<template v-else-if="screen === 'dpp-entry'">
					<DppEntryEditorScreen
						:editor="editor"
						:pending="pending"
						:error-summary="errorSummary"
						@save-funding="onSaveFunding"
						@save-direct="onSaveDirect"
						@cancel="go(dppReference)"
					/>
				</template>

				<template v-else-if="screen === 'dpp-review'">
					<DppValidationScreen
						:detail="validation"
						:classifications="classifications"
						:pending="pending"
						:error-summary="errorSummary"
						@classify="onClassify"
						@accept="onAccept"
						@open-return-dialog="returnDialog = true"
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

				<template v-else-if="screen === 'plan'">
					<AnnualPlanScreen
						:plan="annualPlan"
						:pending="pending"
						:error-summary="errorSummary"
						@open-form-dialog="formDialog = true"
						@navigate="onNavigate"
						@back="frappe.set_route(WORKSPACE_PAGE)"
						@request-funding="onRequestPlanFunding"
						@submit-consolidated="onSubmitConsolidatedPlan"
						@begin-update="onBeginUpdate"
					/>
					<FormPlanItemsDialog
						v-if="formDialog"
						:entries="annualPlan.unallocated_sources || []"
						:pending="pending"
						:error="errorSummary"
						@confirm="onFormConfirm"
						@cancel="formDialog = false"
					/>
				</template>

				<template v-else-if="screen === 'plan-item'">
					<PlanItemEditorScreen
						:item="planItem"
						:pending="pending"
						:error-summary="errorSummary"
						@save="onSavePlanItem"
						@dissolve="onDissolvePlanItem"
						@back="onBackToPlan"
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
					<GovernanceTaskScreen
						:task="governanceTask"
						:pending="pending"
						:error-summary="errorSummary"
						@confirm="onGovernanceConfirm"
						@open-return-dialog="governanceReturnDialog = true"
					/>
					<GovernanceReturnDialog
						v-if="governanceReturnDialog"
						:dialog="governanceTask.return_dialog"
						:pending="pending"
						:error="errorSummary"
						@confirm="onGovernanceReturn"
						@cancel="governanceReturnDialog = false"
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
import ReturnIssuesDialog from "./components/ReturnIssuesDialog.vue";
import AnnualPlanScreen from "./components/AnnualPlanScreen.vue";
import FormPlanItemsDialog from "./components/FormPlanItemsDialog.vue";
import PlanItemEditorScreen from "./components/PlanItemEditorScreen.vue";
import FinanceTaskScreen from "./components/FinanceTaskScreen.vue";
import FinanceReturnDialog from "./components/FinanceReturnDialog.vue";
import GovernanceTaskScreen from "./components/GovernanceTaskScreen.vue";
import GovernanceReturnDialog from "./components/GovernanceReturnDialog.vue";

const WORKSPACE_PAGE = "procurement-planning";
const DPP_PAGE = "departmental-procurement-plan";
const PLAN_PAGE = "annual-procurement-plan";
const PLAN_ITEM_PAGE = "procurement-plan-item";
const { route } = useRouteState(WORKSPACE_PAGE);

const railEl = ref(null);
const loading = ref(true);
const pending = ref(false);
const error = ref("");
const errorSummary = ref("");
const supportRef = ref("");
const workspace = ref({});
const dpp = ref({});
const editor = ref({});
const certified = ref(false);
const validation = ref({});
const classifications = ref({});
const returnDialog = ref(false);
const annualPlan = ref({});
const planItem = ref({});
const formDialog = ref(false);
const financeTask = ref({});
const financeReturnDialog = ref(false);
const governanceTask = ref({});
const governanceReturnDialog = ref(false);

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
	if (pageSlug.value === WORKSPACE_PAGE && segments.value[0] === "finance" && segments.value[1]) {
		return "finance";
	}
	if (pageSlug.value === WORKSPACE_PAGE && segments.value[0] === "review" && segments.value[1]) {
		return "governance";
	}
	if (pageSlug.value === PLAN_PAGE && planReference.value) return "plan";
	if (pageSlug.value === PLAN_ITEM_PAGE && planItemId.value) return "plan-item";
	return "workspace";
});

const validationTaskId = computed(() =>
	segments.value[0] === "dpp-review" ? segments.value[1] || "" : ""
);

const financeTaskId = computed(() =>
	segments.value[0] === "finance" ? segments.value[1] || "" : ""
);

const governanceTaskId = computed(() =>
	segments.value[0] === "review" ? segments.value[1] || "" : ""
);

const entryId = computed(() =>
	segments.value[1] === "entry" ? segments.value[2] || "" : ""
);

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

let loadSeq = 0;

// `quiet` refreshes in place — the skeleton replaces the whole screen, so
// flipping `loading` after every action made the screen flash on each
// round-trip; a quiet load keeps the current content mounted until the new
// data lands. Only the route-driven watch below shows the skeleton.
async function load(opts) {
	const quiet = !!(opts && opts.quiet === true);
	const seq = ++loadSeq;
	if (!quiet) loading.value = true;
	error.value = "";
	errorSummary.value = "";
	try {
		if (screen.value === "workspace") {
			const loaded = await api.getPlanningWorkspace({
				financial_year: financialYear.value || undefined,
			});
			if (seq !== loadSeq) return;
			workspace.value = loaded;
			const context = loaded.context || {};
			if (context.financial_year) financialYear.value = context.financial_year;
		} else if (screen.value === "dpp") {
			const loaded = await api.getDepartmentalPlan(dppReference.value);
			if (seq !== loadSeq) return;
			dpp.value = loaded;
			certified.value = false;
		} else if (screen.value === "dpp-entry") {
			const loaded = await api.getDppEntryEditor(
				dppReference.value, entryId.value || undefined
			);
			if (seq !== loadSeq) return;
			editor.value = loaded;
		} else if (screen.value === "dpp-review") {
			const loaded = await api.getDppValidationTask(validationTaskId.value);
			if (seq !== loadSeq) return;
			validation.value = loaded;
			classifications.value = {};
			returnDialog.value = false;
		} else if (screen.value === "plan") {
			const loaded = await api.getAnnualPlan(planReference.value);
			if (seq !== loadSeq) return;
			annualPlan.value = loaded;
			formDialog.value = false;
		} else if (screen.value === "plan-item") {
			const loaded = await api.getPlanItem(planItemId.value);
			if (seq !== loadSeq) return;
			planItem.value = loaded;
		} else if (screen.value === "finance") {
			const loaded = await api.getFinanceTask(financeTaskId.value);
			if (seq !== loadSeq) return;
			financeTask.value = loaded;
			financeReturnDialog.value = false;
		} else if (screen.value === "governance") {
			const loaded = await api.getPlanGovernanceTask(governanceTaskId.value);
			if (seq !== loadSeq) return;
			governanceTask.value = loaded;
			governanceReturnDialog.value = false;
		}
	} catch (e) {
		if (seq !== loadSeq) return;
		error.value = e.message;
		supportRef.value = newSupportRef();
	} finally {
		if (seq === loadSeq) loading.value = false;
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

function onViewAcceptedNeeds() {
	frappe.set_route("departmental-needs");
}

async function onSubmit() {
	const result = await run("submit-dpp", (key) =>
		api.submitDepartmentalPlan({
			dpp_version: dpp.value.version?.name,
			certification_confirmed: certified.value,
			expected_record_version: dpp.value.record_version,
			idempotency_key: key,
		})
	);
	if (result) await load({ quiet: true });
}

async function onSaveFunding(payload) {
	const result = await run("save-need-funding", (key) =>
		api.saveNeedFunding({
			dpp_version: editor.value.dpp_version,
			entry_id: payload.entry_id,
			budget_line: payload.budget_line || undefined,
			indicative_amount: payload.indicative_amount || undefined,
			not_proceeding_reason: payload.not_proceeding_reason || undefined,
			expected_record_version: editor.value.record_version,
			idempotency_key: key,
		})
	);
	if (result) go(dppReference.value);
}

async function onSaveDirect(payload) {
	const result = await run("save-direct", (key) =>
		api.saveDirectRequirement({
			dpp_version: editor.value.dpp_version,
			entry_values: JSON.stringify(payload.values),
			entry_id: payload.entry_id || undefined,
			expected_record_version: editor.value.record_version,
			idempotency_key: key,
		})
	);
	if (result) go(dppReference.value);
}

function onClassify(entryId, value) {
	classifications.value = { ...classifications.value, [entryId]: value };
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

async function onFormConfirm(dppEntries, mode) {
	const result = await run("form-plan-items", (key) =>
		api.formPlanItems({
			plan_version: annualPlan.value.version_reference,
			dpp_entries: JSON.stringify(dppEntries),
			mode,
			expected_record_version: annualPlan.value.record_version,
			idempotency_key: key,
		})
	);
	if (result) {
		formDialog.value = false;
		if (result.single) {
			frappe.set_route(PLAN_ITEM_PAGE, result.created_items[0]);
		} else {
			await load({ quiet: true });
		}
	}
}

async function onSavePlanItem(values) {
	const result = await run("save-plan-item", (key) =>
		api.savePlanItem({
			plan_item: planItem.value.plan_item_id,
			item_values: JSON.stringify(values),
			expected_record_version: planItem.value.record_version,
			idempotency_key: key,
		})
	);
	if (result) await load({ quiet: true });
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
	const result = await run("request-plan-funding", (key) =>
		api.requestPlanFundingConfirmation({
			plan_version: annualPlan.value.version_reference,
			expected_record_version: annualPlan.value.record_version,
			idempotency_key: key,
		})
	);
	if (result) await load({ quiet: true });
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
	if (result) frappe.set_route(WORKSPACE_PAGE, "review", result.task);
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

async function onGovernanceConfirm(resolutionReference) {
	const command = governanceTask.value.stage === "Accounting Officer adoption" ? "adopt" : "approve";
	const result = await run(command, (key) =>
		command === "adopt"
			? api.adoptAndSubmitPlan({
					task: governanceTask.value.task,
					task_token: governanceTask.value.task_token,
					idempotency_key: key,
				})
			: api.approveAnnualPlan({
					task: governanceTask.value.task,
					task_token: governanceTask.value.task_token,
					resolution_reference: resolutionReference,
					idempotency_key: key,
				})
	);
	if (result) frappe.set_route(WORKSPACE_PAGE);
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

watch([pageSlug, segments], () => load(), { immediate: true, deep: true });

const railTrail = computed(() => {
	const trail = [{ label: "Procurement Planning", route: [WORKSPACE_PAGE] }];
	if (screen.value === "dpp-review") {
		trail.push({ label: "DPP review" });
	}
	if (screen.value === "finance") {
		trail.push({ label: "Finance" });
	}
	if (screen.value === "governance") {
		trail.push({ label: "Review" });
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
