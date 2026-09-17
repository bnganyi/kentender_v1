<!-- NDS-UI-01 requester/reviewer workspace (§12.1), rendering NDS-DES-01,
     NDS-DES-02 and the NDS-DES-14 shared states with their exact copy.
     NDS-CHG-001 v1.13 §11.2/§11.3 — one existing workspace route for both the
     Author and the Head of User Department; this component branches on
     content (a decision queue only exists when there is one), never on a
     role switch. -->
<template>
	<div>
		<!-- NDS-DES-14 LOADING -->
		<div v-if="loading" class="kt-panel-lg" style="max-width: 900px">
			<div data-testid="nds-loading-text" style="font-size: 14px; color: var(--kt-color-neutral-700)">
				Loading departmental needs…
			</div>
			<div v-for="row in 3" :key="row" class="kt-skel-row" style="margin-top: 12px">
				<div class="kt-skel" style="width: 78%"></div>
				<div class="kt-skel" style="width: 56%"></div>
				<div class="kt-skel" style="width: 56%"></div>
				<div class="kt-skel" style="width: 46%"></div>
			</div>
		</div>

		<!-- NDS-DES-14 LOAD-FAILURE -->
		<div
			v-else-if="error"
			class="kt-panel-lg"
			style="max-width: 620px; text-align: center; display: flex; flex-direction: column; align-items: center; gap: 10px"
		>
			<div style="font-family: var(--kt-font-heading); font-size: 20px; font-weight: 600">
				Departmental Needs could not be loaded
			</div>
			<p style="margin: 0; font-size: 14.5px; color: var(--kt-color-neutral-700)">
				Try again. If the problem continues, contact support.
			</p>
			<button class="kt-btn kt-btn-secondary" @click="$emit('reload')">Try again</button>
		</div>

		<!-- NDS-DES-14 DENIED — kept to the full four-role list (Departmental
		     Author, Head of User Department, Procurement Planner, Auditor); the
		     compact design-canvas card omits Procurement Planner for space, but
		     dropping a real read-eligible role from this help text would mislead
		     a Planner into thinking they have no path in. -->
		<div
			v-else-if="outcome === 'NO_AUTHORISED_CONTEXT'"
			class="kt-panel-lg"
			style="max-width: 620px; text-align: center; display: flex; flex-direction: column; align-items: center; gap: 10px"
		>
			<div style="font-family: var(--kt-font-heading); font-size: 20px; font-weight: 600">
				You do not have access to Departmental Needs
			</div>
			<p style="margin: 0; font-size: 14.5px; color: var(--kt-color-neutral-700)">
				This area needs one of these responsibilities: Departmental Author, Head of User
				Department, Procurement Planner or Auditor, assigned to an organisation unit. Ask your
				KenTender administrator to assign one in System setup.
			</p>
		</div>

		<template v-else>
			<div class="kt-panel-lg">
				<div style="display: flex; justify-content: space-between; align-items: flex-start">
					<div>
						<h3 style="margin: 0">Departmental Needs</h3>
						<p class="text-muted" style="font-size: 13px; margin: 6px 0 0">{{ lede }}</p>
					</div>
					<button
						v-if="canCreate"
						class="kt-btn kt-btn-primary"
						data-testid="nds-create-need"
						@click="$emit('create')"
					>
						Create need
					</button>
				</div>

				<!-- §11.1/§11.2 — four separately labelled facts, read-only; no
				     entity row. The switching controls live in the filter row
				     below, not here. -->
				<div class="kt-panel" style="margin-top: var(--kt-space-4)">
					<div class="kt-meta-row">
						<div>
							<span class="kt-label">Department</span>
							<span class="kt-meta-value" style="font-size: 14px" data-testid="nds-department-fact">{{
								context.organisation_unit_label || context.organisation_unit || ""
							}}</span>
						</div>
						<div>
							<span class="kt-label">Financial year</span>
							<span class="kt-meta-value" style="font-size: 14px">{{
								context.financial_year_label || context.financial_year || ""
							}}</span>
						</div>
						<div v-if="canCreate">
							<span class="kt-label">New submissions</span>
							<span class="kt-meta-value" style="font-size: 14px">
								<span :class="['kt-status', submission.open ? 'is-live' : 'is-draft']">{{
									submission.open ? "Open" : "Closed"
								}}</span>
							</span>
						</div>
						<div v-if="canCreate && submission.open && submission.closes_at">
							<span class="kt-label">Closes at</span>
							<span class="kt-meta-value" style="font-size: 14px">{{
								formatInstant(submission.closes_at)
							}}</span>
						</div>
					</div>
				</div>

				<!-- NDS-DES-14 CLOSED-WORKSPACE / NO-OPEN-YEAR — the read contract
				     does not yet distinguish "a year's flag is closed" from "no year
				     is open" (both resolve to `{ open: false }`), so both fixtures
				     share this one notice until that contract gains a flag. -->
				<div
					v-if="canCreate && !submission.open && needs.length"
					class="kt-notice is-warning"
					style="margin-top: var(--kt-space-4)"
					data-testid="nds-submission-closed-notice"
				>
					<div class="kt-notice-body">
						New submissions are closed. You can view existing needs and save changes to
						existing drafts.
					</div>
				</div>

				<!-- §11.2 filters — one row: search, status, financial year,
				     department, Clear filters (DES-01's own single-row layout;
				     splitting this across two rows made the department select's
				     long label read as if the row had wrapped). -->
				<div
					style="
						display: flex;
						gap: var(--kt-space-3);
						margin: var(--kt-space-4) 0;
						align-items: center;
					"
				>
					<input
						class="kt-input"
						style="flex: 1"
						placeholder="Search title or reference"
						data-testid="nds-search"
						:value="search"
						@input="$emit('update:search', $event.target.value)"
					/>
					<select
						class="kt-input"
						style="width: 160px"
						data-testid="nds-status-filter"
						:value="status"
						@change="$emit('update:status', $event.target.value)"
					>
						<option value="">All statuses</option>
						<option v-for="option in STATUSES" :key="option" :value="option">{{ option }}</option>
					</select>
					<select
						class="kt-input"
						style="width: 180px"
						data-testid="nds-fy-filter"
						:value="selectedFinancialYear || context.financial_year || ''"
						@change="$emit('select-financial-year', $event.target.value)"
					>
						<option value="">All financial years</option>
						<option v-for="year in financialYears" :key="year.id" :value="year.id">
							{{ year.label }}
						</option>
					</select>
					<select
						class="kt-input"
						style="width: 200px"
						data-testid="nds-department-filter"
						:value="context.organisation_unit || ''"
						@change="$emit('select-context', $event.target.value)"
					>
						<option
							v-for="row in contexts"
							:key="row.organisation_unit"
							:value="row.organisation_unit"
						>
							{{ row.organisation_unit_label }}
						</option>
					</select>
					<button
						class="kt-btn kt-btn-secondary"
						style="flex: none"
						@click="$emit('clear-filters')"
					>
						Clear filters
					</button>
				</div>

				<!-- NDS-DES-02 first content section — a decision queue only when
				     one exists; never a separate menu entry or role switch. -->
				<template v-if="decisionQueue.length">
					<h6 class="kt-card-title">Needs requiring your decision</h6>
					<NeedsTable
						:needs="decisionQueue"
						:columns="decisionColumns"
						style="margin-bottom: var(--kt-space-2)"
						@action="(row, action) => $emit('action', row, action)"
					/>
					<div class="text-muted" style="font-size: 13px; margin-bottom: var(--kt-space-8)">
						{{ decisionQueue.length === 1 ? "1 need awaiting review" : `${decisionQueue.length} needs awaiting review` }}
					</div>
					<h6 class="kt-card-title">All departmental needs</h6>
				</template>

				<!-- NDS-DES-14 EMPTY-AUTHOR / EMPTY-READER / FILTERED-EMPTY -->
				<div
					v-if="!registerRows.length"
					style="padding: 48px 24px; display: flex; flex-direction: column; align-items: center; text-align: center; gap: 8px"
				>
					<div style="font-family: var(--kt-font-heading); font-size: 18px; font-weight: 600">
						{{ emptyHeadline }}
					</div>
					<p style="margin: 0; font-size: 14px; color: var(--kt-color-neutral-700); max-width: 420px">
						{{ emptyBody }}
					</p>
				</div>

				<NeedsTable
					v-else
					:needs="registerRows"
					:columns="registerColumns"
					@action="(row, action) => $emit('action', row, action)"
				/>

				<div
					v-if="registerRows.length"
					data-testid="nds-count"
					class="text-muted"
					style="margin-top: var(--kt-space-3); font-size: 13px"
				>
					{{ registerCountLabel }}
				</div>
			</div>
		</template>
	</div>
