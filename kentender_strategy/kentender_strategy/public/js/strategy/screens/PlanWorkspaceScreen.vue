<script setup>
// STR-UI-02 Plan workspace + STR-UI-03 Structure editor (STR-DES-03/04/05).
// Routes (STR-CHG-001 v1.7 §10):
//   /app/strategy/plan/{plan_id}                          Overview
//   /app/strategy/plan/{plan_id}/history                  History
//   /app/strategy/plan/{plan_id}/version/{n}/structure    Structure (editor when {n} is the editable Draft)
import { ref, reactive, computed, watch, onMounted, onActivated } from "vue";
import { useRouteState } from "../../strategy_shared/composables/useRouteState.js";
import StructureTree from "../../strategy_shared/components/StructureTree.vue";
import ConfirmDialog from "../../strategy_shared/components/ConfirmDialog.vue";
import AddTargetDialog from "../components/AddTargetDialog.vue";
import { usePageRail } from "../../strategy_shared/composables/usePageRail.js";
import {
	getPlanWorkspace,
	savePlanDraft,
	getVersionHistory,
	getStrategyTree,
	saveStructureDraft,
	submitVersion,
	createSuccessorVersion,
	getFiscalYears,
	getIndicatorUnits,
} from "../data/strategyApi.js";

const { route, epoch } = useRouteState("strategy");
const planId = computed(() => (route.value[1] === "plan" ? route.value[2] || null : null));
const tab = computed(() => {
	const r = route.value;
	if (r[3] === "history") return "history";
	if (r[3] === "version" && r[5] === "structure") return "structure";
	return "overview";
});
const versionParam = computed(() => (route.value[3] === "version" ? route.value[4] || null : null));

const loading = ref(true);
const refreshing = ref(false);
const notFound = ref(false);
const forbidden = ref(false);
const workspace = ref(null);
const tree = ref({ tree: [], counts: {}, expected_version: null });
const history = ref([]);
const historyLoaded = ref(false);
const actionError = ref(null);
const acting = ref(false);
const fiscalYears = ref([]);
const indicatorUnits = ref([]);

// The version whose structure the Structure tab shows: the one named in
// the URL when it belongs to this plan, else the plan's current version.
const structureVersion = computed(() => {
	if (!workspace.value || workspace.value.no_version) return null;
	const n = versionParam.value;
	const found = n ? (workspace.value.versions || []).find((v) => String(v.version_number) === String(n)) : null;
	return found || workspace.value.current_version;
});
const currentVersionId = computed(() => workspace.value?.current_version?.id || null);
// Editable only for the plan's own current Draft — never a superseded or
// Active version reached by URL (§12.2: those always open read-only).
const editable = computed(
	() => !!workspace.value?.is_editable_draft && structureVersion.value?.id === currentVersionId.value
);

