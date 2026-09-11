<!-- Tender Preparation — TPR-CHG-001 v0.6 §12. One Page ("tender-preparation")
     owns every route: workspace, Start (/new/{handoff_id}, the dialog over
     the workspace), editor (/{tender_id}, five tasks + review), approval task
     (/task/{task_id}) and approved view (/{tender_id}/approved). Opening a
     route creates nothing; only Prepare Tender invokes creation. No Procuring
     Entity or Fiscal Year control exists anywhere (§5). -->
<template>
	<div class="kt-industry kt-tpr">
		<div ref="railEl" class="kt-rail-mount"></div>
		<div class="kt-shell" data-testid="tpr-shell" :data-screen="screen" :data-loading="loading ? 'true' : 'false'" :data-refreshing="refreshing ? 'true' : 'false'">
			<template v-if="screen === 'workspace' || screen === 'start'">
				<WorkspaceScreen :loading="loading" :error="error" :support-ref="supportRef" :workspace="workspace" :pending="pending" @reload="load" @navigate="onNavigate" />
				<PrepareTenderDialog v-if="screen === 'start' && workspace.outcome === 'OK'" :detail="startDetail" :loading="startLoading" :pending="pending" :error="dialogError" @cancel="onNavigate([PAGE])" @prepare="onPrepare" @navigate="onNavigate" />
			</template>

			<template v-else-if="screen === 'editor'">
				<StateCard :loading="loading" :error="error" :not-found="notFound" :support-ref="supportRef" prefix="tpr-editor" @reload="load" @home="onNavigate([PAGE])" />
				<template v-if="!loading && !error && !notFound">
					<ReviewScreen v-if="activeTask === 6" :editor="editor" :pending="pending" :error="actionError" @preview="onPreview" @submit="onSubmit" @go-to-task="goToTask" />
					<EditorShell v-else :title="(editor.tender || {}).requirement_title" :status="(editor.tender || {}).version_status" :reference="editorReference" :tasks="taskMeta" :active-task="activeTask" :readiness="editor.readiness" :continue-label="activeTask === 5 ? 'Review Tender' : 'Continue'" :pending="pending" :can-save="!!(editor.permitted_actions || {}).can_save && [1, 4, 5].includes(activeTask)" :error="actionError" @go-to-task="goToTask" @save-draft="onSaveDraft(false)" @continue="onSaveDraft(true)">
						<TaskDetails v-if="activeTask === 1" ref="task1Ref" :editor="editor" :errors="fieldErrors" :editable="editable" />
						<TaskRequirements v-else-if="activeTask === 2" :editor="editor" :pending="pending" @request-upstream-correction="upstreamDialog = true" />
						<TaskPriceSchedule v-else-if="activeTask === 3" :editor="editor" />
						<TaskEvaluation v-else-if="activeTask === 4" ref="task4Ref" :editor="editor" :errors="fieldErrors" :editable="editable" @add-evidence="evidenceDialog = true" @remove-evidence="onRemoveEvidence" />
						<TaskContractTerms v-else-if="activeTask === 5" ref="task5Ref" :editor="editor" :errors="fieldErrors" :editable="editable" />
					</EditorShell>
				</template>
				<ReasonDialog v-if="upstreamDialog" title="Request upstream correction" field-label="Reason" confirm-label="Request correction" notice="Tender Preparation cannot edit an authorised requirement. This Tender Version will be preserved." testid="tpr-upstream-dialog" :pending="pending" :error="dialogError" @confirm="onUpstreamCorrection" @cancel="upstreamDialog = false" />
				<EvidenceDialog v-if="evidenceDialog" :editor="editor" :pending="pending" :error="dialogError" :errors="dialogFieldErrors" @confirm="onAddEvidence" @cancel="evidenceDialog = false" />
				<PreviewDialog v-if="preview" :preview="preview" :loading="previewLoading" @close="preview = null" />
			</template>

			<template v-else-if="screen === 'task'">
				<StateCard :loading="loading" :error="error" :not-found="notFound" :support-ref="supportRef" prefix="tpr-task" @reload="load" @home="onNavigate([PAGE])" />
				<ApprovalTaskScreen v-if="!loading && !error && !notFound" :task="approvalTask" :pending="pending" :error="actionError" @return="returnDialog = true" @approve="onApprove" @preview="onPreview" />
				<ReasonDialog v-if="returnDialog" title="Return for correction" field-label="Correction required" confirm-label="Return for correction" testid="tpr-return-dialog" :pending="pending" :error="dialogError" @confirm="onReturn" @cancel="returnDialog = false" />
				<PreviewDialog v-if="preview" :preview="preview" :loading="previewLoading" @close="preview = null" />
			</template>

			<template v-else-if="screen === 'approved'">
				<StateCard :loading="loading" :error="error" :not-found="notFound" :support-ref="supportRef" prefix="tpr-approved" @reload="load" @home="onNavigate([PAGE])" />
				<ApprovedScreen v-if="!loading && !error && !notFound" :view="approvedView" :pending="pending" :error="actionError" @reopen="reopenDialog = true" />
				<ReasonDialog v-if="reopenDialog" title="Reopen before publication" field-label="Reason for reopening" confirm-label="Reopen Tender" testid="tpr-reopen-dialog" :pending="pending" :error="dialogError" @confirm="onReopen" @cancel="reopenDialog = false" />
			</template>
		</div>
	</div>
