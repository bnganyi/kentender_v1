<!-- PLN-CHG-001 v1.23 §10.3 — the Planning workspace (U01), ported
     class-for-class from U01.dc.html.

     The order is fixed: header, financial year, Annual plan, the one current
     issue, then departmental plans. The reservation shortfall that used to be
     four accounting values here is now one sentence and one recovery action;
     the arithmetic stays in the Plan check detail (PLN22-CHG-003).

     An empty "Your actions" section is omitted entirely rather than rendered
     with a placeholder (§9.1), and waiting work is status on its own document,
     never a duplicate disabled task row. -->
<template>
	<div>
		<!-- loading skeleton: the actual structure, no stale rows or actions -->
		<div v-if="loading" class="kt-card kt-blueprint" style="padding: 0; overflow: hidden" data-testid="pln-loading">
			<i class="kt-corner tl"></i><i class="kt-corner tr"></i>
			<i class="kt-corner bl"></i><i class="kt-corner br"></i>
			<p class="pln-loading-text">Loading procurement planning…</p>
			<div v-for="row in 3" :key="row" class="pln-skel-row">
				<div class="kt-skel" style="width: 72%"></div>
				<div class="kt-skel" style="width: 52%"></div>
				<div class="kt-skel" style="width: 52%"></div>
				<div class="kt-skel" style="width: 44%"></div>
			</div>
		</div>

		<!-- U21-LOAD-FAILURE -->
		<div v-else-if="error" class="kt-card kt-blueprint pln-state-card" data-testid="pln-error">
			<i class="kt-corner tl"></i><i class="kt-corner tr"></i>
			<i class="kt-corner bl"></i><i class="kt-corner br"></i>
			<h3>Procurement Planning could not be loaded</h3>
			<p>Try again. If the problem continues, contact support.</p>
			<button class="kt-btn kt-btn-secondary" @click="$emit('reload')">Try again</button>
			<p class="pln-support-ref">Support reference: {{ supportRef }}</p>
		</div>

		<!-- U21-DENIED: the verdict resolves before any header, filter, content
		     or empty state is painted (PLN18-AC-112). -->
		<div v-else-if="workspace.outcome === 'FORBIDDEN'" class="kt-card kt-blueprint pln-state-card" data-testid="pln-forbidden">
			<i class="kt-corner tl"></i><i class="kt-corner tr"></i>
			<i class="kt-corner bl"></i><i class="kt-corner br"></i>
			<h3>{{ forbidden.heading }}</h3>
			<p>{{ forbidden.text }}</p>
		</div>

		<div v-else-if="workspace.outcome === 'NO_CONTEXT'" class="kt-card kt-blueprint pln-state-card" data-testid="pln-no-context">
			<i class="kt-corner tl"></i><i class="kt-corner tr"></i>
			<i class="kt-corner bl"></i><i class="kt-corner br"></i>
			<h3>Procurement Planning is not available</h3>
			<p>No configured Financial Year is available for Planning.</p>
		</div>

		<template v-else>
			<!-- Page header: title and description upper left; no header action
			     in this composition. -->
			<div class="pln-masthead">
				<div>
					<h1 class="kt-page-title" data-testid="pln-title">{{ header.title }}</h1>
					<p class="kt-page-lede">{{ header.description }}</p>
				</div>
			</div>

			<!-- Financial year sits below the header at the left, bound to the
			     caller's own selection so it never snaps back to the server echo
			     while a new year is still loading. -->
			<div class="pln-filter-strip" data-testid="pln-context-strip">
				<div class="pln-filter-field">
					<label for="pln-fy-select">Financial year</label>
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

			<!-- U01-HOD: the departmental actor's own required outcome comes
			     before everything else. Omitted entirely when there is none. -->
			<template v-if="actionable.length">
				<h3 class="kt-card-title" data-testid="pln-your-actions-heading">
					{{ actionable.length === 1 ? "Your action" : "Your actions" }}
				</h3>
				<div
					v-for="(row, index) in actionable"
					:key="`action-${index}`"
					class="kt-card kt-blueprint pln-action-card"
					data-testid="pln-action"
				>
					<div class="kt-meta-row">
						<div>
							<span class="kt-label">Outcome required</span>
							<span class="kt-meta-value">{{ row.headline }}</span>
						</div>
						<div
							v-for="fact in row.facts || []"
							:key="fact.label"
						>
							<span class="kt-label">{{ fact.label }}</span>
							<span class="kt-meta-value">{{ fact.value }}</span>
						</div>
					</div>
					<p v-if="row.supporting" class="kt-muted">{{ row.supporting }}</p>
					<button
						type="button"
						class="kt-btn kt-btn-primary"
						data-testid="pln-action-button"
						@click="onAction(row)"
					>
						{{ row.action }}
					</button>
				</div>
			</template>

			<!-- U01-DEPARTMENT-AUTHOR / U01-HOD: "Your departmental plan". -->
			<template v-if="ownPlan">
				<h3 class="kt-card-title">{{ ownPlan.heading }}</h3>
				<div class="kt-card kt-blueprint pln-own-plan" data-testid="pln-own-plan">
					<template v-if="ownPlan.empty">
						<p class="kt-muted" data-testid="pln-own-plan-empty">{{ ownPlan.empty_text }}</p>
						<button
							type="button"
							class="kt-btn kt-btn-primary"
							data-testid="pln-start-departmental-plan"
							:disabled="pending"
							@click="$emit('open-departmental-plan', ownPlan.organisation_unit)"
						>
							{{ ownPlan.action }}
						</button>
					</template>
					<template v-else>
						<div class="kt-meta-row">
							<div v-for="fact in ownPlan.facts" :key="fact[0]">
								<span class="kt-label">{{ fact[0] }}</span>
								<span class="kt-meta-value">{{ fact[1] }}</span>
							</div>
							<div>
								<span class="kt-label">Financial year</span>
								<span class="kt-meta-value">{{ context.financial_year_label || context.financial_year }}</span>
							</div>
						</div>
						<button
							v-if="ownPlan.route"
							type="button"
							class="kt-btn kt-btn-primary"
							data-testid="pln-own-plan-action"
							@click="$emit('navigate', ownPlan.route)"
						>
							{{ ownPlan.action }}
						</button>
					</template>
				</div>
			</template>

			<!-- First section — Annual plan. -->
			<div class="pln-section-head">
				<h3 class="kt-card-title">{{ annualPlan.heading }}</h3>
				<button
					v-if="annualPlan.can_prepare_update"
					type="button"
					class="kt-btn kt-btn-primary"
					data-testid="pln-prepare-update"
					:disabled="pending"
					@click="$emit('navigate', planRoute)"
				>
					{{ annualPlan.prepare_update_action }}
				</button>
			</div>

			<template v-if="planRows.length">
				<template v-for="(row, index) in planRows" :key="`plan-${row.kind}`">
					<div class="kt-card kt-blueprint pln-plan-row" :data-testid="`pln-plan-row-${row.kind}`">
						<div class="kt-meta-row">
							<div v-for="fact in row.facts" :key="fact[0]">
								<span class="kt-label">{{ fact[0] }}</span>
								<span class="kt-meta-value">{{ fact[1] }}</span>
							</div>
						</div>
						<button
							type="button"
							class="kt-btn"
							:class="row.action_kind === 'primary' ? 'kt-btn-primary' : 'kt-btn-secondary'"
							:data-testid="`pln-plan-action-${row.kind}`"
							@click="$emit('navigate', row.route)"
						>
							{{ row.action }}
						</button>
					</div>
					<p v-if="row.note" class="kt-muted pln-plan-note" data-testid="pln-plan-note">{{ row.note }}</p>
					<!-- §10.3 U01-CURRENT-UPDATE: the note sits between the two rows. -->
					<p
						v-if="index === 0 && planRows.length > 1 && annualPlan.update_note"
						class="kt-muted pln-plan-note"
						data-testid="pln-update-note"
					>
						{{ annualPlan.update_note }}
					</p>
				</template>
			</template>
			<!-- U01-NO-PLAN — an empty state, never a Create action. -->
			<div v-else class="kt-card kt-blueprint pln-plan-empty" data-testid="pln-annual-plan-empty">
				<p class="kt-meta-value">{{ annualPlan.empty_title }}</p>
				<p class="kt-muted">{{ annualPlan.empty_text }}</p>
			</div>

			<!-- Immediately below the plan row — the one current issue. -->
			<div v-if="currentIssue" class="kt-notice is-warning" data-testid="pln-current-issue">
				<svg class="kt-notice-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
					<path d="M12 3l9 16H3z"></path><path d="M12 10v4M12 17h.01"></path>
				</svg>
				<div class="kt-notice-body pln-notice-split">
					<span>{{ currentIssue.text }}</span>
					<button
						type="button"
						class="kt-btn kt-btn-secondary"
						data-testid="pln-current-issue-action"
						@click="$emit('navigate', currentIssue.route)"
					>
						{{ currentIssue.action }}
					</button>
				</div>
			</div>

			<!-- A late accepted requirement that no departmental plan could
			     include: an explanation, never a bypass. -->
			<div v-if="workspace.not_included" class="kt-notice is-warning" data-testid="pln-not-included">
				<svg class="kt-notice-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
					<path d="M12 3l9 16H3z"></path><path d="M12 10v4M12 17h.01"></path>
				</svg>
				<div class="kt-notice-body">
					<strong>{{ workspace.not_included.title }}</strong>
					<p>{{ workspace.not_included.text }}</p>
				</div>
			</div>

			<!-- Second section — Departmental plans. -->
			<h3 class="kt-card-title">{{ table.heading }}</h3>
			<table v-if="table.rows.length" class="kt-table pln-dept-table" data-testid="pln-departmental-table">
				<thead>
					<tr>
						<th v-for="column in table.columns" :key="column" :class="{ 'is-num': isNumeric(column) }">
							{{ column }}
						</th>
					</tr>
				</thead>
				<tbody>
					<tr v-for="row in table.rows" :key="row.department" data-testid="pln-departmental-row">
						<td>{{ row.department }}</td>
						<td><span class="kt-status" :class="statusClass(row.status)">{{ row.status }}</span></td>
						<td class="is-num">{{ row.requirements }}</td>
						<td class="is-num">{{ row.value }}</td>
						<td>
							<a
								v-if="row.route"
								href="#"
								data-testid="pln-departmental-open"
								@click.prevent="$emit('navigate', row.route)"
							>{{ row.action }}</a>
							<span v-else>—</span>
						</td>
					</tr>
				</tbody>
			</table>
			<p v-else class="kt-muted" data-testid="pln-departmental-empty">{{ table.empty_text }}</p>
			<p v-if="table.rows.length" class="kt-muted" data-testid="pln-count-label">{{ table.count_label }}</p>

			<!-- Waiting work: neutral read-only text, never a queue with controls. -->
			<p
				v-for="(row, index) in workspace.waiting || []"
				:key="`waiting-${index}`"
				class="pln-strip-quiet pln-waiting"
				data-testid="pln-waiting"
			>
				{{ row.item }} · {{ row.scope }}
			</p>
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

