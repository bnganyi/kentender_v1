<!-- PLN-UI-06 DPP validation task (§12.6), rendering PLN-DES-06 v1.12
     class-for-class: immutable submission context (six facts, three columns),
     snapshot rows with the inline requirement-type select and a View
     disclosure of the submitted narrative, the certification card with its
     signed line, and the two decision controls. -->
<template>
	<div>
		<p class="kt-page-kicker">{{ detail.header?.eyebrow }}</p>
		<h1 class="kt-page-title">{{ detail.header?.title }}</h1>
		<p class="pln-quiet-ref">{{ detail.header?.reference_line }}</p>
		<span class="kt-status" :class="badgeClass" data-testid="dppv-badge">
			{{ detail.header?.badge }}
		</span>

		<!-- submission context card -->
		<div class="kt-card kt-blueprint pln-card-pad" data-testid="dppv-context">
			<i class="kt-corner tl"></i><i class="kt-corner tr"></i>
			<i class="kt-corner bl"></i><i class="kt-corner br"></i>
			<div class="pln-field-grid pln-field-grid-3">
				<div class="pln-ro-field">
					<label>Department</label>
					<div class="pln-val">{{ detail.context?.department }}</div>
				</div>
				<div class="pln-ro-field">
					<label>Financial Year</label>
					<div class="pln-val">{{ detail.context?.financial_year }}</div>
				</div>
				<div class="pln-ro-field">
					<label>Submitted by</label>
					<div class="pln-val">{{ detail.context?.submitted_by }}</div>
				</div>
				<div class="pln-ro-field">
					<label>Submitted</label>
					<div class="pln-val">{{ detail.context?.submitted_at }}</div>
				</div>
				<div class="pln-ro-field">
					<label>Requirements</label>
					<div class="pln-val">{{ detail.context?.requirements }}</div>
				</div>
				<div class="pln-ro-field">
					<label>Total indicative value</label>
					<div class="pln-val">{{ detail.context?.total_display }}</div>
				</div>
			</div>
		</div>

		<!-- §6.1 — the certifier sees the task read-only -->
		<div
			v-if="detail.maker_checker_blocked && detail.status === 'Open'"
			class="pln-notice"
			data-testid="dppv-maker-checker"
		>
			<p class="pln-notice-title">You certified this submission</p>
			<p>Another Procurement Planner must validate it.</p>
		</div>

		<div v-if="errorSummary" class="pln-notice is-critical" role="alert" data-testid="dppv-error">
			<p class="pln-notice-title">This decision could not be completed</p>
			<p>{{ errorSummary }}</p>
		</div>

		<!-- submitted requirements table -->
		<div class="kt-card kt-blueprint pln-card-pad" data-testid="dppv-entries">
			<i class="kt-corner tl"></i><i class="kt-corner tr"></i>
			<i class="kt-corner bl"></i><i class="kt-corner br"></i>
			<table class="pln-table">
				<thead>
					<tr>
						<th>Requirement</th>
						<th>Source</th>
						<th class="pln-num">Quantity</th>
						<th>Required by</th>
						<th>Procurement Budget Line</th>
						<th class="pln-num">Amount</th>
						<th>Requirement type</th>
						<th></th>
					</tr>
				</thead>
				<tbody>
					<template v-for="row in detail.entries" :key="row.entry_id">
						<tr :data-testid="`dppv-entry-${row.entry_id}`">
							<td>{{ row.title }}</td>
							<td>{{ row.source_label }}</td>
							<td class="pln-num">{{ row.quantity_display }}</td>
							<td>{{ row.required_by_display }}</td>
							<td>{{ row.budget_line_display }}</td>
							<td class="pln-num">{{ row.amount_display }}</td>
							<td>
								<!-- a not-proceeding entry takes no classification (§5.1) -->
								<span v-if="row.not_proceeding" class="kt-status is-draft">Not proceeding</span>
								<select
									v-else-if="decidable"
									class="kt-input pln-seg-select"
									:data-testid="`dppv-type-${row.entry_id}`"
									:value="classifications[row.entry_id] || ''"
									@change="$emit('classify', row.entry_id, $event.target.value)"
								>
									<option value="" disabled>Select…</option>
									<option v-for="type in detail.requirement_types" :key="type" :value="type">
										{{ type }}
									</option>
								</select>
								<span v-else>{{ classifications[row.entry_id] || "—" }}</span>
							</td>
							<td style="text-align: right">
								<button
									type="button"
									class="kt-btn kt-btn-ghost"
									:data-testid="`dppv-view-${row.entry_id}`"
									:aria-expanded="expanded[row.entry_id] ? 'true' : 'false'"
									@click="toggle(row.entry_id)"
								>
									View
								</button>
							</td>
						</tr>
						<!-- the submitted narrative, read-only (§12.6 "all submitted entry details") -->
						<tr v-if="expanded[row.entry_id]" :data-testid="`dppv-detail-${row.entry_id}`">
							<td colspan="8">
								<div class="pln-field-grid pln-entry-detail">
									<div class="pln-ro-field" style="grid-column: 1 / -1">
										<label>Description</label>
										<div class="pln-val">{{ row.description }}</div>
									</div>
									<div class="pln-ro-field" style="grid-column: 1 / -1">
										<label>Expected operational result</label>
										<div class="pln-val">{{ row.expected_operational_result }}</div>
									</div>
									<div v-if="row.not_proceeding" class="pln-ro-field" style="grid-column: 1 / -1">
										<label>Not proceeding</label>
										<div class="pln-val">{{ row.not_proceeding_reason }}</div>
									</div>
								</div>
							</td>
						</tr>
					</template>
				</tbody>
			</table>
		</div>

		<!-- certification card with the signed line -->
		<div class="pln-cert-box" data-testid="dppv-certification">
			<div class="kt-card-title">{{ detail.certification?.heading }}</div>
			<p>{{ detail.certification?.text }}</p>
			<p class="pln-signed">{{ detail.certification?.signed_line }}</p>
		</div>

		<!-- decision footer -->
		<div v-if="decidable" class="pln-footer-bar">
			<button
				type="button"
				class="kt-btn kt-btn-secondary"
				data-testid="dppv-return"
				:disabled="pending"
				@click="$emit('open-return-dialog')"
			>
				Return to department
			</button>
			<button
				type="button"
				class="kt-btn kt-btn-primary"
				data-testid="dppv-accept"
				:disabled="pending || !fullyClassified"
				@click="$emit('accept')"
			>
				Accept departmental plan
			</button>
		</div>
	</div>
</template>

<script setup>
import { computed, reactive } from "vue";

const props = defineProps({
	detail: { type: Object, default: () => ({}) },
	classifications: { type: Object, default: () => ({}) },
	pending: Boolean,
	errorSummary: String,
});

defineEmits(["classify", "accept", "open-return-dialog"]);

const expanded = reactive({});

function toggle(entryId) {
	expanded[entryId] = !expanded[entryId];
}

const decidable = computed(
	() => props.detail.status === "Open" && !props.detail.maker_checker_blocked
);

const fullyClassified = computed(() =>
	(props.detail.entries || [])
		.filter((row) => !row.not_proceeding)
		.every((row) => props.classifications[row.entry_id])
);

const badgeClass = computed(() =>
	props.detail.header?.badge_kind === "pending" ? "is-pending" : "is-live"
);
</script>
