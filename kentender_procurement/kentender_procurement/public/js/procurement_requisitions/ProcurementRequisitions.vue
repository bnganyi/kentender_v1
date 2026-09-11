<!-- Procurement Requisitions — REQ-CHG-001 v1.6 §12.
     One Page ("procurement-requisitions") owns every route in the table:
     workspace, Start ({plan_item_id}), editor ({requisition_id}),
     department task, procurement task, authorised view. This root reads the
     full route and picks the screen. There is no Procuring Entity or
     Fiscal Year filter anywhere (§1.1/§8) — a Requisition's Financial Year
     is inherited display data. -->
<template>
	<div class="kt-industry kt-req">
		<div ref="railEl" class="kt-rail-mount"></div>
		<!-- One stable page-ready hook (AGENTS.md §6.4/§6.7): specs wait for
		     [data-testid="req-shell"][data-loading="false"]. -->
		<div
			class="kt-shell"
			data-testid="req-shell"
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
				:pending="pending"
				@reload="load"
				@navigate="onNavigate"
			/>
			<StartScreen
				v-else-if="screen === 'start'"
				:loading="loading"
				:error="error"
				:support-ref="supportRef"
				:detail="startDetail"
				:plan-item-id="planItemId"
				:pending="pending"
				@reload="load"
				@navigate="onNavigate"
				@prepare="onPrepare"
			/>
			<template v-else-if="screen === 'editor'">
				<div v-if="loading" class="kt-card kt-blueprint" style="padding: 0; overflow: hidden" data-testid="req-editor-loading">
					<i class="kt-corner tl"></i><i class="kt-corner tr"></i>
					<i class="kt-corner bl"></i><i class="kt-corner br"></i>
					<div v-for="row in 3" :key="row" class="req-skel-row">
						<div class="kt-skel" style="width: 72%"></div>
						<div class="kt-skel" style="width: 52%"></div>
						<div class="kt-skel" style="width: 44%"></div>
					</div>
				</div>
				<div v-else-if="error" class="kt-card kt-blueprint req-state-card" data-testid="req-editor-error">
					<i class="kt-corner tl"></i><i class="kt-corner tr"></i><i class="kt-corner bl"></i><i class="kt-corner br"></i>
					<h3>Procurement Requisitions could not be loaded.</h3>
					<p>Try again. If the problem continues, quote the support reference shown below.</p>
					<button type="button" class="kt-btn kt-btn-secondary" @click="load">Try again</button>
					<p class="req-support-ref">Support reference: {{ supportRef }}</p>
				</div>
				<EditorShell
					v-else
					:title="(editor.requisition || {}).title"
					:status="(editor.version || {}).version_status"
					:reference="editorReference"
					:steps="stepMeta"
					:active-step="activeStep"
					:continue-label="continueLabel"
					:pending="pending"
					:show-upstream-correction="(editor.permitted_actions || {}).can_request_upstream_correction"
					@go-to-step="activeStep = $event"
					@save-draft="onSaveDraft(false)"
					@continue="onSaveDraft(true)"
					@request-upstream-correction="upstreamDialog = true"
				>
					<StepDrawdown v-if="activeStep === 1" ref="stepDrawdownRef" :editor="editor" />
					<StepItems
						v-else-if="activeStep === 2"
						:editor="editor"
						@add-item="itemDialog = { item: null }"
						@edit-item="itemDialog = { item: $event }"
						@remove-item="onRemoveItem"
						@confirm-requirement="onConfirmRequirement"
						@remove-requirement="onRemoveRequirement"
					/>
					<StepTechnical
						v-else-if="activeStep === 3"
						ref="stepTechnicalRef"
						:editor="editor"
						@add-characteristic="characteristicDialog = true"
						@confirm-requirement="onConfirmRequirement"
						@remove-requirement="onRemoveRequirement"
					/>
					<StepServicesAcceptance
						v-else-if="activeStep === 4"
						:editor="editor"
						@add-service="serviceDialog = true"
						@remove-service="onRemoveService"
						@add-acceptance="acceptanceDialog = true"
						@remove-acceptance="onRemoveAcceptance"
						@add-material="materialDialog = true"
						@remove-material="onRemoveMaterial"
					/>
					<StepReview v-else-if="activeStep === 5" :editor="editor" />
					<template v-if="activeStep === 5" #footer>
						<button type="button" class="kt-btn kt-btn-secondary" :disabled="pending" @click="activeStep = 4">Back</button>
						<div class="req-actions">
							<button type="button" class="kt-btn kt-btn-secondary" :disabled="pending" @click="onSaveDraft(false)">Save draft</button>
							<button
								v-if="(editor.permitted_actions || {}).can_submit_directly"
								type="button"
								class="kt-btn kt-btn-primary"
								:disabled="pending"
								data-testid="req-submit-directly"
								@click="onSubmitDirectly"
							>
								Submit to Procurement
							</button>
							<button
								v-else
								type="button"
								class="kt-btn kt-btn-primary"
								:disabled="pending"
								data-testid="req-send-for-approval"
								@click="onSendForDepartmentApproval"
							>
								Send for department approval
							</button>
						</div>
					</template>
				</EditorShell>
				<ItemDialog
					v-if="itemDialog"
					:editor="editor"
					:item="itemDialog.item"
					:pending="pending"
					:error="itemDialogError"
					@confirm="onItemDialogConfirm"
					@cancel="itemDialog = null"
				/>
				<CharacteristicDialog
					v-if="characteristicDialog"
					:editor="editor"
					:pending="pending"
					:error="dialogError"
					:prefill-row="characteristicDialog === true ? null : characteristicDialog"
					@confirm="onCharacteristicDialogConfirm"
					@cancel="characteristicDialog = false"
				/>
				<ServiceDialog
					v-if="serviceDialog"
					:editor="editor"
					:pending="pending"
					:error="dialogError"
					@confirm="onServiceDialogConfirm"
					@cancel="serviceDialog = false"
				/>
				<AcceptanceDialog
					v-if="acceptanceDialog"
					:editor="editor"
					:pending="pending"
					:error="dialogError"
					@confirm="onAcceptanceDialogConfirm"
					@cancel="acceptanceDialog = false"
				/>
				<MaterialDialog
					v-if="materialDialog"
					:editor="editor"
					:pending="pending"
					:error="dialogError"
					@confirm="onMaterialDialogConfirm"
					@cancel="materialDialog = false"
				/>
				<UpstreamCorrectionDialog
					v-if="upstreamDialog"
					:pending="pending"
					:error="dialogError"
					@confirm="onUpstreamCorrectionConfirm"
					@cancel="upstreamDialog = false"
				/>
			</template>
			<template v-else-if="screen === 'department-task'">
				<div v-if="loading" class="kt-card kt-blueprint" style="padding: 0; overflow: hidden" data-testid="req-task-loading">
					<i class="kt-corner tl"></i><i class="kt-corner tr"></i>
					<i class="kt-corner bl"></i><i class="kt-corner br"></i>
					<div v-for="row in 3" :key="row" class="req-skel-row">
						<div class="kt-skel" style="width: 72%"></div>
						<div class="kt-skel" style="width: 52%"></div>
						<div class="kt-skel" style="width: 44%"></div>
					</div>
				</div>
				<div v-else-if="error" class="kt-card kt-blueprint req-state-card" data-testid="req-task-error">
					<i class="kt-corner tl"></i><i class="kt-corner tr"></i><i class="kt-corner bl"></i><i class="kt-corner br"></i>
					<h3>Procurement Requisitions could not be loaded.</h3>
					<p>Try again. If the problem continues, quote the support reference shown below.</p>
					<button type="button" class="kt-btn kt-btn-secondary" @click="load">Try again</button>
					<p class="req-support-ref">Support reference: {{ supportRef }}</p>
				</div>
				<DepartmentTaskScreen
					v-else
					:task="departmentTask"
					:actor-name="(departmentTask.deciding_actor || {}).name"
					:actor-role-label="(departmentTask.deciding_actor || {}).role"
					:pending="pending"
					@return="returnDialog = true"
					@submit="onSubmitFromDepartmentTask"
				/>
				<ReturnDialog
					v-if="returnDialog"
					:pending="pending"
					:error="dialogError"
					@confirm="onReturnDialogConfirm"
					@cancel="returnDialog = false"
				/>
			</template>
			<template v-else-if="screen === 'procurement-task'">
				<div v-if="loading" class="kt-card kt-blueprint" style="padding: 0; overflow: hidden" data-testid="req-task-loading">
					<i class="kt-corner tl"></i><i class="kt-corner tr"></i>
					<i class="kt-corner bl"></i><i class="kt-corner br"></i>
					<div v-for="row in 3" :key="row" class="req-skel-row">
						<div class="kt-skel" style="width: 72%"></div>
						<div class="kt-skel" style="width: 52%"></div>
						<div class="kt-skel" style="width: 44%"></div>
					</div>
				</div>
				<div v-else-if="error" class="kt-card kt-blueprint req-state-card" data-testid="req-task-error">
					<i class="kt-corner tl"></i><i class="kt-corner tr"></i><i class="kt-corner bl"></i><i class="kt-corner br"></i>
					<h3>Procurement Requisitions could not be loaded.</h3>
					<p>Try again. If the problem continues, quote the support reference shown below.</p>
					<button type="button" class="kt-btn kt-btn-secondary" @click="load">Try again</button>
					<p class="req-support-ref">Support reference: {{ supportRef }}</p>
				</div>
				<ProcurementTaskScreen
					v-else
					:task="procurementTask"
					:pending="pending"
					@return="returnDialog = true"
					@authorise="authoriseDialog = true"
					@change-lead-unit="changeLeadUnitDialog = true"
				/>
				<ReturnDialog
					v-if="returnDialog"
					:pending="pending"
					:error="dialogError"
					@confirm="onReturnDialogConfirm"
					@cancel="returnDialog = false"
				/>
				<AuthoriseDialog
					v-if="authoriseDialog"
					:task="procurementTask"
					:pending="pending"
					:error="dialogError"
					@confirm="onAuthoriseDialogConfirm"
					@cancel="authoriseDialog = false"
				/>
				<ChangeLeadUnitDialog
					v-if="changeLeadUnitDialog"
					:task="procurementTask"
					:pending="pending"
					:error="dialogError"
					@confirm="onChangeLeadUnitDialogConfirm"
					@cancel="changeLeadUnitDialog = false"
				/>
			</template>
			<template v-else-if="screen === 'authorised'">
				<div v-if="loading" class="kt-card kt-blueprint" style="padding: 0; overflow: hidden" data-testid="req-authorised-loading">
					<i class="kt-corner tl"></i><i class="kt-corner tr"></i>
					<i class="kt-corner bl"></i><i class="kt-corner br"></i>
					<div v-for="row in 3" :key="row" class="req-skel-row">
						<div class="kt-skel" style="width: 72%"></div>
						<div class="kt-skel" style="width: 52%"></div>
						<div class="kt-skel" style="width: 44%"></div>
					</div>
				</div>
				<div v-else-if="error" class="kt-card kt-blueprint req-state-card" data-testid="req-authorised-error">
					<i class="kt-corner tl"></i><i class="kt-corner tr"></i><i class="kt-corner bl"></i><i class="kt-corner br"></i>
					<h3>Procurement Requisitions could not be loaded.</h3>
					<p>Try again. If the problem continues, quote the support reference shown below.</p>
					<button type="button" class="kt-btn kt-btn-secondary" @click="load">Try again</button>
					<p class="req-support-ref">Support reference: {{ supportRef }}</p>
				</div>
				<AuthorisedScreen
					v-else
					:handoff="authorisedView"
					:pending="pending"
					@open-tender="onOpenTender"
					@revoke="revokeDialog = true"
				/>
				<RevokeDialog
					v-if="revokeDialog"
					:pending="pending"
					:error="dialogError"
					@confirm="onRevokeDialogConfirm"
					@cancel="revokeDialog = false"
				/>
			</template>
		</div>
	</div>
