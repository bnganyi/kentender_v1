<script setup>
// AUTH-ADR-001 v1.6 §13.2/§14.1 — the Organisation structure tab.
//
// The tree is the Frappe tree control mounted inside the section — expand,
// collapse and keyboard traversal are the framework's, never reimplemented
// in Vue (§18.1, "Do not rebuild the Frappe tree control in Vue"). Vue owns
// the surrounding composition: the detail panel, dialogs and states, all
// ported from AUTH-DES-01/02 and the AUTH-DES-08 state copy.
import { nextTick, onMounted, onUnmounted, reactive, ref } from "vue";
import ConfirmDialog from "../components/ConfirmDialog.vue";
import PromptDialog from "../components/PromptDialog.vue";
import UnitDetail from "../components/UnitDetail.vue";
import { orgStructureApi } from "../data/orgStructureApi.js";
import { siteConfigApi } from "../data/siteConfigApi.js";

const emit = defineEmits(["repaired", "view-affected"]);

const loading = ref(true);
const busy = ref(false);
const loadError = ref("");
const state = ref("");
const rootId = ref("");
// AUTH-DES-01 renders the root row like every other: name, code chip,
// status badge. The tree control only knows the root's label, so its code
// and status ride along from the structure payload.
const rootMeta = ref(null);
const selected = ref(null);
const treeEl = ref(null);
const dialog = reactive({ kind: "", value: "", error: "" });

let treeWidget = null;
let active = true;

// AUTH-DES-01 draws 12px chevrons on expandable rows and nothing on leaves —
// not Frappe's folder/dot icons. frappe.ui.Tree accepts a custom icon_set;
// the class="icon" hook is what tree.js swaps on expand/collapse.
const TREE_ICONS = {
	open: '<svg class="icon kt-tree-chevron" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="m6 9 6 6 6-6"></path></svg>',
	closed: '<svg class="icon kt-tree-chevron" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="m9 6 6 6-6 6"></path></svg>',
	leaf: '<span class="kt-tree-leaf-spacer"></span>',
};

async function load({ keepSelection = true } = {}) {
	loading.value = true;
	loadError.value = "";
	try {
		const result = await orgStructureApi.getStructure(
			keepSelection && selected.value ? selected.value.id : ""
		);
		if (!active) return;
		state.value = result.state;
		rootId.value = result.root || "";
		rootMeta.value = (result.tree && result.tree[0]) || null;
		selected.value = result.selected || null;
	} catch (error) {
		loadError.value = error.message;
		state.value = "";
	} finally {
		loading.value = false;
	}
	if (state.value === "ready" || state.value === "empty_root") {
		// The tree host only exists once the loading card is gone, so the
		// Frappe tree mounts after the post-loading render settles.
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
			// AUTH-DES-01 — every row ends with its code chip and a status
			// badge; the root uses the structure payload's own record.
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
			if (!active) return;
			// A node's record id lives in node.data.value (the root's label is
			// its display name, not its id).
			const value = (node.data && node.data.value) || node.value;
			if (value) select(value);
		},
	});
}

function selectedRootLabel() {
	// The root node renders its unit name; the server projection carries it
	// when the root is the current selection, else fall back to the id.
	if (selected.value && selected.value.is_root) return selected.value.name;
	return rootId.value;
}

async function select(unitId) {
	try {
		selected.value = await orgStructureApi.getUnit(unitId);
	} catch (error) {
		loadError.value = error.message;
	}
}

function openDialog(kind) {
	dialog.kind = kind;
	dialog.error = "";
	dialog.value = kind === "rename" ? selected.value?.name || "" : "";
}
function closeDialog() {
	dialog.kind = "";
	dialog.value = "";
	dialog.error = "";
}

async function run(action, { reload = true } = {}) {
	busy.value = true;
	dialog.error = "";
	try {
		await action();
		closeDialog();
		if (reload) await load();
	} catch (error) {
		dialog.error = error.message;
	} finally {
		busy.value = false;
	}
}

const addUnit = () => run(() => orgStructureApi.addUnit(selected.value?.id || rootId.value, dialog.value));
const renameUnit = () =>
	run(() => orgStructureApi.renameUnit(selected.value.id, dialog.value, selected.value.expected_version));
