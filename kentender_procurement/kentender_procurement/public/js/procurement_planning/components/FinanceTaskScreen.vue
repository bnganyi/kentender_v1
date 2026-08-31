<!-- PLN-UI-10 Finance confirmation task (§12.9), rendering PLN-DES-10
     class-for-class: the read-only Plan Item card, the live funding-position
     table with its As-at line, and the decision footer. §12.13/DES-16's
     Finance-shortfall variant omits Confirm and shows the exact deficient
     source instead of the green notice. No editable amounts, Budget Line
     changes, optional note or partial confirmation (§11.12). -->
<template>
	<div>
		<p class="kt-page-kicker">{{ task.header?.eyebrow }}</p>
		<h1 class="kt-page-title">{{ task.header?.title }}</h1>
		<p class="pln-quiet-ref">{{ task.header?.reference_line }}</p>
		<span class="kt-status" :class="badgeClass" data-testid="fnt-badge">
			{{ task.header?.badge }}
		</span>

		<div v-if="errorSummary" class="pln-notice is-critical" role="alert" data-testid="fnt-error">
			<p class="pln-notice-title">This decision could not be completed</p>
			<p>{{ errorSummary }}</p>
		</div>

		<!-- Plan Item card -->
		<div class="kt-card kt-blueprint pln-card-pad" data-testid="fnt-plan-item">
			<i class="kt-corner tl"></i><i class="kt-corner tr"></i>
			<i class="kt-corner bl"></i><i class="kt-corner br"></i>
			<div class="pln-field-grid">
				<div class="pln-ro-field"><label>Plan Item</label><div class="pln-val">{{ task.plan_item?.title }}</div></div>
				<div class="pln-ro-field"><label>Department</label><div class="pln-val">{{ task.plan_item?.department }}</div></div>
				<div class="pln-ro-field"><label>Requirement type</label><div class="pln-val">{{ task.plan_item?.requirement_type }}</div></div>
				<div class="pln-ro-field"><label>Planned value</label><div class="pln-val">{{ task.plan_item?.value_display }}</div></div>
				<div class="pln-ro-field"><label>Procurement method</label><div class="pln-val">{{ task.plan_item?.procurement_method }}</div></div>
				<div class="pln-ro-field"><label>Delivery completion</label><div class="pln-val">{{ task.plan_item?.delivery_completion_display }}</div></div>
			</div>
		</div>

		<!-- Funding position -->
		<div class="kt-card kt-blueprint pln-card-pad" data-testid="fnt-position">
			<i class="kt-corner tl"></i><i class="kt-corner tr"></i>
			<i class="kt-corner bl"></i><i class="kt-corner br"></i>
			<div class="kt-card-title">Funding position</div>
			<p class="pln-quiet-ref">Position as at {{ task.as_at_display }}</p>
			<table class="pln-table">
				<thead>
					<tr>
						<th>Budget Line</th><th>Funding source</th>
						<th class="pln-num">Approved</th><th class="pln-num">Reserved</th>
						<th class="pln-num">Committed</th><th class="pln-num">Available</th>
						<th class="pln-num">Required</th><th class="pln-num">Available after confirmation</th>
					</tr>
				</thead>
				<tbody>
					<tr v-for="(row, idx) in task.lines" :key="idx">
						<td>{{ row.budget_line_label }}</td>
						<td>{{ row.funding_source }}</td>
						<td class="pln-num">{{ row.approved_display }}</td>
						<td class="pln-num">{{ row.reserved_display }}</td>
						<td class="pln-num">{{ row.committed_display }}</td>
						<td class="pln-num">{{ row.available_display }}</td>
						<td class="pln-num">{{ row.required_display }}</td>
						<td class="pln-num">{{ row.available_after_display }}</td>
					</tr>
				</tbody>
			</table>
			<div v-if="task.all_sufficient" class="pln-notice is-live" data-testid="fnt-sufficient">
				Full funding is available for every source allocation.
			</div>
			<div v-else class="pln-notice is-critical" data-testid="fnt-shortfall">
				<p class="pln-notice-title">Funding is insufficient</p>
				<p>The required amount exceeds the current available amount on at least one Budget Line. No reservation has been created.</p>
			</div>
		</div>

		<div v-if="decidable" class="pln-footer-bar">
			<button
				class="kt-btn kt-btn-secondary" data-testid="fnt-return"
				:disabled="pending" @click="$emit('open-return-dialog')"
			>
				Return to planner
			</button>
			<button
				v-if="task.all_sufficient"
				class="kt-btn kt-btn-primary" data-testid="fnt-confirm"
				:disabled="pending" @click="$emit('confirm')"
			>
				Confirm funding
			</button>
		</div>
	</div>
</template>

<script setup>
import { computed } from "vue";

const props = defineProps({
	task: { type: Object, default: () => ({}) },
	pending: Boolean,
	errorSummary: String,
});

defineEmits(["confirm", "open-return-dialog"]);

const decidable = computed(() => props.task.status === "Open");

const badgeClass = computed(() =>
	props.task.header?.badge === "Awaiting Finance" ? "is-pending" : "is-live"
);
</script>
