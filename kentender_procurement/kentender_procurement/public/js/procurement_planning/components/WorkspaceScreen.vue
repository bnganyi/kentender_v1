<!-- PLN-CHG-001 v1.24 §10.3 (KT-STD-001 v1.7 §2.6) — the Planning workspace
     (U01), ported class-for-class from Artboards-U01.dc.html.

     One bare `.kt-page` sheet, never a `.card.blueprint` box per row
     (PLN24-CHG-007). The order is fixed: header with the Financial year
     field inline, a decision-required region when one exists, the actor's
     own departmental plan, the Planner's own Annual plan work (task row plus
     the one current issue), then departmental plans as a quieter register.
     A departmental actor reads a simplified read-only "Annual plan position"
     instead of the Planner's own interactive Annual plan work region — they
     never see Continue/Prepare-update controls that are not theirs to use.

     An empty "Your actions" style region is omitted entirely rather than
     rendered with a placeholder (§9.1), and waiting work is status on its
     own document, never a duplicate disabled task row. -->
<template>
	<div>
		<CommonStates v-if="loading" kind="loading-workspace" testid="pln-loading" />
		<CommonStates v-else-if="error" kind="load-failure" testid="pln-error" :support-ref="supportRef" @action="$emit('reload')" />
		<!-- §9/§3A.1 — the verdict resolves before any header, filter, content
		     or empty state is painted (PLN18-AC-112). -->
		<div v-else-if="workspace.outcome === 'FORBIDDEN'" class="kt-page" data-testid="pln-forbidden">
			<div class="kt-empty">
				<h3 style="font-family: var(--kt-font-heading); font-weight: var(--kt-font-heading-weight); font-size: 23px; margin: 0">
					{{ forbidden.heading }}
				</h3>
				<p v-for="(line, index) in forbidden.text || []" :key="index">{{ line }}</p>
			</div>
		</div>
		<div v-else-if="workspace.outcome === 'NO_CONTEXT'" class="kt-page" data-testid="pln-no-context">
			<div class="kt-empty">
				<!-- §8's own PLN_NO_CONTEXT row is the one authoritative
				     user-facing message (re-diffed 22 Sep 2026 — this previously
				     split a different, invented pair of sentences across a
				     heading and body). No artboard draws this state; the spec's
				     error contract is the only source, so it is used exactly. -->
				<h3 style="font-family: var(--kt-font-heading); font-weight: var(--kt-font-heading-weight); font-size: 23px; margin: 0">
					Procurement Planning is not available for your responsibilities or the current setup.
				</h3>
			</div>
		</div>

		<div v-else class="kt-page">
			<div class="kt-page-head">
				<div>
					<h1 class="kt-page-title" data-testid="pln-title">{{ header.title }}</h1>
					<p class="kt-page-desc">{{ header.description }}</p>
					<!-- Bound to the caller's own selection, never the server echo, so
					     it never snaps back while a new year is still loading. -->
					<div class="field" style="margin-top: var(--kt-space-4); width: 190px" data-testid="pln-context-strip">
						<label for="pln-fy-select">Financial year</label>
						<select
							id="pln-fy-select"
							class="input"
							data-testid="pln-fy-select"
							:value="selectedFinancialYear || context.financial_year || ''"
							@change="$emit('select-financial-year', $event.target.value)"
						>
							<option v-for="year in context.financial_years || []" :key="year.id" :value="year.id">
								{{ year.label }}
							</option>
						</select>
						<button
							v-if="context.resolved_financial_year_source === 'saved_default'"
							type="button"
							class="btn btn-ghost"
							data-testid="pln-fy-reset"
							style="margin-top: 6px"
							@click="$emit('reset-financial-year')"
						>
							Reset
						</button>
					</div>
				</div>
			</div>

			<!-- U01-HOD: the departmental actor's own required decision comes
			     before everything else. Omitted entirely when there is none. -->
			<div v-if="actionable.length" class="kt-region" data-testid="pln-actionable-region">
				<h2 data-testid="pln-your-actions-heading">{{ actionableHeading }}</h2>
				<div v-for="(row, index) in actionable" :key="`action-${index}`" class="kt-task-row" data-testid="pln-action">
					<div style="flex: 1">
						<div class="pln-task-title">{{ actionTitle(row) }}</div>
						<p class="pln-task-desc">{{ actionDescription(row) }}</p>
					</div>
					<button type="button" class="btn btn-primary" data-testid="pln-action-button" @click="onAction(row)">
						{{ row.action }}
					</button>
				</div>
			</div>

			<!-- U01-DEPARTMENT-AUTHOR / U01-HOD: "Your departmental plan". -->
			<div v-if="ownPlan" class="kt-region" data-testid="pln-own-plan-region">
				<h2>{{ ownPlan.heading }}</h2>
				<div data-testid="pln-own-plan">
					<div v-if="ownPlan.empty" class="kt-empty">
						<div class="pln-task-title" data-testid="pln-own-plan-empty">{{ ownPlan.empty_text }}</div>
						<button
							type="button"
							class="btn btn-primary"
							data-testid="pln-start-departmental-plan"
							style="margin-top: var(--kt-space-4)"
							:disabled="pending"
							@click="$emit('open-departmental-plan', ownPlan.organisation_unit)"
						>
							{{ ownPlan.action }}
						</button>
					</div>
					<div v-else class="kt-task-row">
						<div style="flex: 1">
							<div class="pln-task-title">{{ ownPlanTitle }}</div>
							<p class="pln-task-desc">{{ ownPlanNarrative }}</p>
						</div>
						<button
							v-if="ownPlan.route"
							type="button"
							class="btn btn-primary"
							data-testid="pln-own-plan-action"
							@click="$emit('navigate', ownPlan.route)"
						>
							{{ ownPlan.action }}
						</button>
					</div>
				</div>
			</div>

			<!-- A departmental actor reads the Annual Plan; they never act on it
			     (§10.3). Their own read-only "Annual plan position" replaces the
			     Planner's interactive Annual plan work region below. -->
			<div v-if="ownPlan" class="kt-region is-secondary" data-testid="pln-annual-plan-position">
				<h2>Annual plan position</h2>
				<div class="kt-group">
					<p style="margin: 0 0 var(--kt-space-3); font-size: 14px; color: var(--kt-color-neutral-800)">
						{{ annualPositionNote }}
					</p>
					<div class="kt-meta-row">
						<div><span class="kt-label">Plan</span><span style="font-size: 14px">{{ annualPlan.title }}</span></div>
						<div><span class="kt-label">Reference</span><span style="font-size: 14px">{{ annualPlanReference }}</span></div>
						<div><span class="kt-label">State</span><span class="kt-status" :class="planStateClass">{{ planStateLabel }}</span></div>
					</div>
				</div>
			</div>

			<!-- First section — Annual plan work. Dominant, Planner-only. Only the
			     dominant row (the candidate/update when one exists, else the
			     current or draft plan) renders as the interactive task row;
			     U01-CURRENT-UPDATE demotes the current plan itself to a compact
			     read-only baseline below, in its own secondary region — it is
			     never a second interactive task row competing with the update. -->
			<div v-if="!ownPlan" class="kt-region" data-testid="pln-annual-plan-region">
				<h2>Annual plan work</h2>
				<template v-if="dominantRow">
					<div class="kt-task-row" :data-testid="`pln-plan-row-${dominantRow.kind}`">
						<div style="flex: 1">
							<div class="pln-task-title">{{ planRowTitle(dominantRow) }}</div>
							<div style="font-size: 12.5px; color: var(--kt-color-neutral-700); margin-top: 3px">
								{{ planRowSubtitle(dominantRow) }}
							</div>
							<template v-if="dominantRow.kind === 'draft'">
								<div style="display: flex; gap: var(--kt-space-5); margin-top: var(--kt-space-3); font-size: 14px">
									<span>{{ factValue(dominantRow.facts, 'Purchases') }} purchases</span>
									<span>{{ factValue(dominantRow.facts, 'Estimated cost') }} estimated cost</span>
								</div>
							</template>
							<template v-else-if="dominantRow.kind === 'current'">
								<div style="display: flex; gap: var(--kt-space-5); align-items: center; margin-top: var(--kt-space-3); font-size: 14px">
									<span>{{ factValue(dominantRow.facts, 'Approved value') }} approved value</span>
									<span class="kt-status is-live">In force</span>
								</div>
							</template>
							<div v-else-if="dominantRow.kind === 'candidate'" class="kt-meta-row" style="margin-top: var(--kt-space-4); max-width: 900px">
								<div><span class="kt-label">Proposed value</span><span class="kt-meta-value">{{ factValue(dominantRow.facts, 'Proposed value') }}</span></div>
								<div v-if="factValue(dominantRow.facts, 'Affected purchase')">
									<span class="kt-label">Affected purchase</span><span style="font-size: 14px">{{ factValue(dominantRow.facts, 'Affected purchase') }}</span>
								</div>
								<div v-if="factValue(dominantRow.facts, 'Change')">
									<span class="kt-label">Change</span><span style="font-size: 14px">{{ factValue(dominantRow.facts, 'Change') }}</span>
								</div>
							</div>
							<!-- PLN v1.27 §10.3 — a workspace carries no tracker: a blocked or
							     waiting update states the next-step answer on its row
							     (U01-CURRENT-UPDATE-OVER-BUDGET / -WAITING-BUDGET). -->
							<p
								v-if="dominantRow.narrative && dominantRow.narrative.tone === 'blocked'"
								class="pln-row-narrative is-blocked"
								data-testid="pln-row-narrative"
							>{{ dominantRow.narrative.headline }}</p>
							<p
								v-if="dominantRow.narrative && dominantRow.narrative.tone === 'blocked' && dominantRow.narrative.detail"
								class="pln-row-narrative-detail"
								data-testid="pln-row-narrative-detail"
							>{{ dominantRow.narrative.detail }}</p>
							<p
								v-else-if="dominantRow.narrative && dominantRow.narrative.tone !== 'blocked'"
								class="pln-row-narrative is-waiting"
								data-testid="pln-row-narrative"
							><strong>{{ dominantRow.narrative.headline }}</strong><template v-if="dominantRow.narrative.since">{{ " " }}<span class="pln-row-narrative-since">since {{ dominantRow.narrative.since }}</span></template></p>
							<p v-if="dominantRow.note" data-testid="pln-plan-note" style="margin: var(--kt-space-3) 0 0; font-size: 14px; color: var(--kt-color-neutral-800)">{{ dominantRow.note }}</p>
							<p v-if="dominantRow.kind === 'candidate'" data-testid="pln-update-note" style="margin: var(--kt-space-4) 0 0; font-size: 14px; color: var(--kt-color-neutral-800)">
								{{ annualPlan.update_note || 'The current plan remains in force while this update is reviewed.' }}
							</p>
						</div>
						<div style="display: flex; gap: var(--kt-space-3); align-items: center">
							<a
								v-if="dominantRow.secondary_action"
								href="#"
								:data-testid="`pln-plan-secondary-${dominantRow.kind}`"
								@click.prevent="$emit('navigate', dominantRow.secondary_route)"
							>{{ dominantRow.secondary_action }}</a>
							<button
								v-if="dominantRow.kind === 'current' && annualPlan.can_prepare_update"
								type="button"
								class="btn btn-secondary"
								data-testid="pln-prepare-update"
								:disabled="pending"
								@click="$emit('prepare-update')"
							>
								{{ annualPlan.prepare_update_action }}
							</button>
							<button
								v-if="dominantRow.action"
								type="button"
								class="btn"
								:class="dominantRow.action_kind === 'primary' ? 'btn-primary' : 'btn-secondary'"
								:data-testid="`pln-plan-action-${dominantRow.kind}`"
								@click="$emit('navigate', dominantRow.route)"
							>
								{{ dominantRow.action }}
							</button>
						</div>
					</div>
				</template>
				<!-- U01-NO-PLAN — an empty state, never a Create action. -->
				<div v-else class="kt-empty" data-testid="pln-annual-plan-empty">
					<div class="pln-task-title">{{ annualPlan.empty_title }}</div>
					<p>{{ annualPlan.empty_text }}</p>
				</div>

				<!-- Immediately below the plan row (PLN v1.27 §10.3, D2): what stops
				     the funding request as the warning, then what stops only
				     signature as a quieter line — each with its one action. -->
				<template v-for="(issue, index) in issues" :key="`${issue.tone}-${index}`">
					<div v-if="issue.tone === 'dominant'" class="kt-notice is-warning" style="margin-top: var(--kt-space-5)" data-testid="pln-issue">
						<svg class="kt-notice-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
							<path d="M10.3 3.9 1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0z"></path><path d="M12 9v4"></path><path d="M12 17h.01"></path>
						</svg>
						<div style="flex: 1">
							<div class="kt-notice-body"><template v-for="(part, i) in issueParts(issue)" :key="i"><strong v-if="part.strong">{{ part.text }}</strong><template v-else>{{ part.text }}</template></template></div>
							<button
								type="button"
								class="btn btn-secondary"
								style="margin-top: var(--kt-space-3)"
								data-testid="pln-issue-action"
								@click="$emit('navigate', issue.route)"
							>{{ issue.action }}</button>
						</div>
					</div>
					<div v-else class="pln-quiet-issue" data-testid="pln-issue">
						<p><template v-for="(part, i) in issueParts(issue)" :key="i"><strong v-if="part.strong">{{ part.text }}</strong><template v-else>{{ part.text }}</template></template></p>
						<button type="button" class="btn btn-secondary" data-testid="pln-issue-action" @click="$emit('navigate', issue.route)">{{ issue.action }}</button>
					</div>
				</template>

				<!-- A late accepted requirement that no departmental plan could
				     include: an explanation, never a bypass. -->
				<div v-if="workspace.not_included" class="kt-notice is-warning" style="margin-top: var(--kt-space-5)" data-testid="pln-not-included">
					<svg class="kt-notice-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
						<path d="M12 3l9 16H3z"></path><path d="M12 10v4M12 17h.01"></path>
					</svg>
					<div class="kt-notice-body">
						<strong>{{ workspace.not_included.title }}</strong>
						<p>{{ workspace.not_included.text }}</p>
					</div>
				</div>
			</div>

			<!-- U01-CURRENT-UPDATE — the current plan stays visible as a compact
			     read-only baseline while the update is being reviewed; it keeps
			     its established testid so it is still findable as "the current
			     plan row" even though it is no longer the interactive one. -->
			<div v-if="currentRow && candidateRow" class="kt-region is-secondary" data-testid="pln-plan-row-current">
				<h2>Current annual procurement plan</h2>
				<div class="kt-group">
					<div class="kt-meta-row">
						<div><span class="kt-label">Plan</span><span style="font-size: 14px">{{ annualPlan.title }}</span></div>
						<div><span class="kt-label">Reference</span><span style="font-size: 14px">{{ planRowSubtitle(currentRow) }}</span></div>
						<div><span class="kt-label">Approved value</span><span class="kt-meta-value">{{ factValue(currentRow.facts, 'Approved value') }}</span></div>
						<div><span class="kt-label">State</span><span class="kt-status is-live">In force</span></div>
					</div>
				</div>
			</div>

			<!-- Second section — Departmental plans, a quieter register. -->
			<div class="kt-region is-secondary">
				<h2>{{ table.heading }}</h2>
				<table v-if="table.rows.length" class="table" data-testid="pln-departmental-table">
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
									class="btn btn-ghost"
									data-testid="pln-departmental-open"
									@click.prevent="$emit('navigate', row.route)"
								>{{ row.action }}</a>
								<span v-else>—</span>
							</td>
						</tr>
					</tbody>
				</table>
				<p v-else data-testid="pln-departmental-empty">{{ table.empty_text }}</p>
				<p v-if="table.rows.length" style="margin: var(--kt-space-3) 0 0; font-size: 13px; color: var(--kt-color-neutral-700)" data-testid="pln-count-label">
					{{ table.count_label }}
				</p>
			</div>

			<!-- Waiting work: neutral read-only text, never a queue with controls. -->
			<p
				v-for="(row, index) in workspace.waiting || []"
				:key="`waiting-${index}`"
				data-testid="pln-waiting"
			>
				{{ row.item }} · {{ row.scope }}
			</p>
		</div>
	</div>