const deactivateUnit = () =>
	run(() => orgStructureApi.setActive(selected.value.id, false, selected.value.expected_version));
const reactivateUnit = () =>
	run(() => orgStructureApi.setActive(selected.value.id, true, selected.value.expected_version));

async function repair() {
	busy.value = true;
	loadError.value = "";
	try {
		await siteConfigApi.repairRoot();
		emit("repaired");
		await load({ keepSelection: false });
	} catch (error) {
		loadError.value = error.message;
	} finally {
		busy.value = false;
	}
}

onMounted(load);
onUnmounted(() => {
	active = false;
	treeWidget = null;
});
</script>

<template>
	<section class="kt-setup-section" data-testid="kt-setup-org">
		<div class="kt-section-head">
			<div>
				<h2 class="kt-section-title">{{ __("Organisation structure") }}</h2>
				<p class="kt-muted">
					{{ __("Maintain the departments and organisational units used to scope KenTender responsibilities.") }}
				</p>
			</div>
		</div>

		<div v-if="loading" class="kt-card kt-blueprint" data-testid="kt-org-loading">
			<i class="kt-corner tl" /><i class="kt-corner tr" /><i class="kt-corner bl" /><i class="kt-corner br" />
			<span class="kt-eyebrow">{{ __("Loading") }}</span>
			<div class="kt-skel" style="width:80%" />
			<div class="kt-skel" style="width:64%" />
		</div>

		<div v-else-if="loadError" class="kt-card kt-blueprint kt-empty" data-testid="kt-org-error">
			<i class="kt-corner tl" /><i class="kt-corner tr" /><i class="kt-corner bl" /><i class="kt-corner br" />
			<h2>{{ __("System setup could not be loaded") }}</h2>
			<p>{{ __("Try again. If the problem continues, contact support.") }}</p>
			<button type="button" class="kt-btn kt-btn-secondary" @click="load">{{ __("Try again") }}</button>
		</div>

		<!-- AUTH-DES-08 — missing root; never an empty successful tree -->
		<div v-else-if="state === 'needs_repair'" class="kt-card kt-blueprint kt-empty" data-testid="kt-org-needs-repair">
			<i class="kt-corner tl" /><i class="kt-corner tr" /><i class="kt-corner bl" /><i class="kt-corner br" />
			<h2>{{ __("Organisation structure needs repair") }}</h2>
			<p>{{ __("The root organisation unit is missing. Run the governed repair before assigning responsibilities.") }}</p>
			<button
				type="button"
				class="kt-btn kt-btn-secondary"
				:disabled="busy"
				data-testid="kt-org-repair"
				@click="repair"
			>{{ __("Run governed repair") }}</button>
		</div>

		<template v-else>
			<!-- AUTH-DES-08 — root exists with no children -->
			<div v-if="state === 'empty_root'" class="kt-setup-notice" data-testid="kt-org-empty">
				<h3>{{ __("No departments or units yet") }}</h3>
				<p>{{ __("Add the first organisation unit beneath {0}.", [selected ? selected.name : rootId]) }}</p>
			</div>

			<div class="kt-org-columns">
				<div class="kt-card kt-blueprint kt-org-tree-card" data-testid="kt-org-tree">
					<i class="kt-corner tl" /><i class="kt-corner tr" /><i class="kt-corner bl" /><i class="kt-corner br" />
					<div class="kt-card-title">{{ __("Organisation units") }}</div>
					<div ref="treeEl" class="kt-org-tree-host" />
				</div>
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
		</template>

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
			@confirm="deactivateUnit"
			@cancel="closeDialog"
		/>
		<ConfirmDialog
			v-if="dialog.kind === 'reactivate'"
			:title="__('Reactivate this organisation unit?')"
			:body="__('The unit becomes available for new responsibility assignments again.')"
			:confirm-label="__('Reactivate')"
			:error="dialog.error"
			:busy="busy"
			@confirm="reactivateUnit"
			@cancel="closeDialog"
		/>
	</section>
</template>
