<!-- PLN-CHG-001 v1.24 §10.5 — Procurement review of a departmental plan (U06),
     ported from Artboards-U06.dc.html.

     The complete certified content comes first, then one decision. The only
     classification input anywhere is Requirement type; Category is read-only
     text beside it, derived by the server from the same governed catalogue
     entry — a client cannot send one (§4.4).

     Missing classification or stale source evidence removes Accept but never
     Return: a corrective action must stay available precisely when the
     evidence needed for a positive decision is the thing that is wrong
     (§6.3). -->
<template>
	<div>
		<div class="kt-page">
			<div class="kt-page-head">
				<div>
					<h1 class="kt-page-title" data-testid="pln-review-title">{{ title }}</h1>
					<p class="kt-page-desc">Check the certified requirements before adding them to the annual plan.</p>
					<!-- §10.5 U06 header — one compact scope line (icon, reference,
					     submission and year joined by "·", the status badge inline
					     after it), the same `.kt-page-scope` class Departmental Needs
					     already uses for exactly this. This screen previously spelled
					     the four facts out as their own labelled boxes instead — the
					     v1.23 artboard's own layout, ported faithfully at the time but
					     never re-diffed once v1.24 replaced it with this line (found
					     live 22 Sep 2026). -->
					<div class="kt-page-scope" data-testid="pln-review-context">
						<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><path d="M14 2v6h6"/></svg>
						{{ referenceOnly }} · Submission {{ submissionNumber }} · {{ context.financial_year }}
						<span class="kt-status" :class="`is-${task.header?.badge_kind || 'pending'}`" style="margin-left: 6px">{{ statusLabel }}</span>
					</div>
				</div>
			</div>

			<!-- §10.5 — "Immediately show" this the instant the screen has
			     something to decide on; it was missing entirely, not just
			     re-styled, in the ported version (found live 22 Sep 2026). -->
			<div v-if="!task.maker_checker_blocked" class="kt-notice" data-testid="pln-review-decision-required">
				<svg class="kt-notice-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><path d="M12 16v-4"></path><path d="M12 8h.01"></path></svg>
				<div class="kt-notice-body"><strong>Decision required</strong> — classify every included requirement, then accept the complete submission or return it for correction.</div>
			</div>

			<!-- Certification: one quiet line (name, date) with its trigger on
			     the same row, per §10.5 "Certification orientation" — capacity
			     and the full immutable statement reveal together on demand,
			     not as their own always-visible boxes. -->
			<div class="kt-group pln-certified-by" data-testid="pln-review-certified">
				<div style="display: flex; align-items: center; justify-content: space-between; gap: var(--kt-space-5); flex-wrap: wrap">
					<span style="font-size: 13.5px; color: var(--kt-color-neutral-800)">Certified by {{ context.submitted_by }} on {{ context.submitted_at }}</span>
					<button
						type="button"
						class="kt-btn kt-btn-ghost"
						data-testid="pln-review-certification-toggle"
						:aria-expanded="showCertification"
						@click="showCertification = !showCertification"
					>View certification</button>
				</div>
			</div>
			<!-- Not a disclosure: U06 draws no disclosure at all, and this block
			     had a body class with neither a `.kt-disclosure` around it nor a
			     head to open it — a class borrowed for its padding (found live 24
			     Sep 2026). The board draws certification as a plain group. -->
			<div v-if="showCertification" class="kt-group" data-testid="pln-review-certification">
				<div v-if="context.submitted_capacity" class="kt-meta-row" style="margin-bottom: var(--kt-space-3)">
					<div><span class="kt-label">Capacity</span><span class="kt-meta-value">{{ context.submitted_capacity }}</span></div>
				</div>
				{{ certification.text }}
			</div>

			<!-- U06-SEGREGATION — the actor who certified this submission cannot
			     review it. Content stays readable; both decisions are absent. -->
			<div v-if="task.maker_checker_blocked" class="kt-notice is-critical" data-testid="pln-review-segregation">
				<svg class="kt-notice-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
					<circle cx="12" cy="12" r="9"></circle><path d="M12 8v5M12 16h.01"></path>
				</svg>
				<div class="kt-notice-body">You cannot review a departmental plan you certified.</div>
			</div>

			<!-- U06-STALE-SOURCE — Accept goes, Return stays. -->
			<template v-if="staleSources.length">
				<div class="kt-notice is-warning" data-testid="pln-review-stale">
					<svg class="kt-notice-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
						<path d="M12 3l9 16H3z"></path><path d="M12 10v4M12 17h.01"></path>
					</svg>
					<div class="kt-notice-body">
						A source requirement changed after this submission was certified. Return it to the department for correction.
					</div>
				</div>
				<table class="kt-table" data-testid="pln-review-stale-table">
					<thead>
						<tr><th>Requirement</th><th>Revision certified</th><th>Current revision</th></tr>
					</thead>
					<tbody>
						<tr v-for="row in staleSources" :key="row.entry_id">
							<td>{{ row.title }}</td>
							<td>{{ row.certified_revision_display }}</td>
							<td>{{ row.current_revision_display }}</td>
						</tr>
					</tbody>
				</table>
			</template>

			<div class="kt-region">
				<h2>Certified requirements</h2>
				<div class="kt-meta-row" style="max-width: 760px; margin-bottom: var(--kt-space-5)" data-testid="pln-review-summary">
					<div><span class="kt-label">Included requirements</span><span class="kt-meta-value">{{ summary.included_requirements }}</span></div>
					<div><span class="kt-label">Included cost</span><span class="kt-meta-value">{{ summary.included_cost_display }}</span></div>
					<div><span class="kt-label">Excluded requirements</span><span class="kt-meta-value">{{ summary.excluded_requirements }}</span></div>
				</div>

				<!-- One line of source facts, one line of decision — not a
				     nine-column grid of individually labelled facts. -->
				<div
					v-for="row in entries"
					:key="row.entry_id"
					class="pln-review-row"
					data-testid="pln-review-row"
				>
					<div style="display: flex; align-items: flex-start; justify-content: space-between; gap: var(--kt-space-6)">
						<div style="flex: 1">
							<div style="font-family: var(--kt-font-heading); font-size: 19px">{{ row.title }}</div>
							<div style="display: flex; gap: var(--kt-space-5); margin-top: 6px; font-size: 13.5px; color: var(--kt-color-neutral-800)">
								<span>{{ row.quantity_number }} {{ row.unit_label }}</span>
								<span>Required by {{ row.required_by_display }}</span>
								<span style="font-variant-numeric: tabular-nums">{{ row.amount_display }}</span>
							</div>
						</div>
						<a href="#" class="kt-btn kt-btn-ghost" data-testid="pln-review-view" @click.prevent="$emit('view-requirement', row)">View requirement</a>
					</div>

					<div v-if="row.not_proceeding" class="pln-review-excluded" data-testid="pln-review-excluded">
						<div class="kt-meta-row">
							<div>
								<span class="kt-label">Status</span>
								<span class="kt-meta-value"><span class="kt-status is-muted">Not included this year</span></span>
							</div>
							<div>
								<span class="kt-label">Requirement type</span>
								<span class="kt-meta-value">Not applicable</span>
							</div>
						</div>
						<p class="kt-muted">{{ row.not_proceeding_reason }}</p>
					</div>

					<!-- The second line: the one Planner input, and what it derives. -->
					<template v-else>
						<div style="display: grid; grid-template-columns: 260px 240px 1fr; gap: var(--kt-space-5); align-items: end; margin-top: var(--kt-space-4)">
							<div class="kt-field">
								<label :for="`type-${row.entry_id}`">Requirement type</label>
								<!-- Addressable per requirement: a submission with several
								     needs one classification each, and a test (or a
								     screen-reader) has to be able to tell them apart. -->
								<select
									:id="`type-${row.entry_id}`"
									class="kt-input"
									data-testid="pln-review-type"
									:data-entry="row.entry_id"
									:disabled="!canDecide"
									:value="classifications[row.entry_id] || ''"
									@change="$emit('set-classification', { entry_id: row.entry_id, requirement_type: $event.target.value })"
								>
									<option value="">Select a requirement type</option>
									<option v-for="option in requirementTypes" :key="option.requirement_type" :value="option.requirement_type">
										{{ option.requirement_type }}
									</option>
								</select>
							</div>
							<div>
								<span class="kt-label">Category</span>
								<!-- Read-only, derived, never sent: §4.4. -->
								<div style="font-size: 15px; font-weight: 600; margin-top: 4px" data-testid="pln-review-category">{{ categoryFor(row.entry_id) }}</div>
							</div>
							<!-- U06's own third grid column, one per row (its own
							     grid-template-columns already reserved this 1fr — the
							     helper used to live once, globally, at the foot of the
							     whole list instead, disconnected from either row's own
							     controls when a submission carries more than one
							     requirement (found live 22 Sep 2026). -->
							<p class="kt-muted" style="font-size: 12.5px; margin: 0; padding-bottom: 9px" data-testid="pln-review-helper">
								Choose the requirement type. Category is set automatically.
							</p>
						</div>
						<div class="kt-group" style="margin-top: var(--kt-space-4)">
							<span class="kt-label">Budget line</span>
							<div style="font-size: 14px; margin-top: 2px">{{ row.budget_line_display }}</div>
						</div>
					</template>

					<p v-if="!row.not_proceeding && missingClassification(row)" class="pln-error-summary" data-testid="pln-review-row-error">
						Select the requirement type before accepting this departmental plan.
					</p>
				</div>
				<p v-if="!entries.length" class="kt-muted">No requirements in this submission.</p>
			</div>

			<!-- Decision. What acceptance does, and what it does not — one
			     kt-decision block, matching the artboard: the statement and
			     both buttons together, clustered at its right edge. -->
			<template v-if="!task.maker_checker_blocked">
				<div class="kt-decision" data-testid="pln-review-decision">
					<p class="pln-decision-statement" data-testid="pln-review-consequence">
						Accepting makes the included requirements available for annual plan preparation.
						It does not approve the Annual Procurement Plan.
					</p>
					<div class="pln-footer-actions" data-testid="pln-review-footer">
						<button
							type="button"
							class="kt-btn kt-btn-secondary"
							data-testid="pln-review-return"
							:disabled="pending || !canDecide"
							@click="$emit('return-to-department')"
						>
							Return to department
						</button>
						<!-- Absent, not disabled, when the evidence cannot support it. -->
						<button
							v-if="canAccept"
							type="button"
							class="kt-btn kt-btn-primary"
							data-testid="pln-review-accept"
							:disabled="pending"
							@click="$emit('accept')"
						>
							Accept departmental plan
						</button>
					</div>
				</div>
			</template>
		</div>
	</div>