</template>

<script setup>
import { computed, ref, watch } from "vue";
import { useRouteState } from "../req_shared/composables/useRouteState.js";
import { usePageRail } from "../req_shared/composables/usePageRail.js";
import * as api from "./data/requisitionsApi.js";
import WorkspaceScreen from "./components/WorkspaceScreen.vue";
import StartScreen from "./components/StartScreen.vue";
import EditorShell from "./components/EditorShell.vue";
import StepDrawdown from "./components/StepDrawdown.vue";
import StepItems from "./components/StepItems.vue";
import StepTechnical from "./components/StepTechnical.vue";
import StepServicesAcceptance from "./components/StepServicesAcceptance.vue";
import StepReview from "./components/StepReview.vue";
import ItemDialog from "./components/ItemDialog.vue";
import CharacteristicDialog from "./components/CharacteristicDialog.vue";
import ServiceDialog from "./components/ServiceDialog.vue";
import AcceptanceDialog from "./components/AcceptanceDialog.vue";
import MaterialDialog from "./components/MaterialDialog.vue";
import UpstreamCorrectionDialog from "./components/UpstreamCorrectionDialog.vue";
import DepartmentTaskScreen from "./components/DepartmentTaskScreen.vue";
import ReturnDialog from "./components/ReturnDialog.vue";
import ProcurementTaskScreen from "./components/ProcurementTaskScreen.vue";
import AuthoriseDialog from "./components/AuthoriseDialog.vue";
import ChangeLeadUnitDialog from "./components/ChangeLeadUnitDialog.vue";
import AuthorisedScreen from "./components/AuthorisedScreen.vue";
import RevokeDialog from "./components/RevokeDialog.vue";

