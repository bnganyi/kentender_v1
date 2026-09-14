<script setup>
// STR-UI-03 Structure editor (STR-DES-04 / STR-DES-05 / STR-DES-05-AddTarget).
//
// v1.8 §11.4/§11.5/§12.3 (plan D7): the editor keeps the authoritative
// loaded tree plus ONE pending change set — additions (client ids "$n"),
// edits, sibling reorders (Move up / Move down) and removals — and persists
// it once through save_strategy_structure_draft with the tree's expected
// version token. "Submit for approval" validates the visible values, saves
// the pending set if it changed (its own attempt identity), then submits
// the confirmed Draft (a separate identity). Pending client rows are never
// business references: the server's generated IDs replace them on save.
import { ref, reactive, computed, watch, onMounted, onBeforeUnmount, nextTick } from "vue";
import StructureTree from "../../strategy_shared/components/StructureTree.vue";
import ConfirmDialog from "../../strategy_shared/components/ConfirmDialog.vue";
import { runAttempt, hasPendingAttempt } from "../../strategy_shared/data/attempts.js";
import { typeLabel } from "../../strategy_shared/nodeIcons.js";
import { getStrategyTree, saveStructureDraft, submitVersion, getFiscalYears, getIndicatorUnits } from "../data/strategyApi.js";

const props = defineProps({
	plan: { type: Object, required: true },
	version: { type: Object, required: true }, // the Draft version DTO (id, expected_version, has_been_submitted)
	editable: { type: Boolean, default: true },
});
const emit = defineEmits(["submitted", "saved", "dirty"]);

// --- Loaded tree and working copy -----------------------------------------
const loading = ref(true);
const loadError = ref(null);
const expectedVersion = ref(null);
const working = ref([]); // structural roots, each with children (nodes, indicators, targets)
const baseline = ref({}); // id -> snapshot of editable fields
const removed = ref([]); // [{doctype, name, depth}]
const fiscalYears = ref([]);
const indicatorUnits = ref([]);
let tmpCounter = 0;

const STRUCTURAL = new Set(["Pillar", "Programme", "Sub-programme", "Strategic Objective"]);
const isPending = (id) => typeof id === "string" && id.startsWith("$");

function cloneNode(node, parentId) {
	const out = {
		id: node.id,
		node_type: node.node_type,
		title: node.title || "",
		display_order: node.display_order,
		parent_id: parentId || null,
		definition: node.definition || "",
		unit: node.unit || "",
		comparison: node.comparison || "At least",
		target_value: node.target_value ?? "",
		fiscal_year: node.fiscal_year || "",
		target_by_date: node.target_by_date || "",
		period_label: node.period_label || "",
		result_label: node.result_label || "",
		path: node.path || [],
		pending: false,
		children: [],
	};
	out.children = (node.children || []).map((c) => cloneNode(c, node.id));
	return out;
}

function snapshot(node) {
	return {
		node_type: node.node_type,
		title: node.title,
		display_order: node.display_order,
		parent_id: node.parent_id,
		definition: node.definition,
		unit: node.unit,
		comparison: node.comparison,
		target_value: String(node.target_value ?? ""),
		fiscal_year: node.fiscal_year || "",
		target_by_date: node.target_by_date || "",
	};
}

function walk(nodes, fn, parent) {
	for (const n of nodes) {
		fn(n, parent);
		if (n.children) walk(n.children, fn, n);
	}
}

function adopt(treePayload) {
	expectedVersion.value = treePayload.expected_version;
	working.value = (treePayload.tree || []).map((n) => cloneNode(n, null));
	const base = {};
	walk(working.value, (n) => {
		base[n.id] = snapshot(n);
	});
	baseline.value = base;
	removed.value = [];
}

async function load() {
	loading.value = true;
	loadError.value = null;
	try {
		const payload = await getStrategyTree(props.version.id);
		adopt(payload);
		if (selected.value) selected.value = findById(selected.value.id);
	} catch (e) {
		loadError.value = e;
	} finally {
		loading.value = false;
	}
}

