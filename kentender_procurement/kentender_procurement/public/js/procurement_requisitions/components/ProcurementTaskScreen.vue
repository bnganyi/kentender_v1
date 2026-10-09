<!-- REQ-DES-08 — Procurement authorisation (base, checks detail,
     BLOCKING-FUNDING, HOLD, TECHNICAL, return / change-department / Planning
     correction dialogs) and REQ-DES-09 confirmation. The decision and its
     financial consequence lead; funding, Planning availability, certification
     and the decision chain follow; the complete Version is below. Whether
     Authorise is offered is the server's verdict. -->
<template>
	<div class="kt-panel-lg req-page" data-testid="req-procurement-task" :data-mode="view.mode">
		<div class="req-title-row">
			<h3>{{ view.header.title }}</h3>
			<span class="kt-status" :class="view.header.badge.tone" data-testid="req-badge">{{ view.header.badge.label }}</span>
		</div>
		<p class="kt-muted req-lede" style="margin-top: 6px">{{ view.header.description }}</p>

		<Notice :tone="resultTone"><span data-testid="req-procurement-result"><strong>{{ view.result.title }}</strong><template v-if="view.result.detail"><br />{{ view.result.detail }}</template></span></Notice>
		<div v-if="blockedFunding" class="req-rule" style="margin-top: var(--kt-space-4)" data-testid="req-shortfall">
			<div v-for="line in funding.lines" :key="line.budget_line" class="kt-meta-row">
				<div><span class="kt-label">Requested</span><span class="kt-meta-value" style="font-size: 14px">{{ line.this_requisition }}</span></div>
				<div><span class="kt-label">Available</span><span class="kt-meta-value" style="font-size: 14px">{{ line.available_now }}</span></div>
				<div><span class="kt-label">Shortfall</span><span class="kt-meta-value" style="font-size: 14px">{{ line.shortfall }}</span></div>
			</div>
		</div>
		<div v-if="decider" class="req-question" style="margin: var(--kt-space-4) 0 0">{{ view.question }}</div>

		<template v-if="funding.lines && funding.lines.length">
			<CardTitle title="Current funding" icon="dollar" style="margin-top: var(--kt-space-6)" />
			<div v-for="line in funding.lines" :key="line.budget_line" class="req-rule" data-testid="req-funding">
				<div class="kt-meta-row">
					<div><span class="kt-label">Budget Line</span><span class="kt-meta-value" style="font-size: 14px">{{ line.budget_line }}</span></div>
					<div><span class="kt-label">Approved</span><span class="kt-meta-value" style="font-size: 14px">{{ line.approved }}</span></div>
					<div><span class="kt-label">Available now</span><span class="kt-meta-value" style="font-size: 14px">{{ line.available_now }}</span></div>
					<div><span class="kt-label">This requisition</span><span class="kt-meta-value" style="font-size: 14px">{{ line.this_requisition }}</span></div>
					<div v-if="line.sufficient"><span class="kt-label">Available after authorisation</span><span class="kt-meta-value kt-figure is-attention" style="font-size: 14px">{{ line.available_after }}</span></div>
				</div>
				<div v-if="line.sufficient" style="margin-top: var(--kt-space-4)">
					<div class="kt-bar"><i class="kt-bar-reserved" :style="{ width: `${line.reserved_share}%` }"></i></div>
					<div class="req-bar-labels">
						<span class="kt-label">Funding reserved by this requisition · {{ line.reserved_share }}% of the Budget Line</span>
						<span class="kt-label">Free after authorisation · {{ line.free_share }}%</span>
					</div>
				</div>
			</div>
			<table class="table" style="margin: var(--kt-space-3) 0 var(--kt-space-8)">
				<thead><tr><th>Source</th><th class="is-num">Requested value</th></tr></thead>
				<tbody><tr v-for="s in funding.sources" :key="s.department"><td>{{ s.department }}</td><td class="is-num">{{ s.requested_value }}</td></tr></tbody>
			</table>
		</template>

		<CardTitle title="Planning availability" icon="calendar-plain" />
		<div class="req-rule" style="margin-bottom: var(--kt-space-8)">
			<div class="kt-meta-row">
				<div><span class="kt-label">Status</span><span class="kt-meta-value" style="font-size: 14px"><span class="kt-status" :class="planning.status === 'Eligible' ? 'is-live' : 'is-critical'">{{ planning.status }}</span></span></div>
				<div><span class="kt-label">Quantity available</span><span class="kt-meta-value" style="font-size: 14px">{{ planning.quantity_available }}</span></div>
				<div><span class="kt-label">Value available</span><span class="kt-meta-value" style="font-size: 14px">{{ planning.value_available }}</span></div>
				<div><span class="kt-label">Correction hold</span><span class="kt-meta-value" style="font-size: 14px">{{ planning.hold }}</span></div>
			</div>
		</div>

		<CardTitle title="Departmental certification" icon="check-circle" />
		<div class="req-rule" style="margin-bottom: var(--kt-space-4)">
			<div class="kt-meta-row">
				<div><span class="kt-label">Submitted by</span><span class="kt-meta-value" style="font-size: 14px">{{ view.certification.submitted_by }}</span></div>
				<div><span class="kt-label">Lead department</span><span class="kt-meta-value" style="font-size: 14px">{{ view.certification.lead_department }}</span></div>
				<div><span class="kt-label">Submitted at</span><span class="kt-meta-value" style="font-size: 14px">{{ view.certification.submitted_at }}</span></div>
				<div v-if="actions.change_submitting_department"><span class="kt-label">&nbsp;</span><a href="#" style="font-size: 13px" data-testid="req-change-department" @click.stop.prevent="dialog = 'department'">Change submitting department</a></div>
			</div>
		</div>

		<DecisionChain :rows="view.decision_chain || []" style="margin-bottom: var(--kt-space-8)" />

		<ReviewSections :sections="view.sections || []" />

		<div class="req-review-section" style="margin-bottom: var(--kt-space-6)" data-testid="req-checks" :data-open="checksOpen ? 'true' : 'false'">
			<div class="req-review-head">
				<div>
					<CardTitle title="Procurement checks" icon="check-square" style="margin: 0" />
					<p class="kt-muted req-review-summary">{{ view.checks.summary }}</p>
				</div>
				<button type="button" class="req-review-toggle" :aria-expanded="checksOpen ? 'true' : 'false'" data-testid="req-checks-toggle" @click="checksOpen = !checksOpen">{{ checksOpen ? "Hide details" : "Show details" }}</button>
			</div>
			<table v-if="checksOpen" class="table req-review-body">
				<thead><tr><th>Check</th><th>Result</th></tr></thead>
				<tbody>
					<tr v-for="c in view.checks.rows" :key="c.test" :class="{ 'is-failed': !c.ok }"><td>{{ c.check }}</td><td>{{ c.ok ? c.result : c.failure }}</td></tr>
				</tbody>
			</table>
		</div>

		<Disclosure title="Record details" testid="req-record-details" style="margin-bottom: var(--kt-space-6)">
			<div class="kt-meta-row req-facts" style="flex-wrap: wrap">
				<div v-for="fact in view.record_details || []" :key="fact.label"><span class="kt-label">{{ fact.label }}</span><span class="kt-meta-value" style="font-size: 14px"><span v-for="(part, i) in String(fact.value).split('; ')" :key="i" class="req-fact-line">{{ part }}</span></span></div>
			</div>
		</Disclosure>

		<div v-if="actions.authorise" class="req-statement"><div class="kt-label" style="margin-bottom: 4px">Authorisation</div>{{ view.statement }}</div>

		<template v-if="uncertain">
			<p v-if="uncertain === 'checking'" style="font-size: 14px" data-testid="req-uncertain-checking">{{ CHECKING }}</p>
			<Notice v-else-if="uncertain === 'committed'" tone="live"><span data-testid="req-uncertain-committed">{{ committedText }}</span></Notice>
			<Notice v-else tone="warning"><span data-testid="req-uncertain-unconfirmed">{{ RETRY_SAFE }}</span></Notice>
		</template>

		<div v-if="decider && uncertain !== 'checking' && uncertain !== 'committed'" class="req-footer">
			<button v-if="actions.request_planning_correction" type="button" class="btn btn-ghost" :disabled="busy" data-testid="req-action-planning" @click="dialog = 'planning'">Request Planning correction</button>
			<div class="req-actions">
				<button v-if="actions.view_planning_request" type="button" class="btn btn-ghost" data-testid="req-view-planning-request" @click="viewPlanningRequest">View Planning request</button>
				<button v-if="!actions.authorise && actions.refresh" type="button" class="btn btn-secondary" :disabled="busy" data-testid="req-refresh-checks" @click="ctx.reload()">Refresh checks</button>
				<button v-if="actions.return_to_department" type="button" class="btn btn-secondary" :disabled="busy" data-testid="req-return" @click="dialog = 'return'">Return to department</button>
				<button v-if="actions.authorise" type="button" class="btn btn-primary" :disabled="busy" data-testid="req-authorise" @click="dialog = 'authorise'">Authorise requisition</button>
			</div>
		</div>
		<div v-else-if="uncertain !== 'checking'" class="req-footer">
			<button type="button" class="btn btn-ghost" data-testid="req-back" @click="ctx.go()">Back to Requisitions</button>
		</div>

		<AuthoriseDialog v-if="dialog === 'authorise'" :confirmation="view.confirmation" :busy="busy" :error="dialogError('authorise')" @close="dialog = null" @confirm="authorise" />
		<ReasonDialog
			v-if="dialog === 'return'"
			title="Return this requisition to the department?"
			reason-label="Correction required (20–1,000 characters)"
			placeholder="State what must change and identify the affected section"
			confirm-label="Return to department"
			notice="The submitted Version will remain in history and a copied Draft will open for correction."
			:sections="(view.catalogue || {}).affected_sections"
			:busy="busy"
			:error="dialogError('return')"
			testid="req-return-dialog"
			@close="dialog = null"
			@confirm="returnToDepartment"
		/>
		<ReasonDialog
			v-if="dialog === 'department'"
			title="Change submitting department and return?"
			option-label="Submitting department"
			:options="departmentOptions"
			:initial-option="departmentOptions[0] && departmentOptions[0].value"
			reason-label="Reason (required, 20–500 characters)"
			:max="500"
			confirm-label="Confirm change and return"
			notice="The current submission will remain in history. A copied Draft must be certified by the new submitting department before authorisation."
			:busy="busy"
			:error="dialogError('department')"
			testid="req-department-dialog"
			@close="dialog = null"
			@confirm="changeDepartment"
		/>
		<ReasonDialog v-if="dialog === 'planning'" v-bind="PLANNING_CORRECTION" :busy="busy" :error="dialogError('planning')" @close="dialog = null" @confirm="requestPlanning" />
	</div>