const WORKSPACE_PAGE = "procurement-requisitions";
const { route, epoch } = useRouteState(WORKSPACE_PAGE);
// Last payload per screen identity: a revisited screen renders from here at
// once and refreshes in place; the skeleton is only for a screen never
// loaded in this session (AGENTS.md §6.4).
const cache = kentender_core.desk_page.createScreenCache();

const railEl = ref(null);
const loading = ref(true);
const refreshing = ref(false);
const pending = ref(false);
const error = ref("");
const supportRef = ref("");
const workspace = ref({});
const startDetail = ref({});
const editor = ref({});
const activeStep = ref(1);
const itemDialog = ref(null);
const itemDialogError = ref("");
const dialogError = ref("");
const stepDrawdownRef = ref(null);
const stepTechnicalRef = ref(null);
const characteristicDialog = ref(false);
const serviceDialog = ref(false);
const acceptanceDialog = ref(false);
const materialDialog = ref(false);
const upstreamDialog = ref(false);
const departmentTask = ref({});
const returnDialog = ref(false);
const procurementTask = ref({});
const authoriseDialog = ref(false);
const changeLeadUnitDialog = ref(false);
const authorisedView = ref({});
const revokeDialog = ref(false);

const RESERVED_FIRST_SEGMENTS = new Set(["new", "department-task", "procurement-task"]);

