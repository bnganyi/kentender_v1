<script setup>
// Recursive hierarchy renderer shared by the Structure editor (editable) and
// the read-only views (Overview structure, Approval Proposed structure) —
// STR-DES-04/05/07. Ported class-for-class from STR-DES-04.dc.html: each
// node is two stacked lines — icon + bold title, then "· Type" and the
// trailing typed add action — and the parent/child connector is one
// border-left on the recursive children wrapper (.kt-tree-kids).
//
// v1.8 §11.4/§12.3: a Programme offers Add objective directly AND the
// optional Add sub-programme; every add action is typed; rows are
// keyboard-operable (Tab to a row, Enter/Space selects).
import { ref } from "vue";
import { iconPath, iconTone, typeLabel } from "../nodeIcons.js";

const props = defineProps({
	nodes: { type: Array, required: true },
	depth: { type: Number, default: 0 },
	selectedId: { type: String, default: null },
	readOnly: { type: Boolean, default: false },
});
const emit = defineEmits(["select", "add-child"]);

// STR-BR-007 — typed add actions per parent type; a Programme may parent an
// Objective directly when the optional Sub-programme is omitted.
const ADD_ACTIONS = {
	Pillar: [{ childType: "Programme", label: "Add programme" }],
	Programme: [
		{ childType: "Strategic Objective", label: "Add objective" },
		{ childType: "Sub-programme", label: "Add sub-programme" },
	],
	"Sub-programme": [{ childType: "Strategic Objective", label: "Add objective" }],
	"Strategic Objective": [{ childType: "Performance Indicator", label: "Add indicator" }],
	"Performance Indicator": [{ childType: "Performance Target", label: "Add target" }],
};

const COLLAPSIBLE_TYPES = new Set(["Pillar", "Programme", "Sub-programme", "Strategic Objective"]);

const collapsed = ref(new Set());
function hasChildren(node) {
	return Boolean(node.children && node.children.length);
}
function canCollapse(node) {
	return COLLAPSIBLE_TYPES.has(node.node_type) && hasChildren(node);
}
function isCollapsed(node) {
	return canCollapse(node) && collapsed.value.has(node.id);
}
function toggleCollapse(node) {
	const next = new Set(collapsed.value);
	if (next.has(node.id)) next.delete(node.id);
	else next.add(node.id);
	collapsed.value = next;
}
function countDescendants(node) {
	if (!node.children) return 0;
	return node.children.reduce((sum, c) => sum + 1 + countDescendants(c), 0);
}
function addActions(node) {
	if (props.readOnly) return [];
	return ADD_ACTIONS[node.node_type] || [];
}
function rowTitle(node) {
	if (node.node_type === "Performance Target") {
		return node.period_label ? `${node.result_label || node.title} · ${node.period_label}` : node.result_label || node.title;
	}
	return node.title || "";
}
function onRowKeydown(node, event) {
	if (event.key === "Enter" || event.key === " ") {
		event.preventDefault();
		emit("select", node);
	}
}
</script>

<template>
	<template v-for="node in nodes" :key="node.id">
		<div
			class="kt-tree-node"
			:class="{ selected: node.id === selectedId }"
			data-testid="str-tree-node"
			:data-node-type="node.node_type"
			:data-node-id="node.id"
			:data-pending="node.pending ? 'true' : 'false'"
			role="button"
			tabindex="0"
			:aria-pressed="node.id === selectedId ? 'true' : 'false'"
			@click="$emit('select', node)"
			@keydown="onRowKeydown(node, $event)"
		>
			<div class="kt-tree-row" :style="{ gap: canCollapse(node) ? '6px' : '8px' }">
				<button
					v-if="canCollapse(node)"
					type="button"
					class="kt-tree-toggle"
					:class="{ collapsed: isCollapsed(node) }"
					:aria-label="isCollapsed(node) ? __('Expand') : __('Collapse')"
					@click.stop="toggleCollapse(node)"
				>
					<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="9 18 15 12 9 6"></polyline></svg>
				</button>
				<svg
					width="15"
					height="15"
					viewBox="0 0 24 24"
					fill="none"
					:stroke="iconTone(node.node_type)"
					stroke-width="1.5"
					stroke-linecap="round"
					stroke-linejoin="round"
					style="flex-shrink: 0; margin-top: 2px"
					v-html="iconPath(node.node_type)"
				></svg>
				<strong class="kt-tree-title" :class="{ 'kt-muted': !node.title && node.node_type !== 'Performance Target' }">
					{{ rowTitle(node) || __("Untitled {0}", [typeLabel(node.node_type).toLowerCase()]) }}
				</strong>
			</div>
			<div class="kt-tree-meta" :style="{ paddingLeft: canCollapse(node) ? '33px' : '23px' }">
				<span class="kt-tree-type">
					&middot; {{ node.node_type }}
					<span v-if="node.pending" class="kt-tag kt-tag-accent" style="margin-left: 6px" data-testid="str-tree-pending">{{ __("Unsaved") }}</span>
					<span v-if="isCollapsed(node)" class="kt-tree-hidden-count">({{ countDescendants(node) }} {{ __("hidden") }})</span>
				</span>
				<span v-if="addActions(node).length" style="display: inline-flex; gap: 6px">
					<button
						v-for="action in addActions(node)"
						:key="action.childType"
						type="button"
						class="kt-add-child"
						data-testid="str-add-child"
						:data-child-type="action.childType"
						@click.stop="$emit('add-child', { parent: node, childType: action.childType })"
					>
						{{ __(action.label) }}
					</button>
				</span>
			</div>
		</div>
		<div v-if="hasChildren(node) && !isCollapsed(node)" class="kt-tree-kids">
			<StructureTree
				:nodes="node.children"
				:depth="depth + 1"
				:selected-id="selectedId"
				:read-only="readOnly"
				@select="$emit('select', $event)"
				@add-child="$emit('add-child', $event)"
			/>
		</div>
	</template>
</template>
