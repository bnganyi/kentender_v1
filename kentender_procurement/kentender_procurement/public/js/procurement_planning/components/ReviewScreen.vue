<!-- PLN-CHG-001 v1.24 §10.10 — the complete annual-plan review (U11), ported
     from Artboards-U11.dc.html (re-diffed 23 Sep 2026 against the real
     §10.10/U11-* sections).

     Every governance actor reads the same document. Only the header, the prior
     accountability shown, the decision statement and the actual buttons
     change: HOPF signs, the AO adopts, the statutory authority approves, a
     collective body records its own decision, and a reader decides nothing.

     The order matters. Decision summary, visible material issues, concise
     purchase rows, then the actor's statement and their decision — before any
     collapsed evidence. The actor must not scroll through audit evidence to
     reach the decision, and no purchase opens by itself. But nothing material
     is hidden either: an issue that would change the verdict is always in the
     summary, never behind a disclosure.

     The scope line is one line in the page head (kt-page-scope), not a
     four-cell facts row below it — every literal U11-* board agrees, and none
     of them repeat the plan's own title there. And the statement is read
     twice: once as a notice right under the header, before any evidence, and
     again beside the buttons — an actor should not have to reach the bottom
     of the page to learn what they are about to do.

     U11-READER/-READER-HISTORICAL — a reader who holds no decision here (no
     `can_decide`) reads a differently-titled document: header "Annual
     procurement plan", description "Review the plan and its recorded
     evidence." A historical Version additionally says so with its own
     notice. `get_plan_governance_task`'s `historical` field backs it; the
     artboard's own "View current plan" header action is not built here —
     wiring its navigation touches ProcurementPlanning.vue, outside this
     component's own file. -->

