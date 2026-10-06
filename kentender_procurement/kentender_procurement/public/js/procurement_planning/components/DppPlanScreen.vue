<!-- PLN-CHG-001 v1.24 §10.4 — the departmental plan (U02–U05), ported
     class-for-class from Artboards-U02-U05.dc.html.

     One page, two readings of it. The Author sees their own working plan and
     is told plainly that their Head of Department submits it; the HoD sees the
     same plan as a complete review with the certification and one submit
     action beneath it. There is no separate certification page and no invented
     Author-to-HoD handover step (§9.7).

     Excluded requirements stay in the table — they are accounted for, not
     hidden — with their full reason always visible in row detail, never behind
     a disclosure (§10.4 U03-EXCLUDED-ROW).

     Re-diffed 23 Sep 2026 against the actual v1.24 U02/U03/U05 sections (this
     header previously cited a bare "U02-U05.dc.html", unresolvable against the
     real "Artboards-U02-U05.dc.html" file — see kentender_core's
     test_artboard_provenance_gate). Found and fixed: the U05-CORRECTION row
     comment was labelled "What needs to change?" (the *input* label from the
     return dialog) instead of the artboard's own display label "Procurement
     comment"; the "Returned submission"/"Correction submission" context pair
     never rendered for a plain pre-acceptance correction (the backing fields
     were only ever populated on the accepted-update path); U02-CLOSED's
     footer note was rendered as an invented warning banner near the top of
     the page instead of the artboard's own plain paragraph "above the
     footer", in the same slot as the Author's submit hint; that submit hint
     itself carried invented copy ("Only the Head of User Department, or an
     acting head, can submit this plan.") gated on plan readiness, when the
     artboard shows the same fixed sentence on every mutable Author state
     regardless of readiness; and U03-FUNDING's own row kept its live action
     link while its panel was open beneath it, instead of the artboard's
     plain "Editing" text. -->
<template>
	<div>
		<div class="kt-page">
			<div class="kt-page-head">
				<div>
					<h1 class="kt-page-title" data-testid="pln-dpp-title">{{ heading.title }}</h1>
					<p class="kt-page-desc">{{ heading.description }}</p>
					<!-- PLN v1.27 §10.4 — the next step (Your turn / Waiting / Done). -->
					<div ref="headEl" class="kt-guidance-mount" data-testid="pln-dpp-next-step-line"></div>
				</div>
			</div>
			<!-- The DPP journey — reduced to one line on the Author's own draft,
			     where the summary strip and table already fill the first view —
			     then a blocked answer (U02-CLOSED) above the context row. -->
			<div ref="journeyEl" class="kt-guidance-mount" data-testid="pln-dpp-journey"></div>
			<div ref="bodyEl" class="kt-guidance-mount" data-testid="pln-dpp-next-step-block"></div>

			<!-- Record context: separately labelled values, names before codes. -->
			<!-- U02-U05 is the one board that genuinely draws the context row
			     outside the head — and draws it tight, so the facts sit together
			     instead of spreading across the sheet. -->
			<div class="kt-meta-row is-tight pln-context-row" data-testid="pln-dpp-context">
				<div>
					<span class="kt-label">Department</span>
					<span class="kt-meta-value">{{ context.department }}</span>
				</div>
				<div>
					<span class="kt-label">Financial year</span>
					<span class="kt-meta-value">{{ context.financial_year }}</span>
				</div>
				<!-- U02-AUTHOR-DRAFT: the reduced tracker states the stage, so the
				     Status cell goes (v1.27 §10.4); every other variant keeps it. -->
				<div v-if="!plan.journey?.reduced">
					<span class="kt-label">Status</span>
					<span class="kt-meta-value">
						<span class="kt-status" :class="`is-${plan.header?.badge_kind || 'draft'}`">{{ plan.header?.badge }}</span>
					</span>
				</div>
				<div v-if="plan.accepted_submission_number">
					<span class="kt-label">Accepted submission</span>
					<span class="kt-meta-value">{{ plan.accepted_submission_number }}</span>
				</div>
				<!-- U05-CORRECTION — which submission Procurement returned, named
				     separately from the correction draft's own eventual submission
				     number below it. -->
				<div v-if="plan.is_correction && plan.returned_submission_number">
					<span class="kt-label">Returned submission</span>
					<span class="kt-meta-value">{{ plan.returned_submission_number }}</span>
				</div>
				<div v-if="plan.is_correction && plan.candidate_submission_number">
					<span class="kt-label">Correction submission</span>
					<span class="kt-meta-value">{{ plan.candidate_submission_number }}</span>
				</div>
			</div>

			<!-- §4.4 — a returned issue against the whole submission rather
			     than one requirement. -->
			<div
				v-for="(issue, index) in plan.plan_issues || []"
				:key="`plan-issue-${index}`"
				class="kt-notice is-warning"
				data-testid="pln-dpp-plan-issue"
			>
				<svg class="kt-notice-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
					<path d="M12 3l9 16H3z"></path><path d="M12 10v4M12 17h.01"></path>
				</svg>
				<div class="kt-notice-body">
					<strong>What needs to change?</strong>
					<p>{{ issueText(issue) }}</p>
				</div>
			</div>

			<!-- Procurement's request to update this plan: a line of the annual
			     plan update is over its approved budget (owner decision
			     26 Sep 2026). -->
			<div v-if="plan.update_request_notice" class="kt-notice is-warning" data-testid="pln-dpp-update-request">
				<svg class="kt-notice-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
					<path d="M12 3l9 16H3z"></path><path d="M12 10v4M12 17h.01"></path>
				</svg>
				<div class="kt-notice-body">
					<strong>{{ plan.update_request_notice.title }}</strong>
					<p>{{ plan.update_request_notice.text }}</p>
					<p class="pln-dpp-update-request-asked">{{ plan.update_request_notice.asked }}</p>
				</div>
			</div>

			<!-- Needs accepted after this plan was accepted are named by the next
			     step above ("Your turn — Add … to this plan"), with Create update
			     as the principal action; it replaced a separate notice here that
			     stated the same thing (owner decision 26 Sep 2026). -->

			<!-- Summary strip. The Author's cost label says "entered so far" because
			     that is what it is: no complete departmental total exists yet. -->
			<div class="kt-group" data-testid="pln-dpp-summary">
				<div class="kt-meta-row">
					<div><span class="kt-label">Requirements</span><span class="kt-meta-value">{{ summary.requirements }}</span></div>
					<div><span class="kt-label">{{ summary.cost_label }}</span><span class="kt-meta-value">{{ summary.cost }}</span></div>
					<div>
						<span class="kt-label">{{ summary.third_label }}</span>
						<span class="kt-meta-value" :style="summary.attention ? 'color:var(--kt-status-attention)' : ''">{{ summary.third }}</span>
					</div>
				</div>
			</div>

			<div class="kt-region">
				<h2>Requirements</h2>
				<table class="table pln-dpp-table" data-testid="pln-dpp-table">
				<thead>
					<tr>
						<th>Requirement</th>
						<th class="is-num">Quantity</th>
						<th>Unit</th>
						<th>Required by</th>
						<th class="is-num">Estimated cost</th>
						<th>Status</th>
						<th>Action</th>
					</tr>
				</thead>
				<tbody>
					<template v-for="row in pagedEntries" :key="row.entry_id">
						<tr data-testid="pln-dpp-row">
							<td>
								{{ row.title }}
								<div class="kt-muted pln-row-ref">{{ row.reference_line }}</div>
							</td>
							<td class="is-num">{{ row.quantity_number }}</td>
							<td>{{ row.unit_label }}</td>
							<td>{{ row.required_by_display }}</td>
							<td class="is-num">{{ row.amount_display }}</td>
							<td><span class="kt-status" :class="`is-${row.status_kind}`">{{ row.status }}</span></td>
							<td>
								<!-- U03-FUNDING — the row whose panel is already open beneath
								     it names that fact instead of repeating a now-redundant
								     live action link. -->
								<span v-if="fundingEntryId === row.entry_id" class="btn btn-ghost kt-muted" data-testid="pln-dpp-row-editing">Editing</span>
								<a
									v-else-if="row.action"
									href="#"
									class="btn btn-ghost"
									data-testid="pln-dpp-row-action"
									@click.prevent="onRowAction(row)"
								>{{ row.action }}</a>
								<span v-else>—</span>
							</td>
						</tr>
						<!-- U03-FUNDING — the funding panel opens beneath the
						     requirement it is about, with the rest of the plan still
						     visible above and below it. -->
						<tr v-if="fundingEntryId === row.entry_id" class="pln-row-detail" data-testid="pln-dpp-funding-row">
							<td colspan="7">
								<EntryFundingPanel
									:editor="fundingEditor"
									:budget-line="fundingBudgetLine"
									:amount="fundingAmount"
									:pending="pending"
									:error="errorSummary"
									@save="$emit('save-funding')"
									@cancel="$emit('close-funding')"
									@exclude="$emit('exclude-entry', row)"
									@correct-source="$emit('correct-source', row)"
									@update:budget-line="$emit('update:fundingBudgetLine', $event)"
									@update:amount="$emit('update:fundingAmount', $event)"
								/>
							</td>
						</tr>
						<!-- U03-EXCLUDED-ROW — the reason is always visible, never
						     behind a disclosure: it is the whole content of the row. -->
						<tr v-if="row.not_proceeding_reason" class="pln-row-detail" data-testid="pln-dpp-exclusion-reason">
							<td colspan="7">
								<span class="kt-label">Reason for excluding this requirement</span>
								<span>{{ row.not_proceeding_reason }}</span>
							</td>
						</tr>
						<!-- U05-CORRECTION — Procurement's comment sits beside the row
						     it is about, in full. -->
						<tr v-for="(issue, index) in row.issues || []" :key="`${row.entry_id}-issue-${index}`" class="pln-row-detail" data-testid="pln-dpp-issue">
							<td colspan="7">
								<span class="kt-label">Procurement comment</span>
								<span>{{ issueText(issue) }}</span>
							</td>
						</tr>
					</template>
					<tr v-if="!entries.length">
						<td colspan="7" class="kt-muted" data-testid="pln-dpp-empty">No requirements yet.</td>
					</tr>
				</tbody>
				</table>
				<TablePagerHost :total="entriesTotal" :page="entriesPage" :page-size="entriesPageSize" noun="requirement" @update:page="setEntriesPage" @update:page-size="setEntriesPageSize" />

				<div v-if="plan.mutable" class="pln-dpp-add">
					<button type="button" class="btn btn-secondary" data-testid="pln-dpp-add" @click="$emit('add-direct')">
						<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"><path d="M12 5v14"></path><path d="M5 12h14"></path></svg>
						Add a requirement
					</button>
				</div>
			</div>

			<!-- U05-CORRECTION's "For your next departmental update": named, and
			     deliberately without an add action — the correction comes first. -->
			<div v-if="plan.is_correction" class="kt-region is-secondary">
				<h2>For your next departmental update</h2>
				<p data-testid="pln-dpp-next-update">
					Finish this correction first. New requirements belong in the next update.
				</p>
			</div>

			<!-- Certification: the HoD's, on the complete plan, on this page. -->
			<div v-if="certification.show" class="kt-decision" data-testid="pln-dpp-certification">
				<h2 style="font-family: var(--kt-font-heading); font-size: 21px; margin: 0 0 var(--kt-space-3)">Certification</h2>
				<p class="kt-muted">{{ certification.text }}</p>
				<label class="kt-checkbox">
					<input
						type="checkbox"
						data-testid="pln-dpp-certify"
						:checked="certified"
						@change="$emit('update:certified', $event.target.checked)"
					>
					<span class="box"></span>{{ certification.checkbox_label }}
				</label>
			</div>

			<p v-if="errorSummary" class="pln-error-summary" data-testid="pln-dpp-error">{{ errorSummary }}</p>

			<!-- §10.16 C02-DPP-CLOSED — immediately above the action it blocks. -->
			<!-- …unless the next-step block already states it with its fix (D3). -->
			<MissingSettingPanel v-if="plan.missing_setting && !windowClosedBlocker" :panel="plan.missing_setting" />

			<!-- Action area, after all decision content. -->
			<div class="pln-footer" data-testid="pln-dpp-footer">
				<button type="button" class="btn btn-secondary" data-testid="pln-dpp-back" @click="$emit('back')">
					Back
				</button>
				<div class="pln-footer-right">
					<!-- U05-HOD/U05-CORRECTION, U02-CLOSED, U02-AUTHOR-DRAFT — one
					     footer note slot, in priority order: certify, then closed
					     (it replaces the submit hint rather than sitting beside it —
					     §10.4's own "above the footer" placement, not a separate
					     banner), then the Author is told who submits, rather than
					     shown a control they cannot use. -->
					<p v-if="certification.show && !certified" class="kt-muted" data-testid="pln-dpp-certify-hint">
						Confirm the certification to submit this plan.
					</p>
					<!-- U02-CLOSED: the blocked next-step block above says it. -->
					<p v-else-if="plan.submit_hint && !intakeClosed" class="kt-muted" data-testid="pln-dpp-submit-hint">{{ plan.submit_hint }}</p>
					<button
						v-if="plan.mutable"
						type="button"
						class="btn btn-secondary"
						data-testid="pln-dpp-save"
						:disabled="pending"
						@click="$emit('save-draft')"
					>
						Save draft
					</button>
					<button
						v-if="plan.can_submit"
						type="button"
						class="btn btn-primary"
						data-testid="pln-dpp-submit"
						:disabled="pending || !certified"
						@click="$emit('submit')"
					>
						{{ plan.is_correction ? "Resubmit departmental plan" : "Submit departmental plan" }}
					</button>
					<button
						v-if="plan.can_create_update"
						type="button"
						class="btn btn-primary"
						data-testid="pln-dpp-create-update"
						:disabled="pending"
						@click="$emit('create-update')"
					>
						Create update
					</button>
				</div>
			</div>

			<!-- The Planner holding the open task is never stranded on the record. -->
			<div v-if="plan.open_task" class="pln-dpp-task" data-testid="pln-dpp-open-task">
				<button type="button" class="btn btn-primary" @click="$emit('open-task', plan.open_task.route)">
					{{ plan.open_task.label }}
				</button>
			</div>
		</div>
	</div>
</template>

<script setup>
import { computed, ref } from "vue";
import { useGuidance } from "../../pln_shared/composables/useGuidance.js";
import MissingSettingPanel from "./MissingSettingPanel.vue";
import EntryFundingPanel from "./EntryFundingPanel.vue";
import TablePagerHost from "../../pager_shared/TablePagerHost.vue";
import { usePagedRows } from "../../pager_shared/usePagedRows.js";

const props = defineProps({
	plan: { type: Object, default: () => ({}) },
	pending: Boolean,
	certified: Boolean,
	errorSummary: String,
	// §10.4 U03-FUNDING — the one requirement whose funding panel is open,
	// and the caller's own draft of it.
	fundingEntryId: { type: String, default: "" },
	fundingEditor: { type: Object, default: () => ({}) },
	fundingBudgetLine: { type: String, default: "" },
	fundingAmount: { type: [String, Number], default: "" },
});

const emit = defineEmits([
	"view-accepted-needs",
	"add-direct",
	"open-entry",
	"restore-entry",
	"open-funding",
	"save-funding",
	"close-funding",
	"exclude-entry",
	"correct-source",
	"update:fundingBudgetLine",
	"update:fundingAmount",
	"back",
	"save-draft",
	"submit",
	"create-update",
	"open-task",
	"update:certified",
]);

const context = computed(() => props.plan.context || {});
const certification = computed(() => props.plan.certification || {});
const entries = computed(() => props.plan.entries || []);
// The table-pagination standard (AGENTS.md §6.11): a departmental plan's requirements, paged per plan submission.
const {
	pagedRows: pagedEntries, total: entriesTotal, page: entriesPage, pageSize: entriesPageSize, setPage: setEntriesPage, setPageSize: setEntriesPageSize,
} = usePagedRows(entries, () => `planning-dpp:${props.plan.header?.reference_line || ""}`);
const isHod = computed(() => props.plan.access === "hod");

const heading = computed(() => {
	const department = context.value.department_name || context.value.department || "your department";
	// Owner instruction 28 Sep 2026 — a plan nobody can edit is not asked to be
	// reviewed and submitted: an accepted plan beside "Your turn: Add … to this
	// plan" read as a contradiction. The heading names the plan and its state;
	// what to do next is the next step's to say.
	if (!props.plan.mutable && props.plan.version?.status === "Submitted") {
		return {
			title: `${department}'s departmental plan`,
			description: "Submitted to Procurement for review. It cannot be changed while Procurement reviews it.",
		};
	}
	if (!props.plan.mutable && props.plan.current_state === "Accepted") {
		return {
			title: `${department}'s departmental plan`,
			description: "Accepted by Procurement for this financial year.",
		};
	}
	if (isHod.value) {
		return {
			title: `Review ${department}'s departmental plan`,
			description: "Check the requirements and submit the complete departmental plan to Procurement.",
		};
	}
	return {
		title: "Your departmental procurement plan",
		description:
			"Review what your department needs this year. Select a budget line and enter the estimated cost for each requirement you intend to include.",
	};
});

// The HoD reads a finished plan (included cost, excluded count); the Author is
// still entering one (cost so far, what still needs details).
const summary = computed(() => {
	const rows = entries.value;
	const excluded = rows.filter((r) => r.disposition === "Not proceeding");
	const included = rows.filter((r) => r.disposition !== "Not proceeding");
	const needingDetails = included.filter((r) => r.status === "Funding details needed");
	if (isHod.value) {
		return {
			requirements: rows.length,
			cost: props.plan.included_cost_display || "",
			cost_label: "Included cost",
			third: excluded.length,
			third_label: "Excluded requirements",
			attention: false,
		};
	}
	return {
		requirements: rows.length,
		cost: props.plan.included_cost_display || "",
		cost_label: "Cost entered so far",
		third: needingDetails.length,
		third_label: "Requirements needing details",
		attention: needingDetails.length > 0,
	};
});

const headEl = ref(null);
const journeyEl = ref(null);
const bodyEl = ref(null);
useGuidance({ journeyEl, headEl, bodyEl }, { answer: () => props.plan.next_step, journey: () => props.plan.journey, pending: () => props.pending });
const windowClosedBlocker = computed(() =>
	(props.plan.next_step?.blockers || []).some((blocker) => blocker.reason_code === "PLN_WINDOW_CLOSED"),
);

// The initial window is closed for this ordinary draft (not a correction or
// update): the submit hint gives way to the blocked next-step block.
const intakeClosed = computed(() => {
	const window = context.value.window || {};
	return window.state === "Closed" && Boolean(props.plan.mutable) && !props.plan.is_correction;
});

function onRowAction(row) {
	if (row.action === "Include in this year's departmental plan") {
		emit("restore-entry", row);
		return;
	}
	// An accepted requirement's funding belongs here, beneath its own row; a
	// direct requirement is the department's own record and opens as one.
	if (row.opens_funding_panel) {
		emit("open-funding", row);
		return;
	}
	emit("open-entry", row);
}

// §4.4 — a new issue carries one comment; a historical decision still carries
// the retired two-field shape, and both facts of it are shown rather than one
// discarded.
function issueText(issue) {
	if (issue.correction_required) return issue.correction_required;
	return [issue.problem, issue.correction].filter(Boolean).join(" — ");
}
</script>
