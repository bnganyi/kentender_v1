<!-- PLN-CHG-001 v1.24 §10.6 — Annual plan preparation (U07), ported from
     Artboards-U07-U08.dc.html.

     Purchases lead and each one names its own next work. Then one concise Plan
     checks section: three named results, only the ones that decide what to do
     next. The line-by-line comparisons and the reservation arithmetic live in
     their own detail — repeating them here is what made the old preparation
     page unreadable (PLN22-CHG-005).

     There is deliberately no Approval and publication section while the
     Planner is still preparing a Draft, and no stepper: funding and governance
     are sections of one plan's life, not stages of a wizard. -->
<template>
	<div>
		<div class="kt-page">
			<!-- The board's own head: the title, the plan it belongs to, and
			     one scope line identifying the record. This was a six-cell
			     `.kt-meta-row` below the head — the same shape U09 was already
			     corrected away from, left behind here — which read as the
			     page's first section rather than as the record's identity
			     (found live 24 Sep 2026). -->
			<div class="kt-page-head">
				<div>
					<h1 class="kt-page-title" data-testid="ppl-title">{{ title }}</h1>
					<p class="kt-page-desc">{{ plan.header?.title }}</p>
					<div class="kt-page-scope" data-testid="ppl-context">
						<span>{{ plan.plan_reference }}</span>
						<span>· Version {{ plan.version_number }}</span>
						<span>· {{ plan.financial_year_label }}</span>
						<span v-if="plan.is_successor && currentVersion">· Current plan Version {{ currentVersion }}</span>
						<span class="kt-status" :class="badgeClass">{{ statusLabel }}</span>
					</div>
					<!-- KT-STD-001 v1.8 §2.9.1 — Your turn / Waiting / Done, one line
					     in the header after the scope line (U07-FINANCE-COMPLETE). -->
					<div ref="headEl" class="kt-guidance-mount" data-testid="ppl-next-step-line"></div>
					<!-- The decider's own task (FU-14: the record route never
					     strands whoever holds an open task), in the header beside
					     the status and the "Your turn" line it answers — found
					     live 9 Oct 2026 at the foot of the page, below history. -->
					<div v-if="plan.open_task" class="pln-head-action">
						<button type="button" class="btn btn-primary" data-testid="ppl-open-task" @click="$emit('open-task', plan.open_task.route)">
							{{ plan.open_task.label }}
						</button>
					</div>
				</div>
			</div>

			<!-- PLN v1.27 §10.1A.1 — the journey tracker directly below the
			     header, then the blocked next-step block when one is drawn. They
			     replace the Funding "Not yet checked" cell and the old Approval
			     waiting notice (§10.6 v1.26 table). -->
			<div ref="journeyEl" class="kt-guidance-mount" data-testid="ppl-journey"></div>
			<div ref="bodyEl" class="kt-guidance-mount" data-testid="ppl-next-step-block"></div>

			<!-- U07-UPDATE — a successor must say why it exists. The board holds
			     the field in its own region (U07 update family). -->
			<div v-if="plan.is_successor" class="kt-region">
			<div class="field pln-plan-field" data-testid="ppl-change-reason">
				<label for="ppl-change-reason" class="kt-label">Reason for updating the plan</label>
				<textarea
					id="ppl-change-reason"
					class="input"
					rows="2"
					:value="changeReasonDraft"
					:disabled="!plan.mutable"
					@input="changeReasonDraft = $event.target.value"
				></textarea>
			</div>
			</div>

			<!-- §10.6 — Project name is omitted when blank. A whole-plan field with
			     nothing in it is not worth a control on every visit. -->
			<div v-if="plan.project_name || showProjectName" class="field pln-plan-field" data-testid="ppl-project-name">
				<label for="ppl-project" class="kt-label">Project name (if applicable)</label>
				<input
					id="ppl-project"
					class="input"
					data-testid="ppl-project-input"
					:value="projectNameDraft"
					:disabled="!plan.mutable"
					@input="projectNameDraft = $event.target.value"
				>
				<div class="kt-field-hint">Leave blank when the plan covers several projects.</div>
			</div>
			<button
				v-else-if="plan.mutable"
				type="button"
				class="btn btn-ghost pln-plan-field"
				data-testid="ppl-add-project-name"
				@click="showProjectName = true"
			>
				Add a project name
			</button>

			<div ref="purchasesEl" class="kt-region" tabindex="-1" data-testid="ppl-purchases-region">
				<h2>Purchases</h2>
				<template v-if="items.length">
					<table class="table" data-testid="ppl-purchases">
						<thead>
							<tr>
								<th>Purchase</th>
								<th class="is-num">Quantity</th>
								<th>Unit</th>
								<th class="is-num">Estimated cost</th>
								<th>Required by</th>
								<th>Current work</th>
								<th>Action</th>
							</tr>
						</thead>
						<tbody>
							<tr v-for="row in pagedItems" :key="row.plan_item_id" data-testid="ppl-purchase-row">
								<td>
									{{ row.title }}
									<div class="kt-muted pln-row-ref">{{ row.plan_item_id }}</div>
								</td>
								<td class="is-num">{{ row.quantity_number }}</td>
								<td>{{ row.unit_label }}</td>
								<td class="is-num">{{ row.value_display }}</td>
								<td>{{ row.completion_display }}</td>
								<td>
									<span class="kt-status" :class="row.current_work === 'Ready' ? 'is-live' : 'is-attention'" data-testid="ppl-current-work">{{ row.current_work }}</span>
								</td>
								<td>
									<!-- A reader who cannot act on this plan (e.g. a Finance
									     Confirmation Officer) reaches the same, correctly
									     read-only editor — but the row's own label must not
									     promise a control the viewer does not have (found
									     live 23 Sep 2026). -->
									<a href="#" class="btn btn-ghost" data-testid="ppl-purchase-action" @click.prevent="$emit('navigate', row.route)">{{ plan.mutable ? "Edit purchase" : "View purchase" }}</a>
								</td>
							</tr>
						</tbody>
					</table>
					<TablePagerHost :total="itemsTotal" :page="itemsPage" :page-size="itemsPageSize" noun="purchase" @update:page="setItemsPage" @update:page-size="setItemsPageSize" />
					<!-- Right beside the table its own "Current work" column is read
					     from, not a footer sentence several sections and a scroll away
					     that just said "shown above" — a Planner should not have to
					     remember which rows said what after scrolling past
					     Requirements, Plan checks and Changes and history to reach it
					     (found live 23 Sep 2026: the first version of this notice sat
					     only in the footer). -->
					<div v-if="incompleteItems.length" class="kt-notice is-warning" data-testid="ppl-incomplete-notice">
						<svg class="kt-notice-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
							<path d="M12 3l9 16H3z"></path><path d="M12 10v4M12 17h.01"></path>
						</svg>
						<div class="kt-notice-body">
							{{ incompleteItems.length === 1 ? "The purchase above" : `${incompleteItems.length} of the purchases above` }}
							must show Ready in Current work — open it from Action to complete it — before this plan can be sent to Finance for funding review.
						</div>
					</div>
				</template>
				<div v-else class="kt-empty" data-testid="ppl-purchases-empty">No purchases have been added yet.</div>
			</div>

			<!-- U07-UNALLOCATED — the sources still waiting to become purchases. -->
			<div ref="requirementsEl" class="kt-region" :class="{ 'is-secondary': !unallocated.length }" tabindex="-1" data-testid="ppl-requirements">
				<h2>Requirements ready to add</h2>
				<template v-if="unallocated.length">
					<table class="table" data-testid="ppl-unallocated">
						<thead>
							<tr>
								<th v-if="plan.mutable">Select</th>
								<th>Requirement</th>
								<th>Department</th>
								<th class="is-num">Quantity</th>
								<th>Unit</th>
								<th class="is-num">Estimated cost</th>
								<th>Action</th>
							</tr>
						</thead>
						<tbody>
							<tr v-for="row in pagedUnallocated" :key="row.entry_id" data-testid="ppl-unallocated-row">
								<td v-if="plan.mutable">
									<label class="kt-checkbox">
										<input
											type="checkbox"
											data-testid="ppl-select-source"
											:checked="selected.includes(row.entry_id)"
											@change="$emit('toggle-source', row.entry_id)"
										>
										<span class="box"></span>
									</label>
								</td>
								<td>
									{{ row.title }}
									<div class="kt-muted pln-row-ref">{{ row.source_label }}</div>
								</td>
								<td>{{ row.department }}</td>
								<td class="is-num">{{ row.quantity_number }}</td>
								<td>{{ row.unit_label }}</td>
								<td class="is-num">{{ row.amount_display }}</td>
								<td>
									<a href="#" class="btn btn-ghost" data-testid="ppl-view-requirement" @click.prevent="$emit('view-requirement', row)">View requirement</a>
								</td>
							</tr>
						</tbody>
					</table>
					<TablePagerHost :total="unallocatedTotal" :page="unallocatedPage" :page-size="unallocatedPageSize" noun="requirement" @update:page="setUnallocatedPage" @update:page-size="setUnallocatedPageSize" />
					<!-- A reader who cannot form purchases is not offered the control
					     at all: this cycle shows no control a reader cannot use. -->
					<div v-if="plan.mutable" class="pln-add-selected">
						<p v-if="!selected.length" class="kt-muted" data-testid="ppl-select-hint">Select at least one requirement.</p>
						<button
							type="button"
							class="btn btn-primary"
							data-testid="ppl-add-selected"
							:disabled="pending || !selected.length"
							@click="$emit('open-form-dialog')"
						>
							Add selected requirements
						</button>
					</div>
				</template>
				<p v-else class="kt-muted" data-testid="ppl-all-allocated">{{ allAllocatedText }}</p>
			</div>

			<!-- Plan checks (PLN v1.27 §10.1A.3, U07 boards): budget fit is a
			     live computed result, never "not yet checked", and Finance
			     confirmation is its own labelled fact (KT-STD-001 v1.8 §3B.3).
			     When a line is over its approved amount the comparison opens as
			     its own table; when every line fits it is one quiet fact with
			     the table behind "View budget lines". The reservation shortfall
			     is a signature blocker (D2), so it is a plain row with its
			     correction, not the page's dominant warning. -->
			<div ref="checksEl" class="kt-region" tabindex="-1" data-testid="ppl-plan-checks-region">
				<h2>Plan checks</h2>
				<template v-if="budgetFit && !budgetFit.all_within">
					<div class="pln-fit-head" data-testid="ppl-budget-fit-over">
						<span class="pln-fit-title">Budget fit, checked now</span>
						<span class="pln-fit-over">{{ budgetFit.result }}</span>
					</div>
					<table class="table" data-testid="ppl-budget-fit-table">
						<thead><tr><th>Budget line</th><th class="is-num">Approved</th><th class="is-num">This plan</th><th class="is-num">Difference</th></tr></thead>
						<tbody>
							<tr v-for="line in budgetFit.lines" :key="line.budget_line">
								<td><div class="pln-fit-line">{{ line.title }}</div><div class="kt-muted pln-row-ref">{{ line.reference }}</div></td>
								<td class="is-num">{{ line.approved_display }}</td>
								<td class="is-num">{{ line.planned_display }}</td>
								<td class="is-num" :class="{ 'pln-fit-over-cell': line.over }">{{ line.difference_display }}</td>
							</tr>
						</tbody>
					</table>
				</template>
				<div v-for="check in failingChecks" :key="check.label" class="pln-check-row" data-testid="ppl-check-issue">
					<p class="pln-check-row-text"><strong>{{ check.label }}</strong> {{ check.result }}<template v-if="check.detail"> {{ check.detail }}</template></p>
					<button
						v-if="check.action"
						type="button"
						class="btn btn-secondary"
						data-testid="ppl-check-action"
						@click="focusRegion('reservation')"
					>{{ check.action }}</button>
				</div>
				<div v-if="reservationBlock && !reservationBlock.met" ref="reservationEl" tabindex="-1" class="pln-reservation-host">
					<ReservationAllocation :block="reservationBlock" collapsible />
				</div>
				<div class="kt-group" :style="(budgetFit && !budgetFit.all_within) || failingChecks.length ? 'margin-top: var(--kt-space-5)' : ''" data-testid="ppl-plan-checks-group">
					<div class="kt-meta-row pln-plan-checks" data-testid="ppl-plan-checks">
						<div v-if="budgetFit && budgetFit.all_within" data-testid="ppl-budget-fit">
							<span class="kt-label">Budget fit, checked now</span>
							<span class="pln-check-value">{{ budgetFit.result }}</span>
						</div>
						<div data-testid="ppl-finance-confirmation">
							<span class="kt-label">Finance confirmation</span>
							<span class="pln-check-value">{{ financeConfirmation.state }}</span>
						</div>
						<template v-if="financeConfirmation.checked_by">
							<div><span class="kt-label">Checked by</span><span class="pln-check-value">{{ financeConfirmation.checked_by }}</span></div>
							<div><span class="kt-label">Checked at</span><span class="pln-check-value">{{ financeConfirmation.checked_at }}</span></div>
						</template>
						<div v-for="check in passingChecks" :key="check.label">
							<span class="kt-label">{{ check.label }}</span>
							<span class="pln-check-value">{{ check.result }}</span>
						</div>
					</div>
					<details v-if="budgetFit && budgetFit.all_within" class="kt-disclosure" data-testid="ppl-budget-lines" @toggle="linesOpen = $event.target.open">
						<summary class="kt-disclosure-head">
							<div class="kt-disclosure-title-row"><span class="kt-disclosure-title">View budget lines</span></div>
							<svg class="kt-disclosure-chevron" :class="{ 'is-open': linesOpen }" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M6 9l6 6 6-6"></path></svg>
						</summary>
						<div class="kt-disclosure-body">
							<table class="table">
								<thead><tr><th>Budget line</th><th class="is-num">Approved</th><th class="is-num">This plan</th><th class="is-num">Difference</th></tr></thead>
								<tbody>
									<tr v-for="line in budgetFit.lines" :key="line.budget_line">
										<td><div class="pln-fit-line">{{ line.title }}</div><div class="kt-muted pln-row-ref">{{ line.reference }}</div></td>
										<td class="is-num">{{ line.approved_display }}</td>
										<td class="is-num">{{ line.planned_display }}</td>
										<td class="is-num">{{ line.difference_display }}</td>
									</tr>
								</tbody>
							</table>
						</div>
					</details>
				</div>
				<div v-if="reservationBlock && reservationBlock.met" ref="reservationEl" tabindex="-1" class="pln-reservation-host">
					<ReservationAllocation :block="reservationBlock" collapsible />
				</div>
			</div>

			<!-- §10.6 — once the version is Active, its approval and publication
			     are facts about it, not a preparation step, so they appear here
			     rather than as a stage in a wizard. They stay absent while a Draft
			     is still being prepared. -->
			<div v-if="activeView" class="kt-region is-secondary">
				<h2>Approval and publication</h2>
				<div class="kt-meta-row pln-governance-row" data-testid="ppl-governance">
					<div>
						<span class="kt-label">Adopted by the Accounting Officer</span>
						<span class="pln-check-value">{{ activeView.governance_card.ao_adoption_line || "—" }}</span>
					</div>
					<div>
						<span class="kt-label">Approved</span>
						<span class="pln-check-value">{{ activeView.governance_card.statutory_approval_line || "—" }}</span>
					</div>
					<div>
						<span class="kt-label">Published</span>
						<span class="pln-check-value">{{ activeView.governance_card.publication_line || "Not published" }}</span>
						<a
							v-if="activeView.governance_card.publication_route"
							href="#"
							class="pln-check-action"
							data-testid="ppl-view-publication"
							@click.prevent="$emit('navigate', activeView.governance_card.publication_route)"
						>View publication evidence</a>
					</div>
					<div>
						<span class="kt-label">In force since</span>
						<span class="pln-check-value">{{ activeView.summary.activated_display }}</span>
					</div>
				</div>
				<!-- §10.13 — what has actually been procured against it lives in
				     its own surface; this page is about the plan itself. -->
				<a href="#" class="pln-governance-progress" data-testid="ppl-view-progress" @click.prevent="$emit('navigate', ['annual-procurement-plan', plan.plan_reference, 'progress'])">
					View procurement progress
				</a>
			</div>

			<!-- Changes and history: secondary, closed by default. Each
			     acceptance is one timeline entry (§9.4's .kt-timeline,
			     already established in Departmental Needs, Strategy and
			     Tenders) rather than a paragraph per row — a plan built from
			     several departments' acceptances read as a dense wall of
			     text otherwise, for no reason this section needs. -->
			<!-- The board's own disclosure head: the title in its row, and the
			     chevron that says the section opens at all. Both were dropped
			     in the port, leaving a bare small-caps line with no affordance
			     — it read as an orphaned heading over empty space (found live
			     24 Sep 2026). -->
			<details class="kt-disclosure" data-testid="ppl-history" :open="changeRows.length > 0 || null" @toggle="historyOpen = $event.target.open">
				<summary class="kt-disclosure-head">
					<div class="kt-disclosure-title-row">
						<span class="kt-disclosure-title">Changes and history</span>
					</div>
					<svg class="kt-disclosure-chevron" :class="{ 'is-open': historyOpen }" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
						<path d="M6 9l6 6 6-6"></path>
					</svg>
				</summary>
				<div class="kt-disclosure-body">
					<p v-if="changesText" class="kt-muted">{{ changesText }}</p>
					<!-- §10.6 update family — what this update adds, changes or
					     removes against the plan in force; the section starts open
					     when there is any. -->
					<table v-if="changeRows.length" class="table" data-testid="ppl-changes">
						<thead><tr><th>Purchase</th><th>Field</th><th>Current value</th><th>Proposed value</th></tr></thead>
						<tbody>
							<tr v-for="row in changeRows" :key="row.plan_item_id + row.field">
								<td><div class="pln-fit-line">{{ row.title }}</div><div class="kt-muted pln-row-ref">{{ row.plan_item_id }}</div></td>
								<td>{{ row.field }}</td>
								<td>{{ row.current }}</td>
								<td>{{ row.proposed }}</td>
							</tr>
						</tbody>
					</table>
					<div v-if="history.length" class="kt-timeline" data-testid="ppl-history-timeline">
						<div v-for="(row, index) in history" :key="index" class="kt-timeline-row">
							<div class="kt-timeline-dot-col">
								<div class="kt-timeline-dot is-live"></div>
								<div v-if="index < history.length - 1" class="kt-timeline-line"></div>
							</div>
							<div class="kt-timeline-item">
								<div class="kt-timeline-item-title">{{ row.title }}</div>
								<div class="kt-timeline-item-meta">{{ row.meta }}</div>
							</div>
						</div>
					</div>
				</div>
			</details>

			<!-- Everything still standing between this plan and submission, for
			     the one actor who holds that action. Without it they met these
			     one at a time: the server computed the whole list and raised
			     only the first, so each correction earned the next refusal
			     (found live 23 Sep 2026). -->
			<div v-if="submissionIssues.length" data-testid="ppl-submission-issues">
				<p class="kt-label">{{ submissionIssuesHeading }}</p>
				<div v-for="issue in submissionIssues" :key="issue" class="kt-notice is-critical" data-testid="ppl-submission-issue">
					<svg class="kt-notice-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
						<path d="M12 3l9 16H3z"></path><path d="M12 10v4M12 17h.01"></path>
					</svg>
					<div class="kt-notice-body">{{ issue }}</div>
				</div>
			</div>

			<p v-if="errorSummary" class="pln-error-summary" data-testid="ppl-error">{{ errorSummary }}</p>

			<!-- §10.16 C03-METHOD-MISSING / C04-SCHEDULE-MISSING — each missing
			     rule with the purchase it is missing for, immediately above the
			     actions it blocks. A plan can carry one of these per purchase per
			     unresolved rule kind, so MissingSettingGroup collapses more than
			     one to a summary rather than stacking every purchase's own panel
			     full-size (found live 23 Sep 2026, on the item editor's own pair;
			     the same scaling problem applies here at least as much). -->
			<MissingSettingGroup :panels="missingSettings" />

			<!-- The v1.25 Approval waiting notice and Responsible person field are
			     replaced by the next-step line in the header (§10.6 v1.26 table,
			     U07-FINANCE-COMPLETE). -->
			<div class="pln-footer" data-testid="ppl-footer">
				<button
					v-if="plan.can_cancel_update"
					type="button"
					class="btn btn-secondary"
					data-testid="ppl-cancel-update"
					:disabled="pending"
					@click="$emit('cancel-update')"
				>
					Cancel plan update
				</button>
				<span v-else></span>
				<div class="pln-footer-right">
					<button
						v-if="plan.mutable"
						type="button"
						class="btn btn-secondary"
						data-testid="ppl-save"
						:disabled="pending"
						@click="onSave"
					>
						Save draft
					</button>
					<!-- Absent, not disabled, while a blocking check fails (§10.6). -->
					<button
						v-if="plan.can_request_funding"
						type="button"
						class="btn btn-primary"
						data-testid="ppl-request-funding"
						:disabled="pending"
						@click="$emit('request-funding')"
					>
						Send to Finance for funding review
					</button>
					<!-- The HOPF's own action, never the Planner's (§6.2). -->
					<button
						v-if="plan.can_sign_and_submit"
						type="button"
						class="btn btn-primary"
						data-testid="ppl-sign-submit"
						:disabled="pending"
						@click="$emit('submit-consolidated')"
					>
						Sign and submit Annual Plan
					</button>
				</div>
			</div>

		</div>
	</div>