</template>

<script setup>
import { computed, ref } from "vue";

const props = defineProps({
	task: { type: Object, default: () => ({}) },
	classifications: { type: Object, default: () => ({}) },
	pending: Boolean,
});

defineEmits(["set-classification", "accept", "return-to-department", "view-requirement"]);

// §10.5 "Certification orientation" — capacity and the full immutable
// statement reveal together, on demand, beneath the one quiet "Certified by
// … on …" line; never their own always-visible boxes.
const showCertification = ref(false);

const context = computed(() => props.task.context || {});
const certification = computed(() => props.task.certification || {});
// §10.5 summary strip — `get_dpp_validation_task` (dpp_read.py) puts these
// three facts on `context` alongside department/financial year, never on a
// separate `summary` key. Reading a `task.summary` that the read contract
// never sends rendered the three labels with nothing beside them: not an
// empty state, an undefined one (found live 22 Sep 2026).
const summary = computed(() => ({
	included_requirements: context.value.included_requirements,
	included_cost_display: context.value.included_cost_display,
	excluded_requirements: context.value.excluded_requirements,
}));
const entries = computed(() => props.task.entries || []);
const requirementTypes = computed(() => props.task.requirement_types || []);
const staleSources = computed(() => props.task.stale_sources || []);
const canDecide = computed(() => Boolean(props.task.can_decide));

const title = computed(() => `Review ${context.value.department || "the"}'s departmental plan`);
const referenceOnly = computed(() => (props.task.header?.reference_line || "").split(" · ")[0]);
const submissionNumber = computed(() => {
	const match = /Submission (\d+)/.exec(props.task.header?.reference_line || "");
	return match ? match[1] : "";
});
const statusLabel = computed(() =>
	props.task.status === "Open" ? "Awaiting Procurement review" : props.task.header?.badge || "",
);

function categoryFor(entryId) {
	const selected = props.classifications[entryId];
	if (!selected) return "—";
	const match = requirementTypes.value.find((option) => option.requirement_type === selected);
	return match ? match.procurement_category : "—";
}

function missingClassification(row) {
	return canDecide.value && !props.classifications[row.entry_id];
}

// U06-CLASSIFICATION-MISSING and U06-STALE-SOURCE both remove Accept and keep
// Return. The server decides too; this only avoids offering a decision that
// would certainly fail.
const canAccept = computed(() => {
	if (!canDecide.value || staleSources.value.length) return false;
	return entries.value.every((row) => row.not_proceeding || props.classifications[row.entry_id]);
});
</script>