</template>

<script setup>
import { computed } from "vue";
import NeedsTable from "./NeedsTable.vue";
import { formatInstant } from "../data/format.js";

const props = defineProps({
	loading: Boolean,
	error: { type: String, default: "" },
	outcome: { type: String, default: "" },
	context: { type: Object, default: () => ({}) },
	contexts: { type: Array, default: () => [] },
	// get_needs_submission_state() shape: { open, financial_year, label, closes_at }.
	submission: { type: Object, default: () => ({}) },
	needs: { type: Array, default: () => [] },
	actions: { type: Array, default: () => [] },
	search: { type: String, default: "" },
	status: { type: String, default: "" },
	financialYears: { type: Array, default: () => [] },
	selectedFinancialYear: { type: String, default: "" },
});

defineEmits([
	"create",
	"reload",
	"action",
	"update:search",
	"update:status",
	"clear-filters",
	"select-financial-year",
	"select-context",
]);

const STATUSES = ["Draft", "Submitted", "Returned", "Accepted for planning", "Not taken forward"];

// §12.1 — Create need needs both: the server must offer the action (only an
// author in this context does), and Needs submission must be Open. The flag
// check alone would show the button to a reviewer for as long as it is Open.
const canCreate = computed(
	() => props.actions.some((action) => action.code === "create") && !!props.submission.open
);

