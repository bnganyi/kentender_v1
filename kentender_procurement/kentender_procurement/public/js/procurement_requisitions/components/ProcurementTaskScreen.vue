<!-- REQ-DES-09 Procurement authorisation task (§13.11), ported class-for-
     class: the eyebrow+title+status header, the lead-department line with
     its "Change lead department" action (HoPF only, only more than one
     contributing department), fresh Planning-availability and Budget-
     affordability cards, the §5A compatibility table (every row
     independently named, never a single collapsed pass/fail), policy
     justification, validation, the submitted-by line, the certification
     statement, and Return/Authorise footer. No edit, evidence-builder or
     template selector. -->
<template>
	<div class="req-step-content">
		<div class="req-masthead">
			<div class="kt-eyebrow">PROCUREMENT AUTHORISATION</div>
			<div class="req-editor-titlebar">
				<h1 class="req-editor-title">{{ (task.version || {}).requirement_title }}</h1>
				<span class="kt-status is-pending">Submitted to Procurement</span>
			</div>
			<div class="req-editor-reference">{{ reference }}</div>
			<div v-if="task.can_change_lead_unit" class="req-lead-line">
				Lead department: <strong>{{ (task.requisition || {}).lead_org_unit_label }}</strong>.
				<a href="#" class="req-quiet-link" data-testid="req-change-lead-unit" @click.prevent="$emit('change-lead-unit')">Change lead department</a>
			</div>
		</div>

		<div class="req-field-grid">
			<div class="kt-card kt-blueprint req-card-pad">
				<i class="kt-corner tl"></i><i class="kt-corner tr"></i><i class="kt-corner bl"></i><i class="kt-corner br"></i>
				<div class="kt-eyebrow">Fresh Planning availability</div>
				<div class="req-summary-title" :class="planningAvailability.eligible ? 'req-validation-live' : 'req-validation-blocked'">{{ planningAvailability.eligible ? "Eligible" : "Not eligible" }}</div>
				<p class="req-context-body">{{ money(planningAvailability.remaining_amount) }} and {{ planningAvailability.remaining_quantity }} {{ planningAvailability.unit }} remain available</p>
			</div>
			<div class="kt-card kt-blueprint req-card-pad">
				<i class="kt-corner tl"></i><i class="kt-corner tr"></i><i class="kt-corner bl"></i><i class="kt-corner br"></i>
				<div class="kt-eyebrow">Fresh Budget affordability</div>
				<template v-if="budgetAffordability.length">
					<div v-for="row in budgetAffordability" :key="row.budget_line" class="req-summary-title">{{ row.budget_line_label || row.budget_line }}</div>
					<p v-for="row in budgetAffordability" :key="`${row.budget_line}-body`" class="req-context-body">
						{{ money(row.requested_amount) }} requested against {{ money(row.available_before) }} approved and {{ row.sufficient ? "fully available" : `short by ${money(row.shortfall)}` }}
					</p>
				</template>
				<p v-else class="req-context-body">Not yet checked — resolve the findings below first.</p>
			</div>
		</div>

		<div class="kt-card-title">Product suitability — §5A compatibility test</div>
		<table class="kt-table" data-testid="req-compatibility-table">
			<thead>
				<tr>
					<th>Test</th>
					<th>Result</th>
				</tr>
			</thead>
			<tbody>
				<tr v-for="row in compatibility" :key="row.test">
					<td>{{ row.test }}</td>
					<td><span class="kt-status" :class="row.ok ? 'is-live' : 'is-critical'">{{ row.actual }}</span></td>
				</tr>
			</tbody>
		</table>

		<div class="req-policy-line"><span class="kt-label">Policy justification</span><br />{{ task.objective_label }}</div>
		<div class="req-validation-line" :class="validationReport.blocking_count ? 'req-validation-blocked' : 'req-validation-live'">
			Validation: {{ validationReport.blocking_count || 0 }} Blocking · {{ validationReport.warning_count || 0 }} Warning{{ (validationReport.warning_count || 0) === 1 ? "" : "s" }}
		</div>
		<p v-if="(task.submitted_by || {}).name" class="req-table-caption">Submitted by {{ task.submitted_by.name }} · {{ task.submitted_by.decided_at }}</p>

		<div class="kt-card kt-blueprint req-card-pad">
			<i class="kt-corner tl"></i><i class="kt-corner tr"></i><i class="kt-corner bl"></i><i class="kt-corner br"></i>
			<p class="req-certification-statement">I authorise this complete Requisition for Tender Preparation and commit its stated Planning drawdown and Budget reservation.</p>
		</div>

		<div class="req-actions">
			<button v-if="task.can_return" type="button" class="kt-btn kt-btn-secondary" :disabled="pending" data-testid="req-task-return" @click="$emit('return')">Return to department</button>
			<button v-if="task.can_authorise" type="button" class="kt-btn kt-btn-primary" :disabled="pending" data-testid="req-task-authorise" @click="$emit('authorise')">Authorise for Tender Preparation</button>
		</div>
	</div>
</template>

<script setup>
import { computed } from "vue";
import { formatMoney } from "../data/format.js";

const props = defineProps({
	task: { type: Object, required: true },
	pending: Boolean,
});

defineEmits(["return", "authorise", "change-lead-unit"]);

const reference = computed(() => {
	const r = props.task.requisition || {};
	const v = props.task.version || {};
	return [r.requisition_reference, r.plan_item_id, v.version_number ? `Version ${v.version_number}` : ""].filter(Boolean).join(" · ");
});

const planningAvailability = computed(() => props.task.planning_availability || {});
const budgetAffordability = computed(() => props.task.budget_affordability || []);
const compatibility = computed(() => props.task.compatibility || []);
const validationReport = computed(() => props.task.validation || {});

function money(amount) {
	return formatMoney(amount);
}
</script>
