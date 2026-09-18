<script setup>
// STR-UI-02 Plan workspace + STR-UI-03 Structure editor (STR-DES-03/04/05,
// §11.3A Draft Overview). Routes (STR-CHG-001 v1.8 §10):
//   /app/strategy/plan/{plan_id}                               Overview — the Current version
//   /app/strategy/plan/{plan_id}/history                       History of the Current version
//   /app/strategy/plan/{plan_id}/version/{n}                   Overview of exactly Version n
//   /app/strategy/plan/{plan_id}/version/{n}/structure         Structure (editor when n is the editable Draft)
//   /app/strategy/plan/{plan_id}/version/{n}/history           History of exactly Version n
// An explicitly requested version is never silently replaced by the latest
// content (§12.2); the Current version's facts lead and a pending update is
// shown separately (§11.3).
import { ref, reactive, computed, watch, onActivated } from "vue";
import { useRouteState } from "../../strategy_shared/composables/useRouteState.js";
import { usePageRail } from "../../strategy_shared/composables/usePageRail.js";
import { runAttempt } from "../../strategy_shared/data/attempts.js";
import StructureTree from "../../strategy_shared/components/StructureTree.vue";
import ConfirmDialog from "../../strategy_shared/components/ConfirmDialog.vue";
import StructureEditor from "../components/StructureEditor.vue";
import ObjectivesAndTargets from "../components/ObjectivesAndTargets.vue";
import StructureSummary from "../components/StructureSummary.vue";
import VersionTimeline from "../components/VersionTimeline.vue";
import { typeLabel } from "../../strategy_shared/nodeIcons.js";
import { getPlanWorkspace, savePlanDraft, getVersionHistory, getStrategyTree, createSuccessorVersion, discardPlanDraft } from "../data/strategyApi.js";

const { route, epoch } = useRouteState("strategy");
const planId = computed(() => (route.value[1] === "plan" ? route.value[2] || null : null));
const versionParam = computed(() => (route.value[3] === "version" ? route.value[4] || null : null));
const tab = computed(() => {
	const r = route.value;
	if (r[3] === "history") return "history";
	if (r[3] === "version" && r[5] === "structure") return "structure";
	if (r[3] === "version" && r[5] === "history") return "history";
	return "overview";
});

const loading = ref(true);
const refreshing = ref(false);
const notFound = ref(false);
const forbidden = ref(false);
const loadError = ref(null);
const workspace = ref(null);
const history = ref([]);
const historyLoaded = ref(false);
const readTree = ref({ tree: [] });
const readSelected = ref(null);
const actionError = ref(null);
const acting = ref(false);
const editorRef = ref(null);
const editorDirty = ref(false);
const confirmDialog = ref(null);

const version = computed(() => workspace.value?.current_version || null);
const editable = computed(() => !!workspace.value?.is_editable_draft);
const canDiscardDraft = computed(() => !!workspace.value?.capabilities?.discard_draft);
const isDraft = computed(() => version.value?.status === "Draft");
const isCurrent = computed(() => version.value?.status === "Active");
const isPrevious = computed(() => version.value?.status === "Superseded");
const isUpdate = computed(() => !!version.value?.is_update);

const railTrail = computed(() => {
	const items = [
		{ label: __("Home"), route: ["Workspaces", "Procurement Home"] },
		{ label: __("Strategy Alignment"), route: ["strategy"] },
	];
	if (workspace.value?.plan) {
		if (tab.value === "structure" && version.value) {
			items.push({ label: workspace.value.plan.reference, route: ["strategy", "plan", workspace.value.plan.reference] });
			items.push({ label: __("Version {0}", [version.value.version_number]) });
			items.push({ label: __("Structure") });
		} else {
			items.push({ label: workspace.value.plan.reference });
		}
	} else {
		items.push({ label: __("Plan workspace") });
	}
	return items;
});
const railEl = ref(null);
usePageRail(railEl, railTrail);

