<!-- PLN-CHG-001 v1.18 §4.5/§4.7 Annual Plan record, ported class-for-class
     from U07 (Overview/Plan Items/Funding and readiness/Changes — five tabs
     total; Governance and publication is a placeholder here, built out in
     Phase 3F/3G) and U08 (Form Plan Items, still a dialog: §9's own route
     table groups U07/U08 under the one "Annual Plan record route"). The
     Active plan (U14) is rendered by ActivePlanScreen. -->
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
				<!-- FU-14: the actor who holds the open task reaches it from the record -->
				<button
					v-if="plan.open_task"
					type="button"
					class="kt-btn kt-btn-primary"
					data-testid="pln-open-task"
					@click="$emit('open-task', plan.open_task.route)"
				>
					{{ plan.open_task.label }}
				</button>
			</div>
		</div>

		<div v-if="errorSummary" class="pln-notice is-critical" role="alert" data-testid="pln-plan-error">
			<p class="pln-notice-title">This command could not be completed</p>
			<p>{{ errorSummary }}</p>
		</div>

		<!-- §5.2 — funding returned or stale is stated plainly -->
		<div v-if="fundingNotice" class="pln-notice" data-testid="pln-funding-notice">
			<p class="pln-notice-title">{{ fundingNotice.title }}</p>
			<p>{{ fundingNotice.text }}</p>
		</div>

		<div class="kt-tabs" role="tablist">
			<div class="kt-tab" role="tab" :aria-selected="tab === 'overview'" data-testid="pln-tab-overview" @click="tab = 'overview'">Overview</div>
			<div class="kt-tab" role="tab" :aria-selected="tab === 'items'" data-testid="pln-tab-items" @click="tab = 'items'">Plan Items</div>
			<div class="kt-tab" role="tab" :aria-selected="tab === 'funding'" data-testid="pln-tab-funding" @click="tab = 'funding'">Funding and readiness</div>
			<div class="kt-tab" role="tab" :aria-selected="tab === 'governance'" data-testid="pln-tab-governance" @click="tab = 'governance'">Governance and publication</div>
			<div class="kt-tab" role="tab" :aria-selected="tab === 'changes'" data-testid="pln-tab-changes" @click="tab = 'changes'">Changes</div>
		</div>

		<!-- ============================ Overview ============================ -->
		<template v-if="tab === 'overview'">
			<div class="kt-card kt-blueprint pln-strip-grid pln-strip-grid-5" data-testid="pln-plan-summary-strip">
				<i class="kt-corner tl"></i><i class="kt-corner tr"></i>
				<i class="kt-corner bl"></i><i class="kt-corner br"></i>
				<div class="pln-strip-field">
					<label>Plan Items</label>
					<div class="pln-val">{{ plan.summary?.plan_items ?? 0 }}</div>
				</div>
				<div class="pln-strip-field">
					<label>Departmental sources</label>
					<div class="pln-val">{{ plan.summary?.departmental_sources ?? 0 }}</div>
				</div>
				<div class="pln-strip-field">
					<label>Departments</label>
					<div class="pln-val">{{ plan.summary?.departments ?? 0 }}</div>
				</div>
				<div class="pln-strip-field">
					<label>Planned value</label>
					<div class="pln-val">{{ plan.summary?.value_display }}</div>
				</div>
				<div class="pln-strip-field">
					<label>Funding evidence</label>
					<div class="pln-val"><span class="kt-status" :class="fundingClass(plan.summary?.funding_evidence_state)">{{ plan.summary?.funding_evidence_state }}</span></div>
				</div>
			</div>

			<div v-if="topBlocker" class="kt-card kt-blueprint pln-card-pad" style="border-color: var(--status-attention)" data-testid="pln-before-submission">
				<i class="kt-corner tl"></i><i class="kt-corner tr"></i>
				<i class="kt-corner bl"></i><i class="kt-corner br"></i>
				<h3 style="font-size: 16px; margin: 0 0 4px;">Before submission</h3>
				<p>{{ topBlocker }}</p>
				<button type="button" class="kt-btn kt-btn-secondary" data-testid="pln-review-readiness" @click="tab = 'funding'">
					Review readiness
				</button>
			</div>

			<div class="kt-card kt-blueprint pln-card-pad" data-testid="pln-preparation">
				<i class="kt-corner tl"></i><i class="kt-corner tr"></i>
				<i class="kt-corner bl"></i><i class="kt-corner br"></i>
				<div class="kt-card-title">Preparation</div>
				<div class="pln-field" style="max-width: 420px">
					<label for="pln-project-name">Project name (if applicable)</label>
					<input
						id="pln-project-name" type="text" class="kt-input"
						data-testid="pln-project-name" :disabled="!plan.mutable"
						v-model="projectNameDraft"
					>
					<p class="pln-helper-text">Leave blank when this Plan covers several projects or a general portfolio.</p>
				</div>
			</div>

			<div class="pln-footer-bar">
				<button type="button" class="kt-btn kt-btn-ghost" @click="$emit('back')">Back to workspace</button>
				<button
					v-if="plan.mutable"
					type="button"
					class="kt-btn kt-btn-primary"
					data-testid="pln-save-details"
					:disabled="pending || projectNameDraft === (plan.project_name || '')"
					@click="$emit('save-details', { project_name: projectNameDraft })"
				>
					Save draft
				</button>
			</div>
		</template>

		<!-- ============================ Plan Items ============================ -->
		<template v-if="tab === 'items'">
			<div v-if="(plan.summary?.plan_items ?? 0) === 0" class="kt-card kt-blueprint pln-strip-grid" data-testid="pln-items-summary-strip">
				<i class="kt-corner tl"></i><i class="kt-corner tr"></i>
				<i class="kt-corner bl"></i><i class="kt-corner br"></i>
				<div class="pln-strip-field"><label>Plan Items</label><div class="pln-val is-zero">0</div></div>
				<div class="pln-strip-field"><label>Planned value</label><div class="pln-val is-zero">KES 0</div></div>
				<div class="pln-strip-field"><label>Unallocated requirements</label><div class="pln-val">{{ plan.unallocated_sources?.length ?? 0 }}</div></div>
				<div class="pln-strip-field"><label>Unallocated value</label><div class="pln-val">{{ unallocatedValueDisplay }}</div></div>
			</div>

			<div v-if="plan.plan_items?.length" class="kt-card kt-blueprint pln-card-pad" data-testid="pln-plan-items">
				<i class="kt-corner tl"></i><i class="kt-corner tr"></i>
				<i class="kt-corner bl"></i><i class="kt-corner br"></i>
				<table class="pln-table">
					<thead>
						<tr>
							<th>Plan Item</th><th>Department</th><th>Requirement type</th><th>Method</th>
							<th>Reservation</th><th>Completion</th><th class="pln-num">Value</th><th>Status</th>
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
							<td>{{ row.departments }}</td>
							<td>{{ row.requirement_type }}</td>
							<td>{{ row.procurement_method }}</td>
							<td>{{ row.reservation_category }}</td>
							<td>{{ row.completion_display }}</td>
							<td class="pln-num">{{ row.value_display }}</td>
							<td>
								<span class="kt-status" :class="row.source_correction_required ? 'is-critical' : 'is-draft'">
									{{ row.source_correction_required ? "Source correction required" : itemStateLabel(row.item_state) }}
								</span>
							</td>
						</tr>
					</tbody>
				</table>
			</div>

			<div class="kt-card kt-blueprint pln-card-pad" data-testid="pln-unallocated-sources">
				<i class="kt-corner tl"></i><i class="kt-corner tr"></i>
				<i class="kt-corner bl"></i><i class="kt-corner br"></i>
				<div class="kt-card-title">{{ plan.plan_items?.length ? "Accepted requirements not yet allocated" : "" }}</div>
				<template v-if="plan.unallocated_sources?.length">
					<table class="pln-table">
						<thead>
							<tr>
								<th></th><th>Requirement</th><th>Department</th><th>Source origin</th>
								<th>Classification</th><th class="pln-num">Quantity</th>
								<th>Procurement Budget Line</th><th class="pln-num">Amount</th>
							</tr>
						</thead>
						<tbody>
							<tr v-for="row in plan.unallocated_sources" :key="row.dpp_entry">
								<td><input type="checkbox" disabled checked></td>
								<td>{{ row.title }}</td>
								<td>{{ row.department }}</td>
								<td>{{ row.source_origin }}</td>
								<td>{{ row.classification }}</td>
								<td class="pln-num">{{ row.quantity_display }}</td>
								<td>{{ row.budget_line_display || row.budget_line }}</td>
								<td class="pln-num">{{ row.amount_display }}</td>
							</tr>
						</tbody>
					</table>
					<button
						v-if="plan.mutable"
						type="button"
						class="kt-btn kt-btn-primary"
						data-testid="pln-form-items"
						:disabled="pending"
						@click="$emit('open-form-dialog')"
					>
						Form Plan Items
					</button>
				</template>
				<template v-else-if="!plan.plan_items?.length">
					<h3>No accepted departmental entries</h3>
					<p>Accepted departmental entries will appear here automatically.</p>
				</template>
				<template v-else>
					<p style="font-weight: 600; margin: 0 0 4px">No unallocated requirements</p>
					<p style="margin: 0">Every accepted requirement is represented in the Plan Items above.</p>
				</template>
			</div>
		</template>

		<!-- ==================== Funding and readiness ==================== -->
		<template v-if="tab === 'funding'">
			<div v-if="plan.affordability" class="kt-card kt-blueprint pln-card-pad" data-testid="pln-budget-table" style="margin-bottom: 24px">
				<i class="kt-corner tl"></i><i class="kt-corner tr"></i>
				<i class="kt-corner bl"></i><i class="kt-corner br"></i>
				<div class="kt-card-title">Budget</div>
				<table class="pln-table">
					<thead>
						<tr>
							<th>Budget Line</th><th>Funding source</th><th class="pln-num">Approved</th>
							<th class="pln-num">Planned</th><th class="pln-num">Reserved</th>
							<th class="pln-num">Committed</th><th class="pln-num">Available</th>
						</tr>
					</thead>
					<tbody>
						<tr v-for="line in plan.affordability.lines" :key="line.budget_line">
							<td>{{ line.reference }}<span v-if="line.title"> · {{ line.title }}</span></td>
							<td>{{ line.funding_source }}</td>
							<td class="pln-num">{{ moneyDisplay(line.approved) }}</td>
							<td class="pln-num">{{ moneyDisplay(line.planned) }}</td>
							<td class="pln-num">{{ moneyDisplay(line.reserved) }}</td>
							<td class="pln-num">{{ moneyDisplay(line.committed) }}</td>
							<td class="pln-num">{{ moneyDisplay(line.available) }}</td>
						</tr>
					</tbody>
				</table>
				<span class="kt-status" :class="plan.affordability.within_approved ? 'is-live' : 'is-critical'">
					{{ plan.affordability.within_approved ? "Within approved amounts" : "Exceeds approved amounts" }}
				</span>
			</div>

			<div v-if="reservation" class="kt-card kt-blueprint pln-card-pad" data-testid="pln-reservation" style="margin-bottom: 24px">
				<i class="kt-corner tl"></i><i class="kt-corner tr"></i>
				<i class="kt-corner bl"></i><i class="kt-corner br"></i>
				<div class="kt-card-title">Reservation</div>
				<div class="pln-facts-row" style="margin-bottom: 12px">
					<div class="pln-fact"><span class="kt-label">Target</span><span class="pln-fact-val">{{ reservation.target_percent ? `${reservation.target_percent}%` : "Not published" }}</span></div>
					<div class="pln-fact"><span class="kt-label">Required allocation</span><span class="pln-fact-val">{{ reservation.required || "—" }}</span></div>
					<div class="pln-fact"><span class="kt-label">Planned qualifying allocation</span><span class="pln-fact-val">{{ reservation.qualifying }}</span></div>
					<div class="pln-fact"><span class="kt-label">Shortfall</span><span class="pln-fact-val">{{ reservation.shortfall || "—" }}</span></div>
					<div v-if="reservation.basis?.available" class="pln-fact"><span class="kt-label">Budget basis</span><span class="pln-fact-val">{{ reservation.basis.budget_reference }}, Version {{ reservation.basis.version_reference }}</span></div>
				</div>
				<span class="kt-status" :class="reservation.met ? 'is-live' : 'is-attention'">
					{{ reservation.met ? "Required allocation met" : "Required allocation not met" }}
				</span>
			</div>

			<div class="kt-card kt-blueprint pln-card-pad" data-testid="pln-method-schedule-checks" style="margin-bottom: 24px">
				<i class="kt-corner tl"></i><i class="kt-corner tr"></i>
				<i class="kt-corner bl"></i><i class="kt-corner br"></i>
				<div class="kt-card-title">Method and schedule checks</div>
				<span class="kt-status" :class="methodScheduleClass">{{ methodScheduleLabel }}</span>
			</div>

			<div class="kt-card kt-blueprint pln-card-pad" data-testid="pln-readiness">
				<i class="kt-corner tl"></i><i class="kt-corner tr"></i>
				<i class="kt-corner bl"></i><i class="kt-corner br"></i>
				<div class="kt-card-title">Plan readiness</div>
				<table class="pln-table">
					<thead><tr><th>Check</th><th>Result</th></tr></thead>
					<tbody>
						<tr v-for="row in plan.readiness" :key="row.check" :data-testid="`pln-readiness-${slug(row.check)}`">
							<td>{{ row.check }}</td>
							<td>
								<span class="kt-status" :class="kindClass(row.kind)">{{ row.result }}</span>
								<!-- O1 — invariant 26: the Planner confirms flagged items are legitimately separate -->
								<button
									v-if="row.check === 'Contract splitting review' && plan.mutable && plan.splitting_advisories?.length && !plan.splitting_confirmation"
									type="button"
									class="kt-btn kt-btn-ghost pln-inline-action"
									data-testid="pln-confirm-splitting"
									@click="$emit('confirm-splitting')"
								>
									Confirm
								</button>
							</td>
						</tr>
					</tbody>
				</table>
				<ul v-if="plan.splitting_advisories?.length" class="pln-advisory-list" data-testid="pln-splitting-advisories">
					<li v-for="(advisory, index) in plan.splitting_advisories" :key="index">{{ advisory.message || advisory.text }}</li>
				</ul>
			</div>

			<div v-if="plan.can_request_funding || plan.mutable" class="kt-card kt-blueprint pln-card-pad" data-testid="pln-funding-request" style="margin-top: 24px">
				<i class="kt-corner tl"></i><i class="kt-corner tr"></i>
				<i class="kt-corner bl"></i><i class="kt-corner br"></i>
				<p>{{ plan.can_request_funding ? "All pre-Finance readiness checks pass. Financial review has not yet been requested." : "Complete the readiness checks above before requesting plan funding confirmation." }}</p>
				<button
					type="button"
					class="kt-btn kt-btn-primary"
					data-testid="pln-request-funding"
					:disabled="!plan.can_request_funding || pending"
					@click="$emit('request-funding')"
				>
					Request plan funding confirmation
				</button>
			</div>
		</template>

		<!-- ================== Governance and publication ================== -->
		<!-- U11-HOPF (§10.4/§9's "Existing Plan record for preparation") — the
		     Head of Procurement Function's own preparation signature is the
		     existing final submission action, gated to the Draft record's own
		     route; it never gets a task or a review/{task_id} route of its
		     own (there is nothing to look up by task until this signs). -->
		<template v-if="tab === 'governance'">
			<div class="kt-card kt-blueprint pln-card-pad" data-testid="pln-preparation-decisions">
				<i class="kt-corner tl"></i><i class="kt-corner tr"></i>
				<i class="kt-corner bl"></i><i class="kt-corner br"></i>
				<div class="kt-card-title">Decisions</div>
				<p class="pln-card-subhead">No Preparation decision recorded yet.</p>
				<div class="pln-cert-box">
					<p>I confirm that the complete Annual Procurement Plan Version {{ plan.version_number }} is ready for Accounting Officer adoption.</p>
				</div>
			</div>
		</template>

		<!-- ============================ Changes ============================ -->
		<template v-if="tab === 'changes'">
			<div class="kt-card kt-blueprint pln-card-pad" data-testid="pln-changes">
				<i class="kt-corner tl"></i><i class="kt-corner tr"></i>
				<i class="kt-corner bl"></i><i class="kt-corner br"></i>
				<template v-if="plan.changes?.is_initial ?? true">
					<p style="font-weight: 600; margin: 0 0 4px">No earlier Version</p>
					<p style="margin: 0">This is the first Version of the Annual Plan.</p>
				</template>
				<template v-else>
					<table class="pln-table" style="margin-bottom: 12px">
						<thead><tr><th>Field</th><th>Change reason</th></tr></thead>
						<tbody>
							<tr>
								<td>Procurement description</td>
								<td>{{ plan.changes.change_reason || "—" }}</td>
							</tr>
						</tbody>
					</table>
					<div class="pln-facts-row">
						<div class="pln-fact"><span class="kt-label">Source set</span><span class="pln-fact-val">{{ plan.changes.source_set_changed ? "Changed" : "Unchanged" }}</span></div>
						<div class="pln-fact"><span class="kt-label">Quantities</span><span class="pln-fact-val">{{ plan.changes.quantities_changed ? "Changed" : "Unchanged" }}</span></div>
						<div class="pln-fact"><span class="kt-label">Value</span><span class="pln-fact-val">{{ plan.changes.value_changed ? "Changed" : "Unchanged" }}</span></div>
					</div>
				</template>
			</div>
		</template>

		<div v-if="plan.mutable || plan.funding_state === 'Awaiting confirmation'" class="pln-footer-bar">
			<div></div>
			<div class="pln-footer-actions">
				<button
					type="button"
					class="kt-btn kt-btn-primary"
					data-testid="pln-submit-consolidated"
					:disabled="!plan.can_submit || pending"
					@click="$emit('submit-consolidated')"
				>
					Sign and submit Annual Plan
				</button>
			</div>
		</div>
	</div>
</template>

<script setup>
import { computed, ref, watch } from "vue";

const props = defineProps({
	plan: { type: Object, default: () => ({}) },
	pending: Boolean,
	errorSummary: String,
});

defineEmits([
	"open-form-dialog", "navigate", "back", "request-funding", "submit-consolidated",
	"confirm-splitting", "open-task", "save-details",
]);

const tab = ref("overview");
const projectNameDraft = ref(props.plan.project_name || "");

// A quiet in-place refresh (record_version unchanged) carries nothing new —
// re-hydrating would discard what the Planner has typed since.
watch(
	() => props.plan,
	(plan, previous) => {
		if (previous && (previous.record_version ?? null) === (plan?.record_version ?? null)) return;
		projectNameDraft.value = plan?.project_name || "";
	}
);

const badgeClass = computed(() => {
	const badge = props.plan.header?.badge;
	if (badge === "Draft") return "is-draft";
	if (badge === "Returned") return "is-critical";
	if (badge === "Active") return "is-live";
	return "is-pending";
});

const FUNDING_CLASS = {
	Confirmed: "is-live",
	"Awaiting confirmation": "is-pending",
	Returned: "is-critical",
	Stale: "is-critical",
	"Not requested": "is-draft",
};
function fundingClass(state) {
	return FUNDING_CLASS[state] || "is-draft";
}

const KIND_CLASS = {
	neutral: "is-pending",
	live: "is-live",
	attention: "is-attention",
	critical: "is-critical",
	advisory: "is-attention",
};
function kindClass(kind) {
	return KIND_CLASS[kind] || "is-pending";
}

function itemStateLabel(state) {
	return { Draft: "Proposed" }[state] || state;
}

function slug(text) {
	return String(text || "").toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/(^-|-$)/g, "");
}