onMounted(async () => {
	await load();
	try {
		fiscalYears.value = await getFiscalYears(props.plan.id);
	} catch (e) {
		fiscalYears.value = [];
	}
	try {
		indicatorUnits.value = await getIndicatorUnits();
	} catch (e) {
		indicatorUnits.value = [];
	}
});
watch(
	() => props.version.id,
	() => {
		selected.value = null;
		load();
	}
);

// --- Selection ---------------------------------------------------------------
const selected = ref(null);
const focusField = ref(null);

function findById(id, nodes = working.value) {
	for (const n of nodes) {
		if (n.id === id) return n;
		const found = findById(id, n.children);
		if (found) return found;
	}
	return null;
}
function parentOf(node) {
	return node.parent_id ? findById(node.parent_id) : null;
}
function siblingsOf(node) {
	const parent = parentOf(node);
	const list = parent ? parent.children : working.value;
	return list.filter((n) => n.node_type === node.node_type || (STRUCTURAL.has(n.node_type) && STRUCTURAL.has(node.node_type)));
}
function pathOf(node) {
	const out = [];
	let cur = parentOf(node);
	while (cur) {
		out.unshift(cur.title || __("Untitled {0}", [typeLabel(cur.node_type).toLowerCase()]));
		cur = parentOf(cur);
	}
	return out;
}

function select(node) {
	if (node.node_type === "Performance Target") {
		const indicator = parentOf(node);
		selected.value = indicator;
		openTargetEditor(node);
		return;
	}
	selected.value = node;
	closeTargetEditor();
}

// --- Additions -------------------------------------------------------------------
function nextOrder(list) {
	return list.reduce((max, n) => Math.max(max, Number(n.display_order) || 0), 0) + 1;
}

function addChild({ parent, childType }) {
	const id = `$${++tmpCounter}`;
	const parentNode = parent && parent.id != null ? findById(parent.id) : null;
	const list = parentNode ? parentNode.children : working.value;
	const node = cloneNode(
		{
			id,
			node_type: childType,
			title: "",
			display_order: STRUCTURAL.has(childType) ? nextOrder(list.filter((n) => STRUCTURAL.has(n.node_type))) : null,
			children: [],
		},
		parentNode ? parentNode.id : null
	);
	node.pending = true;
	if (childType === "Performance Target") {
		selected.value = parentNode;
		node.comparison = "At least";
		node.target_value = "";
		node.fiscal_year = "";
		node.target_by_date = "";
		parentNode.children.push(node);
		openTargetEditor(node, true);
		return;
	}
	if (childType === "Performance Indicator") {
		parentNode.children.push(node);
	} else if (parentNode) {
		// Structural children before indicators, in order.
		const insertAt = parentNode.children.findIndex((c) => !STRUCTURAL.has(c.node_type));
		if (insertAt === -1) parentNode.children.push(node);
		else parentNode.children.splice(insertAt, 0, node);
	} else {
		working.value.push(node);
	}
	selected.value = node;
	closeTargetEditor();
	focusField.value = "title";
}

function addPillar() {
	addChild({ parent: { id: null }, childType: "Pillar" });
}

// --- Move up / Move down (sibling order only, §12.3) ----------------------------
function structuralSiblings(node) {
	const parent = parentOf(node);
	const list = parent ? parent.children : working.value;
	return list.filter((n) => STRUCTURAL.has(n.node_type)).sort((a, b) => Number(a.display_order) - Number(b.display_order));
}
const canMoveUp = computed(() => {
	if (!selected.value || !STRUCTURAL.has(selected.value.node_type)) return false;
	const s = structuralSiblings(selected.value);
	return s.indexOf(selected.value) > 0;
});
const canMoveDown = computed(() => {
	if (!selected.value || !STRUCTURAL.has(selected.value.node_type)) return false;
	const s = structuralSiblings(selected.value);
	const i = s.indexOf(selected.value);
	return i >= 0 && i < s.length - 1;
});
function move(direction) {
	const node = selected.value;
	if (!node) return;
	const s = structuralSiblings(node);
	const i = s.indexOf(node);
	const j = direction === "up" ? i - 1 : i + 1;
	if (j < 0 || j >= s.length) return;
	const other = s[j];
	const a = node.display_order;
	node.display_order = other.display_order;
	other.display_order = a;
	// Keep the rendered order in step with display_order.
	const parent = parentOf(node);
	const list = parent ? parent.children : working.value;
	list.sort((x, y) => {
		const sx = STRUCTURAL.has(x.node_type) ? 0 : 1;
		const sy = STRUCTURAL.has(y.node_type) ? 0 : 1;
		if (sx !== sy) return sx - sy;
		if (sx === 0) return Number(x.display_order) - Number(y.display_order);
		return 0;
	});
}