</template>

<script setup>
import { computed } from "vue";
import CommonStates from "./CommonStates.vue";

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
	"prepare-update",
]);

const context = computed(() => props.workspace.context || {});
const forbidden = computed(() => props.workspace.forbidden || {});
const actionable = computed(() => props.workspace.actionable || []);
const header = computed(() => props.workspace.header || { title: "", description: "" });
const annualPlan = computed(() => props.workspace.annual_plan || {});
const planRows = computed(() => annualPlan.value.rows || []);
const currentRow = computed(() => planRows.value.find((row) => row.kind === "current") || null);
const candidateRow = computed(() => planRows.value.find((row) => row.kind === "candidate") || null);
// U01-CURRENT-UPDATE demotes the current plan to a compact read-only summary
// once a candidate exists; only one row is ever the interactive task row.
const dominantRow = computed(() => candidateRow.value || currentRow.value || planRows.value.find((row) => row.kind === "draft") || null);
const issues = computed(() => props.workspace.issues || []);
// The server words each issue once, as one sentence, and names the part the
// board emboldens; split on it rather than re-wording anything here.
function issueParts(issue) {
	const text = issue.text || "";
	const strong = issue.strong || "";
	const at = strong ? text.indexOf(strong) : -1;
	if (at < 0) return [{ text, strong: false }];
	return [
		{ text: text.slice(0, at), strong: false },
		{ text: strong, strong: true },
		{ text: text.slice(at + strong.length), strong: false },
	].filter((part) => part.text);
}
const ownPlan = computed(() => props.workspace.your_departmental_plan || null);
const table = computed(() => props.workspace.departmental_table || { columns: [], rows: [] });