const segments = computed(() => route.value.slice(1).filter(Boolean));

// REQ-DES-02 §12: /app/procurement-requisitions/new/{plan_item_id}
const planItemId = computed(() => (segments.value[0] === "new" ? segments.value[1] || "" : ""));

// REQ-CHG-001 v1.6 §12: /app/procurement-requisitions/{requisition_id} — one
// route for the whole five-step editor; step navigation is client-side
// state only (`activeStep`), never a URL segment of its own.
const requisitionId = computed(() =>
	segments.value.length === 1 && !RESERVED_FIRST_SEGMENTS.has(segments.value[0]) ? segments.value[0] : ""
);

// §12: /app/procurement-requisitions/department-task/{task_id}
const departmentTaskId = computed(() => (segments.value[0] === "department-task" ? segments.value[1] || "" : ""));
// §12: /app/procurement-requisitions/procurement-task/{task_id}
const procurementTaskId = computed(() => (segments.value[0] === "procurement-task" ? segments.value[1] || "" : ""));
// §12: /app/procurement-requisitions/{requisition_id}/authorised
const authorisedRequisitionId = computed(() => (segments.value.length === 2 && segments.value[1] === "authorised" ? segments.value[0] : ""));

const screen = computed(() => {
	if (segments.value[0] === "new" && planItemId.value) return "start";
	if (departmentTaskId.value) return "department-task";
	if (procurementTaskId.value) return "procurement-task";
	if (authorisedRequisitionId.value) return "authorised";
	if (requisitionId.value) return "editor";
	return "workspace";
});

const screenKey = computed(() => {
	if (screen.value === "start") return `start:${planItemId.value}`;
	if (screen.value === "editor") return `editor:${requisitionId.value}`;
	if (screen.value === "department-task") return `department-task:${departmentTaskId.value}`;
	if (screen.value === "procurement-task") return `procurement-task:${procurementTaskId.value}`;
	if (screen.value === "authorised") return `authorised:${authorisedRequisitionId.value}`;
	return screen.value;
});

const editorReference = computed(() => {
	const r = editor.value.requisition || {};
	const v = editor.value.version || {};
	return [r.requisition_reference, r.plan_item_id, v.version_number ? `Version ${v.version_number}` : ""].filter(Boolean).join(" · ");
});

// REQ-DES-03..07's left step navigation, driven by the same `validation.steps`
// report `authorise.py` itself rechecks at submission — never a second,
// independently-derived completeness rule.
const STEP_LABELS = { 1: "Request and drawdown", 2: "Equipment items", 3: "Technical and support", 4: "Services and acceptance", 5: "Review and submit" };
function stepHasData(n) {
	const pkg = editor.value.package || {};
	if (n === 2) return (pkg.items || []).length > 0;
	if (n === 3) return (pkg.technical_requirements || []).length > 0;
	if (n === 4) return (pkg.related_services || []).length > 0 || (pkg.acceptance_requirements || []).length > 0;
	return false;
}
const stepMeta = computed(() => {
	const stepsReport = (editor.value.validation || {}).steps || {};
	return [1, 2, 3, 4, 5].map((n) => {
		const info = stepsReport[n] || {};
		const hasData = stepHasData(n);
		let statusText, kind;
		// Steps 2-4 vacuously report `complete: true` from the server the
		// moment no row exists yet to be incomplete about (nothing to flag
		// is not the same as done) — confirmed live: a fresh Draft with zero
		// items rendered Step 3 "Complete" before Step 2 was even touched,
		// contradicting REQ-DES-03/04's own "Not started" display for this
		// exact scenario. "Not started" wins over a vacuous "Complete" for
		// these three steps; Step 1's drawdown/summary fields and Step 5's
		// own aggregate view always carry real content to judge.
		if (n >= 2 && n <= 4 && !hasData) {
			statusText = "Not started";
			kind = "not-started";
		} else if (info.complete) {
			statusText = "Complete";
			kind = "complete";
		} else if (n === activeStep.value) {
			statusText = "In progress";
			kind = "active";
		} else if (n === 5) {
			statusText = `${info.blocking || 0} blocker${(info.blocking || 0) === 1 ? "" : "s"}`;
			kind = "blocked";
		} else {
			statusText = "In progress";
			kind = "active";
		}
		return { number: n, label: STEP_LABELS[n], statusText, kind, enabled: true };
	});
});