// AGENTS.md §6.4 — skeleton only with nothing to show; otherwise revalidate
// in place under data-refreshing.
let loadSeq = 0;
async function loadWorkspace(opts) {
	if (!planId.value) return;
	const quiet = !!(opts && opts.quiet === true) && !!workspace.value;
	const seq = ++loadSeq;
	if (quiet) refreshing.value = true;
	else loading.value = true;
	loadError.value = null;
	try {
		const data = await getPlanWorkspace(planId.value, versionParam.value);
		if (seq !== loadSeq) return;
		notFound.value = !!data.not_found;
		forbidden.value = !!data.forbidden;
		if (!data.not_found && !data.forbidden) {
			workspace.value = data;
			historyLoaded.value = false;
			if (!data.no_version) {
				if (tab.value === "history") loadHistory();
				if (tab.value === "structure" && !data.is_editable_draft) loadReadTree();
			}
			syncDetailForm();
		}
	} catch (e) {
		if (seq === loadSeq) loadError.value = e;
	} finally {
		if (seq === loadSeq) {
			loading.value = false;
			refreshing.value = false;
		}
	}
}

async function loadHistory() {
	if (!version.value || historyLoaded.value) return;
	history.value = await getVersionHistory(version.value.id);
	historyLoaded.value = true;
}
async function loadReadTree() {
	if (!version.value) return;
	readTree.value = await getStrategyTree(version.value.id);
}

watch(
	() => [planId.value, versionParam.value],
	([id], old) => {
		if (!id) return;
		if (!old || id !== old[0] || versionParam.value !== old[1]) {
			workspace.value = null;
			history.value = [];
			historyLoaded.value = false;
			readSelected.value = null;
			actionError.value = null;
			loadWorkspace();
		}
	},
	{ immediate: true }
);
watch(epoch, () => {
	if (workspace.value) loadWorkspace({ quiet: true });
});
let activations = 0;
onActivated(() => {
	if (activations++ > 0 && workspace.value) loadWorkspace({ quiet: true });
});
watch(tab, (t) => {
	if (t === "history") loadHistory();
	if (t === "structure" && workspace.value && !editable.value) loadReadTree();
});

// §12.3 — leaving a dirty editor offers Save / Discard / Stay.
function navigate(routeArray) {
	const run = () => frappe.set_route(...routeArray);
	if (tab.value === "structure" && editorRef.value && editorDirty.value) {
		editorRef.value.guardedNavigate(run);
		return;
	}
	run();
}
function switchTab(t) {
	const target = workspace.value?.routes?.[t];
	if (target) navigate(target);
}