function isNumeric(column) {
	return column === "Requirements" || column === "Estimated cost";
}

function onAction(row) {
	emit("navigate", row.route);
}

/** The value beside a labelled fact the server returned as [label, value] pairs. */
function factValue(facts, label) {
	const match = (facts || []).find((fact) => fact[0] === label);
	return match ? match[1] : "";
}

// §10.3 — the big task-row title names what the row *is*; the server's own
// "kind" discriminator already carries that meaning, so it is translated
// here rather than duplicated as a fourth server-side string.
const PLAN_ROW_TITLE = {
	draft: "Draft annual procurement plan",
	current: "Current annual procurement plan",
	candidate: "Continue plan update",
};

// The server names the row by its real state (a submitted first plan is not
// a "Draft"); the kind-based title is only the fallback for older payloads.
function planRowTitle(row) {
	return row.title || PLAN_ROW_TITLE[row.kind] || row.kind;
}

function planRowSubtitle(row) {
	const version = factValue(row.facts, "Version");
	if (row.kind === "candidate") return `Version ${version}`;
	return [annualPlan.value.plan_reference, version && `Version ${version}`].filter(Boolean).join(" · ");
}

const planStateClass = computed(() => (planRows.value[0]?.kind === "current" ? "is-live" : "is-draft"));
const planStateLabel = computed(() => (planRows.value[0]?.kind === "current" ? "In force" : "Draft"));
const annualPlanReference = computed(() => {
	const version = factValue(planRows.value[0]?.facts, "Version");
	return [annualPlan.value.plan_reference, version && `Version ${version}`].filter(Boolean).join(" · ");
});
const annualPositionNote = computed(() =>
	planStateClass.value === "is-live"
		? "This is the plan currently in force."
		: "The annual procurement plan is being prepared by Procurement. It cannot yet be used to authorise procurement.",
);

const ownPlanTitle = computed(() => factValue(ownPlan.value?.facts, "Department") && `${factValue(ownPlan.value.facts, "Department")} departmental plan · ${factValue(ownPlan.value.facts, "Financial year")}`);
const ownPlanNarrative = computed(() => {
	const status = factValue(ownPlan.value?.facts, "Status");
	if (status === "Draft") return "Draft — complete the requirements and funding details";
	return status;
});

// U01-HOD — the Head of Department's own decision heading names the count;
// U01-DEPARTMENT-AUTHOR's "Continue departmental plan" work never reaches
// this region at all (§10.3 routes it through "Your departmental plan").
// The server words the heading from what the decisions are about.
const actionableHeading = computed(() => props.workspace.actionable_heading || "");

function actionTitle(row) {
	return factValue(row.facts, "Departmental plan") || row.headline;
}

function actionDescription(row) {
	if (row.action === "Review departmental plan") {
		return "Review the complete departmental plan and submit it to Procurement";
	}
	return row.supporting;
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
