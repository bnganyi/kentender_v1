<script setup>
import { ref, reactive, computed, watch, onMounted } from "vue";
import { useRouteState } from "../strategy_shared/composables/useRouteState.js";
import StructureTree from "../strategy_shared/components/StructureTree.vue";
import ConfirmDialog from "../strategy_shared/components/ConfirmDialog.vue";
import {
	getPlanWorkspace,
	getPlanHistory,
	getStrategyTree,
	saveStructureDraft,
	submitVersion,
	activateVersion,
} from "./data/strategyPlanApi.js";

const { route, go } = useRouteState("strategy-plan-workspace");
const planId = computed(() => route.value[1] || null);
const tab = computed(() => route.value[2] || "overview");

const loading = ref(true);
const notFound = ref(false);
const forbidden = ref(false);
const workspace = ref(null);
const tree = ref({ tree: [], counts: {} });
const history = ref([]);
const historyLoaded = ref(false);
const actionError = ref(null);
const acting = ref(false);

function statusClass(status) {
	if (["Active", "Approved"].includes(status)) return "is-live";
	if (["In Review", "Awaiting Approval"].includes(status)) return "is-pending";
	return "is-draft";
}

async function loadWorkspace() {
	if (!planId.value) return;
	loading.value = true;
	notFound.value = false;
	forbidden.value = false;
	actionError.value = null;
	try {
		const data = await getPlanWorkspace(planId.value);
		if (data.not_found) {
			notFound.value = true;
		} else if (data.forbidden) {
			forbidden.value = true;
		} else {
			workspace.value = data;
			if (!data.no_version) {
				tree.value = await getStrategyTree(data.current_version.id);
			}
		}
	} catch (e) {
		actionError.value = e.message || String(e);
	} finally {
		loading.value = false;
	}
}

async function loadHistory() {
	if (!planId.value || historyLoaded.value) return;
	history.value = await getPlanHistory(planId.value);
	historyLoaded.value = true;
}

watch(planId, loadWorkspace, { immediate: true });
watch(tab, (t) => {
	if (t === "history") loadHistory();
});

function switchTab(t) {
	go(planId.value, t);
}

const confirmDialog = ref(null); // 'activate' | 'submit' | null

async function doActivate() {
	if (!workspace.value?.pending_version) return;
	acting.value = true;
	actionError.value = null;
	confirmDialog.value = null;
	try {
		await activateVersion(workspace.value.pending_version.id);
		frappe.show_alert({ message: __("Version activated"), indicator: "green" });
		await loadWorkspace();
	} catch (e) {
		actionError.value = e.message || String(e);
	} finally {
		acting.value = false;
	}
}

async function doSubmit() {
	if (!workspace.value?.current_version) return;
	acting.value = true;
	actionError.value = null;
	confirmDialog.value = null;
	try {
		await submitVersion(workspace.value.current_version.id);
		frappe.show_alert({ message: __("Submitted for review"), indicator: "green" });
		await loadWorkspace();
	} catch (e) {
		actionError.value = e.message || String(e);
	} finally {
		acting.value = false;
	}
}

// --- Structure editor state (STR-UI-03) ---
const selectedNode = ref(null);
const editForm = reactive({});
const creatingChildOf = ref(null); // { parent, childType } while composing a new node/indicator/target
const savingNode = ref(false);

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
}

function startAddChild({ parent, childType }) {
	selectedNode.value = null;
	creatingChildOf.value = { parent, childType };
	Object.assign(editForm, {
		title: "",
		display_order: (parent.children ? parent.children.length : 0) + 1,
		indicator_name: "",
		definition: "",
		unit: "",
		comparison: "At least",
		target_value: "",
		financial_year_id: "",
	});
}

const currentVersionId = computed(() => workspace.value?.current_version?.id);

async function refreshTree() {
	tree.value = await getStrategyTree(currentVersionId.value);
}