</template>

<script setup>
import { computed, ref } from "vue";
import { useReq } from "../data/context.js";
import { CHECKING, RETRY_SAFE, useDecision } from "../data/decision.js";
import { PLANNING_CORRECTION } from "../data/dialogs.js";
import AuthoriseDialog from "./AuthoriseDialog.vue";
import CardTitle from "./shared/CardTitle.vue";
import DecisionChain from "./shared/DecisionChain.vue";
import Disclosure from "./shared/Disclosure.vue";
import Notice from "./shared/Notice.vue";
import ReasonDialog from "./shared/ReasonDialog.vue";
import ReviewSections from "./shared/ReviewSections.vue";

const props = defineProps({ view: { type: Object, required: true } });
const ctx = useReq();
const busy = computed(() => ctx.pending.value);
const actions = computed(() => props.view.actions || {});
const decider = computed(() => props.view.mode === "decider");
const funding = computed(() => props.view.funding || {});
const planning = computed(() => props.view.planning || {});
const blockedFunding = computed(() => funding.value.available && !funding.value.all_sufficient);
const resultTone = computed(() => String((props.view.result || {}).tone || "is-live").replace(/^is-/, ""));
const checksOpen = ref(!!(props.view.checks || {}).open);
// The departments this submission could move to: every contributing one but the current lead.
const departmentOptions = computed(() => ((props.view.change_department || {}).options || []).filter((o) => o.value !== (props.view.change_department || {}).current));

