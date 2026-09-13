<!-- PLN-CHG-001 v1.18 §9.1/§10.2 Procurement Planning workspace, ported
     class-for-class from U01-A..G: masthead, plain inline Financial Year
     filter, the Annual Plan card (one block, or an Active-plus-candidate
     pair — U01-B), one card per actionable row ("Your actions"), the
     amber not-included notice and the "Departmental plans" table — plus
     the Forbidden / no-context / load-error states every KT-STD record
     page shares. No Procuring Entity selector, multi-year control, ranking
     control or Create Annual Plan button exists anywhere on this screen. -->
<template>
	<div>
		<div class="pln-breadcrumb">Home &gt; Procurement Planning</div>

		<div class="pln-masthead">
			<div>
				<div class="kt-page-kicker">PROCUREMENT PLANNING</div>
				<h1 class="kt-page-title">Annual procurement planning</h1>
				<p class="kt-page-lede">
					Prepare departmental requirements, review the Annual Plan and follow its approval.
				</p>
			</div>
		</div>

		<!-- loading skeleton -->
		<div v-if="loading" class="kt-card kt-blueprint" style="padding: 0; overflow: hidden" data-testid="pln-loading">
			<i class="kt-corner tl"></i><i class="kt-corner tr"></i>
			<i class="kt-corner bl"></i><i class="kt-corner br"></i>
			<div v-for="row in 3" :key="row" class="pln-skel-row">
				<div class="kt-skel" style="width: 72%"></div>
				<div class="kt-skel" style="width: 52%"></div>
				<div class="kt-skel" style="width: 52%"></div>
				<div class="kt-skel" style="width: 44%"></div>
			</div>
		</div>

		<!-- load error, with the generated support reference -->
		<div v-else-if="error" class="kt-card kt-blueprint pln-state-card" data-testid="pln-error">
			<i class="kt-corner tl"></i><i class="kt-corner tr"></i>
			<i class="kt-corner bl"></i><i class="kt-corner br"></i>
			<h3>Procurement Planning could not be loaded</h3>
			<p>Try again. If the problem continues, quote the support reference shown below.</p>
			<button class="kt-btn kt-btn-secondary" @click="$emit('reload')">Try again</button>
			<p class="pln-support-ref">Support reference: {{ supportRef }}</p>
		</div>

		<!-- the verdict resolved before anything else rendered (PLN-AC-111..113):
		     no control, no strip, no table. -->
		<div v-else-if="workspace.outcome === 'FORBIDDEN'" class="kt-card kt-blueprint pln-state-card" data-testid="pln-forbidden">
			<i class="kt-corner tl"></i><i class="kt-corner tr"></i>
			<i class="kt-corner bl"></i><i class="kt-corner br"></i>
			<h3>{{ forbidden.heading }}</h3>
			<p>{{ forbidden.text }}</p>
		</div>

		<!-- a responsibility but no eligible Financial Year -->
		<div v-else-if="workspace.outcome === 'NO_CONTEXT'" class="kt-card kt-blueprint pln-state-card" data-testid="pln-no-context">
			<i class="kt-corner tl"></i><i class="kt-corner tr"></i>
			<i class="kt-corner bl"></i><i class="kt-corner br"></i>
			<h3>Procurement Planning is not available</h3>
			<p>No configured Financial Year is available for Planning.</p>
		</div>

		<template v-else>
			<!-- U01's own inline filter: a plain control at text weight, not a
			     bordered card (§11.2). Bound to the caller's own selection, never
			     the server echo: a control bound to the last response snaps back
			     to the old year while the new one is still loading. -->
			<div class="pln-filter-strip" data-testid="pln-context-strip">
				<div class="pln-filter-field">
					<label for="pln-fy-select">Financial Year</label>
					<select
						id="pln-fy-select"
						class="kt-input"
						data-testid="pln-fy-select"
						:value="selectedFinancialYear || context.financial_year || ''"
						@change="$emit('select-financial-year', $event.target.value)"
					>
						<option v-for="year in context.financial_years || []" :key="year.id" :value="year.id">
							{{ year.label }}
						</option>
					</select>
				</div>
				<!-- one schedule-health count, only once an Active plan exists -->
				<span v-if="scheduleHealth" class="pln-strip-quiet" data-testid="pln-schedule-health">
					· {{ scheduleHealth }}
				</span>
				<!-- the remembered selection always has a visible reset -->
				<button
					v-if="context.resolved_financial_year_source === 'saved_default'"
					type="button"
					class="kt-btn kt-btn-ghost pln-filter-reset"
					data-testid="pln-fy-reset"
					@click="$emit('reset-financial-year')"
				>
					Reset
				</button>
			</div>

			<!-- waiting work is neutral read-only text, never a queue with controls -->
			<p
				v-for="(row, index) in workspace.waiting || []"
				:key="`waiting-${index}`"
				class="pln-strip-quiet pln-waiting"
				data-testid="pln-waiting"
			>
				{{ row.item }} · {{ row.scope }}
			</p>

			<div class="pln-cards-col">
				<!-- U01-A/B/C/F/G: the Annual Plan card, one block or an
				     Active-plus-candidate pair; U01-D: no plan yet at all. -->
				<div v-if="planBlocks.length" class="kt-card kt-blueprint pln-card-pad" data-testid="pln-annual-plan-card">
					<i class="kt-corner tl"></i><i class="kt-corner tr"></i>
					<i class="kt-corner bl"></i><i class="kt-corner br"></i>
					<div class="kt-card-title">Annual Plan</div>
					<div class="pln-fact" style="margin-bottom: 12px">
						<span class="kt-label">Reference</span>
						<span class="pln-fact-val">{{ workspace.annual_plan.plan_reference }}</span>
					</div>
					<div
						v-for="block in planBlocks"
						:key="block.kind"
						class="pln-plan-block"
						:data-testid="`pln-plan-block-${block.kind}`"
					>
						<p v-if="block.kind === 'candidate'" class="pln-card-subhead">
							The Active Plan remains in force while this candidate is reviewed.
						</p>
						<div class="pln-plan-block-row">
							<div class="pln-facts-row">
								<div class="pln-fact"><span class="kt-label">Version</span><span class="pln-fact-val">{{ block.version_number }}</span></div>
								<div class="pln-fact"><span class="kt-label">Status</span><span class="kt-status" :class="statusClass(block.version_status)">{{ block.version_status }}</span></div>
								<div class="pln-fact"><span class="kt-label">Funding evidence</span><span class="kt-status" :class="fundingClass(block.funding_state)">{{ block.funding_state }}</span></div>
								<div class="pln-fact"><span class="kt-label">Plan Items</span><span class="pln-fact-val">{{ block.plan_items }}</span></div>
								<div class="pln-fact"><span class="kt-label">{{ block.version_status === 'Draft' ? 'Planned' : 'Approved' }} value</span><span class="pln-fact-val">{{ block.value_display }}</span></div>
							</div>
							<button
								v-if="block.action"
								type="button"
								:class="['kt-btn', block.action_kind === 'primary' ? 'kt-btn-primary' : 'kt-btn-secondary']"
								:disabled="pending"
								:data-testid="`pln-plan-action-${block.kind}`"
								@click="$emit('navigate', block.route)"
							>
								{{ block.action }}
							</button>
						</div>
					</div>
				</div>
				<div v-else class="kt-card kt-blueprint pln-card-pad" data-testid="pln-no-plan">
					<i class="kt-corner tl"></i><i class="kt-corner tr"></i>
					<i class="kt-corner bl"></i><i class="kt-corner br"></i>
					<div class="kt-card-title">No Annual Plan yet for {{ context.financial_year_label || context.financial_year }}</div>
					<p class="pln-card-subhead">The Draft Annual Plan is created when the first departmental plan is accepted.</p>
				</div>

				<!-- one card per actionable row (U01's "YOUR ACTIONS" card): each
				     row's own headline is a distinct piece of work, never merged
				     into one generic "Actions" list. -->
				<div
					v-for="(row, index) in actionable"
					:key="`actionable-${index}`"
					class="kt-card kt-blueprint pln-card-pad"
					data-testid="pln-actionable"
				>
					<i class="kt-corner tl"></i><i class="kt-corner tr"></i>
					<i class="kt-corner bl"></i><i class="kt-corner br"></i>
					<div class="kt-page-kicker">YOUR ACTIONS</div>
					<div class="kt-card-title" style="margin: 4px 0 12px">{{ row.headline }}</div>
					<div class="pln-ready-row">
						<div v-if="row.supporting" class="pln-ready-sub">{{ row.supporting }}</div>
						<button
							type="button"
							class="kt-btn kt-btn-primary"
							:disabled="pending"
							:data-testid="`pln-work-action-${index}`"
							@click="onWorkAction(row)"
						>
							{{ row.action }}
						</button>
					</div>
				</div>

				<!-- the amber not-included notice -->
				<div v-if="workspace.not_included" class="pln-notice" data-testid="pln-not-included">
					<p class="pln-notice-title">{{ workspace.not_included.title }}</p>
					<p>{{ workspace.not_included.text }}</p>
				</div>

				<!-- departmental plans card -->
				<div class="kt-card kt-blueprint pln-card-pad" data-testid="pln-departmental-plans">
					<i class="kt-corner tl"></i><i class="kt-corner tr"></i>
					<i class="kt-corner bl"></i><i class="kt-corner br"></i>
					<div class="kt-card-title">{{ workspace.departmental_plans_heading }}</div>
					<p class="pln-card-subhead">{{ workspace.departmental_plans_lede }}</p>
					<table v-if="(workspace.departmental_plans || []).length" class="pln-table">
						<thead>
							<tr>
								<th>Department</th>
								<th class="pln-num">Submission</th>
								<th class="pln-num">Requirements</th>
								<th class="pln-num">Value</th>
								<th>Status</th>
								<th></th>
							</tr>
						</thead>
						<tbody>
							<tr v-for="row in workspace.departmental_plans" :key="row.dpp_reference">
								<td>{{ row.department }}</td>
								<td class="pln-num">{{ row.version }}</td>
								<td class="pln-num">{{ row.requirements }}</td>
								<td class="pln-num">{{ row.value }}</td>
								<td>
									<span class="kt-status" :class="statusClass(row.status)">{{ row.status }}</span>
								</td>
								<td style="text-align: right">
									<button v-if="row.route" type="button" class="kt-btn kt-btn-ghost" @click="$emit('navigate', row.route)">
										View
									</button>
								</td>
							</tr>
						</tbody>
					</table>
					<p class="pln-table-caption kt-muted" data-testid="pln-count-label">{{ workspace.count_label }}</p>
				</div>
			</div>
		</template>
	</div>
</template>

<script setup>
import { computed } from "vue";

const props = defineProps({
	loading: Boolean,
	error: String,
	supportRef: String,
	workspace: { type: Object, default: () => ({}) },
	selectedFinancialYear: { type: String, default: "" },
	pending: Boolean,
});

const emit = defineEmits(["reload", "select-financial-year", "reset-financial-year", "open-departmental-plan", "navigate"]);

const context = computed(() => props.workspace.context || {});
const forbidden = computed(() => props.workspace.forbidden || {});
const actionable = computed(() => props.workspace.actionable || []);
const planBlocks = computed(() => (props.workspace.annual_plan || {}).blocks || []);

const scheduleHealth = computed(() => {
	const health = props.workspace.schedule_health;
	if (!health || typeof health.total !== "number") return "";
	const noun = health.total === 1 ? "item" : "items";
	return `${health.behind} of ${health.total} ${noun} behind baseline`;
});

// A shared, generic status-to-colour mapping — the exact wording ("Draft",
// "Active", "Awaiting Accounting Officer", ...) is always the server's own
// literal, never re-derived here.
const LIVE_STATUSES = new Set(["Active", "Accepted", "Confirmed"]);
const ATTENTION_STATUSES = new Set(["Draft", "Draft update", "Awaiting Accounting Officer", "Awaiting statutory approval", "Awaiting validation", "Not requested", "Awaiting confirmation"]);
const CRITICAL_STATUSES = new Set(["Returned", "Not submitted — window closed", "Stale", "Publication failed", "Withdrawn for correction"]);

function statusClass(status) {
	if (LIVE_STATUSES.has(status)) return "is-live";
	if (CRITICAL_STATUSES.has(status)) return "is-critical";
	if (ATTENTION_STATUSES.has(status) || /update in progress$/.test(status || "")) return "is-attention";
	if (status === "Published — activation held") return "is-attention";
	return "is-draft";
}

function fundingClass(state) {
	if (state === "Confirmed") return "is-live";
	if (state === "Stale" || state === "Returned") return "is-critical";
	return "is-draft";
}

function onWorkAction(row) {
	const route = row.route || [];
	if (route[0] === "procurement-planning" && route[1] === "open") {
		emit("open-departmental-plan", route[2]);
		return;
	}
	emit("navigate", route);
}
</script>
