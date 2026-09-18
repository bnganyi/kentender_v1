<!-- PLN-CHG-001 v1.23 §10.5 — Procurement review of a departmental plan (U06),
     ported from U06.dc.html.

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
		<div class="pln-masthead">
			<div>
				<h1 class="kt-page-title" data-testid="pln-review-title">{{ title }}</h1>
				<p class="kt-page-lede">Check the certified requirements before adding them to the annual plan.</p>
			</div>
		</div>

		<div class="kt-meta-row pln-context-row" data-testid="pln-review-context">
			<div>
				<span class="kt-label">Reference</span>
				<span class="kt-meta-value">{{ referenceOnly }}</span>
			</div>
			<div>
				<span class="kt-label">Submission</span>
				<span class="kt-meta-value">{{ submissionNumber }}</span>
			</div>
			<div>
				<span class="kt-label">Financial year</span>
				<span class="kt-meta-value">{{ context.financial_year }}</span>
			</div>
			<div>
				<span class="kt-label">Status</span>
				<span class="kt-meta-value">
					<span class="kt-status" :class="`is-${task.header?.badge_kind || 'pending'}`">{{ statusLabel }}</span>
				</span>
			</div>
		</div>

		<!-- Certification: secondary evidence, with the full immutable statement
		     available rather than summarised away. -->
		<div class="kt-meta-row pln-certified-by" data-testid="pln-review-certified">
			<div>
				<span class="kt-label">Certified by</span>
				<span class="kt-meta-value">{{ context.submitted_by }}</span>
			</div>
			<!-- The capacity is what makes the certification mean something;
			     it is omitted rather than guessed (§10.5). -->
			<div v-if="context.submitted_capacity">
				<span class="kt-label">Capacity</span>
				<span class="kt-meta-value">{{ context.submitted_capacity }}</span>
			</div>
			<div>
				<span class="kt-label">Certified at</span>
				<span class="kt-meta-value">{{ context.submitted_at }}</span>
			</div>
		</div>
		<details class="kt-disclosure" data-testid="pln-review-certification">
			<summary class="kt-disclosure-head">
				<span class="kt-disclosure-title">View certification</span>
			</summary>
			<div class="kt-disclosure-body">{{ certification.text }}</div>
		</details>

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

		<div class="kt-kpi-row" data-testid="pln-review-summary">
			<div class="kt-kpi-card">
				<div class="kt-kpi-value">{{ summary.included_requirements }}</div>
				<div class="kt-kpi-sub">Included requirements</div>
			</div>
			<div class="kt-kpi-card">
				<div class="kt-kpi-value">{{ summary.included_cost_display }}</div>
				<div class="kt-kpi-sub">Included cost</div>
			</div>
			<div class="kt-kpi-card">
				<div class="kt-kpi-value">{{ summary.excluded_requirements }}</div>
				<div class="kt-kpi-sub">Excluded requirements</div>
			</div>
		</div>

		<!-- One card per requirement, not a nine-column grid: the first line is
		     the source facts, the second is the only decision the Planner makes
		     about it. -->
		<div
			v-for="row in entries"
			:key="row.entry_id"
			class="kt-card kt-blueprint pln-review-row"
			data-testid="pln-review-row"
		>
			<i class="kt-corner tl"></i><i class="kt-corner tr"></i>
			<i class="kt-corner bl"></i><i class="kt-corner br"></i>
			<div class="kt-meta-row">
				<div class="pln-review-name">
					<span class="kt-label">Requirement</span>
					<span class="kt-meta-value">{{ row.title }}</span>
				</div>
				<div>
					<span class="kt-label">Quantity</span>
					<span class="kt-meta-value">{{ row.quantity_number }}</span>
				</div>
				<div>
					<span class="kt-label">Unit</span>
					<span class="kt-meta-value">{{ row.unit_label }}</span>
				</div>
				<div>
					<span class="kt-label">Required by</span>
					<span class="kt-meta-value">{{ row.required_by_display }}</span>
				</div>
				<div>
					<span class="kt-label">Estimated cost</span>
					<span class="kt-meta-value">{{ row.amount_display }}</span>
				</div>
				<!-- Every other fact in this card is labelled; the action was
				     the one cell that was not, which left the reader to infer
				     what the link was for from the link alone. -->
				<div>
					<span class="kt-label">Action</span>
					<span class="kt-meta-value">
						<a href="#" data-testid="pln-review-view" @click.prevent="$emit('view-requirement', row)">View requirement</a>
					</span>
				</div>
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

			<!-- The second line: budget line, and the one Planner input. -->
			<div v-else class="kt-meta-row pln-review-classify">
				<div>
					<span class="kt-label">Budget line</span>
					<span class="kt-meta-value">{{ row.budget_line_display }}</span>
				</div>
				<div class="kt-field">
					<label :for="`type-${row.entry_id}`" class="kt-label">Requirement type</label>
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
					<!-- The label says where the value comes from: the Planner
					     cannot set it, and a bare "Category" invites the attempt. -->
					<span class="kt-label">Category (derived)</span>
					<!-- Read-only, derived, never sent: §4.4. -->
					<span class="kt-meta-value" data-testid="pln-review-category">{{ categoryFor(row.entry_id) }}</span>
				</div>
			</div>

			<p v-if="!row.not_proceeding && missingClassification(row)" class="pln-error-summary" data-testid="pln-review-row-error">
				Select the requirement type before accepting this departmental plan.
			</p>
		</div>
		<p v-if="!entries.length" class="kt-muted">No requirements in this submission.</p>

		<p v-if="entries.some((r) => !r.not_proceeding)" class="kt-muted" data-testid="pln-review-helper">
			Choose the requirement type. Category is set automatically.
		</p>

		<!-- Decision. What acceptance does, and what it does not. -->
		<template v-if="!task.maker_checker_blocked">
			<p class="kt-muted" data-testid="pln-review-consequence">
				Accepting makes the included requirements available for annual plan preparation.
				It does not approve the Annual Procurement Plan.
			</p>
			<div class="pln-footer" data-testid="pln-review-footer">
				<button
					type="button"
					class="kt-btn kt-btn-secondary"
					data-testid="pln-review-return"
					:disabled="pending || !canDecide"
					@click="$emit('return-to-department')"
				>
					Return to department
				</button>
				<div class="pln-footer-right">
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
</template>

<script setup>
import { computed } from "vue";

const props = defineProps({
	task: { type: Object, default: () => ({}) },
	classifications: { type: Object, default: () => ({}) },
	pending: Boolean,
});

defineEmits(["set-classification", "accept", "return-to-department", "view-requirement"]);

const context = computed(() => props.task.context || {});
const certification = computed(() => props.task.certification || {});
const summary = computed(() => props.task.summary || {});
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