</template>

<script setup>
import { computed, ref, watch } from "vue";
import { useRouteState } from "../tpr_shared/composables/useRouteState.js";
import { usePageRail } from "../tpr_shared/composables/usePageRail.js";
import * as api from "./data/tenderApi.js";
import StateCard from "./components/StateCard.vue";
import WorkspaceScreen from "./components/WorkspaceScreen.vue";
import PrepareTenderDialog from "./components/PrepareTenderDialog.vue";
import EditorShell from "./components/EditorShell.vue";
import TaskDetails from "./components/TaskDetails.vue";
import TaskRequirements from "./components/TaskRequirements.vue";
import TaskPriceSchedule from "./components/TaskPriceSchedule.vue";
import TaskEvaluation from "./components/TaskEvaluation.vue";
import TaskContractTerms from "./components/TaskContractTerms.vue";
import ReviewScreen from "./components/ReviewScreen.vue";
import ApprovalTaskScreen from "./components/ApprovalTaskScreen.vue";
import ApprovedScreen from "./components/ApprovedScreen.vue";
import ReasonDialog from "./components/ReasonDialog.vue";
import EvidenceDialog from "./components/EvidenceDialog.vue";
import PreviewDialog from "./components/PreviewDialog.vue";

const PAGE = "tender-preparation";
const { route, epoch } = useRouteState(PAGE);
const cache = kentender_core.desk_page.createScreenCache();

const railEl = ref(null);
const loading = ref(true);
const refreshing = ref(false);
const pending = ref(false);
const error = ref("");
const notFound = ref(false);
const actionError = ref("");
const dialogError = ref("");
const dialogFieldErrors = ref({});
const fieldErrors = ref({});
const supportRef = ref("");
const workspace = ref({});
const startDetail = ref({});
const startLoading = ref(false);
const editor = ref({});
const approvalTask = ref({});
const approvedView = ref({});
const activeTask = ref(1);
const upstreamDialog = ref(false);
const evidenceDialog = ref(false);
const returnDialog = ref(false);
const reopenDialog = ref(false);
const preview = ref(null);
const previewLoading = ref(false);
const task1Ref = ref(null);
const task4Ref = ref(null);
const task5Ref = ref(null);

