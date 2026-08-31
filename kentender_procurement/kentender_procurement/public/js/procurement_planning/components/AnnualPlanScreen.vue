<!-- PLN-UI-07/08 Annual Plan workbench (§12.7), rendering PLN-DES-07
     class-for-class: summary strip, accepted-entries pool with its
     unallocated caption, and the Plan Items card with its empty state. -->
<template>
	<div>
		<div class="pln-header-row">
			<div class="pln-header-left">
				<p class="kt-page-kicker">{{ plan.header?.eyebrow }}</p>
				<h1 class="kt-page-title">{{ plan.header?.title }}</h1>
				<p class="pln-quiet-ref">{{ plan.header?.reference_line }}</p>
				<span class="kt-status" :class="badgeClass" data-testid="pln-plan-badge">
					{{ plan.header?.badge }}
				</span>
			</div>
			<div class="pln-header-actions">
				<button
					v-if="plan.mutable && plan.unallocated_sources?.length"
					class="kt-btn kt-btn-primary"
					data-testid="pln-form-items"
					:disabled="pending"
					@click="$emit('open-form-dialog')"
				>
					Form Plan Items
				</button>
			</div>
		</div>

		<div v-if="errorSummary" class="pln-notice is-critical" role="alert" data-testid="pln-plan-error">
			<p class="pln-notice-title">This command could not be completed</p>
			<p>{{ errorSummary }}</p>
		</div>

		<!-- summary strip -->
		<div class="kt-card kt-blueprint pln-strip-grid" data-testid="pln-plan-summary-strip">
			<i class="kt-corner tl"></i><i class="kt-corner tr"></i>
			<i class="kt-corner bl"></i><i class="kt-corner br"></i>
			<div class="pln-strip-field">
				<label>Accepted departmental entries</label>
				<div class="pln-val">{{ plan.summary?.accepted_entries ?? 0 }}</div>
			</div>
			<div class="pln-strip-field">
				<label>Allocated</label>
				<div class="pln-val">{{ plan.summary?.allocated ?? 0 }}</div>
			</div>
			<div class="pln-strip-field">
				<label>Plan Items</label>
				<div class="pln-val">{{ plan.summary?.plan_items ?? 0 }}</div>
			</div>
			<div class="pln-strip-field">
				<label>Plan value</label>
				<div class="pln-val">{{ plan.summary?.value_display }}</div>
			</div>
		</div>

		<!-- accepted departmental entries -->
		<div class="kt-card kt-blueprint pln-card-pad" data-testid="pln-unallocated-sources">
			<i class="kt-corner tl"></i><i class="kt-corner tr"></i>
			<i class="kt-corner bl"></i><i class="kt-corner br"></i>
			<div class="kt-card-title">Accepted departmental entries</div>
			<table class="pln-table">
				<thead>
					<tr>
						<th>Requirement</th><th>Department</th><th>Source origin</th>
						<th>Classification</th><th class="pln-num">Quantity</th>
						<th>Budget Line</th><th class="pln-num">Amount</th><th>Status</th>
					</tr>
				</thead>
				<tbody>
					<tr v-for="row in plan.unallocated_sources" :key="row.dpp_entry">
						<td>{{ row.title }}</td>
						<td>{{ row.department }}</td>
						<td>{{ row.source_origin }}</td>
						<td>{{ row.classification }}</td>
						<td class="pln-num">{{ row.quantity_display }}</td>
						<td>{{ row.budget_line }}</td>
						<td class="pln-num">{{ row.amount_display }}</td>
						<td><span class="kt-status is-pending">Unallocated</span></td>
					</tr>
				</tbody>
			</table>
			<p v-if="plan.unallocated_caption" class="pln-table-caption">{{ plan.unallocated_caption }}</p>
		</div>

		<!-- Plan Items -->
		<div class="kt-card kt-blueprint pln-card-pad" data-testid="pln-plan-items">
			<i class="kt-corner tl"></i><i class="kt-corner tr"></i>
			<i class="kt-corner bl"></i><i class="kt-corner br"></i>
			<div class="kt-card-title">Plan Items</div>
			<div v-if="!plan.plan_items?.length" class="pln-empty-state">
				<h3>No Plan Items yet</h3>
				<p>Form Plan Items from the accepted departmental entries above.</p>
			</div>
			<table v-else class="pln-table">
				<thead>
					<tr>
						<th>Plan Item</th><th>Requirement type</th><th class="pln-num">Sources</th>
						<th class="pln-num">Value</th><th>Finance</th><th>Status</th>
					</tr>
				</thead>
				<tbody>
					<tr
						v-for="row in plan.plan_items"
						:key="row.plan_item_id"
						class="pln-row-clickable"
						:data-testid="`pln-item-${row.plan_item_id}`"
						@click="$emit('navigate', row.route)"
					>
						<td>{{ row.title }}</td>
						<td>{{ row.requirement_type }}</td>
						<td class="pln-num">{{ row.sources }}</td>
						<td class="pln-num">{{ row.value_display }}</td>
						<td>{{ row.finance_state }}</td>
						<td>
							<span
								class="kt-status"
								:class="row.source_correction_required ? 'is-critical' : 'is-live'"
							>
								{{ row.source_correction_required ? "Source correction required" : row.item_state }}
							</span>
						</td>
					</tr>
				</tbody>
			</table>
		</div>

		<div class="pln-footer-bar">
			<button class="kt-btn kt-btn-ghost" @click="$emit('back')">Back to workspace</button>
			<button
				v-if="plan.mutable"
				class="kt-btn kt-btn-primary"
				data-testid="pln-submit-consolidated"
				:disabled="!plan.ready_for_submission || pending"
				@click="$emit('submit-consolidated')"
			>
				Submit consolidated Plan
			</button>
		</div>
	</div>
</template>

<script setup>
import { computed } from "vue";

const props = defineProps({
	plan: { type: Object, default: () => ({}) },
	pending: Boolean,
	errorSummary: String,
});

defineEmits(["open-form-dialog", "navigate", "back", "submit-consolidated"]);

const badgeClass = computed(() =>
	props.plan.header?.badge === "Draft" ? "is-draft" : "is-live"
);
</script>