const railTrail = computed(() => {
	const items = [
		{ label: __("Home"), route: ["Workspaces", "Procurement Home"] },
		{ label: __("Strategy Alignment"), route: ["strategy"] },
	];
	if (workspace.value?.plan) {
		if (tab.value === "structure" && structureVersion.value) {
			items.push({ label: workspace.value.plan.reference, route: ["strategy", "plan", workspace.value.plan.reference] });
			items.push({ label: __("Version {0}", [structureVersion.value.version_number]) });
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

onMounted(async () => {
	try {
		indicatorUnits.value = await getIndicatorUnits();
	} catch (e) {
		// Non-fatal: the Unit field's suggestions just stay empty.
	}
});

function expectedResult(target, unit) {
	const suffix = (unit || "").trim().toLowerCase() === "percentage" ? "%" : "";
	return `${target.comparison} ${target.target_value}${suffix}`;
}

function statusClass(status) {
	if (status === "Active") return "is-live";
	if (status === "Submitted for approval") return "is-pending";
	return "is-draft";
}

function eventStatusClass(eventName) {
	if (["Approve", "Approve successor"].includes(eventName)) return "is-live";
	if (eventName === "Submit for approval") return "is-pending";
	return "is-draft";
}

function periodLabel(t) {
	if (t.fiscal_year) return `FY ${t.fiscal_year}`;
	if (t.target_by_date) return __("By {0}", [t.target_by_date]);
	return "—";
}

// AGENTS.md §6.4 — the skeleton is only for a plan with nothing to show
// yet; a revisit, an action, or the page coming back into view revalidates
// in place under data-refreshing.
let loadSeq = 0;
async function loadWorkspace(opts) {
	if (!planId.value) return;
	const quiet = !!(opts && opts.quiet === true) && !!workspace.value;
	const seq = ++loadSeq;
	if (quiet) refreshing.value = true;
	else loading.value = true;
	try {
		const data = await getPlanWorkspace(planId.value);
		if (seq !== loadSeq) return;
		notFound.value = !!data.not_found;
		forbidden.value = !!data.forbidden;
		if (!data.not_found && !data.forbidden) {
			workspace.value = data;
			if (!data.no_version) {
				await loadTree();
				loadFiscalYears();
			}
			if (tab.value === "history") loadHistory(true);
		}
	} catch (e) {
		if (seq === loadSeq) actionError.value = e.message || String(e);
	} finally {
		if (seq === loadSeq) {
			loading.value = false;
			refreshing.value = false;
		}
	}
}

async function loadTree() {
	if (!structureVersion.value) return;
	tree.value = await getStrategyTree(structureVersion.value.id);
	if (selectedNode.value) {
		selectedNode.value = findNodeById(tree.value.tree, selectedNode.value.id) || null;
	}
}

async function loadFiscalYears() {
	try {
		fiscalYears.value = await getFiscalYears(workspace.value.plan.id);
	} catch (e) {
		fiscalYears.value = [];
	}
}

async function loadHistory(force) {
	if (!currentVersionId.value || (historyLoaded.value && !force)) return;
	history.value = await getVersionHistory(currentVersionId.value);
	historyLoaded.value = true;
}

// Route/lifecycle watchers are registered at the END of this script: the
// immediate planId watcher runs during setup and resets editor state that
// is declared below it (a `const` in its temporal dead zone otherwise).

function switchTab(t) {
	const target = workspace.value?.routes?.[t];
	if (target) frappe.set_route(...target);
}

// --- Plan identity (§12.2: editable only while the first version is Draft) ---
const editingIdentity = ref(false);
const identityForm = reactive({ title: "", period_start: "", period_end: "" });
function startEditIdentity() {
	identityForm.title = workspace.value.plan.title;
	identityForm.period_start = workspace.value.plan.period_start;
	identityForm.period_end = workspace.value.plan.period_end;
	editingIdentity.value = true;
}
async function saveIdentity() {
	acting.value = true;
	actionError.value = null;
	try {
		await savePlanDraft(
			{
				plan_id: workspace.value.plan.id,
				plan_version_id: currentVersionId.value,
				title: identityForm.title,
				period_start: identityForm.period_start,
				period_end: identityForm.period_end,
				effective_from: identityForm.period_start,
				effective_to: identityForm.period_end,
			},
			workspace.value.current_version.expected_version
		);
		frappe.show_alert({ message: __("Plan identity saved"), indicator: "green" });
		editingIdentity.value = false;
		await loadWorkspace({ quiet: true });
	} catch (e) {
		actionError.value = e.message || String(e);
	} finally {
		acting.value = false;
	}
}

// Every structure mutation already persists immediately; "Save draft" is
// the STR-DES-04 confirmation affordance for "leave this as Draft".
function saveDraft() {
	frappe.show_alert({ message: __("Draft saved"), indicator: "green" });
}

const confirmDialog = ref(null); // 'submit' | 'create-successor' | 'delete-node' | 'delete-target' | 'discard-changes' | null

async function doSubmit() {
	if (!currentVersionId.value) return;
	acting.value = true;
	actionError.value = null;
	confirmDialog.value = null;
	try {
		await submitVersion(currentVersionId.value, workspace.value.current_version.expected_version);
		frappe.show_alert({ message: __("Submitted for approval"), indicator: "green" });
		historyLoaded.value = false;
		await loadWorkspace({ quiet: true });
		switchTab("overview");
	} catch (e) {
		actionError.value = e.message || String(e);
	} finally {
		acting.value = false;
	}
}

async function doCreateSuccessor() {
	acting.value = true;
	actionError.value = null;
	confirmDialog.value = null;
	try {
		await createSuccessorVersion(workspace.value.plan.id);
		frappe.show_alert({ message: __("Successor version created"), indicator: "green" });
		historyLoaded.value = false;
		await loadWorkspace({ quiet: true });
		switchTab("structure");
	} catch (e) {
		actionError.value = e.message || String(e);
	} finally {
		acting.value = false;
	}
}

// --- Structure editor state (STR-UI-03) ---
const selectedNode = ref(null);
const editForm = reactive({});
const creatingChildOf = ref(null); // { parent, childType } while composing a new node/indicator
const savingNode = ref(false);
const addingTargetTo = ref(null); // the Performance Indicator node, while the Add target dialog is open

const editFormBaseline = ref(null);
function snapshotEditForm() {
	editFormBaseline.value = JSON.stringify(editForm);
}
const isEditFormDirty = computed(() => {
	if (!editFormBaseline.value) return false;
	if (!selectedNode.value && !creatingChildOf.value) return false;
	return JSON.stringify(editForm) !== editFormBaseline.value;
});
const pendingNavigation = ref(null);
function guardedNavigate(run) {
	if (isEditFormDirty.value) {
		pendingNavigation.value = run;
		confirmDialog.value = "discard-changes";
	} else {
		run();
	}
}
function confirmDiscardChanges() {
	confirmDialog.value = null;
	const run = pendingNavigation.value;
	pendingNavigation.value = null;
	if (run) run();
}
function cancelDiscardChanges() {
	confirmDialog.value = null;
	pendingNavigation.value = null;
}

function selectNode(node) {
	creatingChildOf.value = null;
	selectedNode.value = node;
	Object.assign(editForm, {
		title: node.title,
		display_order: node.display_order,
		indicator_name: node.title,
		definition: node.definition,
		unit: node.unit,
	});
	snapshotEditForm();
}

function handleTreeSelect(node) {
	guardedNavigate(() => {
		if (node.node_type === "Performance Target") {
			const path = findPath(tree.value.tree, node.id, []);
			const parent = path && path.length >= 2 ? path[path.length - 2] : null;
			if (parent) {
				selectNode(parent);
				if (editable.value) startEditTarget(node);
				return;
			}
		}
		selectNode(node);
	});
}

function startAddChild({ parent, childType }) {
	guardedNavigate(() => {
		if (childType === "Performance Target") {
			selectNode(parent);
			actionError.value = null;
			addingTargetTo.value = parent;
			return;
		}
		selectedNode.value = null;
		creatingChildOf.value = { parent, childType };
		Object.assign(editForm, {
			title: "",
			display_order: (parent.children ? parent.children.length : 0) + 1,
			indicator_name: "",
			definition: "",
			unit: "",
		});
		snapshotEditForm();
	});
}

function findNodeById(nodes, id) {
	for (const n of nodes) {
		if (n.id === id) return n;
		if (n.children) {
			const found = findNodeById(n.children, id);
			if (found) return found;
		}
	}
	return null;
}

function findPath(nodes, targetId, trail) {
	for (const n of nodes) {
		const nextTrail = [...trail, n];
		if (n.id === targetId) return nextTrail;
		if (n.children && n.children.length) {
			const found = findPath(n.children, targetId, nextTrail);
			if (found) return found;
		}
	}
	return null;
}

const selectedNodeContext = computed(() => {
	if (!selectedNode.value) return "";
	const path = findPath(tree.value.tree, selectedNode.value.id, []);
	if (!path || path.length < 2) return "";
	const ancestors = path.slice(0, -1);
	if (selectedNode.value.node_type === "Performance Indicator") {
		const parent = ancestors[ancestors.length - 1];
		return parent ? `${__("Measures")}: ${parent.title}` : "";
	}
	return ancestors.map((n) => n.title).join(" / ");
});

// §12.3 — every save carries the tree's expected version token; a stale
// tree is rejected with STRATEGY_STALE_WRITE and the values stay on screen.
async function saveStructure(change) {
	const result = await saveStructureDraft(currentVersionId.value, {
		...change,
		expectedVersion: tree.value.expected_version,
	});
	await loadTree();
	return result;
}

// --- Target edit/delete (STR-DES-05 Targets table Action column) ---
const editingTargetId = ref(null);
const targetEditForm = reactive({ comparison: "At least", target_value: "", period: "" });
const DATE_PREFIX = "date:";
const targetPeriodOptions = computed(() => {
	const out = fiscalYears.value.map((fy) => ({ value: fy.name, label: `FY ${fy.name}` }));
	const end = workspace.value?.plan?.period_end;
	if (end) out.push({ value: DATE_PREFIX + end, label: __("By end of plan period ({0})", [end]) });
	return out;
});

function startEditTarget(t) {
	editingTargetId.value = t.id;
	targetEditForm.comparison = t.comparison;
	targetEditForm.target_value = t.target_value;
	targetEditForm.period = t.fiscal_year || (t.target_by_date ? DATE_PREFIX + t.target_by_date : "");
}

function cancelEditTarget() {
	editingTargetId.value = null;
}

function periodFields(period) {
	const isDate = (period || "").startsWith(DATE_PREFIX);
	return {
		fiscal_year: isDate ? null : period || null,
		target_by_date: isDate ? period.slice(DATE_PREFIX.length) : null,
	};
}

async function saveTargetEdit(t) {
	savingNode.value = true;
	actionError.value = null;
	try {
		await saveStructure({
			targets: [
				{
					name: t.id,
					comparison: targetEditForm.comparison,
					target_value: targetEditForm.target_value,
					...periodFields(targetEditForm.period),
				},
			],
		});
		editingTargetId.value = null;
	} catch (e) {
		actionError.value = e.message || String(e);
	} finally {
		savingNode.value = false;
	}
}

const pendingDeleteTarget = ref(null);

function askDeleteTarget(t) {
	pendingDeleteTarget.value = t;
	confirmDialog.value = "delete-target";
}

async function confirmDeleteTarget() {
	const t = pendingDeleteTarget.value;
	if (!t) return;
	confirmDialog.value = null;
	savingNode.value = true;
	actionError.value = null;
	try {
		await saveStructure({ deletes: [{ doctype: "Performance Target", name: t.id }] });
		frappe.show_alert({ message: __("Target deleted"), indicator: "green" });
		pendingDeleteTarget.value = null;
	} catch (e) {
		actionError.value = e.message || String(e);
	} finally {
		savingNode.value = false;
	}
}

async function saveNodeEdit() {
	if (!selectedNode.value || !currentVersionId.value) return;
	savingNode.value = true;
	actionError.value = null;
	try {
		if (selectedNode.value.node_type === "Performance Indicator") {
			await saveStructure({
				indicators: [
					{
						name: selectedNode.value.id,
						indicator_name: editForm.indicator_name,
						definition: editForm.definition,
						unit: editForm.unit,
					},
				],
			});
		} else if (selectedNode.value.node_type !== "Performance Target") {
			await saveStructure({
				nodes: [{ name: selectedNode.value.id, title: editForm.title, display_order: editForm.display_order }],
			});
		}
		frappe.show_alert({ message: __("Changes saved"), indicator: "green" });
		snapshotEditForm();
	} catch (e) {
		actionError.value = e.message || String(e);
	} finally {
		savingNode.value = false;
	}
}

// STR-BR-007/§12.3: a node with descendants cannot be removed until they
// are removed first — the server enforces this; checking here too tells the
// author immediately instead of after a doomed round trip.
const deleteNodeBlockedReason = computed(() => {
	const n = selectedNode.value;
	if (!n) return null;
	if (n.children && n.children.length) {
		if (n.node_type === "Performance Indicator") return __("Delete its targets first, then delete this indicator.");
		if (n.node_type === "Strategic Objective") return __("Delete or move its indicators first, then delete this objective.");
		return __("Delete or move its child items first, then delete this one.");
	}
	return null;
});

function askDeleteNode() {
	if (!selectedNode.value) return;
	confirmDialog.value = "delete-node";
}

async function confirmDeleteNode() {
	if (!selectedNode.value || !currentVersionId.value) return;
	if (deleteNodeBlockedReason.value) {
		confirmDialog.value = null;
		return;
	}
	const doctype = selectedNode.value.node_type === "Performance Indicator" ? "Performance Indicator" : "Strategy Node";
	const label = selectedNode.value.node_type === "Performance Indicator" ? __("Indicator deleted") : __("Node deleted");
	confirmDialog.value = null;
	savingNode.value = true;
	actionError.value = null;
	try {
		await saveStructure({ deletes: [{ doctype, name: selectedNode.value.id }] });
		frappe.show_alert({ message: label, indicator: "green" });
		selectedNode.value = null;
	} catch (e) {
		actionError.value = e.message || String(e);
	} finally {
		savingNode.value = false;
	}
}

async function saveNewChild() {
	if (!creatingChildOf.value || !currentVersionId.value) return;
	const { parent, childType } = creatingChildOf.value;
	savingNode.value = true;
	actionError.value = null;
	try {
		if (childType === "Performance Indicator") {
			await saveStructure({
				indicators: [
					{
						measures_node_id: parent.id,
						indicator_name: editForm.indicator_name,
						definition: editForm.definition,
						unit: editForm.unit,
					},
				],
			});
		} else {
			await saveStructure({
				nodes: [
					{
						node_type: childType,
						parent_node_id: parent.id || null,
						title: editForm.title,
						display_order: editForm.display_order,
					},
				],
			});
		}
		frappe.show_alert({ message: __("Added"), indicator: "green" });
		creatingChildOf.value = null;
	} catch (e) {
		actionError.value = e.message || String(e);
	} finally {
		savingNode.value = false;
	}
}

function addPillar() {
	startAddChild({ parent: { id: null, children: tree.value.tree }, childType: "Pillar" });
}

function closeTargetDialog() {
	addingTargetTo.value = null;
}

async function confirmAddTarget({ fiscal_year, target_by_date, comparison, target_value }) {
	if (!addingTargetTo.value || !currentVersionId.value) return;
	savingNode.value = true;
	actionError.value = null;
	try {
		await saveStructure({
			targets: [{ indicator_id: addingTargetTo.value.id, comparison, target_value, fiscal_year, target_by_date }],
		});
		frappe.show_alert({ message: __("Added"), indicator: "green" });
		addingTargetTo.value = null;
	} catch (e) {
		actionError.value = e.message || String(e);
	} finally {
		savingNode.value = false;
	}
}

// --- Route and lifecycle watchers (see the note above switchTab) ---
watch(
	planId,
	(id, old) => {
		if (!id) return;
		if (id !== old) {
			workspace.value = null;
			tree.value = { tree: [], counts: {}, expected_version: null };
			history.value = [];
			historyLoaded.value = false;
			selectedNode.value = null;
			creatingChildOf.value = null;
			editingIdentity.value = false;
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
});
watch(
	() => structureVersion.value?.id,
	(id, old) => {
		if (id && old && id !== old && workspace.value) {
			selectedNode.value = null;
			creatingChildOf.value = null;
			loadTree();
		}
	}
);
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
			<i class="kt-corner tl"></i><i class="kt-corner tr"></i><i class="kt-corner bl"></i><i class="kt-corner br"></i>
			<div v-for="i in 5" :key="i" class="kt-skel" style="height: 16px; margin-bottom: 10px"></div>
		</div>
		<div v-else-if="notFound" class="kt-card kt-empty" data-testid="str-not-found">
			<h2>{{ __("This plan could not be found.") }}</h2>
		</div>
		<div v-else-if="forbidden" class="kt-card kt-empty" data-testid="str-forbidden">
			<h2>{{ __("You do not have access to Strategy Alignment.") }}</h2>
			<p>{{ __("This area needs one of these responsibilities: Strategy Author, Strategy Approver or Auditor. Ask your KenTender administrator to assign one in System setup.") }}</p>
		</div>
		<template v-else-if="workspace">
			<header style="display: flex; justify-content: space-between; align-items: flex-start">
				<div>
					<div class="kt-muted" style="text-transform: uppercase; font-size: 11px" data-testid="str-plan-eyebrow">
						{{ workspace.plan.reference }}<template v-if="tab === 'structure' && structureVersion"> · {{ __("VERSION") }} {{ structureVersion.version_number }}</template>
					</div>
					<h1 style="font-size: 28px; display: inline-flex; align-items: center; gap: 10px" data-testid="str-plan-title-heading">
						{{ tab === "structure" ? __("Strategy structure") : workspace.plan.title }}
						<span v-if="!workspace.no_version" class="kt-status" data-testid="str-plan-status" :class="statusClass((tab === 'structure' && structureVersion ? structureVersion : workspace.current_version).status)">
							{{ (tab === "structure" && structureVersion ? structureVersion : workspace.current_version).status }}
						</span>
					</h1>
				</div>
				<div style="display: flex; gap: 12px">
					<template v-if="tab === 'structure' && editable">
						<button type="button" class="kt-btn kt-btn-secondary" data-testid="str-save-draft" @click="saveDraft">
							{{ __("Save draft") }}
						</button>
						<button type="button" class="kt-btn kt-btn-primary" :disabled="acting" data-testid="str-submit" @click="confirmDialog = 'submit'">
							{{ __("Submit for approval") }}
						</button>
					</template>
					<button
						v-if="workspace.capabilities.create_successor"
						type="button"
						class="kt-btn kt-btn-secondary"
						:disabled="acting"
						data-testid="str-create-successor"
						@click="confirmDialog = 'create-successor'"
					>
						{{ __("Create successor version") }}
					</button>
				</div>
			</header>

			<p v-if="actionError && tab !== 'structure'" data-testid="str-action-error" style="color: oklch(0.45 0.13 28)">{{ actionError }}</p>

			<div v-if="!workspace.no_version && workspace.current_version.status === 'Draft' && workspace.current_version.return_reason" class="kt-card" data-testid="str-return-reason" style="border-left: 4px solid #92610a">
				<div class="kt-card-title">{{ __("Returned for correction") }}</div>
				<p style="margin: 0">{{ workspace.current_version.return_reason }}</p>
			</div>

			<div class="kt-tabs">
				<div class="kt-tab" data-testid="str-tab-overview" :aria-selected="tab === 'overview'" @click="switchTab('overview')">{{ __("Overview") }}</div>
				<div v-if="!workspace.no_version" class="kt-tab" data-testid="str-tab-structure" :aria-selected="tab === 'structure'" @click="switchTab('structure')">{{ __("Structure") }}</div>
				<div v-if="!workspace.no_version" class="kt-tab" data-testid="str-tab-history" :aria-selected="tab === 'history'" @click="switchTab('history')">{{ __("History") }}</div>
			</div>

			<template v-if="tab === 'overview'">
				<div v-if="workspace.no_version" class="kt-card kt-empty">
					<h2>{{ __("This plan has no version yet.") }}</h2>
				</div>
				<template v-else>
					<div style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px">
						<div class="kt-card kt-blueprint" data-testid="str-identity-card">
							<i class="kt-corner tl"></i><i class="kt-corner tr"></i><i class="kt-corner bl"></i><i class="kt-corner br"></i>
							<div class="kt-card-title" style="display: flex; justify-content: space-between; align-items: center">
								<span>{{ __("Plan identity") }}</span>
								<button v-if="workspace.capabilities.edit_identity && !editingIdentity" type="button" class="kt-add-child" data-testid="str-identity-edit" @click="startEditIdentity">{{ __("Edit") }}</button>
							</div>
							<template v-if="editingIdentity">
								<div class="kt-field"><label>{{ __("Plan title") }}</label><input v-model="identityForm.title" class="kt-input" data-testid="str-identity-title" /></div>
								<div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px">
									<div class="kt-field"><label>{{ __("Plan period start") }}</label><input v-model="identityForm.period_start" class="kt-input" type="date" /></div>
									<div class="kt-field"><label>{{ __("Plan period end") }}</label><input v-model="identityForm.period_end" class="kt-input" type="date" /></div>
								</div>
								<div style="display: flex; justify-content: flex-end; gap: 12px">
									<button type="button" class="kt-btn kt-btn-ghost" @click="editingIdentity = false">{{ __("Cancel") }}</button>
									<button type="button" class="kt-btn kt-btn-primary" :disabled="acting" data-testid="str-identity-save" @click="saveIdentity">{{ __("Save changes") }}</button>
								</div>
							</template>
							<template v-else>
								<div class="kt-row"><dt>{{ __("Plan role") }}</dt><dd>{{ workspace.plan.plan_role }}</dd></div>
								<div class="kt-row"><dt>{{ __("Plan period") }}</dt><dd>{{ workspace.plan.period_label }}</dd></div>
								<div class="kt-row"><dt>{{ __("Active version") }}</dt><dd data-testid="str-active-version">{{ workspace.active_version ? `Version ${workspace.active_version.version_number}` : "—" }}</dd></div>
								<div class="kt-row"><dt>{{ __("Current version") }}</dt><dd data-testid="str-current-version">Version {{ workspace.current_version.version_number }} · {{ workspace.current_version.status }}</dd></div>
								<div class="kt-row"><dt>{{ __("Version effective period") }}</dt><dd>{{ workspace.current_version.effective_period_label || "—" }}</dd></div>
							</template>
						</div>
						<div class="kt-card kt-blueprint" data-testid="str-authority-card">
							<i class="kt-corner tl"></i><i class="kt-corner tr"></i><i class="kt-corner bl"></i><i class="kt-corner br"></i>
							<div class="kt-card-title">{{ workspace.readiness ? __("Readiness") : __("Current authority") }}</div>
							<template v-if="workspace.readiness">
								<div v-for="c in workspace.readiness.checks" :key="c.check" class="kt-row" data-testid="str-readiness-row">
									<dt>{{ c.check }}</dt>
									<dd><span class="kt-status" :class="c.ready ? 'is-live' : 'is-pending'">{{ c.ready ? __("Ready") : __("Not ready") }}</span></dd>
								</div>
								<div v-if="workspace.submission_authority.submitted_by && workspace.current_version.status === 'Submitted for approval'" class="kt-row">
									<dt>{{ __("Submitted by") }}</dt><dd>{{ workspace.submission_authority.submitted_by.actor_name || workspace.submission_authority.submitted_by.actor }}</dd>
								</div>
								<div v-if="workspace.routes.approval" class="kt-row">
									<dt>{{ __("Approval task") }}</dt><dd><a href="#" data-testid="str-open-approval" @click.prevent="frappe.set_route(...workspace.routes.approval)">{{ __("Open approval task") }}</a></dd>
								</div>
							</template>
							<template v-else-if="workspace.current_authority && workspace.current_authority.approved_by">
								<div class="kt-row"><dt>{{ __("Approved and activated by") }}</dt><dd data-testid="str-approved-by">{{ workspace.current_authority.approved_by.actor_name || workspace.current_authority.approved_by.actor }}</dd></div>
								<div class="kt-row"><dt>{{ __("Approved and activated") }}</dt><dd>{{ workspace.current_authority.approved_by.at_label || workspace.current_authority.approved_by.at }}</dd></div>
							</template>
							<p v-else class="kt-muted">{{ __("No authority events recorded yet.") }}</p>
						</div>
						<div class="kt-card kt-blueprint" style="grid-column: 1 / -1" data-testid="str-summary-card">
							<i class="kt-corner tl"></i><i class="kt-corner tr"></i><i class="kt-corner bl"></i><i class="kt-corner br"></i>
							<div class="kt-card-title" style="margin-bottom: 16px">{{ __("Structure summary") }}</div>
							<div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px 24px">
								<div style="display: flex; align-items: center; gap: 12px">
									<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#003d9b" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><rect x="4" y="4" width="6" height="16"/><rect x="14" y="4" width="6" height="16"/></svg>
									<div><div class="kt-muted" style="font-size: 12px">{{ __("Pillars") }}</div><div class="kt-figure" style="font-size: 16px; font-weight: 600; color: #003d9b">{{ workspace.structure_summary.pillars }}</div></div>
								</div>
								<div style="display: flex; align-items: center; gap: 12px">
									<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#003d9b" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="m12.83 2.18 8.58 3.9a1 1 0 0 1 0 1.83l-8.58 3.9a2 2 0 0 1-1.66 0L2.6 7.91a1 1 0 0 1 0-1.83z"/><path d="M2 12a1 1 0 0 0 .58.91l8.6 3.91a2 2 0 0 0 1.65 0l8.58-3.9A1 1 0 0 0 22 12"/><path d="M2 17a1 1 0 0 0 .58.91l8.6 3.91a2 2 0 0 0 1.65 0l8.58-3.9A1 1 0 0 0 22 17"/></svg>
									<div><div class="kt-muted" style="font-size: 12px">{{ __("Programmes") }}</div><div class="kt-figure" style="font-size: 16px; font-weight: 600; color: #003d9b">{{ workspace.structure_summary.programmes }}</div></div>
								</div>
								<div style="display: flex; align-items: center; gap: 12px">
									<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#003d9b" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><line x1="6" y1="3" x2="6" y2="15"/><circle cx="18" cy="6" r="3"/><circle cx="6" cy="18" r="3"/><path d="M18 9a9 9 0 0 1-9 9"/></svg>
									<div><div class="kt-muted" style="font-size: 12px">{{ __("Sub-programmes") }}</div><div class="kt-figure" style="font-size: 16px; font-weight: 600; color: #003d9b">{{ workspace.structure_summary.sub_programmes }}</div></div>
								</div>
								<div style="display: flex; align-items: center; gap: 12px">
									<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#047857" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="5"/><circle cx="12" cy="12" r="1"/></svg>
									<div><div class="kt-muted" style="font-size: 12px">{{ __("Strategic objectives") }}</div><div class="kt-figure is-live" style="font-size: 16px; font-weight: 600" data-testid="str-count-objectives">{{ workspace.structure_summary.strategic_objectives }}</div></div>
								</div>
								<div style="display: flex; align-items: center; gap: 12px">
									<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#92610a" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M22 12h-4l-3 9L9 3l-3 9H2"/></svg>
									<div><div class="kt-muted" style="font-size: 12px">{{ __("Performance indicators") }}</div><div class="kt-figure is-attention" style="font-size: 16px; font-weight: 600">{{ workspace.structure_summary.performance_indicators }}</div></div>
								</div>
								<div style="display: flex; align-items: center; gap: 12px">
									<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#92610a" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="2" x2="12" y2="6"/><line x1="12" y1="18" x2="12" y2="22"/><line x1="2" y1="12" x2="6" y2="12"/><line x1="18" y1="12" x2="22" y2="12"/></svg>
									<div><div class="kt-muted" style="font-size: 12px">{{ __("Performance targets") }}</div><div class="kt-figure is-attention" style="font-size: 16px; font-weight: 600" data-testid="str-count-targets">{{ workspace.structure_summary.performance_targets }}</div></div>
								</div>
							</div>
						</div>
						<div v-if="workspace.versions.length > 1" class="kt-card" style="grid-column: 1 / -1" data-testid="str-versions-card">
							<div class="kt-card-title">{{ __("Versions") }}</div>
							<table class="kt-table">
								<thead><tr><th>{{ __("Version") }}</th><th>{{ __("Status") }}</th><th>{{ __("Effective period") }}</th><th></th></tr></thead>
								<tbody>
									<tr v-for="v in workspace.versions" :key="v.id" data-testid="str-version-row">
										<td>{{ __("Version") }} {{ v.version_number }} · {{ v.reference }}</td>
										<td><span class="kt-status" :class="statusClass(v.status)">{{ v.status }}</span></td>
										<td>{{ v.effective_period_label || "—" }}</td>
										<td><a href="#" @click.prevent="frappe.set_route('strategy', 'plan', workspace.plan.reference, 'version', String(v.version_number), 'structure')">{{ __("Structure") }}</a></td>
									</tr>
								</tbody>
							</table>
						</div>
					</div>
				</template>
			</template>

			<template v-else-if="tab === 'structure'">
				<div style="display: flex; gap: 16px; align-items: flex-start">
					<div class="kt-card kt-blueprint" style="width: 42%" data-testid="str-hierarchy">
						<i class="kt-corner tl"></i><i class="kt-corner tr"></i><i class="kt-corner bl"></i><i class="kt-corner br"></i>
						<div style="display: flex; justify-content: space-between; align-items: center">
							<div class="kt-card-title" style="border-bottom: none; padding-bottom: 0">{{ __("Plan hierarchy") }}</div>
							<button v-if="editable" type="button" class="kt-add-child" data-testid="str-add-pillar" @click="addPillar">
								{{ __("Add pillar") }}
							</button>
						</div>
						<StructureTree
							:nodes="tree.tree"
							:selected-id="selectedNode?.id"
							:read-only="!editable"
							@select="handleTreeSelect"
							@add-child="startAddChild"
						/>
						<p v-if="!tree.tree.length" class="kt-muted" data-testid="str-no-structure">{{ __("No structure yet.") }}</p>
					</div>
					<div class="kt-card kt-blueprint" style="width: 58%; position: sticky; top: 80px" data-testid="str-node-panel">
						<i class="kt-corner tl"></i><i class="kt-corner tr"></i><i class="kt-corner bl"></i><i class="kt-corner br"></i>
						<!-- Scroll only this inner wrapper: the corner decorations sit
						     outside it so their -6px offset never becomes scrollable content. -->
						<div style="max-height: calc(100vh - 96px); overflow-y: auto; overflow-x: hidden">
							<p v-if="actionError && !addingTargetTo" data-testid="str-action-error" style="color: oklch(0.45 0.13 28); margin-top: 0">{{ actionError }}</p>
							<template v-if="creatingChildOf">
								<div class="kt-card-title">{{ __("New") }} {{ creatingChildOf.childType }}</div>
								<template v-if="creatingChildOf.childType === 'Performance Indicator'">
									<div class="kt-field"><label>{{ __("Indicator name") }}</label><input v-model="editForm.indicator_name" class="kt-input" data-testid="str-indicator-name" /></div>
									<div class="kt-field"><label>{{ __("Definition") }}</label><textarea v-model="editForm.definition" class="kt-input" rows="2" data-testid="str-indicator-definition"></textarea></div>
									<div class="kt-field"><label>{{ __("Unit") }}</label><input v-model="editForm.unit" class="kt-input" list="kt-indicator-units" data-testid="str-indicator-unit" /></div>
								</template>
								<template v-else>
									<div class="kt-field"><label>{{ __("Title") }}</label><input v-model="editForm.title" class="kt-input" data-testid="str-node-title" /></div>
									<div class="kt-field"><label>{{ __("Display order") }}</label><input v-model="editForm.display_order" class="kt-input" type="number" data-testid="str-node-order" /></div>
								</template>
								<div style="display: flex; justify-content: flex-end; gap: 12px">
									<button type="button" class="kt-btn kt-btn-ghost" @click="creatingChildOf = null">{{ __("Cancel") }}</button>
									<button type="button" class="kt-btn kt-btn-primary" :disabled="savingNode" data-testid="str-node-save" @click="saveNewChild">
										{{ __("Save changes") }}
									</button>
								</div>
							</template>
							<template v-else-if="selectedNode">
								<div class="kt-card-title" data-testid="str-selected-type">{{ selectedNode.node_type }}</div>
								<p v-if="selectedNodeContext" class="kt-muted" style="margin-top: -8px; margin-bottom: 12px">{{ selectedNodeContext }}</p>
								<template v-if="selectedNode.node_type === 'Performance Indicator'">
									<div class="kt-field"><label>{{ __("Indicator name") }}</label><input v-model="editForm.indicator_name" class="kt-input" data-testid="str-indicator-name" :disabled="!editable" /></div>
									<div class="kt-field"><label>{{ __("Definition") }}</label><textarea v-model="editForm.definition" class="kt-input" rows="2" data-testid="str-indicator-definition" :disabled="!editable"></textarea></div>
									<div class="kt-field"><label>{{ __("Unit") }}</label><input v-model="editForm.unit" class="kt-input" list="kt-indicator-units" data-testid="str-indicator-unit" :disabled="!editable" /></div>
									<div class="kt-card-title" style="margin-top: 16px">{{ __("Targets") }}</div>
									<table class="kt-table" data-testid="str-targets-table">
										<thead><tr><th>{{ __("Period") }}</th><th>{{ __("Expected result") }}</th><th v-if="editable">{{ __("Action") }}</th></tr></thead>
										<tbody>
											<template v-for="t in selectedNode.children" :key="t.id">
												<tr v-if="editingTargetId !== t.id" data-testid="str-target-row">
													<td>{{ periodLabel(t) }}</td>
													<td data-testid="str-target-result">{{ expectedResult(t, selectedNode.unit) }}</td>
													<td v-if="editable">
														<a href="#" data-testid="str-target-edit" @click.prevent="startEditTarget(t)">{{ __("Edit") }}</a>
														&nbsp;
														<a href="#" style="color: oklch(0.45 0.13 28)" data-testid="str-target-delete" @click.prevent="askDeleteTarget(t)">{{ __("Delete") }}</a>
													</td>
												</tr>
												<tr v-else data-testid="str-target-edit-row">
													<td colspan="3">
														<div style="display: flex; gap: 8px; align-items: center; flex-wrap: wrap">
															<select v-model="targetEditForm.period" class="kt-input" style="width: 200px" data-testid="str-target-edit-period">
																<option value="">{{ __("Select a period") }}</option>
																<option v-for="o in targetPeriodOptions" :key="o.value" :value="o.value">{{ o.label }}</option>
															</select>
															<select v-model="targetEditForm.comparison" class="kt-input" style="width: 130px" data-testid="str-target-edit-comparison">
																<option>At least</option><option>At most</option><option>Equal to</option>
															</select>
															<input v-model="targetEditForm.target_value" class="kt-input" style="width: 100px" type="number" data-testid="str-target-edit-value" />
															<button type="button" class="kt-btn kt-btn-ghost" @click="cancelEditTarget">{{ __("Cancel") }}</button>
															<button type="button" class="kt-btn kt-btn-primary" :disabled="savingNode" data-testid="str-target-edit-save" @click="saveTargetEdit(t)">{{ __("Save") }}</button>
														</div>
													</td>
												</tr>
											</template>
										</tbody>
									</table>
									<button
										v-if="editable"
										type="button"
										class="kt-btn kt-btn-secondary"
										style="margin-top: 8px; margin-bottom: 24px"
										data-testid="str-add-target"
										@click="startAddChild({ parent: selectedNode, childType: 'Performance Target' })"
									>
										{{ __("Add target") }}
									</button>
								</template>
								<template v-else-if="selectedNode.node_type !== 'Performance Target'">
									<div class="kt-field"><label>{{ __("Title") }}</label><input v-model="editForm.title" class="kt-input" data-testid="str-node-title" :disabled="!editable" /></div>
									<div class="kt-field"><label>{{ __("Display order") }}</label><input v-model="editForm.display_order" class="kt-input" type="number" data-testid="str-node-order" :disabled="!editable" /></div>
								</template>
								<div
									v-if="editable && selectedNode.node_type !== 'Performance Target'"
									style="display: flex; justify-content: space-between; padding-top: 16px; border-top: 1px solid var(--kt-color-divider)"
								>
									<button type="button" class="kt-btn kt-btn-secondary kt-danger" :disabled="savingNode" data-testid="str-node-delete" @click="askDeleteNode">
										{{ selectedNode.node_type === "Performance Indicator" ? __("Delete indicator") : __("Delete node") }}
									</button>
									<button type="button" class="kt-btn kt-btn-primary" :disabled="savingNode" data-testid="str-node-save" @click="saveNodeEdit">
										{{ __("Save changes") }}
									</button>
								</div>
							</template>
							<p v-else class="kt-muted">{{ __("Select a hierarchy item to view or edit it.") }}</p>
						</div>
					</div>
				</div>
			</template>

			<template v-else-if="tab === 'history'">
				<div class="kt-card" data-testid="str-history">
					<div class="kt-card-title">{{ __("Version history") }} · {{ __("Version") }} {{ workspace.current_version.version_number }}</div>
					<table class="kt-table">
						<thead><tr><th>{{ __("Date and time") }}</th><th>{{ __("Event") }}</th><th>{{ __("Actor") }}</th><th>{{ __("Reason") }}</th></tr></thead>
						<tbody>
							<tr v-for="(h, i) in history" :key="i" data-testid="str-history-row">
								<td>{{ h.at_label || h.at }}</td>
								<td><span class="kt-status" :class="eventStatusClass(h.event)">{{ h.event }}</span></td>
								<td>{{ h.actor_name || h.actor }}</td>
								<td>{{ h.reason || "—" }}</td>
							</tr>
						</tbody>
					</table>
					<p v-if="!history.length" class="kt-muted">{{ __("No events recorded yet.") }}</p>
				</div>
			</template>
		</template>

		<ConfirmDialog
			:open="confirmDialog === 'submit'"
			:title="__('Submit this version for approval?')"
			:message="__('The draft will move to Submitted for approval and can no longer be edited until returned.')"
			:confirm-label="__('Submit for approval')"
			@confirm="doSubmit"
			@cancel="confirmDialog = null"
		/>
		<ConfirmDialog
			:open="confirmDialog === 'create-successor'"
			:title="__('Create a successor version?')"
			:message="__('A new Draft copy of the current hierarchy, indicators and targets will be created for editing.')"
			:confirm-label="__('Create successor version')"
			@confirm="doCreateSuccessor"
			@cancel="confirmDialog = null"
		/>
		<ConfirmDialog
			:open="confirmDialog === 'discard-changes'"
			:title="__('Discard unsaved changes?')"
			:message="__('Switching to a different item will discard what you just typed here.')"
			:confirm-label="__('Discard changes')"
			@confirm="confirmDiscardChanges"
			@cancel="cancelDiscardChanges"
		/>
		<ConfirmDialog
			:open="confirmDialog === 'delete-node'"
			:title="
				deleteNodeBlockedReason
					? __('This item has children')
					: selectedNode?.node_type === 'Performance Indicator'
					? __('Delete this indicator?')
					: __('Delete this node?')
			"
			:message="deleteNodeBlockedReason || __('This cannot be undone.')"
			:confirm-label="deleteNodeBlockedReason ? __('OK') : __('Delete')"
			@confirm="confirmDeleteNode"
			@cancel="confirmDialog = null"
		/>
		<ConfirmDialog
			:open="confirmDialog === 'delete-target'"
			:title="__('Delete this target?')"
			:message="__('This cannot be undone.')"
			:confirm-label="__('Delete')"
			@confirm="confirmDeleteTarget"
			@cancel="confirmDialog = null"
		/>
		<AddTargetDialog
			:open="Boolean(addingTargetTo)"
			:fiscal-years="fiscalYears"
			:plan-period-end="workspace?.plan?.period_end || ''"
			:unit="addingTargetTo?.unit"
			:saving="savingNode"
			:error="actionError"
			@confirm="confirmAddTarget"
			@cancel="closeTargetDialog"
		/>
		<datalist id="kt-indicator-units">
			<option v-for="u in indicatorUnits" :key="u" :value="u"></option>
		</datalist>
	</div>
</template>
