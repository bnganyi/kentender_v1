<!-- PLN-CHG-001 v1.23 §10.10 — the complete annual-plan review (U11), ported
     from U11.dc.html.

     Every governance actor reads the same document. Only the header, the prior
     accountability shown, the decision statement and the actual buttons
     change: HOPF signs, the AO adopts, the statutory authority approves, a
     collective body records its own decision, and a reader decides nothing.

     The order matters. Decision summary, visible material issues, concise
     purchase rows, then the actor's statement and their decision — before any
     collapsed evidence. The actor must not scroll through audit evidence to
     reach the decision, and no purchase opens by itself. But nothing material
     is hidden either: an issue that would change the verdict is always in the
     summary, never behind a disclosure. -->
<template>
	<div>
		<div class="pln-masthead pln-masthead-split">
			<div>
				<h1 class="kt-page-title" data-testid="rev-title">{{ actor.title }}</h1>
				<p class="kt-page-lede">{{ actor.description }}</p>
			</div>
			<button
				v-if="task.can_download_review_pack"
				type="button"
				class="kt-btn kt-btn-secondary"
				data-testid="rev-download"
				@click="$emit('download-pack')"
			>
				Download review pack
			</button>
		</div>

		<div class="kt-meta-row pln-context-row" data-testid="rev-context">
			<div>
				<span class="kt-label">Plan</span>
				<span class="kt-meta-value">{{ task.header?.title }}</span>
			</div>
			<div>
				<span class="kt-label">Plan reference</span>
				<span class="kt-meta-value">{{ task.plan_reference }}</span>
			</div>
			<div>
				<span class="kt-label">Version</span>
				<span class="kt-meta-value">{{ task.version_number }}</span>
			</div>
			<div>
				<span class="kt-label">Current stage</span>
				<span class="kt-meta-value"><span class="kt-status is-attention">{{ stageLabel }}</span></span>
			</div>
		</div>

		<!-- U11-READER historical variant. -->
		<p v-if="task.historical" class="kt-muted" data-testid="rev-historical">Historical plan — read only</p>

		<!-- First section — Decision summary. -->
		<h3 class="kt-card-title">Decision summary</h3>
		<div class="kt-kpi-row" data-testid="rev-summary">
			<div class="kt-kpi-card">
				<div class="kt-kpi-value">{{ summary.value_display }}</div>
				<div class="kt-kpi-sub">Estimated cost</div>
			</div>
			<div class="kt-kpi-card">
				<div class="kt-kpi-value">{{ summary.purchases }}</div>
				<div class="kt-kpi-sub">Purchases</div>
			</div>
			<div class="kt-kpi-card">
				<div class="kt-kpi-value">{{ summary.departments }}</div>
				<div class="kt-kpi-sub">Departments</div>
			</div>
		</div>
		<div class="kt-meta-row" data-testid="rev-checks">
			<div>
				<span class="kt-label">Funding</span>
				<span class="kt-meta-value">{{ summary.funding }}</span>
			</div>
			<div>
				<span class="kt-label">Reserved procurement</span>
				<span class="kt-meta-value">{{ summary.reservation }}</span>
			</div>
			<div>
				<span class="kt-label">Schedule</span>
				<span class="kt-meta-value">{{ summary.schedule }}</span>
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
							<a href="#" data-testid="rev-review-purchase" @click.prevent="toggle(row.plan_item_id)">Review purchase</a>
						</td>
					</tr>
					<!-- One level of detail, opened deliberately. -->
					<tr v-if="open.includes(row.plan_item_id)" class="pln-row-detail" data-testid="rev-purchase-detail">
						<td colspan="7">
							<div class="kt-meta-row">
								<div>
									<span class="kt-label">Estimated cost</span>
									<span class="kt-meta-value">{{ row.value_display }}</span>
								</div>
								<div>
									<span class="kt-label">Procurement approach</span>
									<span class="kt-meta-value">{{ row.procurement_method }}</span>
								</div>
								<div>
									<span class="kt-label">Departments</span>
									<span class="kt-meta-value">{{ row.department }}</span>
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

		<!-- Second section — Accountability. Two compact labelled rows. -->
		<h3 class="kt-card-title">Accountability</h3>
		<div class="kt-meta-row" data-testid="rev-accountability">
			<div>
				<span class="kt-label">Funding</span>
				<span class="kt-meta-value">{{ fundingLine }}</span>
			</div>
			<!-- Absent before the signature exists (U11-HOPF). -->
			<div v-if="signature">
				<span class="kt-label">Preparation</span>
				<span class="kt-meta-value" data-testid="rev-preparation">
					Signed by {{ signature.actor_name }}, {{ signature.capacity }} · {{ signature.signed_at_display }}
				</span>
			</div>
		</div>
		<p class="kt-muted">Funding confirmation does not set money aside.</p>

		<!-- The decision comes before the collapsed evidence, not after it. -->
		<template v-if="task.status === 'Open' && task.can_decide">
			<!-- U11-COLLECTIVE — the body decides; the recorder records. -->
			<div v-if="authority.is_board" class="kt-meta-row" data-testid="rev-collective">
				<div>
					<span class="kt-label">Decision belongs to</span>
					<span class="kt-meta-value">{{ authority.capacity_detail }}</span>
				</div>
				<div>
					<span class="kt-label">Recorded by</span>
					<span class="kt-meta-value">{{ task.recorder_name || "—" }}</span>
				</div>
				<div class="kt-field">
					<label for="rev-resolution" class="kt-label">Resolution reference</label>
					<input
						id="rev-resolution"
						class="kt-input"
						data-testid="rev-resolution"
						:value="resolution"
						@input="$emit('update:resolution', $event.target.value)"
					>
				</div>
			</div>

			<!-- U11-LATE-ADOPTION — the AO must say why, before deciding. -->
			<div v-if="task.late_activation_required" class="kt-field" data-testid="rev-late">
				<div class="kt-meta-row">
					<div>
						<span class="kt-label">Financial year started</span>
						<span class="kt-meta-value">{{ task.financial_year_started_display }}</span>
					</div>
				</div>
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

			<div class="pln-footer" data-testid="rev-footer">
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
				<span v-else></span>
				<div class="pln-footer-right">
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

		<!-- Supporting evidence, all closed. Complete, reachable, secondary. -->
		<details class="kt-disclosure" data-testid="rev-funding-evidence">
			<summary class="kt-disclosure-head"><span class="kt-disclosure-title">Funding evidence</span></summary>
			<div class="kt-disclosure-body">
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
			</div>
		</details>

		<details class="kt-disclosure" data-testid="rev-plan-checks">
			<summary class="kt-disclosure-head"><span class="kt-disclosure-title">Review Plan checks</span></summary>
			<div class="kt-disclosure-body">
				<div class="kt-meta-row">
					<div>
						<span class="kt-label">Required allocation</span>
						<span class="kt-meta-value">{{ reservation.required_allocation_display }}</span>
					</div>
					<div>
						<span class="kt-label">Planned qualifying allocation</span>
						<span class="kt-meta-value">{{ reservation.planned_qualifying_display }}</span>
					</div>
					<div>
						<span class="kt-label">Budget basis</span>
						<span class="kt-meta-value">{{ reservation.budget_basis_reference }} · {{ reservation.budget_version_display }}</span>
					</div>
				</div>
			</div>
		</details>

		<details class="kt-disclosure" data-testid="rev-history">
			<summary class="kt-disclosure-head"><span class="kt-disclosure-title">Changes and history</span></summary>
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
</template>

<script setup>
import { computed, ref } from "vue";
import MissingSettingPanel from "./MissingSettingPanel.vue";

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

const summary = computed(() => props.task.decision_summary || {});
const issues = computed(() => summary.value.issues || []);
const items = computed(() => props.task.items || []);
const funding = computed(() => props.task.funding || {});
const reservation = computed(() => props.task.reservation || {});
const history = computed(() => props.task.history || []);
const authority = computed(() => props.task.authority_card || {});
const signature = computed(() => props.task.preparation_signature);

const stageLabel = computed(() => {
	if (props.task.stage === "Accounting Officer adoption") return "Awaiting Accounting Officer";
	if (props.task.stage === "Statutory approval") return `Awaiting ${authority.value.capacity_detail || "statutory authority"}`;
	return props.task.stage || "";
});

const fundingLine = computed(() => {
	const at = funding.value.at_approval || {};
	if (!at.actor_name) return "Not yet checked";
	return `Within each approved budget line · Checked by ${at.actor_name} · ${at.decided_at_display}`;
});

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

const actor = computed(() => {
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
