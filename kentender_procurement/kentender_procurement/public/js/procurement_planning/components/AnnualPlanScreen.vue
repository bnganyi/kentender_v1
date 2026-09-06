<!-- PLN-UI-07/08 Annual Plan workbench (§12.7), rendering PLN-DES-07 v1.12
     class-for-class: the five-field summary strip (with Reserved share), the
     accepted-entries pool with its unallocated caption, the Plan Items card
     with its empty state, the nine-row Plan readiness card and the footer's
     version-level funding request + submission. The Active plan (PLN-DES-14)
     is rendered by ActivePlanScreen. -->
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
					type="button"
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

		<!-- §5.2 — funding returned or stale is stated plainly -->
		<div v-if="fundingNotice" class="pln-notice" data-testid="pln-funding-notice">
			<p class="pln-notice-title">{{ fundingNotice.title }}</p>
			<p>{{ fundingNotice.text }}</p>
		</div>

		<!-- summary strip -->
		<div class="kt-card kt-blueprint pln-strip-grid pln-strip-grid-5" data-testid="pln-plan-summary-strip">
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
			<div class="pln-strip-field">
				<label>Reserved share</label>
				<div class="pln-val" data-testid="pln-reserved-share">{{ plan.summary?.reserved_share_display }}</div>
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
						<th>Procurement Budget Line</th><th class="pln-num">Amount</th><th>Status</th>
					</tr>
				</thead>
				<tbody>
					<tr v-for="row in plan.unallocated_sources" :key="row.dpp_entry">
						<td>{{ row.title }}</td>
						<td>{{ row.department }}</td>
						<td>{{ row.source_origin }}</td>
						<td>{{ row.classification }}</td>
						<td class="pln-num">{{ row.quantity_display }}</td>
						<td>{{ row.budget_line_display || row.budget_line }}</td>
						<td class="pln-num">{{ row.amount_display }}</td>
						<td><span class="kt-status is-pending">Unallocated</span></td>
					</tr>
				</tbody>
			</table>
			<p v-if="plan.unallocated_caption" class="pln-table-caption">{{ plan.unallocated_caption }}</p>
			<!-- PLN-DES-16 — no accepted sources -->
			<div v-else class="pln-empty-state" data-testid="pln-no-sources">
				<h3>No accepted departmental entries</h3>
				<p>Accepted departmental entries will appear here automatically.</p>
			</div>
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
							<span
								class="kt-status"
								:class="row.source_correction_required ? 'is-critical' : 'is-draft'"
							>
								{{ row.source_correction_required ? "Source correction required" : itemStateLabel(row.item_state) }}
							</span>
						</td>
					</tr>
				</tbody>
			</table>
		</div>

		<!-- Plan readiness (nine rows; a tenth for a county entity) -->
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

		<div class="pln-footer-bar">
			<button type="button" class="kt-btn kt-btn-ghost" @click="$emit('back')">Back to workspace</button>
			<div v-if="plan.mutable || plan.funding_state === 'Awaiting Finance'" class="pln-footer-actions">
				<button
					type="button"
					class="kt-btn kt-btn-secondary"
					data-testid="pln-request-funding"
					:disabled="!plan.can_request_funding || pending"
					@click="$emit('request-funding')"
				>
					Request plan funding confirmation
				</button>
				<button
					type="button"
					class="kt-btn kt-btn-primary"
					data-testid="pln-submit-consolidated"
					:disabled="!plan.can_submit || pending"
					@click="$emit('submit-consolidated')"
				>
					{{ plan.is_correction ? "Submit corrected Plan" : "Submit consolidated Plan" }}
				</button>
			</div>
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

defineEmits(["open-form-dialog", "navigate", "back", "request-funding", "submit-consolidated", "confirm-splitting"]);

const badgeClass = computed(() => {
	const badge = props.plan.header?.badge;
	if (badge === "Draft") return "is-draft";
	if (badge === "Returned") return "is-critical";
	if (badge === "Active") return "is-live";
	return "is-pending";
});

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

const fundingNotice = computed(() => {
	const state = props.plan.funding_state;
	if (state === "Awaiting Finance") {
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
