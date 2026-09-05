<!-- PLN-UI-14 Active Annual Procurement Plan (§12.12), rendering PLN-DES-14
     class-for-class: the five-field strip with Schedule health and Activated,
     the Plan Items table with the live Requisition-availability projection
     and a per-row schedule toggle, the three-tier Schedule card (baseline
     locked, forecast revisable through the cascade dialog, actual
     projection-only — em dashes until a projection arrives), and the
     adoption/approval/publication card. The only edit path is "Shift
     schedule from here" (PLN-DES-14A). -->
<template>
	<div>
		<div class="pln-header-row">
			<div class="pln-header-left">
				<p class="kt-page-kicker">{{ plan.header?.eyebrow }}</p>
				<h1 class="kt-page-title">{{ plan.header?.title }}</h1>
				<p class="pln-quiet-ref">{{ plan.header?.reference_line }}</p>
				<span class="kt-status is-live" data-testid="pln-plan-badge">{{ plan.header?.badge }}</span>
			</div>
			<button
				v-if="plan.can_act && !plan.has_open_successor"
				type="button"
				class="kt-btn kt-btn-primary" data-testid="pln-begin-update"
				:disabled="pending" @click="$emit('begin-update')"
			>
				Prepare plan update
			</button>
		</div>

		<div v-if="errorSummary" class="pln-notice is-critical" role="alert" data-testid="pln-plan-error">
			<p class="pln-notice-title">This command could not be completed</p>
			<p>{{ errorSummary }}</p>
		</div>

		<div class="kt-card kt-blueprint pln-strip-grid pln-strip-grid-5" data-testid="pln-active-summary-strip">
			<i class="kt-corner tl"></i><i class="kt-corner tr"></i>
			<i class="kt-corner bl"></i><i class="kt-corner br"></i>
			<div class="pln-strip-field"><label>Plan Items</label><div class="pln-val">{{ view.summary?.plan_items }}</div></div>
			<div class="pln-strip-field"><label>Approved value</label><div class="pln-val">{{ view.summary?.value_display }}</div></div>
			<div class="pln-strip-field"><label>Departments</label><div class="pln-val">{{ view.summary?.departments }}</div></div>
			<div class="pln-strip-field"><label>Schedule health</label><div class="pln-val" data-testid="pln-active-health">{{ view.summary?.schedule_health_display }}</div></div>
			<div class="pln-strip-field"><label>Activated</label><div class="pln-val">{{ view.summary?.activated_display }}</div></div>
		</div>

		<div class="kt-card kt-blueprint pln-card-pad" data-testid="pln-active-items">
			<i class="kt-corner tl"></i><i class="kt-corner tr"></i>
			<i class="kt-corner bl"></i><i class="kt-corner br"></i>
			<div class="kt-card-title">Plan Items</div>
			<table class="pln-table">
				<thead>
					<tr>
						<th>Plan Item</th><th>Department</th><th>Source origin</th><th>Strategic Objective</th>
						<th>Method</th><th>Completion</th><th class="pln-num">Value</th>
						<th>Requisition availability</th><th></th>
					</tr>
				</thead>
				<tbody>
					<tr v-for="row in view.items" :key="row.plan_item_id" :data-testid="`pln-active-row-${row.plan_item_id}`">
						<td>{{ row.plan_item_id }} · {{ row.title }}</td>
						<td>{{ row.department }}</td>
						<td>{{ row.source_origin }}</td>
						<td>{{ row.strategic_objective_label }}</td>
						<td>{{ row.procurement_method }}</td>
						<td>{{ row.completion_display }}</td>
						<td class="pln-num">{{ row.value_display }}</td>
						<td>{{ row.requisition_availability_display }}</td>
						<td style="text-align: right">
							<button
								type="button"
								class="kt-btn kt-btn-ghost"
								:data-testid="`pln-active-schedule-${row.plan_item_id}`"
								:aria-expanded="opened === row.plan_item_id ? 'true' : 'false'"
								@click="toggle(row.plan_item_id)"
							>
								{{ opened === row.plan_item_id ? "Hide schedule" : "View" }}
							</button>
						</td>
					</tr>
				</tbody>
			</table>
		</div>

		<!-- Schedule card for the opened item -->
		<div v-if="openedItem" class="kt-card kt-blueprint pln-card-pad" data-testid="pln-schedule-card">
			<i class="kt-corner tl"></i><i class="kt-corner tr"></i>
			<i class="kt-corner bl"></i><i class="kt-corner br"></i>
			<div class="kt-card-title">Schedule — {{ openedItem.title }}</div>
			<table class="pln-table pln-schedule-table">
				<thead>
					<tr><th>Milestone</th><th>Baseline</th><th>Forecast</th><th>Actual</th><th>Variance vs baseline</th><th></th></tr>
				</thead>
				<tbody>
					<tr v-for="row in openedItem.schedule" :key="row.milestone" :data-testid="`pln-schedule-${row.milestone}`" :class="{ 'is-behind': row.behind }">
						<td>{{ row.label }}</td>
						<td class="pln-baseline-val">{{ display(row.baseline) }}</td>
						<td><span class="pln-forecast-val">{{ display(row.forecast) }}</span></td>
						<td class="pln-actual-val">{{ row.actual ? display(row.actual) : "—" }}</td>
						<td>{{ variance(row) }}</td>
						<td style="text-align: right">
							<button
								v-if="row.can_shift && plan.can_act"
								type="button"
								class="kt-btn kt-btn-ghost"
								:data-testid="`pln-shift-${row.milestone}`"
								@click="$emit('shift', { item: openedItem, milestone: row.milestone })"
							>
								Shift schedule from here
							</button>
						</td>
					</tr>
				</tbody>
			</table>
		</div>

		<div class="kt-card kt-blueprint pln-card-pad" data-testid="pln-active-governance">
			<i class="kt-corner tl"></i><i class="kt-corner tr"></i>
			<i class="kt-corner bl"></i><i class="kt-corner br"></i>
			<div class="kt-card-title">Adoption, approval and publication</div>
			<div class="pln-field-grid pln-field-grid-3">
				<div class="pln-ro-field"><label>Accounting Officer adoption</label><div class="pln-val">{{ view.governance_card?.ao_adoption_line }}</div></div>
				<div class="pln-ro-field"><label>Statutory approval</label><div class="pln-val">{{ view.governance_card?.statutory_approval_line }}</div></div>
				<div class="pln-ro-field">
					<label>Publication</label>
					<div class="pln-val">
						{{ view.governance_card?.publication_line }}
						<button
							v-if="view.governance_card?.publication_route"
							type="button"
							class="kt-btn kt-btn-ghost pln-inline-action"
							data-testid="pln-publication-link"
							@click="$emit('navigate', view.governance_card.publication_route)"
						>
							View
						</button>
					</div>
				</div>
			</div>
		</div>

		<div class="pln-footer-bar">
			<button type="button" class="kt-btn kt-btn-ghost" @click="$emit('back')">Back to workspace</button>
		</div>
	</div>
</template>

<script setup>
import { computed, ref } from "vue";

const props = defineProps({
	plan: { type: Object, default: () => ({}) },
	pending: Boolean,
	errorSummary: String,
});

defineEmits(["begin-update", "navigate", "back", "shift"]);

const view = computed(() => props.plan.active_view || {});
const opened = ref("");
const openedItem = computed(() => (view.value.items || []).find((row) => row.plan_item_id === opened.value) || null);

function toggle(planItemId) {
	opened.value = opened.value === planItemId ? "" : planItemId;
}

const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
function display(iso) {
	if (!iso) return "—";
	const [y, m, d] = iso.split("-").map(Number);
	return `${d} ${MONTHS[m - 1]} ${y}`;
}

// PLN-DES-14 — variance is a fact of an actual date; without one it is an em dash
function variance(row) {
	if (row.variance_baseline_days == null) return "—";
	const days = row.variance_baseline_days;
	if (days === 0) return "On baseline";
	return `${days > 0 ? "+" : ""}${days} day${Math.abs(days) === 1 ? "" : "s"}`;
}
</script>
