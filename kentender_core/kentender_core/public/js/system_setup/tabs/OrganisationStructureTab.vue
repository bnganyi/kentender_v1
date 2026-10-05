<script setup>
// The Organisation structure tab, ported from C05-Organisation-Structure.dc.html
// (AUTH-DES-01/02/08 and CFG v0.14 §10.12's missing-root and ambiguous
// variants, D24).
//
// The tree is the Frappe tree control mounted inside the section — expand,
// collapse and keyboard traversal are the framework's, never reimplemented
// in Vue (AUTH v1.9 §13.1: the board draws it as a static list only to fix
// the spacing around it). Vue owns the rest: the selected unit's facts and
// actions, the dialogs and the states.
//
// The selected unit is part of the link (`#organisation-structure/{unit}`),
// so reload and Back return to it.
import { nextTick, onMounted, onUnmounted, reactive, ref, watch } from "vue";
import { onSetupRevalidate } from "../composables/useRouteState.js";
import ConfirmDialog from "../components/ConfirmDialog.vue";
import PromptDialog from "../components/PromptDialog.vue";
import UnitDetail from "../components/UnitDetail.vue";
import { orgStructureApi } from "../data/orgStructureApi.js";
import { siteConfigApi } from "../data/siteConfigApi.js";

const props = defineProps({
	// §6/§11.1 — the Administrator-only repair authority, from the server's
	// own capability projection rather than a role guess in the browser.
	canRepair: { type: Boolean, default: false },
	// The unit named by the link; empty selects the root.
	unitId: { type: String, default: "" },
});
const emit = defineEmits(["repaired", "view-affected", "open"]);

const loading = ref(true);
const busy = ref(false);
const loadError = ref("");
const state = ref("");
const conflicts = ref([]);
const rootId = ref("");
// The tree control only knows the root's label; its code and status ride
// along from the structure payload so the root row reads like every other.
const rootMeta = ref(null);
const selected = ref(null);
const treeEl = ref(null);
const dialog = reactive({ kind: "", value: "", error: "" });
// The control that opened a dialog, so closing it returns focus there.
let trigger = null;

let treeWidget = null;
let active = true;
// frappe.ui.Tree fires on_click for a reloaded parent, and for the root as it
// expands it on load; neither is a person choosing a unit, and following
// them would rewrite the link (a reload on a unit's link would jump to the
// root). Only an on_click shortly after a real click in the tree counts —
// the control runs its own handler 100ms after the click.
let reloading = false;
let lastUserClick = 0;
const USER_CLICK_WINDOW_MS = 1000;
function noteUserClick() {
	lastUserClick = Date.now();
}

// Chevrons on expandable rows and nothing on leaves, not Frappe's folder/dot
// icons. frappe.ui.Tree accepts a custom icon_set; the class="icon" hook is
// what tree.js swaps on expand/collapse.
const TREE_ICONS = {
	open: '<svg class="icon kt-tree-chevron" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="m6 9 6 6 6-6"></path></svg>',
	closed: '<svg class="icon kt-tree-chevron" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="m9 6 6 6-6 6"></path></svg>',
	leaf: '<span class="kt-tree-leaf-spacer"></span>',
};

async function load() {
	loading.value = true;
	loadError.value = "";
	try {
		const result = await orgStructureApi.getStructure(props.unitId || "");
		if (!active) return;
		state.value = result.state;
		conflicts.value = result.conflicts || [];
		rootId.value = result.root || "";
		rootMeta.value = (result.tree && result.tree[0]) || null;
		selected.value = result.selected || null;
	} catch (error) {
		loadError.value = error.message;
		state.value = "";
	} finally {
		loading.value = false;
	}
	if (state.value === "ready") {
		// The tree host only exists once the loading line is gone.
		await nextTick();
		mountTree();
	}
}