// --- Removal ------------------------------------------------------------------------
const deletionAllowed = computed(() => props.editable && !props.version.has_been_submitted);
const deleteBlockedReason = computed(() => {
	const n = selected.value;
	if (!n) return null;
	if (!deletionAllowed.value) return __("Items cannot be deleted after the plan has been submitted. Edit them instead.");
	if (n.children && n.children.length) {
		if (n.node_type === "Performance Indicator") return __("Remove its targets first, then delete this indicator.");
		if (n.node_type === "Strategic Objective") return __("Remove or move its indicators first, then delete this objective.");
		return __("Remove or move the items under it first, then delete this {0}.", [typeLabel(n.node_type).toLowerCase()]);
	}
	return null;
});
const confirmDialog = ref(null); // 'delete' | 'unsaved' | null
const pendingNavigation = ref(null);

function removeNode(node) {
	const parent = parentOf(node);
	const list = parent ? parent.children : working.value;
	const idx = list.indexOf(node);
	if (idx >= 0) list.splice(idx, 1);
	if (!isPending(node.id)) {
		const doctype = node.node_type === "Performance Target" ? "Performance Target" : node.node_type === "Performance Indicator" ? "Performance Indicator" : "Strategy Node";
		removed.value.push({ doctype, name: node.id });
	}
}
function askDelete() {
	if (!selected.value) return;
	confirmDialog.value = "delete";
}
function confirmDelete() {
	confirmDialog.value = null;
	if (!selected.value || deleteBlockedReason.value) return;
	const node = selected.value;
	removeNode(node);
	selected.value = null;
	closeTargetEditor();
}

// --- Inline target editor (STR-DES-05-AddTarget) ----------------------------------
const targetEditor = reactive({ open: false, targetId: null, isNew: false, mode: "fiscal_year", fiscal_year: "", target_by_date: "", comparison: "At least", target_value: "", error: "" });
function openTargetEditor(target, isNew = false) {
	targetEditor.open = true;
	targetEditor.targetId = target.id;
	targetEditor.isNew = isNew || isPending(target.id);
	targetEditor.mode = target.target_by_date && !target.fiscal_year ? "target_by_date" : "fiscal_year";
	targetEditor.fiscal_year = target.fiscal_year || "";
	targetEditor.target_by_date = target.target_by_date || "";
	targetEditor.comparison = target.comparison || "At least";
	targetEditor.target_value = target.target_value ?? "";
	targetEditor.error = "";
}
function closeTargetEditor() {
	targetEditor.open = false;
	targetEditor.targetId = null;
	targetEditor.error = "";
}
const editingTarget = computed(() => (targetEditor.targetId ? findById(targetEditor.targetId) : null));
function applyTargetEditor() {
	const t = editingTarget.value;
	if (!t) return;
	const value = String(targetEditor.target_value).trim();
	if (targetEditor.mode === "fiscal_year" && !targetEditor.fiscal_year) {
		targetEditor.error = __("Select the financial year this target is for.");
		return;
	}
	if (targetEditor.mode === "target_by_date" && !targetEditor.target_by_date) {
		targetEditor.error = __("Enter the date this target is due by.");
		return;
	}
	if (value === "" || Number.isNaN(Number(value))) {
		targetEditor.error = __("Enter a numeric target value.");
		return;
	}
	const unit = (selected.value?.unit || "").trim().toLowerCase();
	if (unit === "percentage" && (Number(value) < 0 || Number(value) > 100)) {
		targetEditor.error = __("Percentage targets must be between 0 and 100.");
		return;
	}
	// §11.5 — exactly one period mode; switching modes drops the inactive value.
	t.fiscal_year = targetEditor.mode === "fiscal_year" ? targetEditor.fiscal_year : "";
	t.target_by_date = targetEditor.mode === "target_by_date" ? targetEditor.target_by_date : "";
	t.comparison = targetEditor.comparison;
	t.target_value = value;
	t.period_label = t.fiscal_year ? fyLabel(t.fiscal_year) : __("By {0}", [t.target_by_date]);
	t.result_label = `${t.comparison} ${value}${unitSuffix.value}`;
	closeTargetEditor();
}
function discardNewTarget() {
	const t = editingTarget.value;
	if (t && isPending(t.id)) removeNode(t);
	closeTargetEditor();
}
function removeTarget(t) {
	if (!deletionAllowed.value) return;
	removeNode(t);
	if (targetEditor.targetId === t.id) closeTargetEditor();
}
function fyLabel(name) {
	const fy = fiscalYears.value.find((f) => f.name === name);
	return fy ? fy.label : `FY ${name}`;
}
const unitSuffix = computed(() => ((selected.value?.unit || "").trim().toLowerCase() === "percentage" ? "%" : selected.value?.unit || ""));

