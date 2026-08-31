<!-- PLN-UI-11/12 Annual Plan governance decisions (§12.10), rendering
     PLN-DES-11 (Accounting Officer adoption) and PLN-DES-12 (statutory
     approval) from the same read model and screen: the exact immutable
     `submitted_snapshot` Plan table, never a live query, plus the
     stage-specific authority card and decision statement. No professional
     review, Head of Procurement Function, editable Plan content, optional
     comments or publication controls. -->
<template>
	<div>
		<p class="kt-page-kicker">{{ task.header?.eyebrow }}</p>
		<h1 class="kt-page-title">{{ task.header?.title }}</h1>
		<span class="kt-status" :class="badgeClass" data-testid="pgt-badge">
			{{ task.header?.badge }}
		</span>

		<div v-if="errorSummary" class="pln-notice is-critical" role="alert" data-testid="pgt-error">
			<p class="pln-notice-title">This decision could not be completed</p>
			<p>{{ errorSummary }}</p>
		</div>

		<!-- authority card (statutory stage only) -->
		<div
			v-if="task.authority_card"
			class="kt-card kt-blueprint pln-card-pad"
			data-testid="pgt-authority"
		>
			<i class="kt-corner tl"></i><i class="kt-corner tr"></i>
			<i class="kt-corner bl"></i><i class="kt-corner br"></i>
			<div class="pln-field-grid">
				<div class="pln-ro-field">
					<label>{{ task.authority_card.is_board ? "Governing body" : "Capacity" }}</label>
					<div class="pln-val">{{ task.authority_card.capacity }}</div>
				</div>
				<div class="pln-ro-field">
					<label>Accounting Officer adoption</label>
					<div class="pln-val">{{ task.authority_card.ao_adoption_line }}</div>
				</div>
			</div>
		</div>

		<!-- immutable Plan table -->
		<div class="kt-card kt-blueprint pln-card-pad" data-testid="pgt-items">
			<i class="kt-corner tl"></i><i class="kt-corner tr"></i>
			<i class="kt-corner bl"></i><i class="kt-corner br"></i>
			<div class="kt-card-title">Plan Items</div>
			<table class="pln-table">
				<thead>
					<tr>
						<th>Plan Item</th><th>Department</th><th>Source origin</th>
						<th class="pln-num">Quantity</th><th>Strategic Objective</th>
						<th>Method</th><th class="pln-num">Value</th><th>Completion</th><th>Finance</th>
					</tr>
				</thead>
				<tbody>
					<tr v-for="row in task.items" :key="row.plan_item_id">
						<td>{{ row.plan_item_id }} · {{ row.title }}</td>
						<td>{{ row.department }}</td>
						<td>{{ row.source_origin }}</td>
						<td class="pln-num">{{ row.quantity_display }}</td>
						<td>{{ row.strategic_objective_label }}</td>
						<td>{{ row.procurement_method }}</td>
						<td class="pln-num">{{ row.value_display }}</td>
						<td>{{ row.delivery_completion_display }}</td>
						<td><span class="kt-status is-live">{{ row.finance_state }}</span></td>
					</tr>
				</tbody>
			</table>
			<p class="pln-table-caption">{{ task.caption }}</p>
		</div>

		<!-- decision statement (AO stage only) -->
		<div v-if="task.decision_statement" class="pln-cert-box" data-testid="pgt-statement">
			<p>{{ task.decision_statement }}</p>
		</div>

		<div v-if="task.authority_card?.is_board" class="pln-field" data-testid="pgt-resolution-field">
			<label for="pgt-resolution">Resolution reference</label>
			<input
				id="pgt-resolution" class="kt-input" data-testid="pgt-resolution"
				v-model="resolutionReference"
			/>
		</div>

		<div v-if="decidable" class="pln-footer-bar">
			<button
				class="kt-btn kt-btn-secondary" data-testid="pgt-return"
				:disabled="pending" @click="$emit('open-return-dialog')"
			>
				Return for correction
			</button>
			<button
				class="kt-btn kt-btn-primary" data-testid="pgt-confirm"
				:disabled="pending || (task.authority_card?.is_board && !resolutionReference.trim())"
				@click="$emit('confirm', resolutionReference.trim())"
			>
				{{ task.confirm_label }}
			</button>
		</div>
	</div>
</template>

<script setup>
import { computed, ref } from "vue";

const props = defineProps({
	task: { type: Object, default: () => ({}) },
	pending: Boolean,
	errorSummary: String,
});

defineEmits(["confirm", "open-return-dialog"]);

const resolutionReference = ref("");

const decidable = computed(() => props.task.status === "Open");

const badgeClass = computed(() =>
	props.task.header?.badge === "Draft" ? "is-draft" : "is-pending"
);
</script>
