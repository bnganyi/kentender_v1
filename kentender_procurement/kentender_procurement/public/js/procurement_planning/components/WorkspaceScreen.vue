<!-- PLN-UI-01 Procurement Planning workspace (§12.1), rendering PLN-DES-01
     v1.12 class-for-class: masthead, the plain inline Financial Year filter,
     the headline-plus-button actionable card (absent when empty), the amber
     not-included notice and the "Departmental plans feeding this Annual Plan"
     card — plus the PLN-DES-16 Forbidden / load-error states.
     No Procuring Entity selector exists anywhere (§10). -->
<template>
	<div>
		<!-- Masthead — present in every state. -->
		<div class="pln-masthead">
			<div>
				<div class="kt-page-kicker">PROCUREMENT PLANNING</div>
				<h1 class="kt-page-title">Annual procurement planning</h1>
				<p class="kt-page-lede">
					Turn accepted departmental plans into a funded and approved Annual
					Procurement Plan.
				</p>
			</div>
			<!-- PLN-DES-01: no header action button -->
		</div>

		<!-- loading skeleton -->
		<div
			v-if="loading"
			class="kt-card kt-blueprint"
			style="padding: 0; overflow: hidden"
			data-testid="pln-loading"
		>
			<i class="kt-corner tl"></i><i class="kt-corner tr"></i>
			<i class="kt-corner bl"></i><i class="kt-corner br"></i>
			<div v-for="row in 3" :key="row" class="pln-skel-row">
				<div class="kt-skel" style="width: 72%"></div>
				<div class="kt-skel" style="width: 52%"></div>
				<div class="kt-skel" style="width: 52%"></div>
				<div class="kt-skel" style="width: 44%"></div>
			</div>
		</div>

		<!-- PLN-DES-16 load error, with the generated support reference -->
		<div
			v-else-if="error"
			class="kt-card kt-blueprint pln-state-card"
			data-testid="pln-error"
		>
			<i class="kt-corner tl"></i><i class="kt-corner tr"></i>
			<i class="kt-corner bl"></i><i class="kt-corner br"></i>
			<h3>Procurement Planning could not be loaded</h3>
			<p>Try again. If the problem continues, quote the support reference shown below.</p>
			<button class="kt-btn kt-btn-secondary" @click="$emit('reload')">Try again</button>
			<p class="pln-support-ref">Support reference: {{ supportRef }}</p>
		</div>

		<!-- PLN-DES-16 Forbidden — the verdict resolved before anything else
		     rendered (PLN-AC-111..113): no control, no strip, no table. -->
		<div
			v-else-if="workspace.outcome === 'FORBIDDEN'"
			class="kt-card kt-blueprint pln-state-card"
			data-testid="pln-forbidden"
		>
			<i class="kt-corner tl"></i><i class="kt-corner tr"></i>
			<i class="kt-corner bl"></i><i class="kt-corner br"></i>
			<h3>{{ forbidden.heading }}</h3>
			<p>{{ forbidden.text }}</p>
		</div>

		<!-- a responsibility but no eligible Financial Year -->
		<div
			v-else-if="workspace.outcome === 'NO_CONTEXT'"
			class="kt-card kt-blueprint pln-state-card"
			data-testid="pln-no-context"
		>
			<i class="kt-corner tl"></i><i class="kt-corner tr"></i>
			<i class="kt-corner bl"></i><i class="kt-corner br"></i>
			<h3>Procurement Planning is not available</h3>
			<p>No configured Financial Year is available for Planning.</p>
		</div>

		<template v-else>
			<!-- PLN-DES-01 inline filter: a plain control at text weight, not a
			     bordered card (§11.2). -->
			<div class="pln-filter-strip" data-testid="pln-context-strip">
				<div class="pln-filter-field">
					<label for="pln-fy-select">Financial Year</label>
					<!-- Bound to the caller's own selection, not the server echo: Vue
					     re-patches `value` on every render, so a control bound to the
					     last response snaps back to the old year while the new one
					     is still loading. -->
					<select
						id="pln-fy-select"
						class="kt-input"
						data-testid="pln-fy-select"
						:value="selectedFinancialYear || context.financial_year || ''"
						@change="$emit('select-financial-year', $event.target.value)"
					>
						<option
							v-for="year in context.financial_years || []"
							:key="year.id"
							:value="year.id"
						>
							{{ year.label }}
						</option>
					</select>
				</div>
				<span v-if="annualPlanSummary" class="pln-strip-quiet" data-testid="pln-plan-summary">
					· {{ annualPlanSummary }}
				</span>
				<!-- §12.1 — one schedule-health count, only once an Active plan exists -->
				<span
					v-if="scheduleHealth"
					class="pln-strip-quiet"
					data-testid="pln-schedule-health"
				>
					· {{ scheduleHealth }}
				</span>
				<!-- §10 — the remembered selection always has a visible reset -->
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

			<!-- §12.1 — waiting work is neutral read-only text, never a queue
			     with controls (PLN-DES-01 draws no waiting table). -->
			<p
				v-for="(row, index) in workspace.waiting || []"
				:key="`waiting-${index}`"
				class="pln-strip-quiet pln-waiting"
				data-testid="pln-waiting"
			>
				{{ row.item }} · {{ row.scope }}
			</p>

			<div class="pln-cards-col">
				<!-- PLN-DES-01 actionable card: headline-plus-button rows, absent
				     entirely when nothing is actionable. -->
				<div
					v-if="actionable.length"
					class="kt-card kt-blueprint pln-card-pad"
					data-testid="pln-actionable"
				>
					<i class="kt-corner tl"></i><i class="kt-corner tr"></i>
					<i class="kt-corner bl"></i><i class="kt-corner br"></i>
					<div class="kt-card-title">{{ actionableTitle }}</div>
					<div
						v-for="(row, index) in actionable"
						:key="index"
						class="pln-ready-row"
						:data-kind="row.kind || 'live'"
						data-testid="pln-action-row"
					>
						<div>
							<div class="pln-ready-headline">{{ row.headline }}</div>
							<div v-if="row.supporting" class="pln-ready-sub">{{ row.supporting }}</div>
						</div>
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

				<!-- PLN-DES-01 amber notice (same treatment as PLN-DES-02's) -->
				<div v-if="workspace.not_included" class="pln-notice" data-testid="pln-not-included">
					<p class="pln-notice-title">{{ workspace.not_included.title }}</p>
					<p>{{ workspace.not_included.text }}</p>
				</div>

				<!-- PLN-DES-01 departmental plans card -->
				<div class="kt-card kt-blueprint pln-card-pad" data-testid="pln-departmental-plans">
					<i class="kt-corner tl"></i><i class="kt-corner tr"></i>
					<i class="kt-corner bl"></i><i class="kt-corner br"></i>
					<div class="kt-card-title">{{ workspace.departmental_plans_heading }}</div>
					<p class="pln-card-subhead">{{ workspace.departmental_plans_lede }}</p>
					<table v-if="(workspace.departmental_plans || []).length" class="pln-table">
						<thead>
							<tr>
								<th>Department</th>
								<th class="pln-num">Version</th>
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
									<span class="kt-status" :class="statusClass(row.status_kind)">
										{{ row.status }}
									</span>
								</td>
								<td style="text-align: right">
									<button
										v-if="row.route"
										type="button"
										class="kt-btn kt-btn-ghost"
										@click="$emit('navigate', row.route)"
									>
										View
									</button>
								</td>
							</tr>
						</tbody>
					</table>
					<p class="pln-table-caption kt-muted" data-testid="pln-count-label">
						{{ workspace.count_label }}
					</p>
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

const annualPlanSummary = computed(
	() => (props.workspace.annual_plan || {}).summary || ""
);

// PLN-DES-01 names the card after its one row; with mixed work it reads as
// the actor's work. The card never renders empty.
const actionableTitle = computed(() =>
	actionable.value.length &&
	actionable.value.every((row) => /ready to consolidate$/.test(row.headline || ""))
		? "Ready to consolidate"
		: "Your work"
);

const scheduleHealth = computed(() => {
	const health = props.workspace.schedule_health;
	if (!health || typeof health.total !== "number") return "";
	const noun = health.total === 1 ? "item" : "items";
	return `${health.behind} of ${health.total} ${noun} behind baseline`;
});

const KIND_CLASS = {
	live: "is-live",
	attention: "is-attention",
	critical: "is-critical",
	muted: "is-draft",
};

function statusClass(kind) {
	return KIND_CLASS[kind] || "is-draft";
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