<template>
	<div>
		<div class="kt-page">
			<div class="kt-page-head">
				<div>
					<h1 class="kt-page-title" data-testid="rev-title">{{ actor.title }}</h1>
					<p class="kt-page-desc">{{ actor.description }}</p>
					<div class="kt-page-scope" data-testid="rev-context">
						<span>{{ task.plan_reference }}</span>
						<span>· Version {{ task.version_number }}</span>
						<span v-if="task.financial_year_label">· {{ task.financial_year_label }}</span>
						<span v-if="scopePhrase">· {{ scopePhrase }}</span>
					</div>
				</div>
				<div v-if="task.can_download_review_pack" class="kt-page-actions">
					<button
						type="button"
						class="kt-btn kt-btn-secondary"
						data-testid="rev-download"
						@click="$emit('download-pack')"
					>
						Download review pack
					</button>
				</div>
			</div>

			<!-- U11-HOPF/-AO/-STATUTORY — the actor reads what they are about to
			     do up front, before any evidence, not only again by the buttons. -->
			<div v-if="canDecideNow" class="kt-notice" data-testid="rev-statement-notice">
				<svg class="kt-notice-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
					<path d="M12 22a10 10 0 1 0 0-20 10 10 0 0 0 0 20z"></path><path d="M12 16v-4"></path><path d="M12 8h.01"></path>
				</svg>
				<div class="kt-notice-body">{{ actor.statement }}</div>
			</div>

			<!-- U11-READER-HISTORICAL — a Version that is no longer the Plan's
			     active one, read plainly rather than left to be inferred from
			     the absent decision area. -->
			<div v-if="task.historical" class="kt-notice is-info" data-testid="rev-historical">
				<svg class="kt-notice-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
					<circle cx="12" cy="12" r="10"></circle><path d="M12 6v6l4 2"></path>
				</svg>
				<div class="kt-notice-body">Historical plan — read only</div>
			</div>

			<!-- First section — Decision summary. -->
			<div class="kt-region">
				<h2>Decision summary</h2>
				<!-- The board states the plan's totals and its checks as one row
				     of six facts. Split into two rows, the checks read as a
				     second section rather than as part of the same summary
				     (found live 24 Sep 2026). -->
				<div class="kt-meta-row" data-testid="rev-summary" style="margin-bottom: var(--kt-space-4)">
					<div>
						<span class="kt-label">Estimated cost</span>
						<span class="kt-meta-value">{{ summary.value_display }}</span>
					</div>
					<div>
						<span class="kt-label">Purchases</span>
						<span class="kt-meta-value">{{ summary.purchases }}</span>
					</div>
					<div>
						<span class="kt-label">Departments</span>
						<span class="kt-meta-value">{{ summary.departments }}</span>
					</div>
					<div data-testid="rev-checks">
						<span class="kt-label">Funding</span>
						<span class="kt-meta-value" style="font-size: 14px">{{ summary.funding }}</span>
					</div>
					<div>
						<span class="kt-label">Reserved procurement</span>
						<span class="kt-meta-value" style="font-size: 14px">{{ summary.reservation }}</span>
					</div>
					<div>
						<span class="kt-label">Schedule</span>
						<span class="kt-meta-value" style="font-size: 14px">{{ summary.schedule }}</span>
					</div>
				</div>

				<!-- Either no blocking issues, or the exact issues. Never neither. -->
				<div v-if="!issues.length" class="kt-notice is-info" data-testid="rev-no-issues">
					<svg class="kt-notice-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
						<circle cx="12" cy="12" r="9"></circle><path d="m8 12 3 3 5-6"></path>
					</svg>
					<div class="kt-notice-body">No blocking issues</div>
				</div>
				<div v-for="issue in issues" :key="issue" class="kt-notice is-critical" data-testid="rev-issue">
					<svg class="kt-notice-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
						<path d="M12 3l9 16H3z"></path><path d="M12 10v4M12 17h.01"></path>
					</svg>
					<div class="kt-notice-body">{{ issue }}</div>
				</div>

				<table class="kt-table" data-testid="rev-purchases">
					<thead>
						<tr>
							<th>Purchase</th><th>Purpose</th><th class="is-num">Quantity</th>
							<th>Unit</th><th>Required by</th><th class="is-num">Estimated cost</th><th>Action</th>
						</tr>
					</thead>
					<tbody>
						<template v-for="row in items" :key="row.plan_item_id">
							<tr data-testid="rev-purchase-row">
								<td>{{ row.title }}</td>
								<td>{{ row.purpose }}</td>
								<td class="is-num">{{ row.quantity_number }}</td>
								<td>{{ row.unit_label }}</td>
								<td>{{ row.delivery_completion_display }}</td>
								<td class="is-num">{{ row.value_display }}</td>
								<td>
									<a href="#" class="kt-btn kt-btn-ghost" data-testid="rev-review-purchase" @click.prevent="toggle(row.plan_item_id)">Review purchase</a>
								</td>
							</tr>
							<!-- One level of detail, opened deliberately. -->
							<tr v-if="open.includes(row.plan_item_id)" class="pln-row-detail" data-testid="rev-purchase-detail">
								<td colspan="7">
									<p v-if="row.purpose" class="kt-muted">{{ row.purpose }}</p>
									<div class="kt-meta-row">
										<div>
											<span class="kt-label">Department</span>
											<span class="kt-meta-value">{{ row.department }}</span>
										</div>
										<div>
											<span class="kt-label">Quantity</span>
											<span class="kt-meta-value">{{ row.quantity_display || row.quantity_number }}</span>
										</div>
										<div>
											<span class="kt-label">Required by</span>
											<span class="kt-meta-value">{{ row.delivery_completion_display }}</span>
										</div>
										<div>
											<span class="kt-label">Estimated cost</span>
											<span class="kt-meta-value">{{ row.value_display }}</span>
										</div>
										<div>
											<span class="kt-label">Procurement approach</span>
											<span class="kt-meta-value">{{ row.procurement_method }}</span>
										</div>
										<div>
											<span class="kt-label">Expected completion</span>
											<span class="kt-meta-value">{{ row.delivery_completion_display }}</span>
										</div>
										<div>
											<span class="kt-label">Departmental deadline</span>
											<span class="kt-meta-value">{{ row.delivery_completion_display }}</span>
										</div>
									</div>
									<!-- §10.11 — the evidence link belongs to a source, not
									     to the purchase: a combined purchase was reviewed on
									     several, and each one has its own departmental
									     certification and acceptance behind it. -->
									<div class="pln-evidence-links">
										<a
											v-for="source in row.sources || []"
											:key="source.source_key"
											href="#"
											class="kt-btn kt-btn-ghost"
											data-testid="rev-view-evidence"
											@click.prevent="$emit('view-evidence', source)"
										>{{ (row.sources || []).length > 1 ? source.title : "View departmental evidence" }}</a>
									</div>
								</td>
							</tr>
						</template>
					</tbody>
				</table>
				<p class="kt-muted" data-testid="rev-caption">{{ task.caption }}</p>
				<!-- U11 boards: Review Plan checks closes the purchases region. -->
				<details class="kt-disclosure" style="margin-top: var(--kt-space-4)" data-testid="rev-plan-checks">
					<summary class="kt-disclosure-head">
		<div class="kt-disclosure-title-row"><span class="kt-disclosure-title">Review Plan checks</span></div>
		<svg class="kt-disclosure-chevron" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M6 9l6 6 6-6"></path></svg>
	</summary>
					<div class="kt-disclosure-body">
						<!-- The same plan-level block U07 shows, read from the calculation
						     frozen at submission (U11 boards; U21-TECHNICAL-DETAIL). Its
						     details sit inline: this disclosure already hides them. -->
						<ReservationAllocation v-if="reservation" :block="reservation" />
						<div class="kt-meta-row" style="margin-top: var(--kt-space-5)" data-testid="rev-plan-checks-schedule">
							<div><span class="kt-label">Schedule</span><span style="font-size: 14px">{{ summary.schedule }}</span></div>
						</div>
					</div>
				</details>
			</div>

			<!-- Second section — Accountability. -->
			<div class="kt-region is-secondary" data-testid="rev-accountability">
				<h2>Accountability</h2>
				<div class="kt-group">
					<div class="kt-meta-row">
						<div>
							<span class="kt-label">Funding</span>
							<span class="kt-meta-value" style="font-size: 14px">{{ fundingAt.actor_name ? "Within each approved budget line" : "Not yet checked" }}</span>
						</div>
						<template v-if="fundingAt.actor_name">
							<div><span class="kt-label">Checked by</span><span class="kt-meta-value" style="font-size: 14px">{{ fundingAt.actor_name }}</span></div>
							<div><span class="kt-label">Checked at</span><span class="kt-meta-value" style="font-size: 14px">{{ fundingAt.decided_at_display }}</span></div>
						</template>
					</div>
				</div>
				<!-- Absent before the signature exists (U11-HOPF). -->
				<div v-if="signature" class="kt-group" data-testid="rev-preparation">
					<div class="kt-meta-row">
						<div><span class="kt-label">Preparation</span><span class="kt-meta-value" style="font-size: 14px">Signed</span></div>
						<div><span class="kt-label">Signed by</span><span class="kt-meta-value" style="font-size: 14px">{{ signature.actor_name }}</span></div>
						<div><span class="kt-label">Capacity</span><span class="kt-meta-value" style="font-size: 14px">{{ signature.capacity }}</span></div>
						<div><span class="kt-label">Signed at</span><span class="kt-meta-value" style="font-size: 14px">{{ signature.signed_at_display }}</span></div>
					</div>
				</div>
				<p class="kt-muted" style="margin-top: var(--kt-space-4)">Funding confirmation does not set money aside.</p>
			</div>

			<!-- Funding evidence — visible, secondary, matching the artboard's own
			     always-open treatment: the other evidence sections stay closed.
			     Between Accountability and the decision, matching the artboard. -->
			<div class="kt-region is-secondary" data-testid="rev-funding-evidence">
				<h2>Funding evidence</h2>
				<table class="kt-table">
					<thead>
						<tr><th>Budget line</th><th class="is-num">Approved</th><th class="is-num">Planned</th><th class="is-num">Difference</th><th>Result</th></tr>
					</thead>
					<tbody>
						<tr v-for="row in funding.rows || []" :key="row.budget_line">
							<td>{{ row.budget_line_reference }}</td>
							<td class="is-num">{{ row.approved_display }}</td>
							<td class="is-num">{{ row.planned_display }}</td>
							<td class="is-num">{{ row.difference_display }}</td>
							<td><span class="kt-status" :class="`is-${row.result_kind}`">{{ row.result }}</span></td>
						</tr>
					</tbody>
				</table>
				<!-- §10.10 fourth section — "View current balances opens funding
				     source, availability and the as-at instant. Do not repeat the
				     full Finance workspace." -->
				<div style="margin-top: var(--kt-space-3)">
					<a
						href="#"
						class="kt-btn kt-btn-ghost"
						data-testid="rev-view-balances"
						@click.prevent="showBalances = !showBalances"
					>View current balances</a>
				</div>
				<div v-if="showBalances" class="pln-row-detail" data-testid="rev-balances">
					<table class="kt-table">
						<thead>
							<tr>
								<th>Budget line</th><th>Funding source</th>
								<th class="is-num">Reserved</th><th class="is-num">Committed</th><th class="is-num">Currently available</th>
							</tr>
						</thead>
						<tbody>
							<tr v-for="row in funding.rows || []" :key="`balance-${row.budget_line}`">
								<td>{{ row.budget_line_reference }}</td>
								<td>{{ row.funding_source }}</td>
								<td class="is-num">{{ row.reserved_display }}</td>
								<td class="is-num">{{ row.committed_display }}</td>
								<td class="is-num">{{ row.available_display }}</td>
							</tr>
						</tbody>
					</table>
					<p class="kt-muted">Balances as at {{ funding.statement_as_at || "—" }}.</p>
				</div>
			</div>

			<!-- The decision comes before the collapsed evidence, not after it. -->
			<template v-if="canDecideNow">
				<!-- U11-COLLECTIVE — the body decides; the recorder records.
				     Facts about who decides, not the input the recorder still
				     owes — that sits in the decision block below, by the
				     statement it belongs next to. -->
				<div v-if="authority.is_board" class="kt-meta-row" data-testid="rev-collective">
					<div>
						<span class="kt-label">Decision belongs to</span>
						<span class="kt-meta-value">{{ authority.capacity_detail }}</span>
					</div>
					<div>
						<span class="kt-label">Recorded by</span>
						<span class="kt-meta-value">{{ task.recorder_name || "—" }}</span>
					</div>
				</div>

				<!-- U11-LATE-ADOPTION — the fact the actor must account for. -->
				<div v-if="task.late_activation_required" class="kt-meta-row" data-testid="rev-late">
					<div>
						<span class="kt-label">Financial year started</span>
						<span class="kt-meta-value">{{ task.financial_year_started_display }}</span>
					</div>
				</div>

				<div class="kt-decision" data-testid="rev-decision">
					<!-- U11-COLLECTIVE — required before the body's decision can be
					     recorded; an editable field, kept out of the facts above. -->
					<div v-if="authority.is_board" class="kt-field" data-testid="rev-resolution-field">
						<label for="rev-resolution" class="kt-label">Resolution reference</label>
						<input
							id="rev-resolution"
							class="kt-input"
							data-testid="rev-resolution"
							:value="resolution"
							@input="$emit('update:resolution', $event.target.value)"
						>
					</div>

					<!-- U11-LATE-ADOPTION — the AO must say why, before deciding,
					     immediately above the decision statement. -->
					<div v-if="task.late_activation_required" class="kt-field" data-testid="rev-late-reason-field">
						<label for="rev-late-reason" class="kt-label">Why is this initial plan being submitted after the financial year started?</label>
						<textarea
							id="rev-late-reason"
							class="kt-input"
							rows="2"
							data-testid="rev-late-reason"
							:value="lateReason"
							@input="$emit('update:lateReason', $event.target.value)"
						></textarea>
					</div>

					<p class="pln-decision-statement" data-testid="rev-statement">{{ actor.statement }}</p>

					<p v-if="errorSummary" class="pln-error-summary" data-testid="rev-error">{{ errorSummary }}</p>

					<!-- §10.16 C01-ROUTE-MISSING — adoption creates the statutory
					     approval task, so an unassigned approver blocks it. Stated with
					     the decision, immediately above it. -->
					<MissingSettingPanel v-if="task.missing_setting" :panel="task.missing_setting" />

					<div class="pln-footer-actions" data-testid="rev-footer">
						<button
							v-if="actor.secondary"
							type="button"
							class="kt-btn kt-btn-secondary"
							data-testid="rev-secondary"
							:disabled="pending"
							@click="actor.secondary_is_return ? $emit('open-return-dialog') : $emit('back')"
						>
							{{ actor.secondary }}
						</button>
						<!-- Absent, not disabled, when a material issue blocks it:
						     the server gates it too (§10.10). -->
						<button
							v-if="task.can_decide_positive && !issues.length"
							type="button"
							class="kt-btn kt-btn-primary"
							data-testid="rev-confirm"
							:disabled="pending"
							@click="$emit('confirm')"
						>
							{{ actor.confirm }}
						</button>
					</div>
				</div>
			</template>

			<details class="kt-disclosure" data-testid="rev-history">
				<summary class="kt-disclosure-head">
	<div class="kt-disclosure-title-row"><span class="kt-disclosure-title">Changes and history</span></div>
	<svg class="kt-disclosure-chevron" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M6 9l6 6 6-6"></path></svg>
