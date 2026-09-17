<!-- PLN-CHG-001 v1.23 §10.6 — Annual plan preparation (U07), ported from
     U07.dc.html.

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
		<div class="pln-masthead">
			<div>
				<h1 class="kt-page-title" data-testid="ppl-title">{{ title }}</h1>
			</div>
		</div>

		<div class="kt-meta-row pln-context-row" data-testid="ppl-context">
			<div>
				<span class="kt-label">Plan</span>
				<span class="kt-meta-value">{{ plan.header?.title }}</span>
			</div>
			<div>
				<span class="kt-label">Reference</span>
				<span class="kt-meta-value">{{ plan.plan_reference }}</span>
			</div>
			<div>
				<span class="kt-label">Version</span>
				<span class="kt-meta-value">{{ plan.version_number }}</span>
			</div>
			<div>
				<span class="kt-label">Status</span>
				<span class="kt-meta-value">
					<span class="kt-status" :class="badgeClass">{{ statusLabel }}</span>
				</span>
			</div>
			<div v-if="plan.is_successor && currentVersion">
				<span class="kt-label">Current plan</span>
				<span class="kt-meta-value">Version {{ currentVersion }}</span>
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

		<h3 class="kt-card-title">Purchases</h3>
		<table v-if="items.length" class="kt-table" data-testid="ppl-purchases">
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
					<td>{{ row.current_work }}</td>
					<td>
						<a href="#" data-testid="ppl-edit-purchase" @click.prevent="$emit('navigate', row.route)">Edit purchase</a>
					</td>
				</tr>
			</tbody>
		</table>
		<p v-else class="kt-muted" data-testid="ppl-purchases-empty">No purchases have been added yet.</p>

		<!-- U07-UNALLOCATED — the sources still waiting to become purchases. -->
		<h3 class="kt-card-title">Requirements ready to add</h3>
		<template v-if="unallocated.length">
			<table class="kt-table" data-testid="ppl-unallocated">
				<thead>
					<tr>
						<th>Select</th>
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
						<td>
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
							<a href="#" data-testid="ppl-view-requirement" @click.prevent="$emit('view-requirement', row)">View requirement</a>
						</td>
					</tr>
				</tbody>
			</table>
			<div class="pln-add-selected">
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

		<!-- Plan checks: three results, each naming its own correction. -->
		<h3 class="kt-card-title">Plan checks</h3>
		<div class="kt-meta-row pln-plan-checks" data-testid="ppl-plan-checks">
			<div v-for="check in planChecks" :key="check.label">
				<span class="kt-label">{{ check.label }}</span>
				<span class="kt-meta-value">
					<span v-if="check.kind === 'critical'" class="kt-status is-critical">{{ check.result }}</span>
					<span v-else>{{ check.result }}</span>
					<a
						v-if="check.action"
						href="#"
						class="pln-check-action"
						data-testid="ppl-check-action"
						@click.prevent="$emit('navigate', check.route)"
					>{{ check.action }}</a>
				</span>
			</div>
		</div>

		<!-- Changes and history: secondary, closed by default. -->
		<details class="kt-disclosure" data-testid="ppl-history">
			<summary class="kt-disclosure-head">
				<span class="kt-disclosure-title">Changes and history</span>
			</summary>
			<div class="kt-disclosure-body">
				<p class="kt-muted">{{ changesText }}</p>
				<p v-for="(row, index) in history" :key="index" class="kt-muted">{{ row }}</p>
			</div>
		</details>

		<p v-if="errorSummary" class="pln-error-summary" data-testid="ppl-error">{{ errorSummary }}</p>

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

		<!-- U07-FINANCE-COMPLETE — who is waited on, named. -->
		<p v-if="plan.waiting_on" class="kt-muted" data-testid="ppl-waiting-on">{{ plan.waiting_on }}</p>

		<div v-if="plan.open_task" class="pln-dpp-task">
			<button type="button" class="kt-btn kt-btn-primary" data-testid="ppl-open-task" @click="$emit('open-task', plan.open_task.route)">
				{{ plan.open_task.label }}
			</button>
		</div>
	</div>
</template>

<script setup>
import { computed, ref, watch } from "vue";

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
const unallocated = computed(() => props.plan.unallocated_sources || []);
const planChecks = computed(() => props.plan.plan_checks || []);
const history = computed(() => props.plan.history_lines || []);
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