const segments = computed(() => route.value.slice(1).filter(Boolean));
const handoffId = computed(() => (segments.value[0] === "new" ? segments.value[1] || "" : ""));
const taskId = computed(() => (segments.value[0] === "task" ? segments.value[1] || "" : ""));
const approvedTenderId = computed(() => (segments.value.length === 2 && segments.value[1] === "approved" ? segments.value[0] : ""));
const tenderId = computed(() => (segments.value.length === 1 && !["new", "task"].includes(segments.value[0]) ? segments.value[0] : ""));

const screen = computed(() => {
	if (handoffId.value) return "start";
	if (taskId.value) return "task";
	if (approvedTenderId.value) return "approved";
	if (tenderId.value) return "editor";
	return "workspace";
});
const screenKey = computed(() => {
	if (screen.value === "start" || screen.value === "workspace") return "workspace";
	if (screen.value === "editor") return `editor:${tenderId.value}`;
	if (screen.value === "task") return `task:${taskId.value}`;
	return `approved:${approvedTenderId.value}`;
});
const editable = computed(() => !!(editor.value.permitted_actions || {}).can_save);
const editorReference = computed(() => {
	const t = editor.value.tender || {};
	return [t.tender_reference, t.requisition_reference, t.version_number ? `Version ${t.version_number}` : ""].filter(Boolean).join(" · ");
});
const TASK_LABELS = { 1: "Tender details", 2: "Goods and requirements", 3: "Price schedule", 4: "Submission and evaluation", 5: "Contract terms" };
const taskMeta = computed(() => {
	const tasks = editor.value.tasks || {};
	const counts = (editor.value.inherited || {}).counts || {};
	return [1, 2, 3, 4, 5].map((n) => {
		const info = tasks[String(n)] || {};
		let statusText = info.complete ? "Complete" : `${(info.missing || []).length} to complete`;
		if (n === 2) statusText = `Complete · ${counts.items || 0} item${counts.items === 1 ? "" : "s"}`;
		if (n === 3) statusText = `Complete · Generated from ${counts.items || 0} item${counts.items === 1 ? "" : "s"}`;
		return { number: n, label: TASK_LABELS[n], statusText };
	});
});

function newSupportRef() {
	const now = new Date();
	const pad = (n) => String(n).padStart(2, "0");
	return `TPR-ERR-${now.getFullYear()}${pad(now.getMonth() + 1)}${pad(now.getDate())}-${pad(now.getHours())}${pad(now.getMinutes())}`;
}

function fetchFor(scr) {
	switch (scr) {
		case "workspace":
		case "start":
			return api.getTenderPreparationWorkspace();
		case "editor":
			return api.getTenderEditor(tenderId.value);
		case "task":
			return api.getTenderApprovalTask(taskId.value);
		case "approved":
			return api.getApprovedTender(approvedTenderId.value);
		default:
			return Promise.resolve(null);
	}
}
function applyLoaded(scr, loaded) {
	if (scr === "workspace" || scr === "start") workspace.value = loaded;
	else if (scr === "editor") editor.value = loaded;
	else if (scr === "task") approvalTask.value = loaded;
	else if (scr === "approved") approvedView.value = loaded;
}

