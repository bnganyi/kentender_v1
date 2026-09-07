<!-- REQ-DES-04 Step 2: Equipment items (§13.6/§13.6A), ported class-for-
     class: the item table (one row per drawdown line — an item links to
     exactly one drawdown line, never several, §5.6), the "Add equipment
     item" button, and one baseline-proposal banner per item, shown the
     moment the item is added, each row independently Confirm/Remove-able
     while still amber "Proposed" (never silently already-confirmed). -->
<template>
	<div class="req-step-content">
		<div class="req-step-content-header">
			<div class="kt-card-title req-no-margin">Equipment items</div>
			<button type="button" class="kt-btn kt-btn-secondary" data-testid="req-add-item" @click="$emit('add-item')">Add equipment item</button>
		</div>

		<table class="kt-table" data-testid="req-items-table">
			<thead>
				<tr>
					<th>Item</th>
					<th>Planning source</th>
					<th>Category</th>
					<th class="req-num">Quantity</th>
					<th>Intended use</th>
					<th>Delivery</th>
					<th></th>
				</tr>
			</thead>
			<tbody>
				<tr v-for="item in items" :key="item.requisition_item_id">
					<td>{{ item.item_name }}</td>
					<td>{{ item.plan_item_line_id }}</td>
					<td>{{ item.equipment_category }}</td>
					<td class="req-num">{{ item.quantity }} {{ item.unit }}</td>
					<td>{{ item.intended_use }}</td>
					<td>{{ deliveryLabel(item) }}</td>
					<td>
						<a href="#" class="req-quiet-link" @click.prevent="$emit('edit-item', item)">Edit</a>
						·
						<a href="#" class="req-quiet-link" @click.prevent="$emit('remove-item', item)">Remove</a>
					</td>
				</tr>
			</tbody>
		</table>

		<div
			v-for="group in baselineGroups"
			:key="group.itemId"
			class="kt-card kt-blueprint req-card-pad-tight"
			:data-testid="`req-baseline-banner-${group.itemId}`"
		>
			<i class="kt-corner tl"></i><i class="kt-corner tr"></i><i class="kt-corner bl"></i><i class="kt-corner br"></i>
			<div class="req-baseline-intro">
				<strong>{{ group.rows.length }} baseline characteristic{{ group.rows.length === 1 ? "" : "s" }} proposed</strong>
				for {{ group.itemName }} ({{ group.planSourceId }}).
			</div>
			<table class="kt-table">
				<thead>
					<tr>
						<th>Characteristic</th>
						<th>Comparison</th>
						<th>Proposed value</th>
						<th>Status</th>
					</tr>
				</thead>
				<tbody>
					<tr v-for="row in group.rows" :key="row.technical_requirement_id">
						<td>{{ characteristicLabel(row.characteristic_key) }}</td>
						<td>{{ row.comparison }}</td>
						<td>{{ proposedValue(row) }}</td>
						<td>
							<span class="kt-status is-attention">Proposed</span>
							<a href="#" class="req-quiet-link req-confirm-link" :data-testid="`req-confirm-${row.technical_requirement_id}`" @click.prevent="$emit('confirm-requirement', row)">Confirm</a>
							·
							<a href="#" class="req-quiet-link" @click.prevent="$emit('remove-requirement', row)">Remove</a>
						</td>
					</tr>
				</tbody>
			</table>
		</div>
	</div>
</template>

<script setup>
import { computed } from "vue";

const props = defineProps({
	editor: { type: Object, required: true },
});

defineEmits(["add-item", "edit-item", "remove-item", "confirm-requirement", "remove-requirement"]);

const items = computed(() => (props.editor.package || {}).items || []);
const technicalRequirements = computed(() => (props.editor.package || {}).technical_requirements || []);
const catalogueByKey = computed(() => {
	const map = {};
	for (const c of (props.editor.catalogue || {}).characteristics || []) map[c.key] = c;
	return map;
});

function characteristicLabel(key) {
	return (catalogueByKey.value[key] || {}).label || key;
}

function proposedValue(row) {
	if (!row.required_value_json) return "";
	try {
		const parsed = JSON.parse(row.required_value_json);
		return parsed.value ?? parsed.other ?? "";
	} catch (e) {
		return "";
	}
}

function deliveryLabel(item) {
	const parts = [];
	if (item.delivery_location) parts.push(item.delivery_location);
	if (item.latest_delivery_date) parts.push(item.latest_delivery_date);
	return parts.join(" · ");
}

// REQ-DES-04/13.6A — one banner per item, only its own row-status="Proposed"
// characteristics that actually carry a suggested value (a characteristic
// proposed with no default — e.g. Memory, Storage capacity — waits for
// Step 3's own typed entry instead of appearing here as something to
// confirm-or-remove at a glance).
const baselineGroups = computed(() => {
	const groups = [];
	for (const item of items.value) {
		const rows = technicalRequirements.value.filter(
			(r) => r.applies_to_id === item.requisition_item_id && r.row_status === "Proposed" && r.required_value_json
		);
		if (rows.length) groups.push({ itemId: item.requisition_item_id, itemName: item.item_name, planSourceId: item.plan_item_line_id, rows });
	}
	return groups;
});
</script>