function mountTree() {
	if (!treeEl.value || !rootId.value) return;
	treeEl.value.innerHTML = "";
	// eslint-disable-next-line no-undef
	treeWidget = new frappe.ui.Tree({
		parent: $(treeEl.value),
		label: selectedRootLabel(),
		root_value: rootId.value,
		method: "kentender_core.api.organisation_structure_api.tree_children",
		// frappe.ui.Tree reads args.doctype when rendering node anchors; the
		// endpoint accepts and ignores it.
		args: { doctype: "Organisation Unit" },
		expandable: true,
		icon_set: TREE_ICONS,
		with_skeleton: 0,
		get_label: (node) => node.data?.label || node.label,
		on_render: (node) => {
			// Every row ends with its code and a status badge; the root uses
			// the structure payload's own record.
			const data = node.is_root ? rootMeta.value || {} : node.data || {};
			const code = data.unit_code || data.code || "";
			const status = data.status || "";
			if (!code && !status) return;
			const meta = document.createElement("span");
			meta.className = "kt-tree-meta";
			if (code) {
				const chip = document.createElement("span");
				chip.className = "kt-tree-code";
				chip.textContent = code;
				meta.appendChild(chip);
			}
			const badge = document.createElement("span");
			badge.className =
				status === "Active" ? "kt-status is-live kt-tree-badge" : "kt-status is-pending kt-tree-badge";
			badge.textContent = status === "Active" ? __("Active") : __("Inactive");
			meta.appendChild(badge);
			node.$tree_link?.append(meta);
		},
		on_click: (node) => {
			if (!active || reloading || Date.now() - lastUserClick > USER_CLICK_WINDOW_MS) return;
			// A node's record id lives in node.data.value (the root's label is
			// its display name, not its id).
			const value = (node.data && node.data.value) || node.value;
			if (value && value !== selected.value?.id) emit("open", value);
		},
	});
	highlight(selected.value?.id);
}

function selectedRootLabel() {
	if (selected.value && selected.value.is_root) return selected.value.name;
	return rootMeta.value?.name || rootId.value;
}

function highlight(unitId) {
	const node = treeNodeFor(unitId);
	if (!node || !treeWidget) return;
	treeWidget.select_link(node);
	treeWidget.set_selected_node(node);
}

// A stale response must never clobber a newer one — e.g. the framework's own
// on_click side effect during reload_node() fires for the reloaded parent.
let selectSeq = 0;

async function select(unitId) {
	const seq = ++selectSeq;
	try {
		const unit = await orgStructureApi.getUnit(unitId);
		if (!active || seq !== selectSeq) return;
		selected.value = unit;
		highlight(unit.id);
	} catch (error) {
		if (!active || seq !== selectSeq) return;
		loadError.value = error.message;
	}
}

// The link names the selection: follow it (Back, a tree click, a reload).
watch(
	() => props.unitId,
	(unitId) => {
		if (state.value !== "ready") return;
		const wanted = unitId || rootId.value;
		if (wanted && wanted !== selected.value?.id) select(wanted);
	}
);

function treeNodeFor(unitId) {
	if (!treeWidget || !unitId) return null;
	// The root node's key in frappe.ui.Tree is its display label, not its id.
	if (unitId === rootId.value) return treeWidget.root_node;
	return treeWidget.nodes[unitId] || null;
}

function updateNodeDisplay(node, unit) {
	node.data = { ...(node.data || {}), value: node.data?.value ?? unit.id, label: unit.name, unit_code: unit.code, status: unit.status };
	if (node.is_root) {
		rootMeta.value = { ...(rootMeta.value || {}), name: unit.name, unit_code: unit.code, status: unit.status };
	}
	const label = node.$tree_link && node.$tree_link.find(".tree-label");
	if (label && label.length) label.html(` ${treeWidget.get_node_label(node)}`);
	node.$tree_link && node.$tree_link.find(".kt-tree-meta").remove();
	treeWidget.on_render && treeWidget.on_render(node);
}

// Only the part of the tree that changed is refreshed. Rebuilding the whole
// widget collapses every expanded branch back to the root and, on a long
// tree, shrinks the page past the browser's unchanged scroll position.
async function afterStructureChange({ parentId = null, focusUnit, updateNodeOnly = false } = {}) {
	if (!treeWidget) {
		await load();
		emit("open", focusUnit);
		return;
	}
	if (!updateNodeOnly) {
		const parentNode = treeNodeFor(parentId);
		if (!parentNode) {
			await load();
			emit("open", focusUnit);
			return;
		}
		// A childless node renders as a leaf; force it back to "has children"
		// before the reload, or frappe.ui.Tree's own expand logic — gated on
		// this flag — leaves the freshly loaded child hidden.
		parentNode.expandable = true;
		reloading = true;
		try {
			await treeWidget.reload_node(parentNode);
		} finally {
			reloading = false;
		}
	}
	const seq = ++selectSeq;
	try {
		const unit = await orgStructureApi.getUnit(focusUnit);
		if (!active || seq !== selectSeq) return;
		selected.value = unit;
		const node = treeNodeFor(focusUnit);
		if (node && updateNodeOnly) updateNodeDisplay(node, unit);
		highlight(focusUnit);
		emit("open", focusUnit);
	} catch (error) {
		if (!active || seq !== selectSeq) return;
		loadError.value = error.message;
	}
}