const dialog = ref(null);
const { uncertain, committedText, decide } = useDecision(ctx);
function dialogError(label) {
	return ctx.commandError.value && ctx.commandError.value.label === label ? ctx.commandError.value.message : "";
}
const taskClosed = () => (props.view.task || {}).status !== "Open";

async function authorise() {
	const done = await decide(
		"authorise",
		(key) => ctx.api.authorise({ requisition: props.view.requisition, task: props.view.task.task, expected_record_version: props.view.root_record_version, idempotency_key: key }),
		{ committed: taskClosed, text: "Requisition authorised" }
	);
	if (done || uncertain.value) dialog.value = null;
}
async function returnToDepartment({ reason, affected_section }) {
	const done = await decide(
		"return",
		(key) => ctx.api.returnToDepartment({ task: props.view.task.task, reason, affected_section, expected_record_version: props.view.task.record_version, idempotency_key: key }),
		{ committed: taskClosed, text: "Requisition returned to the department" }
	);
	if (done || uncertain.value) dialog.value = null;
}
async function changeDepartment({ reason, option }) {
	const done = await decide(
		"department",
		(key) => ctx.api.changeLeadDepartment({ task: props.view.task.task, new_lead_org_unit: option, reason, expected_record_version: props.view.task.record_version, idempotency_key: key }),
		{ committed: taskClosed, text: "Requisition returned for certification by the new submitting department" }
	);
	if (done || uncertain.value) dialog.value = null;
}
async function requestPlanning({ reason }) {
	const done = await ctx.run("planning", (key) => ctx.api.requestPlanningCorrection({ requisition: props.view.requisition, reason, expected_record_version: props.view.root_record_version, idempotency_key: key }));
	if (done) dialog.value = null;
}
function viewPlanningRequest() {
	window.frappe.set_route("procurement-planning");
}
</script>