</template>

<script setup>
import { computed, nextTick, ref, watch } from "vue";
import { settingsStated, useGuidance } from "../../pln_shared/composables/useGuidance.js";
import MissingSettingGroup from "./MissingSettingGroup.vue";
import ReservationAllocation from "./ReservationAllocation.vue";
import TablePagerHost from "../../pager_shared/TablePagerHost.vue";
import { usePagedRows } from "../../pager_shared/usePagedRows.js";

const props = defineProps({
	plan: { type: Object, default: () => ({}) },
	selected: { type: Array, default: () => [] },
	pending: Boolean,
	errorSummary: String,
});

const emit = defineEmits([
	"open-form-dialog",
	"navigate",
	"toggle-source",
	"view-requirement",
	"request-funding",
	"submit-consolidated",
	"cancel-update",
	"open-task",
	"save-details",
	"guidance-command",
]);

const headEl = ref(null);
const journeyEl = ref(null);
const bodyEl = ref(null);
const purchasesEl = ref(null);
const requirementsEl = ref(null);
const checksEl = ref(null);
const reservationEl = ref(null);
const linesOpen = ref(false);

// §11.9 v1.27 — each fix maps to this page's own handler: a hand-off command
// goes to the root's command runner (Request budget revision / Request
// departmental plan update); Review reserved procurement moves focus on this
// page; Choose a procurement method opens the purchase. The wording and the
// choice of fixes are the server's.
const FOCUS = { purchases: purchasesEl, reservation: reservationEl, requirements: requirementsEl };
function focusRegion(target) {
	const el = (FOCUS[target] || checksEl).value || checksEl.value;
	if (!el) return;
	// The reservation block is already on screen when its fix is pressed, so
	// moving to it shows nothing; the answer is the working under it (which
	// purchases count, and why), which is closed until asked for.
	if (target === "reservation") el.querySelector("details")?.setAttribute("open", "");
	nextTick(() => {
		el.scrollIntoView({ behavior: "smooth", block: "start" });
		el.focus({ preventScroll: true });
	});
}
function onGuidance(item) {
	if (!item) return;
	if (item.kind === "command") emit("guidance-command", item);
	else if (item.kind === "focus") focusRegion(item.target);
	else if (item.kind === "route" && item.target) emit("navigate", item.target);
}
useGuidance(
	{ journeyEl, headEl, bodyEl },
	{ answer: () => props.plan.next_step, journey: () => props.plan.journey, pending: () => props.pending },
	{ onFix: onGuidance, onLink: onGuidance },
);