const CONTINUE_LABELS = { 1: "Continue to equipment items", 2: "Continue to technical and support", 3: "Continue to services and acceptance", 4: "Continue to review" };
const continueLabel = computed(() => CONTINUE_LABELS[activeStep.value] || "Continue");

function newSupportRef() {
	const now = new Date();
	const pad = (n) => String(n).padStart(2, "0");
	return (
		`REQ-ERR-${now.getFullYear()}${pad(now.getMonth() + 1)}${pad(now.getDate())}` +
		`-${pad(now.getHours())}${pad(now.getMinutes())}`
	);
}

function fetchFor(scr) {
	switch (scr) {
		case "workspace":
			return api.getRequisitionWorkspace();
		case "start":
			return api.getEligiblePlanItemDetail(planItemId.value);
		case "editor":
			return api.getRequisitionEditor(requisitionId.value);
		case "department-task":
			return api.getDepartmentApprovalTask(departmentTaskId.value);
		case "procurement-task":
			return api.getProcurementAuthorisationTask(procurementTaskId.value);
		case "authorised":
			return api.getAuthorisedRequisitionHandoff(authorisedRequisitionId.value);
		default:
			return Promise.resolve(null);
	}
}

function applyLoaded(scr, loaded) {
	switch (scr) {
		case "workspace":
			workspace.value = loaded;
			break;
		case "start":
			startDetail.value = loaded;
			break;
		case "department-task":
			departmentTask.value = loaded;
			break;
		case "procurement-task":
			procurementTask.value = loaded;
			break;
		case "authorised":
			authorisedView.value = loaded;
			break;
		case "editor":
			editor.value = loaded;
			break;
	}
}

// RUN-CHG-001 / AGENTS.md §6.4 — a shared sequence-token utility instead of
// a hand-rolled `let loadSeq = 0` counter, so a slower, older response can
// never overwrite a newer one.
const loadGuard = kentender_core.desk_page.createSequenceGuard();
let inFlightKey = "";

// The skeleton shows only for a screen with nothing to show yet. A screen
// already loaded this session renders its last payload at once and
// refreshes in place; `quiet` forces the in-place path.
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
	try {
		const loaded = await fetchFor(scr);
		if (!loadGuard.isCurrent(token)) return;
		cache.set(key, loaded);
		applyLoaded(scr, loaded);
	} catch (e) {
		if (!loadGuard.isCurrent(token)) return;
		error.value = e.message;
		supportRef.value = newSupportRef();
	} finally {
		if (loadGuard.isCurrent(token)) {
			loading.value = false;
			refreshing.value = false;
			inFlightKey = "";
		}
	}
}

function onNavigate(routeSegments) {
	if (!routeSegments || !routeSegments.length) return;
	frappe.set_route(...routeSegments);
}

async function onPrepare(planItem) {
	if (pending.value) return;
	pending.value = true;
	error.value = "";
	try {
		const result = await api.prepareItEquipmentRequisition({
			plan_item_id: planItem,
			idempotency_key: api.newIdempotencyKey("prepare"),
		});
		frappe.set_route(WORKSPACE_PAGE, result.requisition);
	} catch (e) {
		error.value = e.message;
	} finally {
		pending.value = false;
	}
}

// Shared runner for every editor command: refuses re-entry while one is
// already in flight and surfaces the server's own message inline (never a
// default Frappe popup — AGENTS.md §6.10). RUN-CHG-001 (AGENTS.md §6.4): the
// post-mutation reload that refreshes each row's `record_version` must be
// the last thing awaited *inside* the function passed to `run()`, before its
// `finally` clears `pending` — never a separate `await load(...)` issued
// after `run()` has already returned. Every call site below folds its reload
// into the function it passes to `run()` for exactly this reason.
async function run(fn) {
	if (pending.value) return null;
	pending.value = true;
	error.value = "";
	try {
		return await fn();
	} catch (e) {
		error.value = e.message;
		return null;
	} finally {
		pending.value = false;
	}
}

