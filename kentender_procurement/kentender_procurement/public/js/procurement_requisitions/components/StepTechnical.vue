<!-- REQ-DES-05 Step 3: Technical and support (§13.7), ported class-for-class:
     the "All items" / per-item tabs, the technical characteristics table
     (every row the catalogue makes available for this Draft's equipment
     categories, Confirmed or still amber "Proposed" per §13.6A), the "Add
     characteristic" dialog trigger, and the warranty-and-support panel. -->
<template>
	<div class="req-step-content">
		<div class="req-seg" role="tablist" v-if="tabs.length > 1">
			<label v-for="tab in tabs" :key="tab.key" class="req-seg-opt">
				<input type="radio" name="req-tech-tab" :checked="activeTab === tab.key" @change="activeTab = tab.key" />{{ tab.label }}
			</label>
		</div>

		<div class="req-step-content-header">
			<div class="kt-card-title req-no-margin">Technical characteristics</div>
			<button type="button" class="kt-btn kt-btn-secondary" data-testid="req-add-characteristic" @click="$emit('add-characteristic')">Add characteristic</button>
		</div>

		<table class="kt-table" data-testid="req-technical-table">
			<thead>
				<tr>
					<th>Characteristic</th>
					<th>Comparison</th>
					<th>Required value</th>
					<th>Unit</th>
					<th>Status</th>
					<th></th>
				</tr>
			</thead>
			<tbody>
				<tr v-for="row in visibleRows" :key="row.technical_requirement_id">
					<td>{{ characteristicLabel(row.characteristic_key) }}</td>
					<td>{{ row.comparison }}</td>
					<td>{{ requiredValueText(row) }}</td>
					<td>{{ row.unit || "—" }}</td>
					<td>
						<span class="kt-status" :class="row.row_status === 'Confirmed' ? 'is-live' : 'is-attention'">{{ row.row_status }}</span>
					</td>
					<td>
						<a v-if="row.row_status === 'Proposed'" href="#" class="req-quiet-link req-confirm-link" :data-testid="`req-confirm-${row.technical_requirement_id}`" @click.prevent="$emit('confirm-requirement', row)">Confirm</a>
						<template v-if="row.row_status === 'Proposed'"> · </template>
						<a href="#" class="req-quiet-link" @click.prevent="$emit('remove-requirement', row)">Remove</a>
					</td>
				</tr>
				<tr v-if="!visibleRows.length">
					<td colspan="6" class="req-empty-row">No technical characteristics yet.</td>
				</tr>
			</tbody>
		</table>

		<div class="kt-card-title">Warranty and support</div>
		<div class="req-field-grid-3">
			<div class="kt-field">
				<label for="tech-warranty">Minimum warranty</label>
				<input id="tech-warranty" type="number" min="0" step="1" class="kt-input" :value="fields.minimum_warranty_months" @input="fields.minimum_warranty_months = Number($event.target.value)" /> <span class="kt-muted">months</span>
			</div>
			<div class="kt-field">
				<label id="tech-onsite-lbl">On-site support required</label>
				<div class="req-seg" role="radiogroup" aria-labelledby="tech-onsite-lbl">
					<label class="req-seg-opt"><input type="radio" :checked="fields.onsite_support_required" @change="fields.onsite_support_required = true" />Yes</label>
					<label class="req-seg-opt"><input type="radio" :checked="!fields.onsite_support_required" @change="fields.onsite_support_required = false" />No</label>
				</div>
			</div>
			<div class="kt-field">
				<label for="tech-response">Maximum support response</label>
				<input id="tech-response" type="number" min="0" step="1" class="kt-input" :value="fields.maximum_support_response_hours" @input="fields.maximum_support_response_hours = Number($event.target.value)" /> <span class="kt-muted">hours</span>
			</div>
			<div class="kt-field">
				<label id="tech-mfr-lbl">Manufacturer support required</label>
				<div class="req-seg" role="radiogroup" aria-labelledby="tech-mfr-lbl">
					<label class="req-seg-opt"><input type="radio" :checked="fields.manufacturer_support_required" @change="fields.manufacturer_support_required = true" />Yes</label>
					<label class="req-seg-opt"><input type="radio" :checked="!fields.manufacturer_support_required" @change="fields.manufacturer_support_required = false" />No</label>
				</div>
			</div>
			<div class="kt-field">
				<label for="tech-service-location">Service location constraint</label>
				<select id="tech-service-location" class="kt-input" :value="fields.service_location_constraint" @change="fields.service_location_constraint = $event.target.value">
					<option value="None">None</option>
					<option value="Within Kenya">Within Kenya</option>
					<option value="At delivery location">At delivery location</option>
				</select>
			</div>
		</div>
		<div class="kt-field">
			<label for="tech-support-desc">Support description</label>
			<textarea id="tech-support-desc" class="kt-input" rows="2" maxlength="500" :value="fields.support_description" @input="fields.support_description = $event.target.value"></textarea>
		</div>
	</div>