const projectNameDraft = ref(props.plan.project_name || "");
const changeReasonDraft = ref(props.plan.change_reason || "");
const showProjectName = ref(Boolean(props.plan.project_name));

// A quiet in-place refresh (record_version unchanged) carries nothing new —
// re-hydrating would discard what the Planner has typed since.
watch(
	() => props.plan,
	(plan, previous) => {
		if (previous && (previous.record_version ?? null) === (plan?.record_version ?? null)) return;
		projectNameDraft.value = plan?.project_name || "";
		changeReasonDraft.value = plan?.change_reason || "";
		showProjectName.value = Boolean(plan?.project_name);
	},
);

const items = computed(() => props.plan.plan_items || []);
const incompleteItems = computed(() => items.value.filter((row) => row.current_work && row.current_work !== "Ready"));
const activeView = computed(() => props.plan.active_view);
// §10.16 — a setting the next-step block already states is not drawn again
// as its own panel beside it.
const missingSettings = computed(() => {
	const stated = settingsStated(props.plan.next_step);
	return (props.plan.missing_settings || []).filter((panel) => !stated.has(panel.setting));
});
const unallocated = computed(() => props.plan.unallocated_sources || []);
// The table-pagination standard (AGENTS.md §6.11): a plan's purchases and ready requirements are paged per plan, and the
// selection (`selected`, held by the root) is by entry id, so it survives a change of page.
const {
	pagedRows: pagedItems, total: itemsTotal, page: itemsPage, pageSize: itemsPageSize, setPage: setItemsPage, setPageSize: setItemsPageSize,
} = usePagedRows(items, () => `planning-purchases:${props.plan.plan_reference}`);
const {
	pagedRows: pagedUnallocated, total: unallocatedTotal, page: unallocatedPage, pageSize: unallocatedPageSize,
	setPage: setUnallocatedPage, setPageSize: setUnallocatedPageSize,
} = usePagedRows(unallocated, () => `planning-requirements:${props.plan.plan_reference}`);
const planChecks = computed(() => props.plan.plan_checks || []);
const failingChecks = computed(() => planChecks.value.filter((check) => check.kind === "critical"));
const budgetFit = computed(() => props.plan.budget_fit || null);
const financeConfirmation = computed(() => ({ state: "Not requested", checked_by: "", checked_at: "", ...(props.plan.finance_confirmation || {}) }));
const reservationBlock = computed(() => (props.plan.summary || {}).reservation_allocation || null);
const passingChecks = computed(() =>
	planChecks.value.filter((check) => check.kind !== "critical" && !(reservationBlock.value && check.label === "Reserved procurement")),
);
const changeRows = computed(() => props.plan.changes?.rows || []);
const historyOpen = ref(changeRows.value.length > 0);
const submissionIssues = computed(() => props.plan.submission_issues || []);
const submissionIssuesHeading = computed(() => {
	const n = submissionIssues.value.length;
	return `${n} ${n === 1 ? "issue" : "issues"} must be resolved before this plan can be submitted`;
});
const history = computed(() => props.plan.history || []);
const currentVersion = computed(() => props.plan.current_version_number);

const title = computed(() => (props.plan.is_successor ? "Prepare plan update" : "Prepare the annual procurement plan"));
const statusLabel = computed(() => (props.plan.is_successor ? "Draft update" : props.plan.header?.badge));


const changesText = computed(() =>
	props.plan.changes?.is_initial ? "This is the first version of the annual plan." : "",
);

const allAllocatedText = computed(() => {
	const count = items.value.reduce((total, row) => total + (row.sources || 0), 0);
	if (!count) return "No departmental requirements are available to add yet.";
	const noun = count === 1 ? "requirement is" : "requirements are";
	const purchases = items.value.length === 1 ? "purchase" : "purchases";
	return `All ${count} departmental ${noun} included in the ${items.value.length} ${purchases} above.`;
});

const badgeClass = computed(() => {
	const badge = props.plan.header?.badge;
	if (badge === "Draft") return "is-draft";
	if (badge === "Returned") return "is-critical";
	if (badge === "Active") return "is-live";
	return "is-attention";
});

function onSave() {
	emit("save-details", { project_name: projectNameDraft.value, change_reason: changeReasonDraft.value });
}
</script>
