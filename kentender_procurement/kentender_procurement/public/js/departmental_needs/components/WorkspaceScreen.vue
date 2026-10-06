<!-- NDS-UI-01 requester/reviewer workspace (§12.1), rendering NDS-DES-01,
     NDS-DES-02 and the NDS-DES-14 shared states with their exact copy,
     ported class-for-class from NDS Artboards.dc.html.
     NDS-CHG-001 v1.13 §11.2/§11.3 — one existing workspace route for both the
     Author and the Head of User Department; this component branches on
     content (a decision queue only exists when there is one), never on a
     role switch. -->
<template>
	<div>
		<!-- NDS-DES-14 LOADING -->
		<div v-if="loading" class="kt-page">
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

		<!-- NDS-DES-14 LOAD-FAILURE — occupies the sheet alone, per KT-PAT-001
		     §5's page-states recipe: no protected header/filters/rows behind it. -->
		<div v-else-if="error" class="kt-page">
			<div
				style="max-width: 620px; margin: 0 auto; text-align: center; display: flex; flex-direction: column; align-items: center; gap: 10px"
			>
				<div style="font-family: var(--kt-font-heading); font-size: 20px; font-weight: 600">
					Departmental Needs could not be loaded.
				</div>
				<p style="margin: 0; font-size: 14.5px; color: var(--kt-color-neutral-700)">
					Try again. If the problem continues, contact support.
				</p>
				<button class="btn btn-secondary" @click="$emit('reload')">Try again</button>
			</div>
		</div>

		<!-- NDS-DES-14 DENIED — kept to the full four-role list (Departmental
		     Author, Head of User Department, Procurement Planner, Auditor); the
		     compact design-canvas card omits Procurement Planner for space, but
		     dropping a real read-eligible role from this help text would mislead
		     a Planner into thinking they have no path in. -->
		<div v-else-if="outcome === 'NO_AUTHORISED_CONTEXT'" class="kt-page">
			<div
				style="max-width: 620px; margin: 0 auto; text-align: center; display: flex; flex-direction: column; align-items: center; gap: 10px"
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
		</div>

		<div v-else class="kt-page">
			<div class="kt-page-head">
				<div>
					<h1 class="kt-page-title">{{ pageTitle }}</h1>
					<p class="kt-page-desc">{{ lede }}</p>
					<!-- §11.1/§11.2 — one compact scope line replaces the four
					     separately labelled Department/FY/submission facts; its
					     parts stay distinguishable through typographic grouping,
					     not a bordered context card. -->
					<div class="kt-page-scope">
						<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" style="color: var(--kt-color-accent-700)"><circle cx="12" cy="12" r="10" /><path d="M12 6v6l4 2" /></svg>
						<!-- §12.1 — several departments combined (nothing resolved
						     to one) is a normal state, not an error; name it the
						     same way the filter option below already does rather
						     than leaving the fact blank. -->
						<span style="font-weight: 600" data-testid="nds-department-fact">{{
							context.organisation_unit_label || context.organisation_unit || "All departments"
						}}</span>
						<span class="text-muted">·</span>
						<span>{{ context.financial_year_label || context.financial_year || "All financial years" }}</span>
						<template v-if="canCreate && submission.open && submission.closes_at">
							<span class="text-muted">·</span>
							<span class="text-muted" data-volatile="true">New submissions open until {{ formatInstant(submission.closes_at) }}</span>
						</template>
					</div>
				</div>
				<div v-if="canCreate" class="kt-page-actions">
					<button class="btn btn-primary" data-testid="nds-create-need" @click="$emit('create')">
						<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M12 5v14M5 12h14" /></svg>Create need
					</button>
				</div>
			</div>

			<!-- NDS-DES-14 CLOSED-WORKSPACE / NO-OPEN-YEAR — `isAuthor`, not
			     `canCreate` (that one requires submission.open, which would make
			     this condition self-contradictory and the notice unreachable —
			     found while auditing this exact family). The read contract does
			     not yet distinguish "a year's flag is closed" from "no year is
			     open" (both resolve to `{ open: false, financial_year: "",
			     closes_at: "" }`), so both fixtures share this one notice and its
			     "New submissions" fact; the Financial year/Closed at facts render
			     only once that data is actually present. -->
			<div
				v-if="isAuthor && !submission.open && needs.length"
				class="kt-notice is-warning"
				data-testid="nds-submission-closed-notice"
			>
				<div class="kt-notice-body">
					New submissions are closed. You can view existing needs and save changes to
					existing drafts.
					<div class="kt-meta-row is-tight" style="gap: 28px; margin-top: 14px">
						<div v-if="submission.label || submission.financial_year">
							<span class="kt-label">Financial year</span><span class="kt-meta-value">{{ submission.label || submission.financial_year }}</span>
						</div>
						<div><span class="kt-label">New submissions</span><span class="kt-meta-value">Closed</span></div>
						<div v-if="submission.closes_at">
							<span class="kt-label">Closed at</span><span class="kt-meta-value">{{ formatInstant(submission.closes_at) }}</span>
						</div>
					</div>
				</div>
			</div>

			<!-- §11.2 — the Author's own in-progress Draft/Returned correction,
			     elevated to a dominant Level-1 task row rather than left to be
			     found only in the register below (NDS-CHG-001 v1.14 §11.2). This
			     need also still appears as its own row in the register — the
			     artboard's own "2 needs" count includes it — so it needs its own
			     testids, distinct from the register's `nds-need-row`/
			     `nds-row-action`, or the two would collide on the same reference. -->
			<div v-if="continueRows.length" class="kt-region">
				<h2>Continue your work</h2>
				<div
					v-for="row in continueRows"
					:key="row.name"
					class="kt-task-row"
					data-testid="nds-continue-row"
					:data-reference="row.reference"
					:data-status="row.status"
				>
					<div style="flex: 1; min-width: 0">
						<div style="font-family: var(--kt-font-heading); font-weight: 600; font-size: 19px">{{ row.title || "Untitled need" }}</div>
						<div class="text-muted" style="font-size: 12px; margin-top: 2px" data-volatile="true">{{ row.reference }}</div>
						<div style="display: flex; align-items: center; gap: 8px; margin-top: 10px; font-size: 13px; color: var(--kt-color-neutral-800)">
							<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" style="color: var(--kt-color-neutral-700)"><rect width="20" height="5" x="2" y="3" rx="1" /><path d="M4 8v11a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8" /><path d="M10 12h4" /></svg>
							<span>{{ row.quantity_label }}</span>
							<span class="text-muted">·</span>
							<span>Required by {{ row.required_by_label }}</span>
						</div>
						<div style="display: flex; align-items: center; gap: 10px; margin-top: 10px">
							<StatusPill :label="row.status" />
							<span style="font-size: 13px; color: var(--kt-color-neutral-800)">{{ continueNarrative(row) }}</span>
						</div>
					</div>
					<button
						v-if="row.actions[0]"
						type="button"
						class="btn btn-primary"
						data-testid="nds-continue-action"
						:data-action="row.actions[0].code"
						@click="$emit('action', row, row.actions[0])"
					>
						{{ row.actions[0].label }}
						<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14" /><path d="m12 5 7 7-7 7" /></svg>
					</button>
				</div>
			</div>

			<!-- NDS-DES-02 first content section — a decision queue only when
			     one exists; never a separate menu entry or role switch. -->
			<div v-if="decisionQueue.length" class="kt-region">
				<h2>{{ decisionQueue.length === 1 ? "1 need requires your decision" : `${decisionQueue.length} needs require your decision` }}</h2>
				<div
					v-for="row in decisionQueue"
					:key="row.name"
					class="kt-task-row"
					data-testid="nds-need-row"
					:data-reference="row.reference"
					:data-status="row.status"
				>
					<div style="flex: 1; min-width: 0">
						<div style="font-family: var(--kt-font-heading); font-weight: 600; font-size: 20px">{{ row.title || "Untitled need" }}</div>
						<div class="text-muted" style="font-size: 12px; margin-top: 2px" data-volatile="true">{{ row.reference }}</div>
						<div style="display: flex; align-items: center; gap: 8px; margin-top: 12px; font-size: 13px; color: var(--kt-color-neutral-800)">
							<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" style="color: var(--kt-color-accent-700)"><path d="M16 3h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h2" /><rect width="8" height="4" x="8" y="2" rx="1" ry="1" /><path d="m9 14 2 2 4-4" /></svg>
							<span>{{ decisionNarrative(row) }}</span>
						</div>
						<div style="display: flex; align-items: center; gap: 8px; margin-top: 8px; font-size: 13px; color: var(--kt-color-neutral-800)">
							<span>{{ row.quantity_label }}</span>
							<span class="text-muted">·</span>
							<span>Required by {{ row.required_by_label }}</span>
						</div>
					</div>
					<button
						type="button"
						class="btn btn-primary"
						data-testid="nds-row-action"
						:data-action="row.actions[0].code"
						@click="$emit('action', row, row.actions[0])"
					>
						{{ decisionActionLabel(row) }}
						<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14" /><path d="m12 5 7 7-7 7" /></svg>
					</button>
				</div>
			</div>

			<div class="kt-region is-secondary">
				<h2>{{ decisionQueue.length ? "All departmental needs" : "All my needs" }}</h2>

				<!-- §11.2 filters — search, status, financial year, department,
				     Clear filters, local to the register they filter. DES-02's
				     fixed-scope fixture shows only Search + Status; FY/Department
				     stay Author-only, matching the same decisionQueue.length
				     signal already used for the register's own column set below. -->
				<div class="kt-filter-bar">
					<div class="field is-wide">
						<label for="nds-workspace-search">Search title or reference</label>
						<span class="nds-search-field"
							><svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8" /><path d="m21 21-4.3-4.3" /></svg
							><input
								id="nds-workspace-search"
								class="input"
								placeholder="Search title or reference"
								data-testid="nds-search"
								:value="search"
								@input="$emit('update:search', $event.target.value)"
						/></span>
					</div>
					<!-- Field order: Search, Status, Financial year, Department, Clear
					     filters — confirmed against 5 separate NDS-DES-01/-RETURNED/
					     -14-EMPTY-READER/-FILTERED-EMPTY/-NO-OPEN-YEAR artboard sections,
					     all consistent. NDS-DES-TECHNICAL-REGISTER's own artboard section
					     draws Department before Financial year before Status instead — a
					     genuine inconsistency against the other 5, not fixable by
					     reordering this one shared filter bar without breaking them;
					     flagged for a design decision rather than guessed at (23 Sep 2026). -->
					<div class="field">
						<label for="nds-workspace-status">Status</label>
						<select
							id="nds-workspace-status"
							class="input"
							data-testid="nds-status-filter"
							:value="status"
							@change="$emit('update:status', $event.target.value)"
						>
							<option value="">All statuses</option>
							<option v-for="option in STATUSES" :key="option" :value="option">{{ option }}</option>
						</select>
					</div>
					<div v-if="!decisionQueue.length" class="field">
						<label for="nds-workspace-fy">Financial year</label>
						<select
							id="nds-workspace-fy"
							class="input"
							data-testid="nds-fy-filter"
							:value="selectedFinancialYear || context.financial_year || ''"
							@change="$emit('select-financial-year', $event.target.value)"
						>
							<option value="">All financial years</option>
							<option v-for="year in financialYears" :key="year.id" :value="year.id">
								{{ year.label }}
							</option>
						</select>
					</div>
					<div v-if="!decisionQueue.length" class="field">
						<label for="nds-workspace-department">Department</label>
						<!-- §12.1 — several departments "remain available through
						     ordinary changeable filters; they do not block page
						     entry," and clearing this filter is the visible reset
						     back to every authorised department combined. -->
						<select
							id="nds-workspace-department"
							class="input"
							data-testid="nds-department-filter"
							:value="context.organisation_unit || ''"
							@change="$emit('select-context', $event.target.value)"
						>
							<option value="">All departments</option>
							<option
								v-for="row in contexts"
								:key="row.organisation_unit"
								:value="row.organisation_unit"
							>
								{{ row.organisation_unit_label }}
							</option>
						</select>
					</div>
					<button type="button" class="btn btn-secondary" @click="$emit('clear-filters')">
						Clear filters
					</button>
				</div>

				<!-- NDS-DES-14 EMPTY-AUTHOR / EMPTY-READER / FILTERED-EMPTY -->
				<div v-if="!registerRows.length" class="kt-empty">
					<div style="font-family: var(--kt-font-heading); font-size: 18px; font-weight: 600">
						{{ emptyHeadline }}
					</div>
					<p style="margin: 8px 0 0; font-size: 14px; color: var(--kt-color-neutral-700)">
						{{ emptyBody }}
					</p>
				</div>

				<NeedsTable
					v-else
					:needs="pagedRows"
					:columns="registerColumns"
					@action="(row, action) => $emit('action', row, action)"
				/>

				<TablePagerHost
					v-if="registerRows.length"
					:total="registerRows.length"
					:page="currentPage"
					:page-size="pageSize"
					:noun="registerNoun"
					@update:page="(n) => $emit('update:page', n)"
					@update:page-size="changePageSize"
				/>
			</div>
		</div>
	</div>
</template>

<script setup>
import { computed } from "vue";
import NeedsTable from "./NeedsTable.vue";
import TablePagerHost from "../../pager_shared/TablePagerHost.vue";
import StatusPill from "./StatusPill.vue";
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
	// The table-pagination standard: the root keeps these so a visit to a need
	// and back lands on the same page.
	page: { type: Number, default: 1 },
	pageSize: { type: Number, default: 10 },
});

const emit = defineEmits([
	"update:page",
	"update:pageSize",
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

// NDS-DES-14-CLOSED-WORKSPACE/NO-OPEN-YEAR — whether this actor authors here
// at all, independent of whether intake happens to be Open right now: an
// eligible Author keeps the "My needs" framing and lede while submissions
// are closed (the artboards above keep both), only the Create button itself
// disappears. Kept separate from `canCreate` below, which folds the flag
// back in for exactly that button.
const isAuthor = computed(() => props.actions.some((action) => action.code === "create"));

// §12.1 — Create need needs both: the server must offer the action (only an
// author in this context does), and Needs submission must be Open. The flag
// check alone would show the button to a reviewer for as long as it is Open.
const canCreate = computed(() => isAuthor.value && !!props.submission.open);

const lede = computed(() =>
	isAuthor.value
		? "Describe your department's requirements and follow their review."
		: "Review submitted requirements and view the department's needs."
);

// §11.2/§11.3 — "My needs" for the Author's own list, "Departmental Needs"
// once a reviewer's shared decision queue is in view.
const pageTitle = computed(() => (isAuthor.value ? "My needs" : "Departmental Needs"));

// §11.2 — the Author's own in-progress work, elevated out of the register
// into its own dominant task-row region. An "edit" action (Continue on a
// Draft, Correct on a Returned correction) is exactly the signal the
// workspace service already uses to mean "this row is incomplete and its
// own author owns it" (services/workspace.py `_actions`) — reused here
// rather than inventing a second notion of "in progress."
const continueRows = computed(() =>
	props.needs.filter((row) => (row.actions || [])[0]?.code === "edit")
);

// §11.3 — rows with an open decision the viewer may act on lead the page,
// separate from the full department register below.
const decisionQueue = computed(() =>
	props.needs.filter((row) => ["review", "withdrawal"].includes((row.actions || [])[0]?.code))
);

// "Initial requirement submitted by Grace Wanjiku" (NDS-DES-02) — built from
// the same `review_kind` label the server already sends for the retired
// decision-queue table's "Review" column, plus the requester's name.
function decisionNarrative(row) {
	const kind = row.actions?.[0]?.review_kind || "Requirement";
	return `${kind} submitted by ${row.author_label || "the requester"}`;
}

function continueNarrative(row) {
	return row.status === "Returned"
		? "Correct this requirement before resubmission."
		: "Continue describing this requirement before submission.";
}

// NDS-DES-02's dominant task-row action reads "Review requirement" — more
// specific than the register's plain "Review"/"Review withdrawal" (already
// exact from the server, kept as-is), since this button is the page's one
// primary action rather than a row among many.
function decisionActionLabel(row) {
	const action = row.actions?.[0];
	if (!action) return "";
	return action.code === "review" ? "Review requirement" : action.label;
}

const registerColumns = computed(() =>
	decisionQueue.value.length
		? [
				// §11.3 — the department register (HoD view): Requester replaces the
				// author's own "Requested by" phrasing once a decision section
				// already leads the page.
				{ key: "need", label: "Requirement" },
				{ key: "organisation_unit_label", label: "Department" },
				{ key: "author_label", label: "Requester" },
				{ key: "quantity_required_by", label: "Quantity and required by" },
				{ key: "status", label: "Status", status: true },
				{ key: "action", label: "Action", align: "right" },
			]
		: [
				// §11.2 — the author's own list.
				{ key: "need", label: "Requirement" },
				{ key: "organisation_unit_label", label: "Department" },
				{ key: "quantity_required_by", label: "Quantity and required by" },
				{ key: "status", label: "Status", status: true },
				{ key: "action", label: "Action", align: "right" },
			]
);

// The full register excludes rows already shown in the decision queue above —
// §11.3's two sections partition the same list, they do not repeat a row.
const registerRows = computed(() => {
	if (!decisionQueue.value.length) return props.needs;
	const queued = new Set(decisionQueue.value.map((row) => row.name));
	return props.needs.filter((row) => !queued.has(row.name));
});

// The noun the pager counts in: §11.2 "2 needs" (the author's own list) vs.
// §11.3 "2 department needs" (the register beneath a decision queue) — counted
// from what is actually rendered in this table, not the server's raw total
// across both sections.
const registerNoun = computed(() => (decisionQueue.value.length ? "department need" : "need"));

// The register is paged in the browser: the decision queue and "continue"
// sections above it need every row, so the server sends the whole list.
const pageCount = computed(() => Math.max(1, Math.ceil(registerRows.value.length / props.pageSize)));
const currentPage = computed(() => Math.min(Math.max(props.page, 1), pageCount.value));
const pagedRows = computed(() => {
	const start = (currentPage.value - 1) * props.pageSize;
	return registerRows.value.slice(start, start + props.pageSize);
});

function changePageSize(size) {
	emit("update:pageSize", size);
	emit("update:page", 1);
}

// An empty list under active filters means "nothing matched", not "nothing
// exists" — the create-first copy would misstate the workspace.
const filtersActive = computed(
	() => !!(props.search || props.status || props.selectedFinancialYear)
);

const emptyHeadline = computed(() => {
	if (filtersActive.value) return "No needs match your filters";
	return isAuthor.value ? "No departmental needs yet" : "No departmental needs to display";
});

const emptyBody = computed(() => {
	if (filtersActive.value) return "Adjust your search or clear the filters.";
	return isAuthor.value
		? "Describe the first requirement for your department."
		: "";
});
</script>
