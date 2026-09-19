<!-- PLN-CHG-001 v1.23 §10.13 — Procurement progress (U14), ported from
     U14.dc.html.

     The first view answers three questions and no others: what was planned,
     how much of it an authorised requisition covers, and what has actually
     started. Everything else is evidence behind a disclosure.

     Two rules shape what is absent. There is no completion column, because no
     owning module supplies completion evidence yet, and a column that reads
     "not yet available" on every row is worse than no column (PLN22-AC-009).
     And there is no forecast column and no "Update expected dates" action:
     the forecast facility is deferred in full (§10.14, PLN23-CHG-001), so
     dates here are the approved ones and the owner's own actuals. -->
<template>
	<div>

		<!-- No plan in force is a plain fact about the year, not a failure. -->
		<div v-if="progress.outcome === 'NO_ACTIVE_PLAN'" class="kt-card kt-blueprint pln-state-card" data-testid="prg-no-plan">
			<i class="kt-corner tl"></i><i class="kt-corner tr"></i>
			<i class="kt-corner bl"></i><i class="kt-corner br"></i>
			<h3>No plan is in force yet</h3>
			<p>Procurement progress appears once an annual plan is approved and active.</p>
		</div>

		<template v-else>
			<div class="pln-sheet">
				<div class="pln-masthead">
					<div>
						<h1 class="kt-page-title" data-testid="prg-title">Procurement progress</h1>
						<p class="kt-page-lede">Follow authorised procurement against the current annual plan.</p>
					</div>
				</div>

				<div class="kt-meta-row pln-context-row" data-testid="prg-context">
					<div>
						<span class="kt-label">Plan</span>
						<span class="kt-meta-value">{{ progress.plan_reference }}</span>
					</div>
					<div>
						<span class="kt-label">Version</span>
						<span class="kt-meta-value">{{ progress.version_number }}</span>
					</div>
					<div>
						<span class="kt-label">Status</span>
						<span class="kt-meta-value"><span class="kt-status is-live">{{ progress.status }}</span></span>
					</div>
					<div>
						<span class="kt-label">Financial year</span>
						<span class="kt-meta-value">{{ progress.financial_year_label }}</span>
					</div>
				</div>

				<div v-if="items.length" class="pln-progress-grid" data-testid="prg-purchases">
					<div v-for="row in items" :key="row.plan_item_id" class="kt-card pln-progress-card" data-testid="prg-purchase">
						<!-- U14-HOLD — the hold sits in the row it actually affects,
						     above that purchase's facts, and links to the requests
						     rather than offering to restart anything. -->
						<div v-if="row.hold" class="kt-notice is-warning" data-testid="prg-hold">
							<svg class="kt-notice-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
								<path d="M12 3l9 16H3z"></path><path d="M12 10v4M12 17h.01"></path>
							</svg>
							<div class="kt-notice-body">
								{{ row.hold.text }}
								<a href="#" data-testid="prg-view-corrections" @click.prevent="$emit('view-corrections', row.plan_item_id)">
									{{ row.hold.link_text }} ({{ row.hold.open_requests }})
								</a>
							</div>
						</div>

						<h6 class="kt-card-title">{{ row.title }}</h6>
						<div class="kt-muted pln-row-ref">{{ row.plan_item_id }}</div>

						<div class="kt-meta-row" data-testid="prg-scope">
							<div>
								<span class="kt-label">Planned</span>
								<span class="kt-meta-value">{{ row.planned_display }}</span>
							</div>
							<div>
								<span class="kt-label">Covered by authorised requisitions</span>
								<span class="kt-meta-value">{{ row.covered_display }}</span>
							</div>
							<div>
								<span class="kt-label">Not yet covered</span>
								<span class="kt-meta-value">{{ row.not_covered_display }}</span>
							</div>
							<div>
								<span class="kt-label">Procurement stage</span>
								<span class="kt-meta-value">{{ row.procurement_stage }}</span>
							</div>
						</div>

						<!-- U14-FULL-COVERAGE — the proceedings behind the coverage,
						     each one's own quantity and value, never merged. -->
						<details v-if="row.proceedings.length" class="kt-disclosure" data-testid="prg-evidence">
							<summary class="kt-disclosure-head">
								<span class="kt-disclosure-title">View procurement evidence</span>
							</summary>
							<div class="kt-disclosure-body">
								<table class="kt-table">
									<thead>
										<tr><th>Proceeding</th><th>Requisition</th><th>Covered</th><th>Stage</th></tr>
									</thead>
									<tbody>
										<tr v-for="proceeding in row.proceedings" :key="proceeding.proceeding_id" data-testid="prg-proceeding">
											<td>{{ proceeding.proceeding_id }}</td>
											<td>{{ proceeding.requisition_reference || "—" }}</td>
											<td>{{ proceeding.covered_display }}</td>
											<td>{{ proceeding.stage }}</td>
										</tr>
									</tbody>
								</table>

								<!-- U14-ACTUALS — one dated table per proceeding, and
								     only for a proceeding whose owner has actually
								     reported something. -->
								<template v-for="proceeding in datedProceedings(row)" :key="`d-${proceeding.proceeding_id}`">
									<h6 class="kt-card-title pln-progress-dates-head">{{ proceeding.proceeding_id }}</h6>
									<table class="kt-table" data-testid="prg-milestones">
										<thead>
											<tr>
												<th>Milestone</th><th>Approved date</th><th>Actual date</th>
												<th class="is-num">Days after approved date</th>
											</tr>
										</thead>
										<tbody>
											<tr v-for="milestone in proceeding.milestones" :key="milestone.milestone" data-testid="prg-milestone-row">
												<td>{{ milestone.label }}</td>
												<td>{{ milestone.approved_display }}</td>
												<td>{{ milestone.actual_display }}</td>
												<td class="is-num">{{ milestone.days_after_approved }}</td>
											</tr>
										</tbody>
									</table>
									<!-- Only where both endpoints actually exist. -->
									<table v-if="proceeding.durations.length" class="kt-table" data-testid="prg-durations">
										<thead>
											<tr>
												<th>From</th><th>To</th><th class="is-num">Planned elapsed days</th>
												<th class="is-num">Actual elapsed days</th><th class="is-num">Difference</th>
											</tr>
										</thead>
										<tbody>
											<tr v-for="duration in proceeding.durations" :key="`${duration.from_label}-${duration.to_label}`" data-testid="prg-duration-row">
												<td>{{ duration.from_label }}</td>
												<td>{{ duration.to_label }}</td>
												<td class="is-num">{{ duration.planned_elapsed_days }}</td>
												<td class="is-num">{{ duration.actual_elapsed_days }}</td>
												<td class="is-num">{{ duration.difference_days }}</td>
											</tr>
										</tbody>
									</table>
								</template>
							</div>
						</details>

						<div class="pln-progress-actions">
							<a href="#" data-testid="prg-view-purchase" @click.prevent="$emit('navigate', row.route)">View purchase details</a>
						</div>
					</div>
				</div>
				<p v-else class="kt-muted" data-testid="prg-empty">This plan has no purchases.</p>
			<p v-if="errorSummary" class="pln-error-summary" data-testid="prg-error">{{ errorSummary }}</p>
			</div>
		</template>
	</div>
</template>

<script setup>
import { computed } from "vue";

const props = defineProps({
	progress: { type: Object, default: () => ({}) },
	pending: Boolean,
	errorSummary: String,
});

defineEmits(["navigate", "view-corrections", "back"]);

const items = computed(() => props.progress.items || []);

// A proceeding with no owner-supplied date contributes no table at all —
// the server sends an empty list rather than rows of placeholders.
function datedProceedings(row) {
	return (row.proceedings || []).filter((p) => (p.milestones || []).length);
}
</script>