</summary>
				<div class="kt-disclosure-body">
					<p class="kt-muted">{{ task.changes?.is_initial ? "First annual plan" : "" }}</p>
					<table class="kt-table">
						<!-- §10.10 — which decision, what came of it, in what
						     capacity, by whom and when. The outcome sits next to the
						     decision it belongs to, and the time is part of the
						     record, not a date. -->
						<thead><tr><th>Decision</th><th>Outcome</th><th>Capacity</th><th>Person</th><th>Date/time</th></tr></thead>
						<tbody>
							<tr v-for="(row, index) in history" :key="index">
								<td>{{ row.stage }}</td><td>{{ row.outcome }}</td><td>{{ row.capacity }}</td>
								<td>{{ row.actor }}</td><td>{{ row.date_display }}</td>
							</tr>
						</tbody>
					</table>
				</div>
			</details>
		</div>
	</div>
</template>

<script setup>
import { computed, ref } from "vue";
import MissingSettingPanel from "./MissingSettingPanel.vue";
import ReservationAllocation from "./ReservationAllocation.vue";

const props = defineProps({
	task: { type: Object, default: () => ({}) },
	resolution: { type: String, default: "" },
	lateReason: { type: String, default: "" },
	pending: Boolean,
	errorSummary: String,
});

defineEmits([
	"confirm",
	"open-return-dialog",
	"back",
	"download-pack",
	"view-evidence",
	"update:resolution",
	"update:lateReason",
]);