const loadGuard = kentender_core.desk_page.createSequenceGuard();
let inFlightKey = "";
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
	notFound.value = false;
	try {
		const loaded = await fetchFor(scr);
		if (!loadGuard.isCurrent(token)) return;
		if (loaded && loaded.outcome === "NOT_FOUND") {
			notFound.value = true;
			return;
		}
		cache.set(key, loaded);
		applyLoaded(scr, loaded);
	} catch (e) {
		if (!loadGuard.isCurrent(token)) return;
		// §11.3 TPR_NOT_FOUND — an absent or invisible record answers 404 and
		// paints "Tender not found" inline; anything else is a load error.
		if (e && e.httpStatus === 404) {
			notFound.value = true;
			return;
		}
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

async function loadStart() {
	if (!handoffId.value) return;
	startLoading.value = true;
	dialogError.value = "";
	try {
		startDetail.value = await api.getTenderCompatibility(handoffId.value);
	} catch (e) {
		startDetail.value = { outcome: "LOAD_FAILED", message: e.message };
	} finally {
		startLoading.value = false;
	}
}

function onNavigate(routeSegments) {
	if (!routeSegments || !routeSegments.length) return;
	frappe.set_route(...routeSegments);
}
function goToTask(n) {
	fieldErrors.value = {};
	actionError.value = "";
	if (n === 6) {
		onEnterReview();
		return;
	}
	activeTask.value = n;
}

async function run(fn, { inline = true } = {}) {
	if (pending.value) return null;
	pending.value = true;
	if (inline) actionError.value = "";
	try {
		return await fn();
	} catch (e) {
		if (inline) actionError.value = e.message;
		else dialogError.value = e.message;
		return null;
	} finally {
		pending.value = false;
	}
}

function currentTaskPayload() {
	const refByTask = { 1: task1Ref, 4: task4Ref, 5: task5Ref };
	const target = refByTask[activeTask.value];
	return target && target.value && target.value.getPayload ? target.value.getPayload() : {};
}

async function saveCurrentTask() {
	if (![1, 4, 5].includes(activeTask.value) || !editable.value) return true;
	const payload = currentTaskPayload();
	if (!Object.keys(payload).length) return true;
	const t = editor.value.tender || {};
	const result = await run(async () => {
		const r = await api.saveTenderDraft({ tender: tenderId.value, draft_values: JSON.stringify(payload), expected_record_version: t.record_version, idempotency_key: api.newIdempotencyKey("save-draft") });
		if (r.ok !== false) await load({ quiet: true });
		return r;
	});
	if (!result) return false;
	if (result.ok === false) {
		fieldErrors.value = result.errors || {};
		actionError.value = "Correct the highlighted fields.";
		return false;
	}
	fieldErrors.value = {};
	return true;
}

async function onSaveDraft(continueToNext) {
	const saved = await saveCurrentTask();
	if (!saved) return;
	if (continueToNext) {
		if (activeTask.value === 5) await onEnterReview();
		else activeTask.value += 1;
	}
}

async function onEnterReview() {
	if (editable.value) {
		const t = editor.value.tender || {};
		const result = await run(async () => {
			const r = await api.runTenderReadiness({ tender: tenderId.value, expected_record_version: t.record_version, idempotency_key: api.newIdempotencyKey("readiness") });
			await load({ quiet: true });
			return r;
		});
		if (!result) return;
	}
	activeTask.value = 6;
}

async function onPreview(output) {
	const tender = screen.value === "task" ? (approvalTask.value.tender || {}).tender : tenderId.value;
	preview.value = { output, html: "", digest: "" };
	previewLoading.value = true;
	try {
		const loaded = await api.getTenderPreview(tender, output);
		preview.value = loaded.outcome === "NOT_FOUND" ? { output, html: `<p>${loaded.message}</p>`, digest: "" } : loaded;
	} catch (e) {
		preview.value = { output, html: `<p>${e.message}</p>`, digest: "" };
	} finally {
		previewLoading.value = false;
	}
}

async function onSubmit() {
	const t = editor.value.tender || {};
	const result = await run(() => api.submitTenderForApproval({ tender: tenderId.value, expected_record_version: t.record_version, idempotency_key: api.newIdempotencyKey("submit") }));
	if (!result) return;
	cache.set("workspace", null);
	frappe.set_route(PAGE);
}

async function onAddEvidence(fields) {
	const t = editor.value.tender || {};
	dialogError.value = "";
	dialogFieldErrors.value = {};
	const result = await run(async () => {
		const r = await api.addTenderEvidenceRequirement({ tender: tenderId.value, evidence_values: JSON.stringify(fields), expected_record_version: t.record_version, idempotency_key: api.newIdempotencyKey("add-evidence") });
		if (r.ok !== false) await load({ quiet: true });
		return r;
	}, { inline: false });
	if (!result) return;
	if (result.ok === false) {
		dialogFieldErrors.value = result.errors || {};
		return;
	}
	evidenceDialog.value = false;
}
async function onRemoveEvidence(row) {
	const t = editor.value.tender || {};
	await run(async () => {
		const r = await api.removeTenderEvidenceRequirement({ tender: tenderId.value, evidence_requirement_id: row.evidence_requirement_id, expected_record_version: t.record_version, idempotency_key: api.newIdempotencyKey("remove-evidence") });
		await load({ quiet: true });
		return r;
	});
}
async function onUpstreamCorrection(reason) {
	const t = editor.value.tender || {};
	const result = await run(() => api.requestTenderUpstreamCorrection({ tender: tenderId.value, reason, expected_record_version: t.record_version, idempotency_key: api.newIdempotencyKey("upstream") }), { inline: false });
	if (!result) return;
	upstreamDialog.value = false;
	cache.set("workspace", null);
	frappe.set_route(PAGE);
}
async function onPrepare(handoff) {
	const result = await run(() => api.prepareTender({ handoff, idempotency_key: api.newIdempotencyKey("prepare") }), { inline: false });
	if (!result) return;
	cache.set("workspace", null);
	frappe.set_route(PAGE, result.tender);
}
async function onReturn(reason) {
	const task = approvalTask.value || {};
	const result = await run(() => api.returnTenderForCorrection({ task: task.task, reason, expected_record_version: (task.tender || {}).record_version, idempotency_key: api.newIdempotencyKey("return") }), { inline: false });
	if (!result) return;
	returnDialog.value = false;
	cache.set("workspace", null);
	frappe.set_route(PAGE);
}
async function onApprove() {
	const task = approvalTask.value || {};
	const result = await run(() => api.approveTenderForPublication({ task: task.task, expected_record_version: (task.tender || {}).record_version, idempotency_key: api.newIdempotencyKey("approve") }));
	if (!result) return;
	cache.set("workspace", null);
	frappe.set_route(PAGE, result.tender, "approved");
}
async function onReopen(reason) {
	const view = approvedView.value || {};
	const result = await run(() => api.reopenApprovedTender({ tender: (view.tender || {}).tender, reason, expected_record_version: (view.tender || {}).record_version, idempotency_key: api.newIdempotencyKey("reopen") }), { inline: false });
	if (!result) return;
	reopenDialog.value = false;
	cache.set("workspace", null);
	frappe.set_route(PAGE, result.tender);
}

watch(tenderId, () => {
	activeTask.value = 1;
	fieldErrors.value = {};
	actionError.value = "";
	upstreamDialog.value = false;
	evidenceDialog.value = false;
	preview.value = null;
});
watch(taskId, () => { returnDialog.value = false; dialogError.value = ""; actionError.value = ""; preview.value = null; });
watch(approvedTenderId, () => { reopenDialog.value = false; dialogError.value = ""; actionError.value = ""; });
watch(handoffId, (id) => { if (id) loadStart(); else startDetail.value = {}; }, { immediate: true });
watch([segments], () => load({ entering: true }), { immediate: true, deep: true });
watch(epoch, () => { if (cache.has(screenKey.value)) load({ quiet: true }); });

const railTrail = computed(() => {
	const trail = [{ label: __("Home"), route: ["Workspaces", "Procurement Home"] }, { label: "Tender Preparation", route: [PAGE] }];
	if (screen.value === "start") trail.push({ label: "Start Tender" });
	if (screen.value === "editor") trail.push({ label: (editor.value.tender || {}).tender_reference || tenderId.value });
	if (screen.value === "task") trail.push({ label: (approvalTask.value.tender || {}).tender_reference || "Approval task" });
	if (screen.value === "approved") trail.push({ label: (approvedView.value.tender || {}).tender_reference || approvedTenderId.value });
	return trail;
});
usePageRail(railEl, railTrail, { showPeSwitcher: false });
</script>
