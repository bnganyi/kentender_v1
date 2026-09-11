<!-- REQ-DES-04's "Add equipment item" dialog (§13.6). Not in the artboard
     file itself (only the workspace/editor screens and the four decision
     dialogs are drawn there) — built on kt_industry_tokens.css's own shared
     .kt-dialog-backdrop/.kt-dialog chrome (the same one Planning's own
     ReasonDialog.vue uses), so it stays visually consistent with every
     other dialog in the application rather than inventing a competing
     dialog shell (AGENTS.md §6.6). AGENTS.md §6.3: an in-Vue dialog, never
     frappe.ui.Dialog on this Vue-owned surface. -->
<template>
	<div class="kt-dialog-backdrop" data-testid="req-item-dialog" @keydown.esc="$emit('cancel')">
		<div class="kt-dialog" role="dialog" aria-modal="true" ref="dialogEl" tabindex="-1">
			<div class="kt-dialog-title">{{ editing ? "Edit equipment item" : "Add equipment item" }}</div>

			<div class="kt-field">
				<label for="item-source">Planning source</label>
				<select id="item-source" class="kt-input" :value="fields.plan_item_line_id" @change="fields.plan_item_line_id = $event.target.value">
					<option value="" disabled>Select a drawdown line</option>
					<option v-for="line in drawdownLines" :key="line.drawdown_line_id" :value="line.drawdown_line_id">
						{{ line.organisation_unit_label }} — {{ line.source_title }}
					</option>
				</select>
				<p v-if="errors.plan_item_line_id" class="req-field-error">{{ errors.plan_item_line_id }}</p>
			</div>

			<div class="kt-field">
				<label for="item-category">Equipment category</label>
				<select id="item-category" class="kt-input" :value="fields.equipment_category" @change="fields.equipment_category = $event.target.value">
					<option value="" disabled>Select a category</option>
					<option v-for="category in equipmentCategories" :key="category" :value="category">{{ category }}</option>
				</select>
				<p v-if="errors.equipment_category" class="req-field-error">{{ errors.equipment_category }}</p>
			</div>

			<div class="kt-field">
				<label for="item-name">Item name</label>
				<input id="item-name" class="kt-input" :value="fields.item_name" @input="fields.item_name = $event.target.value" />
				<p v-if="errors.item_name" class="req-field-error">{{ errors.item_name }}</p>
			</div>

			<div class="req-field-grid">
				<div class="kt-field">
					<label for="item-quantity">Quantity</label>
					<input id="item-quantity" type="number" min="1" step="1" class="kt-input" :value="fields.quantity" @input="fields.quantity = Number($event.target.value)" />
					<p v-if="errors.quantity" class="req-field-error">{{ errors.quantity }}</p>
				</div>
				<div class="kt-field">
					<label for="item-unit">Unit</label>
					<input id="item-unit" class="kt-ro" value="Each" disabled />
				</div>
			</div>

			<div class="kt-field">
				<label for="item-use">Intended use</label>
				<textarea id="item-use" class="kt-input" rows="3" maxlength="500" :value="fields.intended_use" @input="fields.intended_use = $event.target.value"></textarea>
				<p v-if="errors.intended_use" class="req-field-error">{{ errors.intended_use }}</p>
			</div>

			<div class="req-field-grid">
				<div class="kt-field">
					<label for="item-location">Delivery location</label>
					<select id="item-location" class="kt-input" :value="fields.delivery_location" @change="fields.delivery_location = $event.target.value">
						<option v-for="loc in deliveryLocations" :key="loc.name" :value="loc.name">{{ loc.location_name }}</option>
					</select>
					<p v-if="errors.delivery_location" class="req-field-error">{{ errors.delivery_location }}</p>
				</div>
				<div class="kt-field">
					<label for="item-date">Latest delivery date</label>
					<input id="item-date" type="date" class="kt-input" :value="fields.latest_delivery_date" @input="fields.latest_delivery_date = $event.target.value" />
					<p v-if="errors.latest_delivery_date" class="req-field-error">{{ errors.latest_delivery_date }}</p>
				</div>
			</div>

			<p v-if="error" class="req-field-error" role="alert">{{ error }}</p>

			<div class="kt-dialog-actions">
				<button type="button" class="kt-btn kt-btn-secondary" @click="$emit('cancel')">Cancel</button>
				<button type="button" class="kt-btn kt-btn-primary" :disabled="pending" data-testid="req-item-dialog-confirm" @click="confirm">
					{{ editing ? "Save changes" : "Add item" }}
				</button>
			</div>
		</div>
	</div>
</template>

<script setup>
import { computed, nextTick, onMounted, reactive, ref } from "vue";

const props = defineProps({
	editor: { type: Object, required: true },
	item: { type: Object, default: null },
	pending: Boolean,
	error: { type: String, default: "" },
});

const emit = defineEmits(["confirm", "cancel"]);

const editing = computed(() => !!props.item);
const dialogEl = ref(null);
const drawdownLines = computed(() => props.editor.drawdown_context || []);
const equipmentCategories = computed(() => (props.editor.catalogue || {}).equipment_categories || []);
const deliveryLocations = computed(() => props.editor.delivery_locations || []);

const fields = reactive({
	plan_item_line_id: (props.item && props.item.plan_item_line_id) || "",
	equipment_category: (props.item && props.item.equipment_category) || "",
	item_name: (props.item && props.item.item_name) || "",
	quantity: (props.item && props.item.quantity) || 1,
	intended_use: (props.item && props.item.intended_use) || "",
	delivery_location: (props.item && props.item.delivery_location) || (deliveryLocations.value[0] || {}).name || "",
	latest_delivery_date: (props.item && props.item.latest_delivery_date) || "",
});

const errors = reactive({});

function validate() {
	const next = {};
	if (!fields.plan_item_line_id) next.plan_item_line_id = "A Planning source is required.";
	if (!fields.equipment_category) next.equipment_category = "An equipment category is required.";
	if (!fields.item_name.trim()) next.item_name = "An item name is required.";
	if (!fields.quantity || fields.quantity <= 0) next.quantity = "A positive quantity is required.";
	if (!fields.intended_use.trim()) next.intended_use = "Intended use is required.";
	if (!fields.delivery_location) next.delivery_location = "A delivery location is required.";
	if (!fields.latest_delivery_date) next.latest_delivery_date = "A latest delivery date is required.";
	Object.keys(errors).forEach((k) => delete errors[k]);
	Object.assign(errors, next);
	return Object.keys(next).length === 0;
}

function confirm() {
	if (!validate()) return;
	emit("confirm", { ...fields });
}

onMounted(() => {
	nextTick(() => dialogEl.value && dialogEl.value.focus());
});
</script>