const open = ref([]);
const showBalances = ref(false);

const summary = computed(() => props.task.decision_summary || {});
const issues = computed(() => summary.value.issues || []);
const items = computed(() => props.task.items || []);
const funding = computed(() => props.task.funding || {});
const reservation = computed(() => props.task.reservation || null);
const history = computed(() => props.task.history || []);
const authority = computed(() => props.task.authority_card || {});
const signature = computed(() => props.task.preparation_signature);

const canDecideNow = computed(() => props.task.status === "Open" && props.task.can_decide);

// U11-HOPF/-AO/-STATUTORY vs U11-READER/-READER-HISTORICAL — the scope
// line's last segment: what an actor still owes, or that a reader is simply
// looking at the current plan. Historical drops it — the notice below
// already says so.
const scopePhrase = computed(() => {
	if (props.task.historical) return "";
	if (!props.task.can_decide) return "Current plan";
	if (props.task.stage === "Accounting Officer adoption") return "Awaiting Accounting Officer";
	if (props.task.stage === "Statutory approval") return `Awaiting ${authority.value.capacity_detail || "statutory authority"}`;
	return props.task.stage || "";
});

const fundingAt = computed(() => funding.value.at_approval || {});

// Only these four things differ between actors. The document does not.
const ACTORS = {
	"Head of Procurement Function": {
		title: "Review and submit the annual procurement plan",
		description: "Review the complete plan before sending it to the Accounting Officer.",
		statement: "I confirm that this complete annual procurement plan is ready for Accounting Officer adoption.",
		confirm: "Sign and submit Annual Plan",
		secondary: "Back to annual plan",
		secondary_is_return: false,
	},
	"Accounting Officer adoption": {
		title: "Review the annual procurement plan",
		description: "Review the proposed purchases. If you adopt the plan, it will go to the configured approving authority.",
		statement: "By selecting Adopt and submit, you adopt the complete plan shown here and send it for approval.",
		confirm: "Adopt and submit",
		secondary: "Return for correction",
		secondary_is_return: true,
	},
	"Statutory approval": {
		title: "Approve the annual procurement plan",
		description: "Review the plan adopted by the Accounting Officer.",
		statement: "By selecting Approve Annual Procurement Plan, you approve the complete plan shown here. Publication and activation checks must still be completed.",
		confirm: "Approve Annual Procurement Plan",
		secondary: "Return for correction",
		secondary_is_return: true,
	},
};

const COLLECTIVE = {
	title: "Record the decision",
	description: "Record the decision the body actually took on this plan.",
	statement: "Record approval only if the body approved this plan.",
	confirm: "Record approval",
	secondary: "Record return for correction",
	secondary_is_return: true,
};

// U11-READER/-READER-HISTORICAL — a reader who holds no decision here (an
// Auditor, or anyone once the review is no longer Open) reads the same
// complete document under its own title, never an actor's decision framing
// they cannot act on.
const READER = {
	title: "Annual procurement plan",
	description: "Review the plan and its recorded evidence.",
};

const actor = computed(() => {
	if (!props.task.can_decide) return READER;
	if (props.task.stage === "Statutory approval" && authority.value.is_board) {
		return { ...COLLECTIVE, title: `Record the ${authority.value.capacity_detail}'s decision` };
	}
	return ACTORS[props.task.stage] || ACTORS["Accounting Officer adoption"];
});

function toggle(planItemId) {
	open.value = open.value.includes(planItemId)
		? open.value.filter((id) => id !== planItemId)
		: [...open.value, planItemId];
}
</script>