// --- Change set ---------------------------------------------------------------------
function changed(node) {
	const base = baseline.value[node.id];
	if (!base) return true;
	const now = snapshot(node);
	return Object.keys(now).some((k) => String(now[k] ?? "") !== String(base[k] ?? ""));
}
const changeSet = computed(() => {
	const nodes = [];
	const indicators = [];
	const targets = [];
	walk(working.value, (n) => {
		if (STRUCTURAL.has(n.node_type)) {
			if (isPending(n.id)) {
				nodes.push({ client_id: n.id, node_type: n.node_type, parent_node_id: n.parent_id || null, title: n.title, display_order: n.display_order });
			} else if (changed(n)) {
				nodes.push({ name: n.id, title: n.title, display_order: n.display_order, parent_node_id: n.parent_id || null });
			}
		} else if (n.node_type === "Performance Indicator") {
			if (isPending(n.id)) {
				indicators.push({ client_id: n.id, measures_node_id: n.parent_id, indicator_name: n.title, definition: n.definition, unit: n.unit });
			} else if (changed(n)) {
				indicators.push({ name: n.id, indicator_name: n.title, definition: n.definition, unit: n.unit });
			}
		} else if (n.node_type === "Performance Target") {
			const fields = {
				comparison: n.comparison,
				target_value: n.target_value === "" ? null : Number(n.target_value),
				fiscal_year: n.fiscal_year || null,
				target_by_date: n.target_by_date || null,
			};
			if (isPending(n.id)) targets.push({ client_id: n.id, indicator_id: n.parent_id, ...fields });
			else if (changed(n)) targets.push({ name: n.id, ...fields });
		}
	});
	const order = { "Performance Target": 0, "Performance Indicator": 1, "Strategy Node": 2 };
	const deletes = [...removed.value].sort((a, b) => order[a.doctype] - order[b.doctype]).reverse().reverse();
	return { nodes, indicators, targets, deletes: deletes.sort((a, b) => order[a.doctype] - order[b.doctype]).map(({ doctype, name }) => ({ doctype, name })) };
});
const isDirty = computed(() => {
	const c = changeSet.value;
	return !!(c.nodes.length || c.indicators.length || c.targets.length || c.deletes.length);
});
watch(isDirty, (d) => emit("dirty", d), { immediate: true });

// --- Validation (visible values, §8.2) -------------------------------------------
const errors = ref({}); // id -> message
const errorSummary = ref("");
function validateVisible() {
	const out = {};
	walk(working.value, (n) => {
		if (STRUCTURAL.has(n.node_type) && !(n.title || "").trim()) out[n.id] = __("Enter the {0}.", [typeLabel(n.node_type).toLowerCase()]);
		if (n.node_type === "Performance Indicator") {
			if (!(n.title || "").trim()) out[n.id] = __("Enter the indicator.");
			else if (!(n.definition || "").trim()) out[n.id] = __("Explain how the indicator is measured.");
			else if (!(n.unit || "").trim()) out[n.id] = __("Enter the unit.");
		}
		if (n.node_type === "Performance Target") {
			const hasFy = !!n.fiscal_year;
			const hasDate = !!n.target_by_date;
			if (hasFy === hasDate) out[n.id] = __("Set the target for exactly one financial year or target date.");
			else if (String(n.target_value ?? "").trim() === "" || Number.isNaN(Number(n.target_value))) out[n.id] = __("Enter a numeric target value.");
		}
	});
	errors.value = out;
	const ids = Object.keys(out);
	if (ids.length) {
		errorSummary.value = __("Complete the highlighted items before submitting or approving.");
		const first = findById(ids[0]);
		if (first) select(first);
		return false;
	}
	errorSummary.value = "";
	return true;
}