async function onSaveDraft(continueToNext) {
	if (activeStep.value === 1 && stepDrawdownRef.value) {
		const version = editor.value.version || {};
		const payload = stepDrawdownRef.value.getPayload();
		// RUN-CHG-001 — the reload that refreshes record_version must be
		// awaited inside the guarded function, before run()'s finally clears
		// pending.
		const result = await run(async () => {
			const r = await api.saveRequisitionSummary({
				requisition: requisitionId.value,
				summary_values: JSON.stringify(payload),
				expected_record_version: version.record_version,
				idempotency_key: api.newIdempotencyKey("save-summary"),
			});
			await load({ quiet: true });
			return r;
		});
		if (!result) return;
	} else if (activeStep.value === 3 && stepTechnicalRef.value) {
		const pkg = editor.value.package || {};
		const payload = stepTechnicalRef.value.getPayload();
		const result = await run(async () => {
			const r = await api.saveWarrantyAndSupport({
				requisition: requisitionId.value,
				warranty_values: JSON.stringify(payload),
				expected_record_version: pkg.record_version,
				idempotency_key: api.newIdempotencyKey("save-warranty"),
			});
			await load({ quiet: true });
			return r;
		});
		if (!result) return;
	} else {
		// Steps 2/4/5 mutate via their own dialog handlers, not this
		// function — this reload just revalidates before advancing.
		await load({ quiet: true });
	}
	if (continueToNext && activeStep.value < 5) activeStep.value += 1;
}

async function onItemDialogConfirm(fields) {
	const pkg = editor.value.package || {};
	itemDialogError.value = "";
	const isEditing = !!(itemDialog.value && itemDialog.value.item);
	const result = await run(async () => {
		const r = isEditing
			? await api.updateRequisitionItem({
					requisition: requisitionId.value,
					requisition_item_id: itemDialog.value.item.requisition_item_id,
					item_values: JSON.stringify(fields),
					expected_record_version: pkg.record_version,
					idempotency_key: api.newIdempotencyKey("update-item"),
				})
			: await api.addRequisitionItem({
					requisition: requisitionId.value,
					item_values: JSON.stringify(fields),
					expected_record_version: pkg.record_version,
					idempotency_key: api.newIdempotencyKey("add-item"),
				});
		await load({ quiet: true });
		return r;
	});
	if (!result) {
		itemDialogError.value = error.value;
		error.value = "";
		return;
	}
	itemDialog.value = null;
}

async function onRemoveItem(item) {
	const pkg = editor.value.package || {};
	await run(async () => {
		const r = await api.removeRequisitionItem({
			requisition: requisitionId.value,
			requisition_item_id: item.requisition_item_id,
			expected_record_version: pkg.record_version,
			idempotency_key: api.newIdempotencyKey("remove-item"),
		});
		await load({ quiet: true });
		return r;
	});
}

async function onConfirmRequirement(row) {
	// A baseline rule that proposes no default (Memory, Storage capacity)
	// cannot be blindly confirmed — the server rejects it (REQ_CONTROL_INVALID)
	// exactly because that would produce a "Confirmed" row requiring nothing
	// (found live). Route it through the same dialog used to add a
	// characteristic, pre-filled and locked to this row, so the author
	// supplies the value the confirmation actually needs.
	if (!row.required_value_json) {
		characteristicDialog.value = row;
		return;
	}
	const pkg = editor.value.package || {};
	await run(async () => {
		const r = await api.confirmProposedRequirement({
			requisition: requisitionId.value,
			technical_requirement_id: row.technical_requirement_id,
			expected_record_version: pkg.record_version,
			idempotency_key: api.newIdempotencyKey("confirm-requirement"),
		});
		await load({ quiet: true });
		return r;
	});
}

async function onRemoveRequirement(row) {
	const pkg = editor.value.package || {};
	await run(async () => {
		const r = await api.removeTechnicalRequirement({
			requisition: requisitionId.value,
			technical_requirement_id: row.technical_requirement_id,
			expected_record_version: pkg.record_version,
			idempotency_key: api.newIdempotencyKey("remove-requirement"),
		});
		await load({ quiet: true });
		return r;
	});
}

async function onCharacteristicDialogConfirm(fields) {
	const pkg = editor.value.package || {};
	const confirmingRow = characteristicDialog.value !== true ? characteristicDialog.value : null;
	dialogError.value = "";
	const result = await run(async () => {
		const r = confirmingRow
			? await api.confirmProposedRequirement({
					requisition: requisitionId.value,
					technical_requirement_id: confirmingRow.technical_requirement_id,
					expected_record_version: pkg.record_version,
					confirmation_values: JSON.stringify({ value: fields.value, other_value: fields.other_value }),
					idempotency_key: api.newIdempotencyKey("confirm-requirement-with-value"),
				})
			: await api.addTechnicalRequirement({
					requisition: requisitionId.value,
					technical_requirement_values: JSON.stringify(fields),
					expected_record_version: pkg.record_version,
					idempotency_key: api.newIdempotencyKey("add-technical-requirement"),
				});
		await load({ quiet: true });
		return r;
	});
	if (!result) {
		dialogError.value = error.value;
		error.value = "";
		return;
	}
	characteristicDialog.value = false;
}

