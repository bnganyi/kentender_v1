<!-- TPR-DES-03 · Task 2 — Goods and requirements (§8.2, §13.5): review-only.
     Six read-only panels with stable IDs — Goods and delivery, Technical
     requirements, Warranty and support, Related services, Acceptance
     requirements (empty states when the fixture has neither), Supporting
     materials — and the one action, Request upstream correction. No
     quantity, description, requirement, warranty, service, acceptance row
     or file is editable; no upload exists (TPR-AC-009). -->
<template>
	<div>
		<div class="tpr-actions-end">
			<button v-if="canRequestCorrection" type="button" class="kt-btn kt-btn-secondary" :disabled="pending" data-testid="tpr-upstream-trigger" @click="$emit('request-upstream-correction')">Request upstream correction</button>
		</div>
		<div class="tpr-section">
			<div class="kt-card-title">Goods and delivery</div>
			<table class="kt-table" data-testid="tpr-goods">
				<thead><tr><th>ID</th><th>Item</th><th class="tpr-num">Qty</th><th>Unit</th><th>Delivery location</th><th>Latest date</th><th>Warranty</th></tr></thead>
				<tbody>
					<tr v-for="line in inherited.goods || []" :key="line.source_item_ids">
						<td>{{ line.source_item_ids }}</td><td>{{ line.description }}</td><td class="tpr-num">{{ line.quantity }}</td><td>{{ line.unit }}</td><td>{{ line.destination }}</td><td>{{ line.latest_delivery_date }}</td><td>{{ line.minimum_warranty }}</td>
					</tr>
				</tbody>
			</table>
		</div>
		<div class="tpr-section">
			<div class="kt-card-title">Technical requirements — {{ technicalGroupLabel }}</div>
			<table class="kt-table" data-testid="tpr-technical">
				<thead><tr><th>ID</th><th>Requirement</th><th>Comparison</th><th>Value</th></tr></thead>
				<tbody>
					<tr v-for="row in inherited.technical_requirements || []" :key="row.technical_requirement_id">
						<td>{{ row.technical_requirement_id }}</td><td>{{ row.label }}</td><td>{{ row.comparison }}</td><td>{{ row.required_value }}<template v-if="row.unit"> {{ row.unit }}</template></td>
					</tr>
				</tbody>
			</table>
		</div>
		<div class="tpr-section">
			<div class="kt-card-title">Warranty and support</div>
			<p class="tpr-ro-val" style="margin: 0" data-testid="tpr-warranty">{{ warrantyLine }}</p>
		</div>
		<div class="tpr-section tpr-grid-2">
			<div>
				<div class="kt-card-title">Related services</div>
				<table v-if="(inherited.related_services || []).length" class="kt-table">
					<thead><tr><th>ID</th><th>Service</th><th>Required result</th><th>Completion</th></tr></thead>
					<tbody><tr v-for="s in inherited.related_services" :key="s.service_requirement_id"><td>{{ s.service_requirement_id }}</td><td>{{ s.service_type }}</td><td>{{ s.required_result }}</td><td>{{ s.completion_date }}</td></tr></tbody>
				</table>
				<p v-else class="tpr-muted">No related services for this Requisition.</p>
			</div>
			<div>
				<div class="kt-card-title">Acceptance requirements</div>
				<table v-if="(inherited.acceptance_requirements || []).length" class="kt-table" data-testid="tpr-acceptance">
					<thead><tr><th>ID</th><th>Check</th><th>Pass condition</th><th>Evidence</th></tr></thead>
					<tbody><tr v-for="a in inherited.acceptance_requirements" :key="a.acceptance_requirement_id"><td>{{ a.acceptance_requirement_id }}</td><td>{{ a.check_type }}</td><td>{{ a.pass_condition }}</td><td>{{ a.evidence_type }}</td></tr></tbody>
				</table>
				<p v-else class="tpr-muted">No acceptance requirements beyond delivery.</p>
			</div>
		</div>
		<div class="tpr-section">
			<div class="kt-card-title">Supporting materials</div>
			<table v-if="(inherited.supporting_materials || []).length" class="kt-table">
				<thead><tr><th>ID</th><th>Title</th><th>Type</th><th>Treatment</th><th>Linked requirement IDs</th></tr></thead>
				<tbody><tr v-for="m in inherited.supporting_materials" :key="m.supporting_material_id"><td>{{ m.supporting_material_id }}</td><td>{{ m.title }}</td><td>{{ m.document_type }}</td><td>{{ m.treatment }}</td><td>{{ m.linked_requirement_ids }}</td></tr></tbody>
			</table>
			<p v-else class="tpr-muted">No supporting materials attached.</p>
		</div>
	</div>
</template>

<script setup>
import { computed } from "vue";

const props = defineProps({ editor: { type: Object, default: () => ({}) }, pending: Boolean });
defineEmits(["request-upstream-correction"]);
const inherited = computed(() => props.editor.inherited || {});
const canRequestCorrection = computed(() => !!(props.editor.permitted_actions || {}).can_request_upstream_correction);
const technicalGroupLabel = computed(() => {
	const rows = inherited.value.technical_requirements || [];
	return rows.length ? `${rows[0].technical_requirement_id} to ${rows[rows.length - 1].technical_requirement_id}` : "none";
});
const warrantyLine = computed(() => {
	const w = inherited.value.warranty_support || {};
	const parts = [`${w.minimum_warranty_months} months minimum warranty`];
	if (w.onsite_support_required) parts.push("on-site support included");
	if (w.maximum_support_response_hours) parts.push(`${w.maximum_support_response_hours}-hour support response`);
	if (w.manufacturer_support_required) parts.push("manufacturer-backed");
	if (w.service_location_constraint) parts.push(w.service_location_constraint.toLowerCase());
	return parts.join(", ") + ".";
});
</script>
