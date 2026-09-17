<!-- PLN-CHG-001 v1.18 §10.4 (U11) — the complete governance review: one
     long read-only page (Plan Items, Sources, Funding, Method and
     schedule, Reservations, Changes, Decisions) reached at its own task
     route (/procurement-planning/review/{task_id}) for Accounting Officer
     adoption and statutory approval. The Head of Procurement Function's own
     preparation signature (U11-HOPF) is a different screen entirely — see
     AnnualPlanScreen's Governance tab, reached on the Draft Plan's own
     record route per §9 ("Existing Plan record for preparation"); there is
     no governance task yet at that stage to route to.

     §10.4's own seclinks are anchor jumps down one page, not a tab switch
     (ported verbatim from the artboard's .seclinks) — every section stays
     reachable by scroll, reload or browser Find, and "View full details"
     on a Plan Item leaves to its own existing PlanItemEditorScreen route
     rather than duplicating that screen's content here. -->
<template>
	<div>
		<div class="pln-rhead">
			<div>
				<p class="kt-page-kicker">{{ task.header?.eyebrow }}</p>
				<h1 class="kt-page-title">{{ task.header?.title }}</h1>
				<div class="pln-rmeta">
					<span><span class="kt-label">Reference</span> {{ task.plan_reference }}</span>
					<span><span class="kt-label">Version</span> {{ task.version_number }}</span>
					<span class="kt-status" :class="badgeClass">{{ task.header?.badge }}</span>
				</div>
			</div>
			<a
				v-if="task.can_download_review_pack"
				:href="reviewPackUrl" class="kt-btn kt-btn-secondary" data-testid="rvw-download-pack"
			>Download review pack</a>
		</div>

		<nav class="pln-seclinks" data-testid="rvw-seclinks">
			<a v-for="link in SECTIONS" :key="link.id" :class="{ active: activeSection === link.id }" @click="scrollTo(link.id)">{{ link.label }}</a>
		</nav>

		<div v-if="errorSummary" class="pln-notice is-critical" role="alert" data-testid="rvw-error">
			<p class="pln-notice-title">This decision could not be completed</p>
			<p>{{ errorSummary }}</p>
		</div>

		<div v-if="task.late_activation_reason" class="pln-notice" data-testid="rvw-late-activation">
			<p class="pln-notice-title">Submitted after the start of the Financial Year</p>
			<p>{{ task.late_activation_reason }}</p>
		</div>

		<!-- U11-stale — the submitted content never changes; only the current
		     funding evidence has drifted from what was decided on. -->
		<div v-if="!task.funding_current" class="kt-card kt-blueprint pln-card-pad" data-testid="rvw-stale-notice" style="border-color: var(--kt-status-attention)">
			<p class="pln-notice-title" style="color: var(--kt-status-attention)">Review basis has changed</p>
			<p>The current Budget basis no longer matches the funding confirmation. The submitted content remains unchanged.</p>
		</div>

		<section id="rvw-items" class="pln-review-section">
			<div class="kt-card kt-blueprint pln-card-pad" data-testid="rvw-items">
				<i class="kt-corner tl"></i><i class="kt-corner tr"></i>
				<i class="kt-corner bl"></i><i class="kt-corner br"></i>
				<div class="kt-card-title">Plan Items</div>
				<table class="pln-table">
					<thead><tr><th>Plan Item</th><th>Category</th><th class="pln-num">Quantity</th><th>Unit</th><th class="pln-num">Value</th><th>Required by</th><th></th></tr></thead>
					<tbody>
						<tr v-for="row in task.items" :key="row.plan_item_id">
							<td>{{ row.title }}</td>
							<td>{{ row.procurement_category }}</td>
							<td class="pln-num">{{ row.quantity_number }}</td>
							<td>{{ row.unit_label }}</td>
							<td class="pln-num">{{ row.value_display }}</td>
							<td>{{ row.delivery_completion_display }}</td>
							<td><a @click="$emit('navigate', row.route)">View full details</a></td>
						</tr>
					</tbody>
				</table>
				<p class="pln-table-caption" data-testid="rvw-caption">{{ task.caption }}</p>
				<p class="pln-table-caption pln-table-caption-tight" data-testid="rvw-advisory-line">{{ task.advisory_line }}</p>
			</div>
		</section>

		<section id="rvw-sources" class="pln-review-section">
			<div class="kt-card kt-blueprint pln-card-pad" data-testid="rvw-sources">
				<i class="kt-corner tl"></i><i class="kt-corner tr"></i>
				<i class="kt-corner bl"></i><i class="kt-corner br"></i>
				<div class="kt-card-title">Sources</div>
				<table class="pln-table">
					<thead><tr><th>Source</th><th>Department</th><th class="pln-num">Quantity</th><th>Unit</th><th class="pln-num">Amount</th><th></th></tr></thead>
					<tbody>
						<tr v-for="row in task.sources" :key="row.source_key">
							<td>{{ row.plan_item_title }}</td>
							<td>{{ row.department }}</td>
							<td class="pln-num">{{ row.quantity_display }}</td>
							<td>{{ row.unit_label }}</td>
							<td class="pln-num">{{ row.amount_display }}</td>
							<td><a @click="$emit('open-source', row.source_key)" data-testid="rvw-source-link">View source evidence</a></td>
						</tr>
					</tbody>
				</table>
			</div>
		</section>

		<section id="rvw-funding" class="pln-review-section">
			<div class="kt-card kt-blueprint pln-card-pad" data-testid="rvw-funding">
				<i class="kt-corner tl"></i><i class="kt-corner tr"></i>
				<i class="kt-corner bl"></i><i class="kt-corner br"></i>
				<div class="kt-card-title">Funding</div>
				<table class="pln-table" style="margin-bottom: 12px">
					<thead>
						<tr>
							<th>Budget Line</th><th>Funding source</th><th class="pln-num">Approved</th>
							<th class="pln-num">Planned</th><th class="pln-num">Reserved</th><th class="pln-num">Committed</th><th class="pln-num">Available</th>
						</tr>
					</thead>
					<tbody>
						<tr v-for="row in task.funding?.rows" :key="row.budget_line">
							<td>{{ row.budget_line_label }}</td>
							<td>{{ row.funding_source }}</td>
							<td class="pln-num">{{ row.approved_display }}</td>
							<td class="pln-num">{{ row.planned_display }}</td>
							<td class="pln-num">{{ row.reserved_display }}</td>
							<td class="pln-num">{{ row.committed_display }}</td>
							<td class="pln-num">{{ row.available_display }}</td>
						</tr>
					</tbody>
				</table>
				<div class="pln-facts-row">
					<div class="pln-fact"><span class="kt-label">Statement as at</span><span class="pln-fact-val">{{ task.funding?.statement_as_at }}</span></div>
					<div class="pln-fact"><span class="kt-label">Confirmed by</span><span class="pln-fact-val">{{ task.funding?.confirmed_by }}</span></div>
				</div>
			</div>
		</section>

		<section id="rvw-method" class="pln-review-section">
			<div
				v-for="card in task.method_and_schedule" :key="card.plan_item_id"
				class="kt-card kt-blueprint pln-card-pad pln-method-card" data-testid="rvw-method"
			>
				<i class="kt-corner tl"></i><i class="kt-corner tr"></i>
				<i class="kt-corner bl"></i><i class="kt-corner br"></i>
				<div class="kt-card-title">Method and eligibility — {{ card.title }}</div>
				<div class="pln-facts-row" style="margin-bottom: 12px">
					<div class="pln-fact"><span class="kt-label">Method</span><span class="pln-fact-val">{{ card.method.method }}</span></div>
					<div class="pln-fact"><span class="kt-label">Procedure profile</span><span class="pln-fact-val">{{ card.method.profile }}</span></div>
					<div class="pln-fact"><span class="kt-label">Profile Version</span><span class="pln-fact-val">{{ card.method.version_number }}</span></div>
					<div class="pln-fact"><span class="kt-label">Conditions</span><span class="kt-status" :class="card.method.conditions_complete ? 'is-live' : 'is-pending'">{{ card.method.conditions_complete ? "Complete" : "Incomplete" }}</span></div>
				</div>
				<div class="pln-facts-row" style="margin-bottom: 20px">
					<div class="pln-fact"><span class="kt-label">Evidence</span><span class="pln-fact-val">{{ card.method.evidence_line }}</span></div>
					<div class="pln-fact"><span class="kt-label">Required specific authorisation</span><span class="pln-fact-val">{{ card.method.specific_authorisation }}</span></div>
				</div>
				<div class="kt-card-title">Schedule</div>
				<table class="pln-table" style="margin-bottom: 12px">
					<thead><tr><th>Milestone</th><th>Baseline</th></tr></thead>
					<tbody>
						<tr v-for="row in card.schedule.rows" :key="row.milestone">
							<td>{{ row.label }}</td>
							<td>{{ row.date_display }}<span v-if="row.source_boundary" style="font-size: 11px; color: var(--color-neutral-700)"> (source boundary)</span></td>
						</tr>
					</tbody>
				</table>
				<div class="pln-facts-row" style="margin-bottom: 12px">
					<div v-for="(label, field) in PERIOD_LABELS" :key="field" class="pln-fact">
						<span class="kt-label">{{ label }}</span><span class="pln-fact-val">{{ card.schedule.periods_display?.[field] }}</span>
					</div>
				</div>
				<div class="pln-facts-row">
					<div class="pln-fact"><span class="kt-label">Estimated delivery period</span><span class="pln-fact-val">{{ card.schedule.estimated_delivery_period_days }} calendar days</span></div>
					<div class="pln-fact"><span class="kt-label">Estimated completion</span><span class="pln-fact-val">{{ card.schedule.estimated_completion_display }}</span></div>
				</div>
			</div>
		</section>

		<section id="rvw-reservations" class="pln-review-section">
			<div class="kt-card kt-blueprint pln-card-pad" data-testid="rvw-reservation">
				<i class="kt-corner tl"></i><i class="kt-corner tr"></i>
				<i class="kt-corner bl"></i><i class="kt-corner br"></i>
				<div class="kt-card-title">Reservation</div>
				<div class="pln-facts-row" style="margin-bottom: 12px">
					<div class="pln-fact"><span class="kt-label">Target</span><span class="pln-fact-val">{{ task.reservation?.target_percent ? `${task.reservation.target_percent}%` : "Not mandatory" }}</span></div>
					<div class="pln-fact"><span class="kt-label">Required allocation</span><span class="pln-fact-val">{{ task.reservation?.required_allocation_display }}</span></div>
					<div class="pln-fact"><span class="kt-label">Planned qualifying allocation</span><span class="pln-fact-val">{{ task.reservation?.planned_qualifying_display }}</span></div>
					<div class="pln-fact"><span class="kt-label">Shortfall</span><span class="pln-fact-val">{{ task.reservation?.shortfall_display || "KES 0" }}</span></div>
					<div class="pln-fact"><span class="kt-label">Share of annual budget</span><span class="pln-fact-val">{{ task.reservation?.share_of_annual_display }}</span></div>
				</div>
				<div class="pln-facts-row" style="margin-bottom: 12px">
					<div class="pln-fact"><span class="kt-label">Budget basis</span><span class="pln-fact-val">{{ task.reservation?.budget_basis_reference }}</span></div>
					<div class="pln-fact"><span class="kt-label">Budget Version</span><span class="pln-fact-val">{{ task.reservation?.budget_version_display }}</span></div>
					<div class="pln-fact"><span class="kt-label">County requirement</span><span class="pln-fact-val">{{ task.reservation?.county_requirement_display }}</span></div>
				</div>
				<span class="kt-status" :class="task.reservation?.met ? 'is-live' : 'is-pending'">{{ task.reservation?.met ? "Required allocation met" : "Required allocation not met" }}</span>
			</div>
		</section>

		<section id="rvw-changes" class="pln-review-section">
			<div class="kt-card kt-blueprint pln-card-pad" data-testid="rvw-changes">
				<i class="kt-corner tl"></i><i class="kt-corner tr"></i>
				<i class="kt-corner bl"></i><i class="kt-corner br"></i>
				<div class="kt-card-title">Changes</div>
				<template v-if="task.changes?.is_initial ?? true">
					<p style="font-weight: 600; margin: 0 0 4px">No earlier Version</p>
					<p style="margin: 0">This is the first Version of the Annual Plan.</p>
				</template>
				<template v-else>
					<table class="pln-table" style="margin-bottom: 12px">
						<thead><tr><th>Field</th><th>Change reason</th></tr></thead>
						<tbody><tr><td>Procurement description</td><td>{{ task.changes.change_reason || "—" }}</td></tr></tbody>
					</table>
					<div class="pln-facts-row">
						<div class="pln-fact"><span class="kt-label">Source set</span><span class="pln-fact-val">{{ task.changes.source_set_changed ? "Changed" : "Unchanged" }}</span></div>
						<div class="pln-fact"><span class="kt-label">Quantities</span><span class="pln-fact-val">{{ task.changes.quantities_changed ? "Changed" : "Unchanged" }}</span></div>
						<div class="pln-fact"><span class="kt-label">Value</span><span class="pln-fact-val">{{ task.changes.value_changed ? "Changed" : "Unchanged" }}</span></div>
					</div>
				</template>
			</div>
		</section>

		<section id="rvw-decisions" class="pln-review-section">
			<GovernanceHistory :history="task.history || []" />

			<div v-if="task.authority_card" class="kt-card kt-blueprint pln-card-pad" data-testid="rvw-authority" style="margin-top: 16px">
				<i class="kt-corner tl"></i><i class="kt-corner tr"></i>
				<i class="kt-corner bl"></i><i class="kt-corner br"></i>
				<div class="pln-field-grid">
					<div class="pln-ro-field">
						<label>{{ task.authority_card.is_board ? "Governing body" : "Capacity" }}</label>
						<div class="pln-val">{{ task.authority_card.is_board ? task.authority_card.capacity_detail || task.authority_card.capacity : task.authority_card.capacity }}</div>
					</div>
					<div v-if="task.authority_card.is_board" class="pln-ro-field">
						<label>Required capacity</label>
						<div class="pln-val">Authorised Council decision recorder</div>
					</div>
					<div v-else class="pln-ro-field">
						<label>Accounting Officer adoption</label>
						<div class="pln-val">{{ task.authority_card.ao_adoption_line }}</div>
					</div>
				</div>
			</div>

			<div v-if="task.decision_statement" class="pln-cert-box" data-testid="rvw-statement" style="margin-top: 16px">
				<p>{{ task.decision_statement }}</p>
			</div>

			<div v-if="task.authority_card?.is_board && task.can_decide" class="pln-field" style="max-width: 320px; margin-top: 12px" data-testid="rvw-resolution-field">
				<label for="rvw-resolution">Resolution reference</label>
				<input id="rvw-resolution" type="text" class="kt-input" data-testid="rvw-resolution" v-model="resolutionReference" />
			</div>

			<div v-if="task.can_decide" class="pln-footer-bar">
				<button
					type="button" class="kt-btn kt-btn-secondary" data-testid="rvw-return"
					:disabled="pending" @click="$emit('open-return-dialog')"
				>Return for correction</button>
				<button
					type="button" class="kt-btn kt-btn-primary" data-testid="rvw-confirm"
					:disabled="pending || !task.can_decide_positive || (task.authority_card?.is_board && !resolutionReference.trim())"
					@click="$emit('confirm', resolutionReference.trim())"
				>{{ task.confirm_label }}</button>
			</div>
		</section>
	</div>
</template>

<script setup>
import { computed, ref } from "vue";
import GovernanceHistory from "./GovernanceHistory.vue";
import { reviewPackDownloadUrl } from "../data/planningApi.js";

const props = defineProps({
	task: { type: Object, default: () => ({}) },
	pending: Boolean,
	errorSummary: String,
});

defineEmits(["confirm", "open-return-dialog", "navigate", "open-source"]);

const resolutionReference = ref("");
const activeSection = ref("rvw-items");

const SECTIONS = [
	{ id: "rvw-items", label: "Plan Items" },
	{ id: "rvw-sources", label: "Sources" },
	{ id: "rvw-funding", label: "Funding" },
	{ id: "rvw-method", label: "Method and schedule" },
	{ id: "rvw-reservations", label: "Reservations" },
	{ id: "rvw-changes", label: "Changes" },
	{ id: "rvw-decisions", label: "Decisions" },
];

const PERIOD_LABELS = {
	tendering_period_days: "Tendering",
	evaluation_period_days: "Evaluation",
	award_approval_buffer_days: "Award approval buffer",
	notification_buffer_days: "Notification buffer",
	standstill_period_days: "Standstill",
};

const badgeClass = computed(() => (props.task.header?.badge === "Active" ? "is-live" : "is-pending"));

const reviewPackUrl = computed(() => (props.task.task ? reviewPackDownloadUrl(props.task.task) : ""));

function scrollTo(id) {
	activeSection.value = id;
	const el = document.getElementById(id);
	if (el) el.scrollIntoView({ behavior: "smooth", block: "start" });
}
</script>