async function onServiceDialogConfirm(fields) {
	const pkg = editor.value.package || {};
	dialogError.value = "";
	const result = await run(async () => {
		const r = await api.addRelatedService({
			requisition: requisitionId.value,
			service_values: JSON.stringify(fields),
			expected_record_version: pkg.record_version,
			idempotency_key: api.newIdempotencyKey("add-service"),
		});
		await load({ quiet: true });
		return r;
	});
	if (!result) {
		dialogError.value = error.value;
		error.value = "";
		return;
	}
	serviceDialog.value = false;
}

async function onRemoveService(row) {
	const pkg = editor.value.package || {};
	await run(async () => {
		const r = await api.removeRelatedService({
			requisition: requisitionId.value,
			service_requirement_id: row.service_requirement_id,
			expected_record_version: pkg.record_version,
			idempotency_key: api.newIdempotencyKey("remove-service"),
		});
		await load({ quiet: true });
		return r;
	});
}

async function onAcceptanceDialogConfirm(fields) {
	const pkg = editor.value.package || {};
	dialogError.value = "";
	const result = await run(async () => {
		const r = await api.addAcceptanceRequirement({
			requisition: requisitionId.value,
			acceptance_values: JSON.stringify(fields),
			expected_record_version: pkg.record_version,
			idempotency_key: api.newIdempotencyKey("add-acceptance"),
		});
		await load({ quiet: true });
		return r;
	});
	if (!result) {
		dialogError.value = error.value;
		error.value = "";
		return;
	}
	acceptanceDialog.value = false;
}

async function onRemoveAcceptance(row) {
	const pkg = editor.value.package || {};
	await run(async () => {
		const r = await api.removeAcceptanceRequirement({
			requisition: requisitionId.value,
			acceptance_requirement_id: row.acceptance_requirement_id,
			expected_record_version: pkg.record_version,
			idempotency_key: api.newIdempotencyKey("remove-acceptance"),
		});
		await load({ quiet: true });
		return r;
	});
}

async function onMaterialDialogConfirm(fields) {
	const pkg = editor.value.package || {};
	dialogError.value = "";
	const result = await run(async () => {
		const r = await api.addSupportingMaterial({
			requisition: requisitionId.value,
			material_values: JSON.stringify(fields),
			expected_record_version: pkg.record_version,
			idempotency_key: api.newIdempotencyKey("add-material"),
		});
		await load({ quiet: true });
		return r;
	});
	if (!result) {
		dialogError.value = error.value;
		error.value = "";
		return;
	}
	materialDialog.value = false;
}

async function onRemoveMaterial(row) {
	const pkg = editor.value.package || {};
	await run(async () => {
		const r = await api.removeSupportingMaterial({
			requisition: requisitionId.value,
			supporting_material_id: row.supporting_material_id,
			expected_record_version: pkg.record_version,
			idempotency_key: api.newIdempotencyKey("remove-material"),
		});
		await load({ quiet: true });
		return r;
	});
}

async function onUpstreamCorrectionConfirm(reason) {
	const root = editor.value.requisition || {};
	dialogError.value = "";
	const result = await run(() =>
		api.requestUpstreamPlanCorrection({
			requisition: requisitionId.value,
			reason,
			expected_record_version: root.record_version,
			idempotency_key: api.newIdempotencyKey("upstream-correction"),
		})
	);
	if (!result) {
		dialogError.value = error.value;
		error.value = "";
		return;
	}
	upstreamDialog.value = false;
	frappe.set_route(WORKSPACE_PAGE);
}

async function onSendForDepartmentApproval() {
	const root = editor.value.requisition || {};
	const result = await run(() =>
		api.sendForDepartmentApproval({
			requisition: requisitionId.value,
			expected_record_version: root.record_version,
			idempotency_key: api.newIdempotencyKey("send-for-approval"),
		})
	);
	if (!result) return;
	frappe.set_route(WORKSPACE_PAGE);
}

async function onSubmitDirectly() {
	const root = editor.value.requisition || {};
	const result = await run(() =>
		api.submitRequisitionToProcurement({
			requisition: requisitionId.value,
			expected_record_version: root.record_version,
			idempotency_key: api.newIdempotencyKey("submit-directly"),
		})
	);
	if (!result) return;
	frappe.set_route(WORKSPACE_PAGE);
}

async function onSubmitFromDepartmentTask() {
	const root = departmentTask.value.requisition || {};
	const taskId = (departmentTask.value.task || {}).task;
	const result = await run(() =>
		api.submitRequisitionToProcurement({
			requisition: root.requisition,
			task: taskId,
			expected_record_version: root.record_version,
			idempotency_key: api.newIdempotencyKey("submit-department-task"),
		})
	);
	if (!result) return;
	frappe.set_route(WORKSPACE_PAGE);
}

