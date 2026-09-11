<!-- REQ-DES-06 Step 4: Services and acceptance (§13.8), ported class-for-
     class: the "Related services required" info line (the table itself is
     absent entirely when No, never shown empty), the acceptance-checks
     table (at least one row required, §5.9), and the supporting-materials
     panel with its Add button and "No supporting materials added." empty
     copy. -->
<template>
	<div class="req-step-content">
		<div class="req-info-banner">
			Related services required: <strong>{{ relatedServicesRequired ? "Yes" : "No" }}</strong>
			<template v-if="!relatedServicesRequired"> — no related-service rows apply to this Requisition.</template>
		</div>

		<div v-if="relatedServicesRequired">
			<div class="req-step-content-header">
				<div class="kt-card-title req-no-margin">Related services</div>
				<button type="button" class="kt-btn kt-btn-secondary" data-testid="req-add-service" @click="$emit('add-service')">Add related service</button>
			</div>
			<table class="kt-table" data-testid="req-services-table">
				<thead>
					<tr>
						<th>Service type</th>
						<th>Applies to</th>
						<th>Required result</th>
						<th>Completion date</th>
						<th>Evidence</th>
						<th></th>
					</tr>
				</thead>
				<tbody>
					<tr v-for="row in relatedServices" :key="row.service_requirement_id">
						<td>{{ row.service_type }}</td>
						<td>{{ appliesToLabel(row) }}</td>
						<td>{{ row.required_result }}</td>
						<td>{{ row.completion_date }}</td>
						<td>{{ row.acceptance_evidence }}</td>
						<td><a href="#" class="req-quiet-link" @click.prevent="$emit('remove-service', row)">Remove</a></td>
					</tr>
					<tr v-if="!relatedServices.length">
						<td colspan="6" class="req-empty-row">No related services added.</td>
					</tr>
				</tbody>
			</table>
		</div>

		<div>
			<div class="kt-card-title">Acceptance checks</div>
			<table class="kt-table" data-testid="req-acceptance-table">
				<thead>
					<tr>
						<th>Check</th>
						<th>Applies to</th>
						<th>Pass condition</th>
						<th>Evidence</th>
						<th></th>
					</tr>
				</thead>
				<tbody>
					<tr v-for="row in acceptanceRequirements" :key="row.acceptance_requirement_id">
						<td>{{ row.check_type }}</td>
						<td>{{ appliesToLabel(row) }}</td>
						<td>{{ row.pass_condition }}</td>
						<td>{{ row.evidence_type }}</td>
						<td><a href="#" class="req-quiet-link" @click.prevent="$emit('remove-acceptance', row)">Remove</a></td>
					</tr>
					<tr v-if="!acceptanceRequirements.length">
						<td colspan="5" class="req-empty-row">No acceptance checks added.</td>
					</tr>
				</tbody>
			</table>
			<div class="req-step-content-header" style="margin-top: 12px">
				<span></span>
				<button type="button" class="kt-btn kt-btn-secondary" data-testid="req-add-acceptance" @click="$emit('add-acceptance')">Add acceptance check</button>
			</div>
		</div>

		<div class="req-step-content-header">
			<div class="kt-card-title req-no-margin">Supporting materials</div>
			<button type="button" class="kt-btn kt-btn-secondary" data-testid="req-add-material" @click="$emit('add-material')">Add supporting material</button>
		</div>
		<table v-if="supportingMaterials.length" class="kt-table" data-testid="req-materials-table">
			<thead>
				<tr>
					<th>Title</th>
					<th>Type</th>
					<th>Treatment</th>
					<th>File check</th>
					<th></th>
				</tr>
			</thead>
			<tbody>
				<tr v-for="row in supportingMaterials" :key="row.supporting_material_id">
					<td>{{ row.title }}</td>
					<td>{{ row.document_type }}</td>
					<td>{{ row.treatment }}</td>
					<td>{{ row.file_check_result }}</td>
					<td><a href="#" class="req-quiet-link" @click.prevent="$emit('remove-material', row)">Remove</a></td>
				</tr>
			</tbody>
		</table>
		<div v-else class="req-table-caption">No supporting materials added.</div>
	</div>
</template>

<script setup>
import { computed } from "vue";

const props = defineProps({
	editor: { type: Object, required: true },
});

defineEmits(["add-service", "remove-service", "add-acceptance", "remove-acceptance", "add-material", "remove-material"]);

const relatedServicesRequired = computed(() => !!(props.editor.version || {}).related_services_required);
const pkg = computed(() => props.editor.package || {});
const relatedServices = computed(() => pkg.value.related_services || []);
const acceptanceRequirements = computed(() => pkg.value.acceptance_requirements || []);
const supportingMaterials = computed(() => pkg.value.supporting_materials || []);
const itemsById = computed(() => {
	const map = {};
	for (const item of pkg.value.items || []) map[item.requisition_item_id] = item;
	return map;
});

function appliesToLabel(row) {
	if (row.applies_to_scope === "All items") return "All items";
	if (row.applies_to_scope === "Item") return (itemsById.value[row.applies_to_id] || {}).item_name || row.applies_to_id;
	return row.applies_to_id;
}
</script>