function moneyDisplay(amount) {
	return `KES ${Number(amount || 0).toLocaleString("en-KE", { maximumFractionDigits: 0 })}`;
}

const reservation = computed(() => props.plan.summary?.reservation || null);

const unallocatedValueDisplay = computed(() => {
	const total = (props.plan.unallocated_sources || []).reduce((sum, row) => sum + (Number(row.indicative_amount) || 0), 0);
	return moneyDisplay(total);
});

const topBlocker = computed(() => props.plan.blockers?.[0]?.message || "");

const methodScheduleClass = computed(() => (props.plan.readiness || []).some((r) => r.kind === "attention" || r.kind === "critical") ? "is-attention" : "is-live");
const methodScheduleLabel = computed(() => (methodScheduleClass.value === "is-live" ? "Configuration verified" : "Production configuration not verified"));

const fundingNotice = computed(() => {
	const state = props.plan.funding_state;
	if (state === "Awaiting confirmation") {
		return { title: "Awaiting Finance confirmation", text: "The Plan is locked while the Finance Confirmation Officer confirms the affordability statement." };
	}
	if (state === "Returned") {
		return { title: "Plan funding returned by Finance", text: "Correct the Plan Items and request plan funding confirmation again." };
	}
	if (state === "Stale") {
		return { title: "Funding confirmation is no longer current", text: "A per-line total changed since Finance confirmed. Request plan funding confirmation again before submission." };
	}
	return null;
});
</script>