// --- Save / submit orchestration -------------------------------------------------
const saving = ref(false);
const submitting = ref(false);
const actionError = ref(null);
const actionNotice = ref(null);
const unknownOutcome = ref(false);
const saveScope = computed(() => `structure-save:${props.version.id}`);
const submitScope = computed(() => `submit:${props.version.id}`);

async function persist() {
	const payload = changeSet.value;
	const result = await runAttempt(
		saveScope.value,
		(key) => saveStructureDraft(props.version.id, { ...payload, expectedVersion: expectedVersion.value }, key),
		{ onUnknown: () => (unknownOutcome.value = true) }
	);
	unknownOutcome.value = false;
	// Client ids → generated IDs: the server returns names in the order sent.
	const map = {};
	payload.nodes.forEach((item, i) => {
		if (item.client_id && result.nodes[i]) map[item.client_id] = result.nodes[i];
	});
	payload.indicators.forEach((item, i) => {
		if (item.client_id && result.indicators[i]) map[item.client_id] = result.indicators[i];
	});
	payload.targets.forEach((item, i) => {
		if (item.client_id && result.targets[i]) map[item.client_id] = result.targets[i];
	});
	const selectedId = selected.value ? map[selected.value.id] || selected.value.id : null;
	adopt(await getStrategyTree(props.version.id));
	selected.value = selectedId ? findById(selectedId) : null;
	errors.value = {};
	errorSummary.value = "";
	emit("saved", result);
	return result;
}

async function save() {
	if (!validateVisible()) return false;
	if (!isDirty.value) {
		frappe.show_alert({ message: __("No changes to save"), indicator: "blue" });
		return true;
	}
	saving.value = true;
	actionError.value = null;
	actionNotice.value = null;
	try {
		await persist();
		frappe.show_alert({ message: __("Changes saved"), indicator: "green" });
		return true;
	} catch (e) {
		actionError.value = e.unknownOutcome
			? __("We could not confirm the result. Checking the existing request…")
			: __("Your changes were not saved.") + " " + (e.message || "");
		return false;
	} finally {
		saving.value = false;
	}
}

async function submit() {
	if (!validateVisible()) return;
	submitting.value = true;
	actionError.value = null;
	actionNotice.value = null;
	let savedFirst = false;
	try {
		if (isDirty.value) {
			await persist();
			savedFirst = true;
		}
		const result = await runAttempt(
			submitScope.value,
			(key) => submitVersion(props.version.id, expectedVersion.value, key),
			{ onUnknown: () => (unknownOutcome.value = true) }
		);
		unknownOutcome.value = false;
		frappe.show_alert({ message: __("Submitted for approval"), indicator: "green" });
		emit("submitted", result);
	} catch (e) {
		if (e.unknownOutcome) actionError.value = __("We could not confirm the result. Checking the existing request…");
		else if (savedFirst || !isDirty.value) actionError.value = __("Your changes were saved, but the plan was not submitted.") + " " + (e.message || "");
		else actionError.value = __("Your changes were not saved.") + " " + (e.message || "");
	} finally {
		submitting.value = false;
	}
}

// --- Unsaved-changes guard (§12.3) -----------------------------------------------
function onBeforeUnload(e) {
	if (!isDirty.value) return;
	e.preventDefault();
	e.returnValue = "";
}
onMounted(() => window.addEventListener("beforeunload", onBeforeUnload));
onBeforeUnmount(() => window.removeEventListener("beforeunload", onBeforeUnload));