function openDialog(kind) {
	trigger = document.activeElement;
	dialog.kind = kind;
	dialog.error = "";
	dialog.value = kind === "rename" ? selected.value?.name || "" : "";
}
async function closeDialog() {
	dialog.kind = "";
	dialog.value = "";
	dialog.error = "";
	await nextTick();
	if (trigger && trigger.isConnected) trigger.focus();
	trigger = null;
}

async function run(action) {
	busy.value = true;
	dialog.error = "";
	try {
		await action();
		trigger = null;
		await closeDialog();
	} catch (error) {
		dialog.error = error.message;
	} finally {
		busy.value = false;
	}
}

const addUnit = () =>
	run(async () => {
		const wasEmpty = state.value === "empty_root";
		const parentId = selected.value?.id || rootId.value;
		const result = await orgStructureApi.addUnit(parentId, dialog.value);
		if (wasEmpty) {
			// The empty state has no tree yet; the first unit brings it in.
			await load();
			emit("open", result.unit);
			return;
		}
		await afterStructureChange({ parentId, focusUnit: result.unit });
	});
const renameUnit = () =>
	run(async () => {
		const unitId = selected.value.id;
		await orgStructureApi.renameUnit(unitId, dialog.value, selected.value.expected_version);
		await afterStructureChange({ focusUnit: unitId, updateNodeOnly: true });
	});
const setActive = (value) =>
	run(async () => {
		const unitId = selected.value.id;
		await orgStructureApi.setActive(unitId, value, selected.value.expected_version);
		await afterStructureChange({ focusUnit: unitId, updateNodeOnly: true });
	});

async function repair() {
	busy.value = true;
	loadError.value = "";
	try {
		await siteConfigApi.repairRoot();
		emit("repaired");
		emit("open", "");
		await load();
	} catch (error) {
		loadError.value = error.message;
	} finally {
		busy.value = false;
	}
}

// Kept alive by the root: a return to this tab re-reads the selected unit in
// place. The tree keeps its expanded branches — re-mounting it would not.
onSetupRevalidate(() => {
	if (state.value === "ready" && selected.value) select(selected.value.id);
	else load();
});
onMounted(load);
onUnmounted(() => {
	active = false;
	treeWidget = null;
});
</script>