</template>

<script setup>
import { computed, reactive, ref, watch } from "vue";

const props = defineProps({
	editor: { type: Object, required: true },
});

defineEmits(["add-characteristic", "confirm-requirement", "remove-requirement"]);

const items = computed(() => (props.editor.package || {}).items || []);
const technicalRequirements = computed(() => (props.editor.package || {}).technical_requirements || []);
const catalogueByKey = computed(() => {
	const map = {};
	for (const c of (props.editor.catalogue || {}).characteristics || []) map[c.key] = c;
	return map;
});

// §13.7 — "All items" plus one tab per distinct item name (two item rows
// sharing the same name, the fixture's own case, collapse into one tab; a
// row scoped to a specific item still shows on that item's own tab).
const tabs = computed(() => {
	const byName = new Map();
	for (const item of items.value) {
		if (!byName.has(item.item_name)) byName.set(item.item_name, new Set());
		byName.get(item.item_name).add(item.requisition_item_id);
	}
	return [{ key: "__all__", label: "All items", itemIds: null }, ...Array.from(byName, ([name, ids]) => ({ key: name, label: name, itemIds: ids }))];
});
const activeTab = ref("__all__");
watch(tabs, (next) => {
	if (!next.some((t) => t.key === activeTab.value)) activeTab.value = "__all__";
});

const visibleRows = computed(() => {
	const tab = tabs.value.find((t) => t.key === activeTab.value);
	if (!tab || !tab.itemIds) return technicalRequirements.value;
	return technicalRequirements.value.filter((r) => r.applies_to_scope === "All items" || tab.itemIds.has(r.applies_to_id));
});

function characteristicLabel(key) {
	return (catalogueByKey.value[key] || {}).label || key;
}

function requiredValueText(row) {
	if (row.required_value_display) return row.required_value_display;
	if (!row.required_value_json) return "Not yet set";
	try {
		const parsed = JSON.parse(row.required_value_json);
		if (parsed.ports) return parsed.ports.map((p) => `${p.port_type} ×${p.minimum_count}`).join(", ");
		if (parsed.values) return parsed.values.join(", ");
		if (parsed.value === "Other" && parsed.other) return parsed.other;
		return String(parsed.value ?? "");
	} catch (e) {
		return "";
	}
}

const fields = reactive({
	minimum_warranty_months: 0,
	onsite_support_required: false,
	maximum_support_response_hours: 0,
	manufacturer_support_required: false,
	service_location_constraint: "None",
	support_description: "",
});

function hydrate() {
	const p = props.editor.package || {};
	fields.minimum_warranty_months = p.minimum_warranty_months || 0;
	fields.onsite_support_required = !!p.onsite_support_required;
	fields.maximum_support_response_hours = p.maximum_support_response_hours || 0;
	fields.manufacturer_support_required = !!p.manufacturer_support_required;
	fields.service_location_constraint = p.service_location_constraint || "None";
	fields.support_description = p.support_description || "";
}

// AGENTS.md §6.4 — an editor never re-hydrates from an in-place refresh that
// carries nothing new — guarded on the package's own record_version, exactly
// like StepDrawdown's guard on the Version's.
watch(() => (props.editor.package || {}).record_version, hydrate, { immediate: true });

function getPayload() {
	return { ...fields };
}

defineExpose({ getPayload });
</script>
