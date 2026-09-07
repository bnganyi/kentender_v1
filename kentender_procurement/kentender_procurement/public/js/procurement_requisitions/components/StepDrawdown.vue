<!-- REQ-DES-03 Step 1: Request and drawdown (§13.5), ported class-for-class:
     four read-only context cards inherited from Planning, the four editable
     fields, and the drawdown table — one row per contributing department,
     each defaulted to the full remaining balance with a quiet "Request full
     remaining balance" link restoring that default. -->
<template>
	<div class="req-step-content">
		<div class="req-context-cards">
			<div class="kt-card kt-blueprint req-context-card">
				<i class="kt-corner tl"></i><i class="kt-corner tr"></i><i class="kt-corner bl"></i><i class="kt-corner br"></i>
				<div class="kt-eyebrow">From approved Procurement Plan</div>
				<div class="req-context-title">Business need</div>
				<p class="req-context-body">{{ editor.business_need }}</p>
			</div>
			<div class="kt-card kt-blueprint req-context-card">
				<i class="kt-corner tl"></i><i class="kt-corner tr"></i><i class="kt-corner bl"></i><i class="kt-corner br"></i>
				<div class="kt-eyebrow">From approved Procurement Plan</div>
				<div class="req-context-title">Expected operational result</div>
				<p class="req-context-body">{{ editor.expected_operational_result }}</p>
			</div>
			<div class="kt-card kt-blueprint req-context-card">
				<i class="kt-corner tl"></i><i class="kt-corner tr"></i><i class="kt-corner bl"></i><i class="kt-corner br"></i>
				<div class="kt-eyebrow">From approved Procurement Plan</div>
				<div class="req-context-title">Method</div>
				<p class="req-context-body">{{ editor.planning_projection.procurement_method }}</p>
			</div>
			<div class="kt-card kt-blueprint req-context-card">
				<i class="kt-corner tl"></i><i class="kt-corner tr"></i><i class="kt-corner bl"></i><i class="kt-corner br"></i>
				<div class="kt-eyebrow">From approved Procurement Plan</div>
				<div class="req-context-title">Planned completion</div>
				<p class="req-context-body">{{ plannedCompletion }}</p>
			</div>
		</div>

		<div class="req-field-grid">
			<div class="kt-field">
				<label for="req-title">Requirement title</label>
				<input id="req-title" class="kt-input" maxlength="160" :value="fields.requirement_title" @input="fields.requirement_title = $event.target.value" />
			</div>
			<div class="kt-field">
				<label for="req-location">Delivery location</label>
				<select id="req-location" class="kt-input" :value="fields.delivery_location" @change="fields.delivery_location = $event.target.value">
					<option v-for="loc in editor.delivery_locations" :key="loc.name" :value="loc.name">{{ loc.location_name }}</option>
				</select>
			</div>
			<div class="kt-field">
				<label for="req-date">Latest delivery date</label>
				<input id="req-date" type="date" class="kt-input" :value="fields.latest_delivery_date" @input="fields.latest_delivery_date = $event.target.value" />
			</div>
			<div class="kt-field">
				<label id="req-relsvc-label">Related services required</label>
				<div class="req-seg" role="radiogroup" aria-labelledby="req-relsvc-label">
					<label class="req-seg-opt"><input type="radio" :checked="!fields.related_services_required" @change="fields.related_services_required = false" />No</label>
					<label class="req-seg-opt"><input type="radio" :checked="fields.related_services_required" @change="fields.related_services_required = true" />Yes</label>
				</div>
			</div>
		</div>

		<div>
			<div class="kt-card-title">Drawdown</div>
			<table class="kt-table">
				<thead>
					<tr>
						<th>Contributing department</th>
						<th>Source requirement</th>
						<th class="req-num">Remaining</th>
						<th class="req-num">Requested quantity</th>
						<th class="req-num">Remaining value</th>
						<th class="req-num">Requested value</th>
						<th></th>
					</tr>
				</thead>
				<tbody>
					<tr v-for="row in drawdownRows" :key="row.drawdown_line_id">
						<td>{{ row.organisation_unit_label }}</td>
						<td>{{ row.source_title }}</td>
						<td class="req-num">{{ row.remaining_quantity }} {{ row.unit }}</td>
						<td class="req-num">
							<input
								class="kt-input req-qty-input"
								type="number"
								min="0"
								:data-testid="`req-drawdown-qty-${row.drawdown_line_id}`"
								:value="lines[row.drawdown_line_id].requested_quantity"
								@input="lines[row.drawdown_line_id].requested_quantity = Number($event.target.value)"
							/>
						</td>
						<td class="req-num">{{ money(row.remaining_value) }}</td>
						<td class="req-num">
							<input
								class="kt-input req-value-input"
								type="number"
								min="0"
								step="0.01"
								:data-testid="`req-drawdown-value-${row.drawdown_line_id}`"
								:value="lines[row.drawdown_line_id].requested_value"
								@input="lines[row.drawdown_line_id].requested_value = Number($event.target.value)"
							/>
						</td>
						<td>
							<a href="#" class="req-quiet-link" @click.prevent="requestFullBalance(row)">Request full balance</a>
						</td>
					</tr>
				</tbody>
			</table>
		</div>
	</div>