// --- §11.3A Plan details (identity for a first Draft, Use from / Use until for a successor Draft) ---
const detailForm = reactive({ title: "", plan_role: "Primary", parent_primary_plan_id: "", period_start: "", period_end: "", effective_from: "", effective_to: "" });
const detailErrors = reactive({ title: "", period_start: "", period_end: "", effective_from: "", effective_to: "" });
function syncDetailForm() {
	if (!workspace.value?.plan) return;
	const p = workspace.value.plan;
	const v = workspace.value.current_version || {};
	Object.assign(detailForm, {
		title: p.title || "",
		plan_role: p.plan_role || "Primary",
		parent_primary_plan_id: p.parent_primary_plan_id || "",
		period_start: p.period_start || "",
		period_end: p.period_end || "",
		effective_from: v.effective_from || "",
		effective_to: v.effective_to || "",
	});
	Object.keys(detailErrors).forEach((k) => (detailErrors[k] = ""));
}
const canEditIdentity = computed(() => !!workspace.value?.capabilities?.edit_identity);
const canEditDates = computed(() => !!workspace.value?.capabilities?.edit_version_dates);
const detailsDirty = computed(() => {
	if (!workspace.value?.plan) return false;
	const p = workspace.value.plan;
	const v = workspace.value.current_version || {};
	if (canEditIdentity.value && (detailForm.title !== (p.title || "") || detailForm.period_start !== (p.period_start || "") || detailForm.period_end !== (p.period_end || ""))) return true;
	if (canEditDates.value && (detailForm.effective_from !== (v.effective_from || "") || detailForm.effective_to !== (v.effective_to || ""))) return true;
	return false;
});
function validateDetails() {
	Object.keys(detailErrors).forEach((k) => (detailErrors[k] = ""));
	if (canEditIdentity.value) {
		if (!detailForm.title.trim()) detailErrors.title = __("Enter a plan title.");
		if (!detailForm.period_start) detailErrors.period_start = __("Enter the start date.");
		if (!detailForm.period_end) detailErrors.period_end = __("Enter the end date.");
		else if (detailForm.period_start && detailForm.period_end <= detailForm.period_start) detailErrors.period_end = __("The end date must be later than the start date.");
	}
	if (canEditDates.value) {
		const p = workspace.value.plan;
		if (!detailForm.effective_from) detailErrors.effective_from = __("Set the date this version applies from.");
		else if (p.period_start && detailForm.effective_from < p.period_start) detailErrors.effective_from = __("Use from must fall within the plan period.");
		if (detailForm.effective_to && p.period_end && detailForm.effective_to > p.period_end) detailErrors.effective_to = __("Use until must fall within the plan period.");
		if (detailForm.effective_from && detailForm.effective_to && detailForm.effective_to < detailForm.effective_from) detailErrors.effective_to = __("Use until must be on or after Use from.");
	}
	return !Object.values(detailErrors).some(Boolean);
}
async function savePlanDetails() {
	if (!validateDetails()) return false;
	acting.value = true;
	actionError.value = null;
	try {
		const payload = { plan_id: workspace.value.plan.id, plan_version_id: version.value.id };
		if (canEditIdentity.value) {
			Object.assign(payload, {
				title: detailForm.title,
				period_start: detailForm.period_start,
				period_end: detailForm.period_end,
				// §12.2 — the first version inherits the plan period.
				effective_from: detailForm.period_start,
				effective_to: detailForm.period_end,
			});
		}
		if (canEditDates.value) {
			Object.assign(payload, { effective_from: detailForm.effective_from, effective_to: detailForm.effective_to || null });
		}
		await runAttempt(`plan-details:${version.value.id}`, (key) => savePlanDraft(payload, version.value.expected_version, key));
		frappe.show_alert({ message: __("Plan details saved"), indicator: "green" });
		await loadWorkspace({ quiet: true });
		return true;
	} catch (e) {
		actionError.value = e.unknownOutcome ? __("We could not confirm the result. Checking the existing request…") : __("Your changes were not saved.") + " " + (e.message || "");
		return false;
	} finally {
		acting.value = false;
	}
}
async function editStructure() {
	if (detailsDirty.value) {
		const ok = await savePlanDetails();
		if (!ok) return;
	}
	switchTab("structure");
}

// --- Update plan (create_strategy_successor_version) ------------------------------
async function doUpdatePlan() {
	confirmDialog.value = null;
	acting.value = true;
	actionError.value = null;
	try {
		const result = await runAttempt(`update-plan:${workspace.value.plan.id}`, (key) => createSuccessorVersion(workspace.value.plan.id, key));
		frappe.show_alert({ message: __("Draft update created"), indicator: "green" });
		frappe.set_route("strategy", "plan", workspace.value.plan.reference, "version", String(result.version_number), "structure");
	} catch (e) {
		actionError.value = e.unknownOutcome ? __("We could not confirm the result. Checking the existing request…") : e.message || String(e);
	} finally {
		acting.value = false;
	}
}

// --- Discard draft (discard_strategy_plan_draft) -----------------------------------
async function doDiscardDraft() {
	confirmDialog.value = null;
	acting.value = true;
	actionError.value = null;
	try {
		const result = await runAttempt(`discard-draft:${version.value.id}`, (key) =>
			discardPlanDraft(version.value.id, version.value.expected_version, key)
		);
		frappe.show_alert({ message: __("Draft discarded"), indicator: "green" });
		if (result.plan_discarded) frappe.set_route("strategy");
		else frappe.set_route("strategy", "plan", workspace.value.plan.reference);
	} catch (e) {
		actionError.value = e.unknownOutcome ? __("We could not confirm the result. Checking the existing request…") : e.message || String(e);
	} finally {
		acting.value = false;
	}
}