const emit = defineEmits([
	"reload",
	"select-financial-year",
	"reset-financial-year",
	"open-departmental-plan",
	"navigate",
]);

const context = computed(() => props.workspace.context || {});
const forbidden = computed(() => props.workspace.forbidden || {});
const actionable = computed(() => props.workspace.actionable || []);
const header = computed(() => props.workspace.header || { title: "", description: "" });
const annualPlan = computed(() => props.workspace.annual_plan || {});
const planRows = computed(() => annualPlan.value.rows || []);
const planRoute = computed(() =>
	annualPlan.value.plan_reference ? ["annual-procurement-plan", annualPlan.value.plan_reference] : null,
);
const currentIssue = computed(() => props.workspace.current_issue || null);
const ownPlan = computed(() => props.workspace.your_departmental_plan || null);
const table = computed(() => props.workspace.departmental_table || { columns: [], rows: [] });

function isNumeric(column) {
	return column === "Requirements" || column === "Estimated cost";
}

function onAction(row) {
	emit("navigate", row.route);
}

// The wording is always the server's own literal; only the colour is decided
// here, and only from that literal.
const LIVE_STATUSES = new Set(["Active", "Accepted", "Confirmed"]);
const ATTENTION_STATUSES = new Set([
	"Draft",
	"Draft update",
	"Awaiting Accounting Officer",
	"Awaiting statutory approval",
	"Awaiting validation",
	"Not requested",
	"Awaiting confirmation",
	"Published — activation held",
]);
const CRITICAL_STATUSES = new Set([
	"Returned",
	"Not submitted — window closed",
	"Stale",
	"Publication failed",
	"Withdrawn for correction",
]);

function statusClass(status) {
	if (LIVE_STATUSES.has(status)) return "is-live";
	if (CRITICAL_STATUSES.has(status)) return "is-critical";
	if (ATTENTION_STATUSES.has(status) || /update in progress$/.test(status || "")) return "is-attention";
	return "is-draft";
}
</script>
