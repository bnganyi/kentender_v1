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
				</div>
			</div>

			<!-- U07-UPDATE — a successor must say why it exists. -->
			<div v-if="plan.is_successor" class="kt-field pln-plan-field" data-testid="ppl-change-reason">
				<label for="ppl-change-reason" class="kt-label">Reason for updating the plan</label>
				<textarea
					id="ppl-change-reason"
					class="kt-input"
					rows="2"
					:value="changeReasonDraft"
					:disabled="!plan.mutable"
					@input="changeReasonDraft = $event.target.value"
				></textarea>
			</div>

			<!-- §10.6 — Project name is omitted when blank. A whole-plan field with
			     nothing in it is not worth a control on every visit. -->
			<div v-if="plan.project_name || showProjectName" class="kt-field pln-plan-field" data-testid="ppl-project-name">
				<label for="ppl-project" class="kt-label">Project name (if applicable)</label>
				<input
					id="ppl-project"
					class="kt-input"
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
				class="kt-btn kt-btn-ghost pln-plan-field"
				data-testid="ppl-add-project-name"
				@click="showProjectName = true"
			>
				Add a project name
			</button>

			<div class="kt-region">
				<h2>Purchases</h2>
				<template v-if="items.length">
					<table class="kt-table" data-testid="ppl-purchases">
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
							<tr v-for="row in items" :key="row.plan_item_id" data-testid="ppl-purchase-row">
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
									<a href="#" class="kt-btn kt-btn-ghost" data-testid="ppl-purchase-action" @click.prevent="$emit('navigate', row.route)">{{ plan.mutable ? "Edit purchase" : "View purchase" }}</a>
								</td>
							</tr>
						</tbody>
					</table>
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
			<div class="kt-region" :class="{ 'is-secondary': !unallocated.length }" data-testid="ppl-requirements">
				<h2>Requirements ready to add</h2>
				<template v-if="unallocated.length">
					<table class="kt-table" data-testid="ppl-unallocated">
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
							<tr v-for="row in unallocated" :key="row.entry_id" data-testid="ppl-unallocated-row">
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
									<a href="#" class="kt-btn kt-btn-ghost" data-testid="ppl-view-requirement" @click.prevent="$emit('view-requirement', row)">View requirement</a>
								</td>
							</tr>
						</tbody>
					</table>
					<!-- A reader who cannot form purchases is not offered the control
					     at all: this cycle shows no control a reader cannot use. -->
					<div v-if="plan.mutable" class="pln-add-selected">
						<p v-if="!selected.length" class="kt-muted" data-testid="ppl-select-hint">Select at least one requirement.</p>
						<button
							type="button"
							class="kt-btn kt-btn-primary"
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

			<!-- Plan checks: three results, each naming its own correction.
			     The board binds them in a `.kt-group` — a left rule with the
			     facts indented under the heading — and bounds the row's width.
			     Both were dropped in the port, so the facts floated flat across
			     the full page and, once a second row joined them, read as one
			     unstructured band (found live 24 Sep 2026). -->
			<div class="kt-region">
				<h2>Plan checks</h2>
				<!-- A failing check is the board's dominant issue: its own
				     warning notice, naming the check and carrying the exact
				     correction as a button. The passing ones stay quiet facts
				     in the group below. All three were built as one flat row
				     of facts with the failing one as a badge, which is why a
				     KES 139,494 shortfall read no louder than "Schedule — all
				     purchases meet their deadlines" (found live 24 Sep 2026). -->
				<div
					v-for="check in failingChecks"
					:key="check.label"
					class="kt-notice is-warning"
					data-testid="ppl-check-issue"
				>
					<svg class="kt-notice-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
						<path d="M12 3l9 16H3z"></path><path d="M12 10v4M12 17h.01"></path>
					</svg>
					<div class="pln-check-issue-body">
						<div class="kt-notice-body"><strong>{{ check.label }}</strong> — {{ check.result }}</div>
						<button
							v-if="check.action"
							type="button"
							class="kt-btn kt-btn-secondary"
							data-testid="ppl-check-action"
							@click="$emit('navigate', check.route)"
						>{{ check.action }}</button>
					</div>
				</div>
				<div class="kt-group" data-testid="ppl-plan-checks-group">
				<div class="kt-meta-row pln-plan-checks" data-testid="ppl-plan-checks">
					<div v-for="check in passingChecks" :key="check.label">
						<span class="kt-label">{{ check.label }}</span>
						<span class="kt-meta-value">{{ check.result }}</span>
					</div>
				</div>
				<!-- The working behind the reserved-procurement result. One
				     obligation, stated once at plan level: what the target is a
				     share of, what it comes to, what is designated so far and
				     what is left. It used to exist only inside the refusal at
				     Sign and submit, as raw unformatted numbers with nothing
				     naming their denominator (found live 23 Sep 2026). Absent
				     entirely where no target is published. -->
				<div v-if="reservationSummary.length" class="kt-meta-row pln-plan-checks pln-plan-checks-working" data-testid="ppl-reservation-summary">
					<div v-for="fact in reservationSummary" :key="fact.label">
						<span class="kt-label">{{ fact.label }}</span>
						<span class="kt-meta-value">{{ fact.value }}</span>
					</div>
				</div>
				</div>
			</div>

			<!-- §10.6 — once the version is Active, its approval and publication
			     are facts about it, not a preparation step, so they appear here
			     rather than as a stage in a wizard. They stay absent while a Draft
			     is still being prepared. -->
			<div v-if="activeView" class="kt-region is-secondary">
				<h2>Approval and publication</h2>
				<div class="kt-meta-row" data-testid="ppl-governance">
					<div>
						<span class="kt-label">Adopted by the Accounting Officer</span>
						<span class="kt-meta-value">{{ activeView.governance_card.ao_adoption_line || "—" }}</span>
					</div>
					<div>
						<span class="kt-label">Approved</span>
						<span class="kt-meta-value">{{ activeView.governance_card.statutory_approval_line || "—" }}</span>
					</div>
					<div>
						<span class="kt-label">Published</span>
						<span class="kt-meta-value">
							{{ activeView.governance_card.publication_line || "Not published" }}
							<a
								v-if="activeView.governance_card.publication_route"
								href="#"
								class="pln-check-action"
								data-testid="ppl-view-publication"
								@click.prevent="$emit('navigate', activeView.governance_card.publication_route)"
							>View publication evidence</a>
						</span>
					</div>
					<div>
						<span class="kt-label">In force since</span>
						<span class="kt-meta-value">{{ activeView.summary.activated_display }}</span>
					</div>
				</div>
				<!-- §10.13 — what has actually been procured against it lives in
				     its own surface; this page is about the plan itself. -->
				<a href="#" data-testid="ppl-view-progress" @click.prevent="$emit('navigate', ['annual-procurement-plan', plan.plan_reference, 'progress'])">
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
			<details class="kt-disclosure" data-testid="ppl-history" @toggle="historyOpen = $event.target.open">
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

			<!-- U07-FINANCE-COMPLETE — who is waited on, named, comes before
			     the final action, not after it (found live 23 Sep 2026: this
			     sat below the footer, so Save draft read as the page's last
			     word even once nothing further was the Planner's to do). -->
			<!-- §10.6 U07-FINANCE-COMPLETE — its own section, as the board
			     draws it: a secondary region, its heading, and the state in a
			     notice. A previous port made it a bare `.kt-meta-row` of
			     labelled facts citing this same variant, which the board does
			     not draw; with no heading and no notice it read as two more
			     loose labels at the bottom of a flat page (found live 24 Sep
			     2026). The people stay a labelled fact rather than being
			     joined into the sentence — the board names one person and
			     several is ordinary here. -->
			<div v-if="waitingOn.notice" class="kt-region is-secondary" data-testid="ppl-waiting-on">
				<h2>Approval</h2>
				<div class="kt-notice">
					<svg class="kt-notice-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
						<path d="M12 22a10 10 0 1 0 0-20 10 10 0 0 0 0 20z"></path><path d="M12 16v-4"></path><path d="M12 8h.01"></path>
					</svg>
					<div class="kt-notice-body">
						<div>{{ waitingOn.notice }}</div>
						<div v-if="waitingOn.people.length" class="pln-responsible">
							<span class="kt-label">{{ waitingOn.people.length === 1 ? "Responsible person" : "Responsible people" }}</span>
							<span class="kt-meta-value" data-testid="ppl-waiting-on-person">
								<span v-for="(name, index) in waitingOn.people" :key="name" class="pln-responsible-name">
									{{ index ? ", " : "" }}{{ name }}
								</span>
							</span>
						</div>
						<div v-else-if="waitingOn.unassigned" class="pln-responsible">
							<span class="kt-label">Responsible person</span>
							<span class="kt-meta-value" data-testid="ppl-waiting-on-unassigned">{{ waitingOn.unassigned }}</span>
						</div>
					</div>
				</div>
			</div>

			<div class="pln-footer" data-testid="ppl-footer">
				<button
					v-if="plan.can_cancel_update"
					type="button"
					class="kt-btn kt-btn-secondary"
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
						class="kt-btn kt-btn-secondary"
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
						class="kt-btn kt-btn-primary"
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
						class="kt-btn kt-btn-primary"
						data-testid="ppl-sign-submit"
						:disabled="pending"
						@click="$emit('submit-consolidated')"
					>
						Sign and submit Annual Plan
					</button>
				</div>
			</div>

			<div v-if="plan.open_task" class="pln-dpp-task">
				<button type="button" class="kt-btn kt-btn-primary" data-testid="ppl-open-task" @click="$emit('open-task', plan.open_task.route)">
					{{ plan.open_task.label }}
				</button>
			</div>
		</div>
	</div>
</template>

<script setup>
import { computed, ref, watch } from "vue";
import MissingSettingGroup from "./MissingSettingGroup.vue";

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
]);

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
const missingSettings = computed(() => props.plan.missing_settings || []);
const unallocated = computed(() => props.plan.unallocated_sources || []);
const planChecks = computed(() => props.plan.plan_checks || []);
const failingChecks = computed(() => planChecks.value.filter((check) => check.kind === "critical"));
const passingChecks = computed(() => planChecks.value.filter((check) => check.kind !== "critical"));
const historyOpen = ref(false);
const reservationSummary = computed(() => (props.plan.summary || {}).reservation_summary || []);
const submissionIssues = computed(() => props.plan.submission_issues || []);
const submissionIssuesHeading = computed(() => {
	const n = submissionIssues.value.length;
	return `${n} ${n === 1 ? "issue" : "issues"} must be resolved before this plan can be submitted`;
});
const history = computed(() => props.plan.history || []);
const currentVersion = computed(() => props.plan.current_version_number);

const title = computed(() => (props.plan.is_successor ? "Prepare plan update" : "Prepare the annual procurement plan"));
const statusLabel = computed(() => (props.plan.is_successor ? "Draft update" : props.plan.header?.badge));

const waitingOn = computed(() => ({
	notice: "",
	people: [],
	unassigned: "",
	...(props.plan.waiting_on || {}),
}));

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