function onSubmitted() {
	historyLoaded.value = false;
	frappe.set_route("strategy", "plan", workspace.value.plan.reference, "version", String(version.value.version_number));
	loadWorkspace({ quiet: true });
}
function onSaved() {
	loadWorkspace({ quiet: true });
}

const headerTitle = computed(() => {
	if (!workspace.value) return "";
	if (tab.value === "structure" && editable.value) return __("Edit plan");
	return workspace.value.plan.title;
});
const readinessFailures = computed(() => workspace.value?.readiness?.failures || []);
// §11.3 — the pending-update notice belongs on the Current version's page,
// never on the update's own page.
const pendingUpdate = computed(() => {
	const p = workspace.value?.pending_update || null;
	if (!p || (version.value && p.version_id === version.value.id)) return null;
	return p;
});
const appliesLabel = computed(() => {
	if (isCurrent.value) return __("This version applies");
	if (isPrevious.value) return __("This version applied");
	return __("This version will apply");
});
function nodePath(node) {
	return (node.path || []).join(" / ");
}
</script>

<template>
	<div
		class="kt-shell"
		data-testid="str-plan"
		:data-tab="tab"
		:data-loading="loading ? 'true' : 'false'"
		:data-refreshing="refreshing ? 'true' : 'false'"
	>
		<div v-if="loading" class="kt-card kt-blueprint" data-testid="str-loading">
			<p class="kt-muted" style="margin: 0 0 8px; font-size: 12px">{{ __("Loading strategic plans…") }}</p>
			<div v-for="i in 5" :key="i" class="kt-skel" style="height: 16px; margin-bottom: 10px"></div>
		</div>
		<div v-else-if="notFound" class="kt-notice is-warning" data-testid="str-not-found">
			<div class="kt-notice-body"><strong>{{ __("This plan record is not available to you.") }}</strong></div>
		</div>
		<div v-else-if="forbidden" class="kt-notice is-critical" data-testid="str-forbidden">
			<svg class="kt-notice-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="11" width="18" height="11" rx="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>
			<div class="kt-notice-body">
				<strong>{{ __("You do not have access to Strategy Alignment.") }}</strong>
				{{ __("This area needs Strategy Author, Strategy Approver or Auditor responsibility, or Administrator/System Manager technical access. Ask your KenTender administrator to check your access in System setup.") }}
			</div>
		</div>
		<div v-else-if="loadError && !workspace" data-testid="str-error">
			<div class="kt-notice is-warning">
				<div class="kt-notice-body"><strong>{{ __("Strategy information could not be loaded.") }}</strong> {{ __("Try again. If the problem continues, contact KenTender support.") }}</div>
			</div>
			<div style="margin-top: 10px"><button type="button" class="kt-btn kt-btn-secondary" @click="loadWorkspace">{{ __("Try again") }}</button></div>
		</div>
		<template v-else-if="workspace">
			<!-- The page title, its tabs and (for Overview/History) everything below
			     sit inside one bordered panel, with a thin rule between sections
			     instead of a gap between separate boxes — matching the current
			     design. The Structure tab is the one exception: the panel ends
			     right after the tabs, and the tree/selected-item boxes below it
			     stay as their own separate boxes. -->
			<div class="kt-card kt-blueprint" style="padding: 0">
				<div style="padding: 20.4px 20.4px 0">
					<header style="display: flex; justify-content: space-between; align-items: flex-start; gap: 13.6px; margin-bottom: 20.4px">
						<div>
							<div class="kt-eyebrow" style="text-transform: uppercase; font-size: 11px; letter-spacing: 0.1em; color: var(--kt-color-accent); margin-bottom: 6px" data-testid="str-plan-eyebrow">
								{{ workspace.plan.reference }}<template v-if="version"> &middot; {{ __("VERSION") }} {{ version.version_number }}</template>
							</div>
							<h1 style="font-size: 30px; margin: 0 0 4px" data-testid="str-plan-title-heading">{{ headerTitle }}</h1>
							<div style="display: flex; align-items: center; gap: 10.2px; flex-wrap: wrap">
								<span v-if="tab === 'structure' && editable" style="font-size: 15px; font-weight: 600">{{ workspace.plan.title }}</span>
								<span v-if="version" class="kt-status" :class="version.status_tone" data-testid="str-plan-status">{{ version.status_label }}</span>
								<a v-if="isPrevious && workspace.routes.current" href="#" data-testid="str-view-current" @click.prevent="navigate(workspace.routes.current)">{{ __("View current plan") }}</a>
							</div>
						</div>
						<div style="display: flex; gap: 6.8px; align-items: flex-start">
							<button v-if="canDiscardDraft" type="button" class="kt-btn kt-btn-secondary kt-danger" :disabled="acting" data-testid="str-discard-draft" @click="confirmDialog = 'discard-draft'">{{ __("Discard draft") }}</button>
							<template v-if="tab === 'structure' && editable">
								<button type="button" class="kt-btn kt-btn-secondary" :disabled="acting" data-testid="str-save-changes" @click="editorRef?.save()">{{ __("Save changes") }}</button>
								<button type="button" class="kt-btn kt-btn-primary" :disabled="acting" data-testid="str-submit" @click="editorRef?.submit()">{{ __("Submit for approval") }}</button>
							</template>
							<div v-else-if="workspace.capabilities.update_plan" style="text-align: right; max-width: 360px">
								<button type="button" class="kt-btn kt-btn-secondary" :disabled="acting" data-testid="str-update-plan" @click="confirmDialog = 'update-plan'">{{ __("Update plan") }}</button>
								<div class="kt-field-hint" style="margin-top: 6px">{{ __("Start a draft from the current plan. The current plan remains in use until the changes are approved.") }}</div>
							</div>
						</div>
					</header>
				</div>

				<p v-if="actionError" class="kt-field-error" data-testid="str-action-error" style="font-size: 14px; margin: 0 20.4px 20.4px" role="alert">{{ actionError }}</p>

				<!-- §11.3 — pending update, separate from the current facts. -->
				<div v-if="pendingUpdate && tab !== 'structure'" class="kt-notice" style="margin: 0 20.4px 20.4px" data-testid="str-pending-update" :data-kind="pendingUpdate.kind">
					<div class="kt-notice-body">
						<strong>{{ pendingUpdate.kind === 'draft' ? __("Update in progress.") : __("Update awaiting Strategy Approver review.") }}</strong>
						{{ __("The current plan remains in use until the changes are approved.") }}
						<a v-if="pendingUpdate.action_label" href="#" data-testid="str-pending-update-continue" @click.prevent="navigate(pendingUpdate.structure_route)">{{ pendingUpdate.action_label }}</a>
						<a v-else href="#" data-testid="str-pending-update-open" @click.prevent="navigate(pendingUpdate.route)">{{ __("View the update") }}</a>
					</div>
				</div>
				<div v-if="version && version.status === 'Draft' && version.return_reason" class="kt-notice is-warning" style="margin: 0 20.4px 20.4px" data-testid="str-return-reason">
					<div class="kt-notice-body"><strong>{{ __("Changes requested.") }}</strong> {{ version.return_reason }}</div>
				</div>
				<div v-if="version && version.status === 'Submitted for approval' && tab !== 'structure'" class="kt-notice" style="margin: 0 20.4px 20.4px" data-testid="str-awaiting-review">
					<div class="kt-notice-body">
						<strong>{{ __("Awaiting Strategy Approver review.") }}</strong> {{ __("No further edits until an authorised Return.") }}
						<a v-if="workspace.routes.approval" href="#" data-testid="str-open-approval" @click.prevent="navigate(workspace.routes.approval)">{{ __("Open approval task") }}</a>
					</div>
				</div>
				<div v-if="tab === 'structure' && editable && isUpdate" class="kt-notice" style="margin: 0 20.4px 20.4px" data-testid="str-editor-notice">
					<div class="kt-notice-body">{{ __("The current plan remains in use until these changes are approved.") }}</div>
				</div>

				<div class="kt-tabs" role="tablist" style="padding: 0 20.4px">
					<button type="button" role="tab" class="kt-tab" data-testid="str-tab-overview" :aria-selected="tab === 'overview'" @click="switchTab('overview')">{{ __("Overview") }}</button>
					<button v-if="!workspace.no_version" type="button" role="tab" class="kt-tab" data-testid="str-tab-structure" :aria-selected="tab === 'structure'" @click="switchTab('structure')">{{ __("Structure") }}</button>
					<button v-if="!workspace.no_version" type="button" role="tab" class="kt-tab" data-testid="str-tab-history" :aria-selected="tab === 'history'" @click="switchTab('history')">{{ __("History") }}</button>
				</div>

				<template v-if="tab === 'overview'">
					<div v-if="workspace.no_version" style="padding: 20.4px"><h2 style="margin: 0">{{ __("This plan has no version yet.") }}</h2></div>
					<template v-else>
						<!-- §11.3A Draft Overview — plan details and version dates -->
						<div v-if="isDraft && (canEditIdentity || canEditDates)" style="padding: 20.4px" data-testid="str-draft-details">
							<div class="kt-card-title">{{ __("Plan details") }}</div>
							<div v-if="canEditIdentity" style="display: grid; gap: 13.6px; max-width: 640px">
								<div class="kt-field">
									<label for="str-detail-title">{{ __("Plan title") }}</label>
									<input id="str-detail-title" v-model="detailForm.title" class="kt-input" data-testid="str-identity-title" />
									<p v-if="detailErrors.title" class="kt-field-error">{{ detailErrors.title }}</p>
								</div>
								<div class="kt-field">
									<label>{{ __("Plan type") }}</label>
									<div class="kt-ro" data-testid="str-detail-plan-type">{{ workspace.plan.plan_type_label }}</div>
								</div>
								<div v-if="workspace.plan.parent_primary_plan_id" class="kt-field">
									<label>{{ __("Main plan") }}</label>
									<div class="kt-ro">{{ workspace.plan.parent_primary_plan_title }}</div>
								</div>
								<div style="display: grid; grid-template-columns: 1fr 1fr; gap: 13.6px">
									<div class="kt-field">
										<label for="str-detail-start">{{ __("Start date") }}</label>
										<input id="str-detail-start" v-model="detailForm.period_start" class="kt-input" type="date" data-testid="str-identity-start" />
										<p v-if="detailErrors.period_start" class="kt-field-error">{{ detailErrors.period_start }}</p>
									</div>
									<div class="kt-field">
										<label for="str-detail-end">{{ __("End date") }}</label>
										<input id="str-detail-end" v-model="detailForm.period_end" class="kt-input" type="date" data-testid="str-identity-end" />
										<p v-if="detailErrors.period_end" class="kt-field-error">{{ detailErrors.period_end }}</p>
									</div>
								</div>
							</div>
							<div v-else style="display: grid; gap: 13.6px; max-width: 640px">
								<div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 20.4px">
									<div><div class="kt-label">{{ __("Plan type") }}</div><div style="font-size: 14px; margin-top: 3px">{{ workspace.plan.plan_type_label }}</div></div>
									<div><div class="kt-label">{{ __("Plan period") }}</div><div style="font-size: 14px; margin-top: 3px">{{ workspace.plan.period_label }}</div></div>
									<div><div class="kt-label">{{ __("Based on") }}</div><div style="font-size: 14px; margin-top: 3px">{{ __("Version {0}", [version.version_number - 1]) }}</div></div>
								</div>
								<div style="display: grid; grid-template-columns: 1fr 1fr; gap: 13.6px">
									<div class="kt-field">
										<label for="str-use-from">{{ __("Use from") }}</label>
										<input id="str-use-from" v-model="detailForm.effective_from" class="kt-input" type="date" data-testid="str-use-from" />
										<p v-if="detailErrors.effective_from" class="kt-field-error">{{ detailErrors.effective_from }}</p>
									</div>
									<div class="kt-field">
										<label for="str-use-until">{{ __("Use until") }}</label>
										<input id="str-use-until" v-model="detailForm.effective_to" class="kt-input" type="date" data-testid="str-use-until" />
										<p v-if="detailErrors.effective_to" class="kt-field-error">{{ detailErrors.effective_to }}</p>
									</div>
								</div>
								<div class="kt-field-hint">{{ __("These dates must fall within the plan period. Approval makes this version current immediately; a future start date prevents approval until that date.") }}</div>
							</div>
							<div style="display: flex; justify-content: flex-end; gap: 10.2px; margin-top: 13.6px">
								<button type="button" class="kt-btn kt-btn-secondary" :disabled="acting || !detailsDirty" data-testid="str-save-plan-details" @click="savePlanDetails">{{ __("Save plan details") }}</button>
								<button type="button" class="kt-btn kt-btn-primary" :disabled="acting" data-testid="str-edit-structure" @click="editStructure">{{ __("Edit structure") }}</button>
							</div>
						</div>

						<div v-else style="padding: 20.4px" data-testid="str-identity-card">
							<div class="kt-card-title">{{ __("Plan details") }}</div>
							<div class="kt-grid-3">
								<div><div class="kt-label">{{ __("Plan type") }}</div><div style="font-size: 14px; margin-top: 3px" data-testid="str-plan-type">{{ workspace.plan.plan_type_label }}</div></div>
								<div><div class="kt-label">{{ __("Plan period") }}</div><div style="font-size: 14px; margin-top: 3px">{{ workspace.plan.period_label }}</div></div>
								<div><div class="kt-label">{{ appliesLabel }}</div><div style="font-size: 14px; margin-top: 3px" data-testid="str-version-applies">{{ version.effective_period_label || "—" }}</div></div>
							</div>
						</div>

						<!-- §11.3 readiness — actual actionable items, not a green checklist -->
						<div v-if="isDraft && readinessFailures.length" class="kt-notice is-warning" style="margin: 0 20.4px 20.4px" data-testid="str-readiness-failures">
							<div class="kt-notice-body">
								<strong>{{ __("Before this plan can be submitted:") }}</strong>
								<span v-for="f in readinessFailures" :key="f.rule" style="display: block">{{ f.message }}</span>
								<a href="#" data-testid="str-readiness-edit" @click.prevent="switchTab('structure')">{{ __("Edit structure") }}</a>
							</div>
						</div>

						<div style="padding: 20.4px; border-top: 1px solid var(--kt-color-divider)" data-testid="str-objectives-card">
							<div class="kt-card-title">{{ __("Objectives and targets") }}</div>
							<ObjectivesAndTargets :objectives="workspace.objectives" :empty-message="__('No objectives yet. Add a pillar, a programme and an objective in Structure.')" />
						</div>

						<div class="kt-grid-2" style="padding: 20.4px; border-top: 1px solid var(--kt-color-divider)">
							<div>
								<div class="kt-card-title">{{ __("Structure summary") }}</div>
								<StructureSummary :counts="workspace.structure_summary" />
							</div>
							<div data-testid="str-authority-card">
								<div class="kt-card-title">{{ __("Approval details") }}</div>
								<VersionTimeline
									v-if="workspace.approval_details"
									:events="[{ event: 'Approve', event_label: workspace.approval_details.label, at_label: workspace.approval_details.at_label, actor_name: workspace.approval_details.actor_name, tone: 'is-live' }]"
								/>
								<p v-else class="kt-muted" style="margin: 0" data-testid="str-no-approval">{{ __("Not yet approved.") }}</p>
								<div v-if="workspace.versions.length > 1" style="margin-top: 13.6px">
									<div class="kt-label" style="margin-bottom: 6px">{{ __("Versions") }}</div>
									<table class="kt-table" data-testid="str-versions-table">
										<thead><tr><th>{{ __("Version") }}</th><th>{{ __("Status") }}</th><th>{{ __("Applies") }}</th></tr></thead>
										<tbody>
											<tr v-for="v in workspace.versions" :key="v.id" data-testid="str-version-row">
												<td><a href="#" @click.prevent="navigate(v.route)">{{ __("Version") }} {{ v.version_number }}</a></td>
												<td><span class="kt-status" :class="v.status_tone">{{ v.status_label }}</span></td>
												<td>{{ v.effective_period_label || "—" }}</td>
											</tr>
										</tbody>
									</table>
								</div>
							</div>
						</div>
					</template>
				</template>

				<template v-else-if="tab === 'history'">
					<div style="padding: 20.4px" data-testid="str-history">
						<div class="kt-card-title">{{ __("History") }} &middot; {{ __("Version") }} {{ version.version_number }}</div>
						<VersionTimeline :events="history" />
					</div>
				</template>
			</div>

			<template v-if="tab === 'structure'">
				<StructureEditor
					v-if="editable"
					ref="editorRef"
					:plan="workspace.plan"
					:version="version"
					:editable="true"
					@dirty="editorDirty = $event"
					@saved="onSaved"
					@submitted="onSubmitted"
				/>
				<div v-else class="kt-editor-grid">
					<div class="kt-card kt-blueprint" data-testid="str-hierarchy">
						<div class="kt-card-title" style="margin-bottom: 4px">{{ __("Plan structure") }}</div>
						<div style="font-size: 12px; color: var(--kt-color-neutral-700); margin-bottom: 13.6px">{{ __("Read-only") }} &middot; {{ version.status_label }}</div>
						<StructureTree :nodes="readTree.tree" :read-only="true" :selected-id="readSelected?.id" @select="readSelected = $event" />
						<p v-if="!readTree.tree.length" class="kt-muted" style="margin: 0" data-testid="str-no-structure">{{ __("No structure recorded.") }}</p>
					</div>
					<div class="kt-card kt-blueprint" style="position: sticky; top: 80px" data-testid="str-node-panel">
						<template v-if="readSelected">
							<div class="kt-card-title" style="margin-bottom: 4px" data-testid="str-selected-type">{{ typeLabel(readSelected.node_type) }}</div>
							<div v-if="nodePath(readSelected)" style="font-size: 12px; color: var(--kt-color-neutral-700); margin-bottom: 13.6px">{{ nodePath(readSelected) }}</div>
							<div v-if="readSelected.node_type === 'Performance Target'"><div class="kt-label">{{ __("Target") }}</div><div style="font-size: 14px; margin-top: 3px">{{ readSelected.result_label }} &middot; {{ readSelected.period_label }}</div></div>
							<template v-else-if="readSelected.node_type === 'Performance Indicator'">
								<div><div class="kt-label">{{ __("Indicator") }}</div><div style="font-size: 14px; margin-top: 3px">{{ readSelected.title }}</div></div>
								<div style="margin-top: 10px"><div class="kt-label">{{ __("How it is measured") }}</div><div style="font-size: 13px; margin-top: 3px; color: var(--kt-color-neutral-800)">{{ readSelected.definition }}</div></div>
								<div style="margin-top: 10px"><div class="kt-label">{{ __("Unit") }}</div><div style="font-size: 14px; margin-top: 3px">{{ readSelected.unit }}</div></div>
							</template>
							<div v-else><div class="kt-label">{{ typeLabel(readSelected.node_type) }}</div><div style="font-size: 14px; margin-top: 3px">{{ readSelected.title }}</div></div>
						</template>
						<p v-else class="kt-muted" style="margin: 0">{{ __("Select an item to read its complete facts.") }}</p>
					</div>
				</div>
			</template>
		</template>

		<ConfirmDialog
			:open="confirmDialog === 'update-plan'"
			:title="__('Update plan?')"
			:message="__('Start a draft from the current plan. The current plan remains in use until the changes are approved.')"
			:confirm-label="__('Update plan')"
			@confirm="doUpdatePlan"
			@cancel="confirmDialog = null"
		/>
		<ConfirmDialog
			:open="confirmDialog === 'discard-draft'"
			:title="__('Discard this draft?')"
			:message="version && version.version_number > 1 ? __('This removes the draft update. The current plan stays in use.') : __('This permanently removes the plan and everything entered for it. This cannot be undone.')"
			:confirm-label="__('Discard draft')"
			danger
			testid="str-confirm-discard"
			@confirm="doDiscardDraft"
			@cancel="confirmDialog = null"
		/>
	</div>
</template>