const lede = computed(() =>
	canCreate.value
		? "Describe your department's requirements and follow their review."
		: "Review submitted requirements and view the department's needs."
);

// §11.3 — rows with an open decision the viewer may act on lead the page,
// separate from the full department register below.
const decisionQueue = computed(() =>
	props.needs.filter((row) => ["review", "withdrawal"].includes((row.actions || [])[0]?.code))
);

const decisionColumns = [
	{ key: "need", label: "Requirement" },
	{ key: "author_label", label: "Submitted by" },
	{ key: "quantity_label", label: "Quantity", align: "right" },
	{ key: "required_by_label", label: "Required by" },
	{ key: "review_kind", label: "Review" },
	{ key: "action", label: "", align: "right" },
];

const registerColumns = computed(() =>
	decisionQueue.value.length
		? [
				// §11.3 — the department register (HoD view): Requester replaces the
				// author's own "Requested by" phrasing once a decision section
				// already leads the page.
				{ key: "need", label: "Requirement" },
				{ key: "author_label", label: "Requester" },
				{ key: "quantity_label", label: "Quantity", align: "right" },
				{ key: "required_by_label", label: "Required by" },
				{ key: "status", label: "Status", status: true },
				{ key: "action", label: "", align: "right" },
			]
		: [
				// §11.2 — the author's own list.
				{ key: "need", label: "Requirement" },
				{ key: "quantity_label", label: "Quantity", align: "right" },
				{ key: "required_by_label", label: "Required by" },
				{ key: "status", label: "Status", status: true },
				{ key: "action", label: "", align: "right" },
			]
);

// The full register excludes rows already shown in the decision queue above —
// §11.3's two sections partition the same list, they do not repeat a row.
const registerRows = computed(() => {
	if (!decisionQueue.value.length) return props.needs;
	const queued = new Set(decisionQueue.value.map((row) => row.name));
	return props.needs.filter((row) => !queued.has(row.name));
});

// §11.2 "2 needs" (the author's own list) vs. §11.3 "2 department needs"
// (the register beneath a decision queue) — computed from what is actually
// rendered in this table, not the server's raw total across both sections.
const registerCountLabel = computed(() => {
	const n = registerRows.value.length;
	const noun = decisionQueue.value.length ? "department need" : "need";
	return `${n} ${noun}${n === 1 ? "" : "s"}`;
});

// An empty list under active filters means "nothing matched", not "nothing
// exists" — the create-first copy would misstate the workspace.
const filtersActive = computed(
	() => !!(props.search || props.status || props.selectedFinancialYear)
);

const emptyHeadline = computed(() => {
	if (filtersActive.value) return "No needs match your filters";
	return canCreate.value ? "No departmental needs yet" : "No departmental needs to display";
});

const emptyBody = computed(() => {
	if (filtersActive.value) return "Adjust your search or clear the filters.";
	return canCreate.value
		? "Describe the first requirement for your department."
		: "";
});
</script>