</template>

<script setup>
import { computed, reactive, watch } from "vue";
import { formatMoney } from "../data/format.js";

const props = defineProps({
	editor: { type: Object, required: true },
});

const fields = reactive({ requirement_title: "", delivery_location: "", latest_delivery_date: "", related_services_required: false });
const lines = reactive({});

function hydrate() {
	const version = props.editor.version || {};
	const locations = props.editor.delivery_locations || [];
	fields.requirement_title = version.requirement_title || "";
	// A native <select> visually highlights its first <option> even when
	// the bound value is "" and matches nothing — confirmed live: the
	// Ministry of Health Headquarters option looked selected while the
	// field was actually still empty, so Save/Continue silently persisted
	// no delivery location at all. Default to the first available location
	// (the fixture always exposes exactly one today) rather than leave a
	// value the control's own rendering already implies is chosen.
	fields.delivery_location = version.delivery_location || (locations[0] || {}).name || "";
	fields.latest_delivery_date = version.latest_delivery_date || "";
	fields.related_services_required = !!version.related_services_required;
	for (const line of version.drawdown_lines || []) {
		lines[line.drawdown_line_id] = { requested_quantity: line.requested_quantity, requested_value: line.requested_value };
	}
}

// AGENTS.md §6.4: an editor never re-hydrates from an in-place refresh that
// carries nothing new — guarded on record_version, so a background
// revalidation never discards what the author has typed.
watch(() => (props.editor.version || {}).record_version, hydrate, { immediate: true });

const drawdownRows = computed(() => props.editor.drawdown_context || []);

function money(amount) {
	return formatMoney(amount);
}

const plannedCompletion = computed(() => {
	const projection = props.editor.planning_projection || {};
	const dates = projection.planned_dates || {};
	return dates.delivery_completion_date || dates.completion_date || "";
});

function requestFullBalance(row) {
	lines[row.drawdown_line_id].requested_quantity = row.remaining_quantity;
	lines[row.drawdown_line_id].requested_value = row.remaining_value;
}

function getPayload() {
	return {
		requirement_title: fields.requirement_title,
		delivery_location: fields.delivery_location,
		latest_delivery_date: fields.latest_delivery_date,
		related_services_required: fields.related_services_required,
		drawdown_lines: Object.entries(lines).map(([drawdown_line_id, v]) => ({
			drawdown_line_id,
			requested_quantity: v.requested_quantity,
			requested_value: v.requested_value,
		})),
	};
}

defineExpose({ getPayload });
</script>
