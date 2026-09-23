<!-- PLN-CHG-001 v1.24 §10.13 — Procurement progress (U14), ported from
     Artboards-U14-U16.dc.html.

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
		<div v-if="progress.outcome === 'NO_ACTIVE_PLAN'" class="kt-empty" data-testid="prg-no-plan">
			<h3>No plan is in force yet</h3>
			<p>Procurement progress appears once an annual plan is approved and active.</p>
		</div>

		<template v-else>
			<div class="kt-page">
				<div class="kt-page-head">
					<div>
						<h1 class="kt-page-title" data-testid="prg-title">Procurement progress</h1>
						<p class="kt-page-desc">Follow authorised procurement against the current annual plan.</p>
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

				<div v-if="items.length" class="kt-region">
					<h2>Purchases</h2>
					<table class="kt-table" data-testid="prg-purchases">
						<thead>
							<tr>
								<th>Purchase</th>
								<th>Planned</th>
								<th>Covered by authorised requisitions</th>
								<th>Not yet covered</th>
								<th>Procurement stage</th>
								<th>Action</th>
							</tr>
						</thead>
						<tbody>
							<template v-for="row in items" :key="row.plan_item_id">
								<!-- U14-HOLD — the hold sits in the row it actually affects,
								     above that purchase's facts, and links to the requests
								     rather than offering to restart anything. -->
								<tr v-if="row.hold" class="pln-row-detail" data-testid="prg-hold">
									<td colspan="6">
										<div class="kt-notice is-warning">
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
									</td>
								</tr>
								<tr data-testid="prg-purchase">
									<td>
										<div style="font-weight: 600">{{ row.title }}</div>
										<div class="kt-muted pln-row-ref">{{ row.plan_item_id }}</div>
									</td>
									<td>{{ row.planned_display }}</td>
									<td>{{ row.covered_display }}</td>
									<td>{{ row.not_covered_display }}</td>
									<td>{{ row.procurement_stage }}</td>
									<td style="text-align: right">
										<a href="#" class="kt-btn kt-btn-ghost" data-testid="prg-view-purchase" @click.prevent="$emit('navigate', row.route)">View purchase details</a>
									</td>
								</tr>
								<!-- U14-FULL-COVERAGE — the proceedings behind the coverage,
								     each one's own quantity and value, never merged. -->
								<tr v-if="row.proceedings.length" class="pln-row-detail">
									<td colspan="6">
										<details class="kt-disclosure" data-testid="prg-evidence">
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
									</td>
								</tr>
							</template>
						</tbody>
					</table>
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