<template>
	<section class="kt-setup-section is-flow" data-testid="kt-setup-org">
		<div class="kt-eyebrow">{{ __("System setup") }}</div>
		<h2 style="margin:4px 0 6px">{{ __("Organisation structure") }}</h2>
		<p class="card-body" style="margin:0 0 24px;max-width:70ch">
			{{ __("Maintain the departments and organisational units used to scope KenTender responsibilities.") }}
		</p>

		<div v-if="loading" role="status" aria-live="polite" data-testid="kt-org-loading">
			<p class="text-muted" style="margin:0 0 10px">{{ __("Loading organisation structure…") }}</p>
			<div class="kt-skel" style="width:80%" />
			<div class="kt-skel" style="width:64%" />
		</div>

		<div v-else-if="loadError" class="kt-notice is-critical" role="alert" data-testid="kt-org-error">
			<svg class="kt-notice-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><path d="M18 6L6 18M6 6l12 12" /></svg>
			<div class="kt-notice-body"><strong>{{ __("System setup could not be loaded.") }}</strong> {{ __("Try again. If the problem continues, contact support.") }}</div>
			<button type="button" class="btn btn-secondary" @click="load">{{ __("Try again") }}</button>
		</div>

		<!-- CFG §10.12 missing root: the governed repair for the Administrator,
		     the escalation for a System Manager; never an empty tree. -->
		<div v-else-if="state === 'needs_repair'" class="kt-notice is-critical" role="alert" style="align-items:flex-start" data-testid="kt-org-needs-repair">
			<svg class="kt-notice-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><path d="M18 6L6 18M6 6l12 12" /></svg>
			<div class="kt-notice-body kt-notice-stack">
				<strong>{{ __("Organisation structure needs repair") }}</strong>
				<span>{{ __("The top-level organisation unit is missing.") }}</span>
				<span v-if="!canRepair" data-testid="kt-org-repair-escalation">{{ __("Ask an Administrator to repair it.") }}</span>
				<button
					v-if="canRepair"
					type="button"
					class="btn btn-primary"
					style="margin-top:6px"
					:disabled="busy"
					data-testid="kt-org-repair"
					@click="repair"
				>{{ __("Repair organisation root") }}</button>
			</div>
		</div>

		<!-- CFG §10.12 ambiguous structure: no repair action for either role. -->
		<div v-else-if="state === 'ambiguous'" class="kt-notice is-critical" role="alert" style="align-items:flex-start" data-testid="kt-org-ambiguous">
			<svg class="kt-notice-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><path d="M18 6L6 18M6 6l12 12" /></svg>
			<div class="kt-notice-body kt-notice-stack">
				<strong>{{ __("Organisation structure needs repair") }}</strong>
				<span>{{ __("The organisation structure cannot be repaired automatically.") }}</span>
				<span>{{ __("Contact support with the listed conflicts.") }}</span>
				<ul class="kt-org-conflicts" data-testid="kt-org-conflicts">
					<li v-for="conflict in conflicts" :key="conflict">{{ conflict }}</li>
				</ul>
			</div>
		</div>

		<!-- AUTH-DES-08 empty: the root exists with nothing beneath it. -->
		<div v-else-if="state === 'empty_root'" class="kt-org-empty" data-testid="kt-org-empty">
			<svg width="34" height="34" viewBox="0 0 24 24" fill="none" stroke="var(--kt-color-neutral-400)" stroke-width="1.5" aria-hidden="true" style="margin:0 auto 12px"><path d="M12 3v6" /><rect x="8" y="3" width="8" height="6" /><path d="M5 15v-3h14v3" /><rect x="2" y="15" width="6" height="6" /><rect x="16" y="15" width="6" height="6" /></svg>
			<p style="font-weight:600;margin:0 0 4px">{{ __("No departments or units yet") }}</p>
			<p class="card-body" style="margin:0 0 16px">{{ __("Add the first organisation unit beneath {0}.", [selected ? selected.name : rootId]) }}</p>
			<button type="button" class="btn btn-primary" data-testid="kt-org-empty-add" @click="openDialog('add')">
				<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><path d="M12 5v14M5 12h14" /></svg>{{ __("Add organisation unit") }}
			</button>
		</div>

		<!-- AUTH-DES-01: the tree beside the selected unit. -->
		<div v-else-if="state === 'ready'" class="kt-org-columns" data-testid="kt-org-tree">
			<div ref="treeEl" class="kt-org-tree-host" :aria-label="__('Organisation units')" @click.capture="noteUserClick" />
			<UnitDetail
				v-if="selected"
				:unit="selected"
				:busy="busy"
				@add="openDialog('add')"
				@rename="openDialog('rename')"
				@deactivate="openDialog('deactivate')"
				@reactivate="openDialog('reactivate')"
				@view-affected="emit('view-affected', selected.id)"
			/>
		</div>

		<!-- AUTH-DES-02 -->
		<PromptDialog
			v-if="dialog.kind === 'add'"
			v-model="dialog.value"
			:title="__('Add organisation unit')"
			:label="__('Organisation unit name')"
			:confirm-label="__('Add organisation unit')"
			:context="[{ label: __('Parent organisation unit'), value: selected ? selected.path.join(' › ') : '' }]"
			:hint="__('The unit code is generated when you save.')"
			:error="dialog.error"
			:busy="busy"
			@confirm="addUnit"
			@cancel="closeDialog"
		/>
		<PromptDialog
			v-if="dialog.kind === 'rename'"
			v-model="dialog.value"
			:title="__('Edit name')"
			:label="__('Organisation unit name')"
			:confirm-label="__('Save name')"
			:context="[{ label: __('Code'), value: selected ? selected.code : '' }]"
			:error="dialog.error"
			:busy="busy"
			@confirm="renameUnit"
			@cancel="closeDialog"
		/>
		<ConfirmDialog
			v-if="dialog.kind === 'deactivate'"
			:title="__('Deactivate this organisation unit?')"
			:body="selected && selected.active_assignments
				? __('{0} active responsibility assignments name this unit. It will no longer be offered for new assignments; history remains visible.', [selected.active_assignments])
				: __('The unit will no longer be offered for new assignments. History remains visible.')"
			:confirm-label="__('Deactivate')"
			destructive
			:error="dialog.error"
			:busy="busy"
			@confirm="setActive(false)"
			@cancel="closeDialog"
		/>
		<ConfirmDialog
			v-if="dialog.kind === 'reactivate'"
			:title="__('Reactivate this organisation unit?')"
			:body="__('The unit becomes available for new responsibility assignments again.')"
			:confirm-label="__('Reactivate')"
			:error="dialog.error"
			:busy="busy"
			@confirm="setActive(true)"
			@cancel="closeDialog"
		/>
	</section>
</template>