function guardedNavigate(run) {
	if (!isDirty.value) {
		run();
		return true;
	}
	pendingNavigation.value = run;
	confirmDialog.value = "unsaved";
	return false;
}
async function guardSave() {
	confirmDialog.value = null;
	const ok = await save();
	const run = pendingNavigation.value;
	pendingNavigation.value = null;
	if (ok && run) run();
}
function guardDiscard() {
	confirmDialog.value = null;
	const run = pendingNavigation.value;
	pendingNavigation.value = null;
	load().then(() => run && run());
}
function guardStay() {
	confirmDialog.value = null;
	pendingNavigation.value = null;
}
defineExpose({ guardedNavigate, isDirty, save, submit });

watch(focusField, async (f) => {
	if (!f) return;
	await nextTick();
	const el = document.querySelector(`[data-testid="str-node-title"], [data-testid="str-indicator-name"]`);
	el?.focus();
	focusField.value = null;
});

const selectedPath = computed(() => (selected.value ? pathOf(selected.value).join(" / ") : ""));
const selectedTypeLabel = computed(() => (selected.value ? typeLabel(selected.value.node_type) : ""));
const hasPendingSave = computed(() => hasPendingAttempt(saveScope.value) || hasPendingAttempt(submitScope.value));
</script>

<template>
	<div data-testid="str-structure-editor" :data-dirty="isDirty ? 'true' : 'false'">
		<p v-if="hasPendingSave && !actionError" class="kt-muted" data-testid="str-pending-attempt" style="margin: 0 0 10px">{{ __("A previous save or submission did not confirm. Saving or submitting again resolves that request.") }}</p>
		<p v-if="actionError" class="kt-field-error" data-testid="str-action-error" style="font-size: 14px; margin: 0 0 10px" role="alert">{{ actionError }}</p>
		<p v-if="errorSummary" class="kt-field-error" data-testid="str-validation-summary" style="font-size: 14px; margin: 0 0 10px" role="alert">{{ errorSummary }}</p>

		<div class="kt-editor-grid">
			<div class="kt-card kt-blueprint" data-testid="str-hierarchy">
				<div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 14px">
					<div class="kt-card-title" style="margin: 0; padding-bottom: 0; border-bottom: none">{{ __("Plan structure") }}</div>
					<button v-if="editable" type="button" class="kt-add-child" data-testid="str-add-pillar" @click="addPillar">{{ __("Add pillar") }}</button>
				</div>
				<div v-if="loading" class="kt-skel" style="height: 60px"></div>
				<template v-else>
					<StructureTree :nodes="working" :selected-id="selected?.id" :read-only="!editable" @select="select" @add-child="addChild" />
					<p v-if="!working.length" class="kt-muted" data-testid="str-no-structure" style="margin: 0">{{ __("Add a pillar to start the plan structure.") }}</p>
				</template>
			</div>

			<div class="kt-card kt-blueprint" style="position: sticky; top: 80px" data-testid="str-node-panel">
				<template v-if="selected">
					<div class="kt-card-title" style="margin-bottom: 4px" data-testid="str-selected-type">{{ selectedTypeLabel }}</div>
					<div style="font-size: 12px; color: var(--kt-color-neutral-700); margin-bottom: 13.6px" data-testid="str-selected-path">
						<template v-if="selected.node_type === 'Performance Indicator'">{{ __("Measures") }}: {{ parentOf(selected)?.title }}</template>
						<template v-else>{{ selectedPath }}</template>
					</div>
					<p v-if="errors[selected.id]" class="kt-field-error" data-testid="str-field-error" style="font-size: 13px; margin: 0 0 10px">{{ errors[selected.id] }}</p>

					<template v-if="selected.node_type === 'Performance Indicator'">
						<div class="kt-field">
							<label for="str-indicator-name">{{ __("Indicator") }}</label>
							<input id="str-indicator-name" v-model="selected.title" class="kt-input" data-testid="str-indicator-name" :disabled="!editable" />
							<div class="kt-field-hint">{{ __("What will show progress towards this objective?") }}</div>
						</div>
						<div class="kt-field" style="margin-top: 10px">
							<label for="str-indicator-definition">{{ __("How it is measured") }}</label>
							<textarea id="str-indicator-definition" v-model="selected.definition" class="kt-input" rows="3" style="height: auto" data-testid="str-indicator-definition" :disabled="!editable"></textarea>
							<div class="kt-field-hint">{{ __("Explain exactly what this indicator counts or calculates.") }}</div>
						</div>
						<div class="kt-field" style="margin-top: 10px; max-width: 220px">
							<label for="str-indicator-unit">{{ __("Unit") }}</label>
							<input id="str-indicator-unit" v-model="selected.unit" class="kt-input" list="kt-indicator-units" data-testid="str-indicator-unit" :disabled="!editable" />
						</div>

						<div style="margin-top: 20.4px">
							<div class="kt-label" style="margin-bottom: 6.8px">{{ __("Targets") }}</div>
							<table class="kt-table" data-testid="str-targets-table">
								<thead><tr><th>{{ __("Period") }}</th><th>{{ __("Target") }}</th><th v-if="editable">{{ __("Action") }}</th></tr></thead>
								<tbody>
									<tr v-for="t in selected.children" :key="t.id" data-testid="str-target-row" :data-pending="isPending(t.id) ? 'true' : 'false'">
										<td>{{ t.period_label || "—" }}</td>
										<td data-testid="str-target-result">{{ t.result_label || "—" }}</td>
										<td v-if="editable">
											<button type="button" class="kt-btn kt-btn-ghost" style="padding: 2px 8px; font-size: 12px; height: auto" data-testid="str-target-edit" @click="openTargetEditor(t)">{{ __("Edit") }}</button>
											<button v-if="deletionAllowed || isPending(t.id)" type="button" class="kt-btn kt-btn-ghost" style="padding: 2px 8px; font-size: 12px; height: auto; color: var(--kt-status-critical)" data-testid="str-target-delete" @click="removeTarget(t)">{{ __("Remove") }}</button>
										</td>
									</tr>
									<tr v-if="!selected.children.length"><td :colspan="editable ? 3 : 2" class="kt-muted">{{ __("No target yet.") }}</td></tr>
								</tbody>
							</table>
							<div v-if="editable" style="display: flex; justify-content: flex-end; margin-top: 6.8px">
								<button type="button" class="kt-btn kt-btn-secondary" style="font-size: 12px; padding: 5px 12px; height: auto" data-testid="str-add-target" @click="addChild({ parent: selected, childType: 'Performance Target' })">{{ __("Add target") }}</button>
							</div>

							<!-- STR-DES-05-AddTarget — inline pending target editor; the page's Save changes commits it. -->
							<div v-if="targetEditor.open && editingTarget" class="kt-panel" style="margin-top: 10px" data-testid="str-target-editor">
								<div class="kt-dialog-title" style="font-size: 16px">{{ targetEditor.isNew ? __("Add performance target") : __("Edit performance target") }}</div>
								<p class="kt-muted" style="font-size: 13px; margin: 4px 0 10px">{{ __("Set the expected value and period for this indicator.") }}</p>
								<div class="kt-field">
									<label for="str-target-mode">{{ __("Set target for") }}</label>
									<div style="display: flex; gap: 8px; align-items: center; flex-wrap: wrap">
										<select id="str-target-mode" v-model="targetEditor.mode" class="kt-input" style="width: 170px" data-testid="str-target-mode">
											<option value="fiscal_year">{{ __("Financial year") }}</option>
											<option value="target_by_date">{{ __("Target date") }}</option>
										</select>
										<select v-if="targetEditor.mode === 'fiscal_year'" v-model="targetEditor.fiscal_year" class="kt-input" style="width: 200px" data-testid="str-target-period" :aria-label="__('Financial year')">
											<option value="">{{ __("Select a financial year") }}</option>
											<option v-for="fy in fiscalYears" :key="fy.name" :value="fy.name">{{ fy.label }}</option>
										</select>
										<input v-else v-model="targetEditor.target_by_date" class="kt-input" type="date" style="width: 200px" data-testid="str-target-date" :aria-label="__('Target date')" />
									</div>
								</div>
								<div class="kt-field" style="margin-top: 10px">
									<label for="str-target-comparison">{{ __("Target") }}</label>
									<div style="display: flex; gap: 8px; align-items: center">
										<select id="str-target-comparison" v-model="targetEditor.comparison" class="kt-input" style="width: 130px" data-testid="str-target-comparison">
											<option>At least</option><option>At most</option><option>Equal to</option>
										</select>
										<input v-model="targetEditor.target_value" class="kt-input" type="number" style="width: 110px" data-testid="str-target-value" :aria-label="__('Target value')" />
										<span class="kt-label" data-testid="str-target-unit">{{ unitSuffix || "—" }}</span>
									</div>
								</div>
								<p v-if="targetEditor.error" class="kt-field-error" data-testid="str-add-target-error" style="font-size: 13px">{{ targetEditor.error }}</p>
								<div style="display: flex; gap: 8px; justify-content: flex-end; margin-top: 10px">
									<button v-if="targetEditor.isNew" type="button" class="kt-btn kt-btn-ghost" style="margin-right: auto" data-testid="str-target-discard" @click="discardNewTarget">{{ __("Discard new target") }}</button>
									<button type="button" class="kt-btn kt-btn-secondary" @click="targetEditor.isNew ? discardNewTarget() : closeTargetEditor()">{{ __("Cancel") }}</button>
									<button type="button" class="kt-btn kt-btn-primary" data-testid="str-target-confirm" @click="applyTargetEditor">{{ targetEditor.isNew ? __("Add target") : __("Update target") }}</button>
								</div>
							</div>
						</div>
					</template>

					<template v-else>
						<div class="kt-field">
							<label for="str-node-title">{{ selectedTypeLabel }}</label>
							<input id="str-node-title" v-model="selected.title" class="kt-input" data-testid="str-node-title" :disabled="!editable" />
							<div v-if="selected.node_type === 'Strategic Objective'" class="kt-field-hint">{{ __("State what the plan aims to achieve.") }}</div>
						</div>
						<div v-if="editable" style="display: flex; gap: 6.8px; margin-top: 13.6px">
							<button type="button" class="kt-move-btn" :disabled="!canMoveUp" data-testid="str-move-up" @click="move('up')">{{ __("Move up") }}</button>
							<button type="button" class="kt-move-btn" :disabled="!canMoveDown" data-testid="str-move-down" @click="move('down')">{{ __("Move down") }}</button>
						</div>
					</template>

					<div v-if="editable" style="display: flex; justify-content: space-between; gap: 10.2px; margin-top: 20.4px">
						<button type="button" class="kt-btn kt-btn-secondary kt-danger" :disabled="saving || submitting" data-testid="str-node-delete" @click="askDelete">
							{{ __("Delete {0}", [selectedTypeLabel.toLowerCase()]) }}
						</button>
						<button type="button" class="kt-btn kt-btn-primary" :disabled="saving || submitting" data-testid="str-node-save" @click="save">{{ __("Save changes") }}</button>
					</div>
				</template>
				<p v-else class="kt-muted" style="margin: 0">{{ working.length ? __("Select an item to view or edit it.") : __("Add a pillar to start the plan structure.") }}</p>
			</div>
		</div>

		<ConfirmDialog
			:open="confirmDialog === 'delete'"
			:title="deleteBlockedReason ? __('This item cannot be deleted yet') : __('Delete {0}?', [selected ? (selected.title || selectedTypeLabel.toLowerCase()) : ''])"
			:message="deleteBlockedReason || __('It will be removed when you save your changes.')"
			:confirm-label="deleteBlockedReason ? __('OK') : __('Delete {0}', [selectedTypeLabel.toLowerCase()])"
			:danger="!deleteBlockedReason"
			@confirm="confirmDelete"
			@cancel="confirmDialog = null"
		/>
		<ConfirmDialog
			:open="confirmDialog === 'unsaved'"
			:title="__('You have unsaved changes')"
			:message="__('Save them before leaving, or discard them. Discarding affects only unsaved work.')"
			:confirm-label="__('Save changes')"
			:secondary-label="__('Discard unsaved changes')"
			:cancel-label="__('Stay here')"
			testid="str-unsaved-dialog"
			@confirm="guardSave"
			@secondary="guardDiscard"
			@cancel="guardStay"
		/>
		<datalist id="kt-indicator-units">
			<option v-for="u in indicatorUnits" :key="u" :value="u"></option>
		</datalist>
	</div>
</template>
