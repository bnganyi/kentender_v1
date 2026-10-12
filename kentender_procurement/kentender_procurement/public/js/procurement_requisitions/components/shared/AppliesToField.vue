<!-- REQ-CHG-001 v1.18 §13.6A — what a service or acceptance row applies to: every item, one kind of item
     (a set sharing a specification) or one item. Hidden while the request has a single item. -->
<template>
	<div v-if="options.length > 1" class="field">
		<label :for="id">Applies to</label>
		<select :id="id" :value="selectedKey" class="input" data-testid="req-applies-to" @change="choose($event.target.value)">
			<option v-for="o in options" :key="o.key" :value="o.key">{{ o.label }}</option>
		</select>
	</div>
</template>

<script setup>
import { computed } from "vue";

const props = defineProps({
	view: { type: Object, required: true },
	scope: { type: String, default: "All items" },
	itemId: { type: String, default: "" },
	itemIds: { type: Array, default: () => [] },
	// A service-scoped acceptance check keeps its scope; this field does not offer it.
	keepService: { type: Boolean, default: false },
});
const emit = defineEmits(["update"]);
const id = `req-applies-${Math.random().toString(36).slice(2, 8)}`;

const items = computed(() => (props.view.equipment || {}).rows || []);
const options = computed(() => {
	const rows = items.value;
	if (rows.length < 2) return [];
	const out = [{ key: "all", label: "All items", scope: "All items", id: "", ids: [] }];
	for (const g of (props.view.equipment || {}).groups || []) {
		const n = (g.requisition_item_ids || []).length;
		if (n > 1 && n < rows.length) out.push({ key: `g:${g.group_id}`, label: `${g.item_name} — all ${n} requirements`, scope: "Items", id: g.requisition_item_ids[0], ids: g.requisition_item_ids });
	}
	for (const r of rows) out.push({ key: `i:${r.requisition_item_id}`, label: `${r.item_name} — ${r.approved_requirement}`, scope: "Item", id: r.requisition_item_id, ids: [r.requisition_item_id] });
	return out;
});
const selectedKey = computed(() => {
	if (props.scope === "Item") return `i:${props.itemId}`;
	if (props.scope === "Items") {
		const hit = options.value.find((o) => o.scope === "Items" && o.ids.length === props.itemIds.length && o.ids.every((i) => props.itemIds.includes(i)));
		return hit ? hit.key : "all";
	}
	return "all";
});
function choose(key) {
	const o = options.value.find((x) => x.key === key);
	if (o) emit("update", { applies_to_scope: o.scope, applies_to_id: o.id, applies_to_item_ids: o.ids });
}
</script>