async function saveNodeEdit() {
	if (!selectedNode.value || !currentVersionId.value) return;
	savingNode.value = true;
	actionError.value = null;
	try {
		if (selectedNode.value.node_type === "Performance Indicator") {
			await saveStructureDraft(currentVersionId.value, {
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
			await saveStructureDraft(currentVersionId.value, {
				nodes: [{ name: selectedNode.value.id, title: editForm.title, display_order: editForm.display_order }],
			});
		}
		frappe.show_alert({ message: __("Changes saved"), indicator: "green" });
		await refreshTree();
	} catch (e) {
		actionError.value = e.message || String(e);
	} finally {
		savingNode.value = false;
	}
}

async function deleteSelectedNode() {
	if (!selectedNode.value || !currentVersionId.value) return;
	const doctype = selectedNode.value.node_type === "Performance Indicator" ? "Performance Indicator" : "Strategy Node";
	savingNode.value = true;
	actionError.value = null;
	try {
		await saveStructureDraft(currentVersionId.value, { deletes: [{ doctype, name: selectedNode.value.id }] });
		selectedNode.value = null;
		await refreshTree();
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
			await saveStructureDraft(currentVersionId.value, {
				indicators: [
					{
						measures_node_id: parent.id,
						indicator_name: editForm.indicator_name,
						definition: editForm.definition,
						unit: editForm.unit,
					},
				],
			});
		} else if (childType === "Performance Target") {
			await saveStructureDraft(currentVersionId.value, {
				targets: [
					{
						indicator_id: parent.id,
						comparison: editForm.comparison,
						target_value: editForm.target_value,
						financial_year_id: editForm.financial_year_id || null,
					},
				],
			});
		} else {
			await saveStructureDraft(currentVersionId.value, {
				nodes: [
					{
						node_type: childType,
						parent_node_id: parent.id,
						title: editForm.title,
						display_order: editForm.display_order,
					},
				],
			});
		}
		frappe.show_alert({ message: __("Added"), indicator: "green" });
		creatingChildOf.value = null;
		await refreshTree();
	} catch (e) {
		actionError.value = e.message || String(e);
	} finally {
		savingNode.value = false;
	}
}

async function addPillar() {
	startAddChild({ parent: { id: null, children: tree.value.tree }, childType: "Pillar" });
}

async function saveNewPillar() {
	savingNode.value = true;
	actionError.value = null;
	try {
		await saveStructureDraft(currentVersionId.value, {
			nodes: [{ node_type: "Pillar", parent_node_id: null, title: editForm.title, display_order: editForm.display_order }],
		});
		creatingChildOf.value = null;
		await refreshTree();
	} catch (e) {
		actionError.value = e.message || String(e);
	} finally {
		savingNode.value = false;
	}
}
</script>

<template>
	<div class="kt-strategy-ui">
		<div class="kt-shell">
			<div v-if="loading">{{ __("Loading...") }}</div>
			<div v-else-if="notFound" class="kt-card kt-empty">
				<h3>{{ __("This plan could not be found.") }}</h3>
			</div>
			<div v-else-if="forbidden" class="kt-card kt-empty">
				<h3>{{ __("You do not have access to this plan.") }}</h3>
			</div>
			<template v-else-if="workspace">
				<header style="display: flex; justify-content: space-between; align-items: flex-start">
					<div>
						<div class="kt-text-muted" style="text-transform: uppercase; font-size: 11px">
							{{ workspace.plan.reference }}
						</div>
						<h1 style="font-size: 28px; display: inline-flex; align-items: center; gap: 10px">
							{{ workspace.plan.title }}
							<span class="kt-status" :class="statusClass(workspace.current_version.status)">
								{{ workspace.current_version.status }}
							</span>
						</h1>
					</div>
					<button
						v-if="workspace.capabilities.activate"
						type="button"
						class="kt-btn kt-btn-primary"
						:disabled="acting"
						@click="confirmDialog = 'activate'"
					>
						{{ __("Activate version") }}
					</button>
				</header>

				<p v-if="actionError" style="color: var(--ktstr-color-danger)">{{ actionError }}</p>

				<div class="kt-tabs">
					<div class="kt-tab" :class="{ active: tab === 'overview' }" @click="switchTab('overview')">{{ __("Overview") }}</div>
					<div class="kt-tab" :class="{ active: tab === 'structure' }" @click="switchTab('structure')">{{ __("Structure") }}</div>
					<div class="kt-tab" :class="{ active: tab === 'history' }" @click="switchTab('history')">{{ __("History") }}</div>
				</div>

				<template v-if="tab === 'overview'">
					<div v-if="workspace.no_version" class="kt-card kt-empty">
						<h3>{{ __("This plan has no version yet.") }}</h3>
					</div>
					<template v-else>
						<div style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px">
							<div class="kt-card">
								<div class="kt-card-title">{{ workspace.pending_version ? __("Version authority") : __("Plan identity") }}</div>
								<template v-if="workspace.pending_version">
									<div class="kv-row"><span class="kv-label">{{ __("Plan period") }}</span><span class="kv-value">{{ workspace.plan.period_label }}</span></div>
									<div class="kv-row"><span class="kv-label">{{ __("Version effective period") }}</span><span class="kv-value">{{ workspace.pending_version.effective_period_label || "—" }}</span></div>
									<div class="kv-row"><span class="kv-label">{{ __("Approved by") }}</span><span class="kv-value">{{ workspace.version_authority.approved_by?.actor || "—" }}</span></div>
									<div class="kv-row"><span class="kv-label">{{ __("Current Active version") }}</span><span class="kv-value">{{ workspace.version_authority.current_active_version ? `Version ${workspace.version_authority.current_active_version.version_number}` : "—" }}</span></div>
								</template>
								<template v-else>
									<div class="kv-row"><span class="kv-label">{{ __("Procuring Entity") }}</span><span class="kv-value">{{ workspace.plan.procuring_entity?.name }}</span></div>
									<div class="kv-row"><span class="kv-label">{{ __("Plan role") }}</span><span class="kv-value">{{ workspace.plan.plan_role }}</span></div>
									<div class="kv-row"><span class="kv-label">{{ __("Plan period") }}</span><span class="kv-value">{{ workspace.plan.period_label }}</span></div>
									<div class="kv-row"><span class="kv-label">{{ __("Active version") }}</span><span class="kv-value">{{ workspace.active_version ? `Version ${workspace.active_version.version_number}` : "—" }}</span></div>
									<div class="kv-row"><span class="kv-label">{{ __("Version effective period") }}</span><span class="kv-value">{{ workspace.current_version.effective_period_label || "—" }}</span></div>
								</template>
							</div>
							<div class="kt-card">
								<div class="kt-card-title">{{ workspace.pending_version ? __("Activation readiness") : __("Current authority") }}</div>
								<template v-if="workspace.pending_version && workspace.readiness">
									<div v-for="c in workspace.readiness.checks" :key="c.check" class="kv-row">
										<span class="kv-label">{{ c.check }}</span>
										<span class="kt-status is-live">{{ c.ready ? __("Ready") : __("Not ready") }}</span>
									</div>
								</template>
								<template v-else-if="workspace.current_authority">
									<div class="kv-row"><span class="kv-label">{{ __("Approved by") }}</span><span class="kv-value">{{ workspace.current_authority.approved_by?.actor || "—" }}</span></div>
									<div class="kv-row"><span class="kv-label">{{ __("Activated") }}</span><span class="kv-value">{{ workspace.current_authority.activated?.actor || "—" }}</span></div>
								</template>
								<p v-else class="kt-text-muted">{{ __("No authority events recorded yet.") }}</p>
							</div>
							<div class="kt-card" style="grid-column: 1 / -1">
								<div class="kt-card-title">{{ __("Structure summary") }}</div>
								<div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px">
									<div><div class="kv-label">{{ __("Pillars") }}</div><div style="font-size: 22px">{{ workspace.structure_summary.pillars }}</div></div>
									<div><div class="kv-label">{{ __("Programmes") }}</div><div style="font-size: 22px">{{ workspace.structure_summary.programmes }}</div></div>
									<div><div class="kv-label">{{ __("Sub-programmes") }}</div><div style="font-size: 22px">{{ workspace.structure_summary.sub_programmes }}</div></div>
									<div><div class="kv-label">{{ __("Strategic objectives") }}</div><div style="font-size: 22px">{{ workspace.structure_summary.strategic_objectives }}</div></div>
									<div><div class="kv-label">{{ __("Strategic outcomes") }}</div><div style="font-size: 22px">{{ workspace.structure_summary.strategic_outcomes }}</div></div>
									<div><div class="kv-label">{{ __("Performance indicators") }}</div><div style="font-size: 22px">{{ workspace.structure_summary.performance_indicators }}</div></div>
									<div><div class="kv-label">{{ __("Performance targets") }}</div><div style="font-size: 22px">{{ workspace.structure_summary.performance_targets }}</div></div>
								</div>
							</div>
						</div>
					</template>
				</template>

				<template v-else-if="tab === 'structure'">
					<div style="display: flex; justify-content: flex-end; gap: 12px" v-if="workspace.is_editable_draft">
						<button type="button" class="kt-btn kt-btn-primary" :disabled="acting" @click="confirmDialog = 'submit'">
							{{ __("Submit for review") }}
						</button>
					</div>
					<div style="display: flex; gap: 16px; align-items: flex-start">
						<div class="kt-card" style="width: 42%">
							<div style="display: flex; justify-content: space-between; align-items: center">
								<div class="kt-card-title">{{ __("Plan hierarchy") }}</div>
								<button v-if="workspace.is_editable_draft" type="button" class="kt-add-child" @click="addPillar">
									{{ __("Add pillar") }}
								</button>
							</div>
							<StructureTree
								:nodes="tree.tree"
								:selected-id="selectedNode?.id"
								:read-only="!workspace.is_editable_draft"
								@select="selectNode"
								@add-child="startAddChild"
							/>
							<p v-if="!tree.tree.length" class="kt-text-muted">{{ __("No structure yet.") }}</p>
						</div>
						<div class="kt-card" style="width: 58%">
							<template v-if="creatingChildOf">
								<div class="kt-card-title">{{ __("New") }} {{ creatingChildOf.childType }}</div>
								<template v-if="creatingChildOf.childType === 'Performance Indicator'">
									<div class="kt-field"><label>{{ __("Indicator name") }}</label><input v-model="editForm.indicator_name" class="kt-input" /></div>
									<div class="kt-field"><label>{{ __("Definition") }}</label><textarea v-model="editForm.definition" class="kt-input" rows="2"></textarea></div>
									<div class="kt-field"><label>{{ __("Unit") }}</label><input v-model="editForm.unit" class="kt-input" /></div>
								</template>
								<template v-else-if="creatingChildOf.childType === 'Performance Target'">
									<div class="kt-field"><label>{{ __("Financial year") }}</label><input v-model="editForm.financial_year_id" class="kt-input" placeholder="FY id" /></div>
									<div class="kt-field"><label>{{ __("Comparison") }}</label>
										<select v-model="editForm.comparison" class="kt-input">
											<option>At least</option><option>At most</option><option>Equal to</option>
										</select>
									</div>
									<div class="kt-field"><label>{{ __("Target value") }}</label><input v-model="editForm.target_value" class="kt-input" type="number" /></div>
								</template>
								<template v-else>
									<div class="kt-field"><label>{{ __("Title") }}</label><input v-model="editForm.title" class="kt-input" /></div>
									<div class="kt-field"><label>{{ __("Display order") }}</label><input v-model="editForm.display_order" class="kt-input" type="number" /></div>
								</template>
								<div style="display: flex; justify-content: flex-end; gap: 12px">
									<button type="button" class="kt-btn kt-btn-ghost" @click="creatingChildOf = null">{{ __("Cancel") }}</button>
									<button
										type="button"
										class="kt-btn kt-btn-primary"
										:disabled="savingNode"
										@click="creatingChildOf.childType === 'Pillar' ? saveNewPillar() : saveNewChild()"
									>
										{{ __("Save changes") }}
									</button>
								</div>
							</template>
							<template v-else-if="selectedNode">
								<div class="kt-card-title">{{ selectedNode.node_type }}</div>
								<template v-if="selectedNode.node_type === 'Performance Indicator'">
									<div class="kt-field"><label>{{ __("Indicator name") }}</label><input v-model="editForm.indicator_name" class="kt-input" :disabled="!workspace.is_editable_draft" /></div>
									<div class="kt-field"><label>{{ __("Definition") }}</label><textarea v-model="editForm.definition" class="kt-input" rows="2" :disabled="!workspace.is_editable_draft"></textarea></div>
									<div class="kt-field"><label>{{ __("Unit") }}</label><input v-model="editForm.unit" class="kt-input" :disabled="!workspace.is_editable_draft" /></div>
									<div class="kt-card-title" style="margin-top: 16px">{{ __("Targets") }}</div>
									<table class="kt-table">
										<thead><tr><th>{{ __("Period") }}</th><th>{{ __("Expected result") }}</th></tr></thead>
										<tbody>
											<tr v-for="t in selectedNode.children" :key="t.id">
												<td>{{ t.period_label || "—" }}</td>
												<td>{{ t.comparison }} {{ t.target_value }}</td>
											</tr>
										</tbody>
									</table>
									<button
										v-if="workspace.is_editable_draft"
										type="button"
										class="kt-btn kt-btn-secondary"
										style="margin-top: 8px"
										@click="startAddChild({ parent: selectedNode, childType: 'Performance Target' })"
									>
										{{ __("Add target") }}
									</button>
								</template>
								<template v-else-if="selectedNode.node_type !== 'Performance Target'">
									<div class="kt-field"><label>{{ __("Title") }}</label><input v-model="editForm.title" class="kt-input" :disabled="!workspace.is_editable_draft" /></div>
									<div class="kt-field"><label>{{ __("Display order") }}</label><input v-model="editForm.display_order" class="kt-input" type="number" :disabled="!workspace.is_editable_draft" /></div>
								</template>
								<div v-if="workspace.is_editable_draft && selectedNode.node_type !== 'Performance Target'" style="display: flex; justify-content: space-between">
									<button type="button" class="kt-btn kt-btn-danger-outline" :disabled="savingNode" @click="deleteSelectedNode">
										{{ selectedNode.node_type === "Performance Indicator" ? __("Delete indicator") : __("Delete node") }}
									</button>
									<button type="button" class="kt-btn kt-btn-primary" :disabled="savingNode" @click="saveNodeEdit">
										{{ __("Save changes") }}
									</button>
								</div>
							</template>
							<p v-else class="kt-text-muted">{{ __("Select a hierarchy item to view or edit it.") }}</p>
						</div>
					</div>
				</template>

				<template v-else-if="tab === 'history'">
					<div class="kt-card">
						<div class="kt-card-title">{{ __("Version history") }}</div>
						<table class="kt-table">
							<thead><tr><th>{{ __("Date and time") }}</th><th>{{ __("Event") }}</th><th>{{ __("Actor") }}</th></tr></thead>
							<tbody>
								<tr v-for="(h, i) in history" :key="i">
									<td>{{ h.at }}</td>
									<td><span class="kt-status is-draft">{{ h.event }}</span></td>
									<td>{{ h.actor }}</td>
								</tr>
							</tbody>
						</table>
						<p v-if="!history.length" class="kt-text-muted">{{ __("No events recorded yet.") }}</p>
					</div>
				</template>
			</template>
		</div>

		<ConfirmDialog
			:open="confirmDialog === 'activate'"
			:title="__('Activate this version?')"
			:message="__('The currently Active version will be superseded. This cannot be undone.')"
			:confirm-label="__('Activate version')"
			@confirm="doActivate"
			@cancel="confirmDialog = null"
		/>
		<ConfirmDialog
			:open="confirmDialog === 'submit'"
			:title="__('Submit this version for review?')"
			:message="__('The draft will move to In Review and can no longer be edited until returned.')"
			:confirm-label="__('Submit for review')"
			@confirm="doSubmit"
			@cancel="confirmDialog = null"
		/>
	</div>
</template>