async function onReturnDialogConfirm(reason) {
	const fromProcurementTask = screen.value === "procurement-task";
	const task = (fromProcurementTask ? procurementTask.value.task : departmentTask.value.task) || {};
	dialogError.value = "";
	const result = await run(() =>
		(fromProcurementTask ? api.returnRequisitionToDepartment : api.returnToDepartmentAuthor)({
			task: task.task,
			reason,
			expected_record_version: task.record_version,
			idempotency_key: api.newIdempotencyKey("return-task"),
		})
	);
	if (!result) {
		dialogError.value = error.value;
		error.value = "";
		return;
	}
	returnDialog.value = false;
	frappe.set_route(WORKSPACE_PAGE);
}

async function onAuthoriseDialogConfirm() {
	const root = procurementTask.value.requisition || {};
	const taskId = (procurementTask.value.task || {}).task;
	dialogError.value = "";
	const result = await run(() =>
		api.authoriseRequisition({
			requisition: root.requisition,
			task: taskId,
			expected_record_version: root.record_version,
			idempotency_key: api.newIdempotencyKey("authorise-task"),
		})
	);
	if (!result) {
		dialogError.value = error.value;
		error.value = "";
		return;
	}
	authoriseDialog.value = false;
	frappe.set_route(WORKSPACE_PAGE);
}

async function onChangeLeadUnitDialogConfirm({ new_lead_org_unit, reason }) {
	const root = procurementTask.value.requisition || {};
	dialogError.value = "";
	const result = await run(async () => {
		const r = await api.changeLeadOrganisationUnit({
			requisition: root.requisition,
			new_lead_org_unit,
			reason,
			expected_record_version: root.record_version,
			idempotency_key: api.newIdempotencyKey("change-lead-unit"),
		});
		await load({ quiet: true });
		return r;
	});
	if (!result) {
		dialogError.value = error.value;
		error.value = "";
		return;
	}
	changeLeadUnitDialog.value = false;
}

// §13.12 — this action deep-links to Tender Preparation; it never creates
// a Tender from a read. Tender Preparation's own screen is out of scope
// for this cycle (03_REQ_Implementation_Plan.md's own non-goals), so this
// follows the same "Planned" destination every other not-yet-built module
// in this Desk shell already uses (Home/Analytics/Contract Management/
// Supplier Management) — never a guessed or fabricated URL.
function onOpenTender() {
	frappe.route_options = { feature: "Tender Preparation" };
	frappe.set_route("coming-soon");
}

async function onRevokeDialogConfirm(reason) {
	const root = authorisedView.value.requisition || {};
	dialogError.value = "";
	const result = await run(() =>
		api.revokeUnconsumedAuthorisation({
			requisition: root.requisition,
			reason,
			expected_record_version: root.record_version,
			idempotency_key: api.newIdempotencyKey("revoke-authorisation"),
		})
	);
	if (!result) {
		dialogError.value = error.value;
		error.value = "";
		return;
	}
	revokeDialog.value = false;
	frappe.set_route(WORKSPACE_PAGE);
}

watch(requisitionId, () => {
	// A direct navigation to a different Requisition (or back to the
	// workspace) must never carry the previous one's editor state forward.
	activeStep.value = 1;
	itemDialog.value = null;
	itemDialogError.value = "";
	characteristicDialog.value = false;
	serviceDialog.value = false;
	acceptanceDialog.value = false;
	materialDialog.value = false;
	upstreamDialog.value = false;
	dialogError.value = "";
});
watch(departmentTaskId, () => {
	returnDialog.value = false;
	dialogError.value = "";
});
watch(procurementTaskId, () => {
	returnDialog.value = false;
	authoriseDialog.value = false;
	changeLeadUnitDialog.value = false;
	dialogError.value = "";
});
watch(authorisedRequisitionId, () => {
	revokeDialog.value = false;
	dialogError.value = "";
});
watch([segments], () => load({ entering: true }), { immediate: true, deep: true });
// The page came back into view on the same route: revalidate what is shown.
watch(epoch, () => {
	if (cache.has(screenKey.value)) load({ quiet: true });
});

const railTrail = computed(() => {
	const trail = [
		{ label: __("Home"), route: ["Workspaces", "Procurement Home"] },
		{ label: "Procurement Requisitions", route: [WORKSPACE_PAGE] },
	];
	if (screen.value === "start") trail.push({ label: "Start Requisition" });
	if (screen.value === "editor") trail.push({ label: (editor.value.requisition || {}).requisition_reference || requisitionId.value });
	if (screen.value === "department-task") trail.push({ label: (departmentTask.value.requisition || {}).requisition_reference || departmentTaskId.value });
	if (screen.value === "procurement-task") trail.push({ label: (procurementTask.value.requisition || {}).requisition_reference || procurementTaskId.value });
	if (screen.value === "authorised") trail.push({ label: (authorisedView.value.requisition || {}).requisition_reference || authorisedRequisitionId.value });
	return trail;
});

// §1.1 — no Procuring Entity switcher anywhere in Requisitions
usePageRail(railEl, railTrail, { showPeSwitcher: false });
</script>
