<script setup>
// Recursive flat-indented hierarchy renderer shared by the Plan workspace
// (read-only), the Structure editor (editable), and the Review task
// (read-only) — STR-DES-04/05/07/10b. Matches the `tree` shape returned by
// kentender_strategy.api.strategy_ui_api.get_strategy_tree.
import { ref } from "vue";

const props = defineProps({
	nodes: { type: Array, required: true },
	depth: { type: Number, default: 0 },
	selectedId: { type: String, default: null },
	readOnly: { type: Boolean, default: false },
});
const emit = defineEmits(["select", "add-child"]);

const DOT_COLOR = {
	Pillar: "#003d9b",
	Programme: "#003d9b",
	"Sub-programme": "#003d9b",
	"Strategic Objective": "#047857",
	"Strategic Outcome": "#047857",
	"Performance Indicator": "#92610a",
	"Performance Target": "#92610a",
};

// STR-DES-04 per-type node icons (same SVG paths as the Structure summary
// figures on the Overview tab) — ported verbatim so the tree row icon and
// the summary card icon for a given node type are always the same glyph.
const NODE_ICON = {
	Pillar: '<rect x="4" y="4" width="6" height="16"/><rect x="14" y="4" width="6" height="16"/>',
	Programme:
		'<path d="m12.83 2.18 8.58 3.9a1 1 0 0 1 0 1.83l-8.58 3.9a2 2 0 0 1-1.66 0L2.6 7.91a1 1 0 0 1 0-1.83z"/><path d="M2 12a1 1 0 0 0 .58.91l8.6 3.91a2 2 0 0 0 1.65 0l8.58-3.9A1 1 0 0 0 22 12"/><path d="M2 17a1 1 0 0 0 .58.91l8.6 3.91a2 2 0 0 0 1.65 0l8.58-3.9A1 1 0 0 0 22 17"/>',
	"Sub-programme":
		'<line x1="6" y1="3" x2="6" y2="15"/><circle cx="18" cy="6" r="3"/><circle cx="6" cy="18" r="3"/><path d="M18 9a9 9 0 0 1-9 9"/>',
	"Strategic Objective": '<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="5"/><circle cx="12" cy="12" r="1"/>',
	"Strategic Outcome":
		'<path d="M4 15s1-1 4-1 5 2 8 2 4-1 4-1V3s-1 1-4 1-5-2-8-2-4 1-4 1z"/><line x1="4" y1="22" x2="4" y2="15"/>',
	"Performance Indicator": '<path d="M22 12h-4l-3 9L9 3l-3 9H2"/>',
	"Performance Target":
		'<circle cx="12" cy="12" r="10"/><line x1="12" y1="2" x2="12" y2="6"/><line x1="12" y1="18" x2="12" y2="22"/><line x1="2" y1="12" x2="6" y2="12"/><line x1="18" y1="12" x2="22" y2="12"/>',
};

const CHILD_TYPE = {
	Pillar: "Programme",
	Programme: "Sub-programme",
	"Sub-programme": "Strategic Objective",
	"Strategic Objective": "Strategic Outcome",
};
const CAN_ADD_INDICATOR = new Set(["Strategic Objective", "Strategic Outcome"]);

function dot(nodeType) {
	return DOT_COLOR[nodeType] || "#666";
}
function icon(nodeType) {
	return NODE_ICON[nodeType] || '<circle cx="12" cy="12" r="9"/>';
}

// STR-DES-04b: collapse/expand affordance per row. Purely a local rendering
// decision for whichever recursion level owns this node's row — no need to
// share state across the recursive component boundary.
const collapsed = ref(new Set());
function hasChildren(node) {
	return Boolean(node.children && node.children.length);
}
function isCollapsed(node) {
	return collapsed.value.has(node.id);
}
function toggleCollapse(node, event) {
	event.stopPropagation();
	const next = new Set(collapsed.value);
	if (next.has(node.id)) next.delete(node.id);
	else next.add(node.id);
	collapsed.value = next;
}
function countDescendants(node) {
	if (!node.children) return 0;
	return node.children.reduce((sum, c) => sum + 1 + countDescendants(c), 0);
}
function canAddChild(node) {
	return !props.readOnly && (Boolean(CHILD_TYPE[node.node_type]) || CAN_ADD_INDICATOR.has(node.node_type));
}
function addChildLabel(node) {
	if (node.node_type === "Performance Indicator") return "Add target";
	if (CAN_ADD_INDICATOR.has(node.node_type)) return "Add indicator";
	return "Add child";
}
function onAddChild(node) {
	if (node.node_type === "Performance Indicator") {
		emit("add-child", { parent: node, childType: "Performance Target" });
	} else if (CAN_ADD_INDICATOR.has(node.node_type) && !CHILD_TYPE[node.node_type]) {
		emit("add-child", { parent: node, childType: "Performance Indicator" });
	} else {
		emit("add-child", { parent: node, childType: CHILD_TYPE[node.node_type] });
	}
}
</script>

<template>
	<template v-for="node in nodes" :key="node.id">
		<div
			class="kt-tree-row"
			:class="{ selected: node.id === selectedId }"
			:style="{ paddingLeft: `${8 + depth * 20}px` }"
			@click="$emit('select', node)"
		>
			<template v-if="depth > 0">
				<span class="kt-tree-line-v" :style="{ left: `${8 + depth * 20 - 11}px` }"></span>
				<span class="kt-tree-line-h" :style="{ left: `${8 + depth * 20 - 11}px` }"></span>
			</template>
			<button
				v-if="hasChildren(node)"
				type="button"
				class="kt-tree-toggle"
				:class="{ collapsed: isCollapsed(node) }"
				@click.stop="toggleCollapse(node, $event)"
			>
				<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="9 18 15 12 9 6"></polyline></svg>
			</button>
			<span v-else class="kt-tree-toggle-spacer"></span>
			<svg
				width="15"
				height="15"
				viewBox="0 0 24 24"
				fill="none"
				:stroke="dot(node.node_type)"
				stroke-width="1.5"
				stroke-linecap="round"
				stroke-linejoin="round"
				style="flex-shrink: 0"
				v-html="icon(node.node_type)"
			></svg>
			<span>{{ node.title }}</span>
			<span v-if="isCollapsed(node)" class="kt-tree-hidden-count">({{ countDescendants(node) }} {{ __("hidden") }})</span>
			<span class="kt-tree-type">{{ node.node_type }}</span>
			<button
				v-if="canAddChild(node)"
				type="button"
				class="kt-add-child"
				@click.stop="onAddChild(node)"
			>
				{{ addChildLabel(node) }}
			</button>
		</div>
		<StructureTree
			v-if="hasChildren(node) && !isCollapsed(node)"
			:nodes="node.children"
			:depth="depth + 1"
			:selected-id="selectedId"
			:read-only="readOnly"
			@select="$emit('select', $event)"
			@add-child="$emit('add-child', $event)"
		/>
	</template>
</template>
