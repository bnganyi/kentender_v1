<!-- PLN-CHG-001 v1.23 §10.4 — the departmental plan (U02–U05), ported from
     U02-U05.dc.html.

     One page, two readings of it. The Author sees their own working plan and
     is told plainly that their Head of Department submits it; the HoD sees the
     same plan as a complete review with the certification and one submit
     action beneath it. There is no separate certification page and no invented
     Author-to-HoD handover step (§9.7).

     Excluded requirements stay in the table — they are accounted for, not
     hidden — with their full reason always visible in row detail, never behind
     a disclosure (§10.4 U03-EXCLUDED-ROW). -->
<template>
	<div>
		<div class="pln-masthead">
			<div>
				<h1 class="kt-page-title" data-testid="pln-dpp-title">{{ heading.title }}</h1>
				<p class="kt-page-lede">{{ heading.description }}</p>
			</div>
		</div>

		<!-- Record context: separately labelled values, names before codes. -->
		<div class="kt-meta-row pln-context-row" data-testid="pln-dpp-context">
			<div>
				<span class="kt-label">Department</span>
				<span class="kt-meta-value">{{ context.department }}</span>
			</div>
			<div>
				<span class="kt-label">Financial year</span>
				<span class="kt-meta-value">{{ context.financial_year }}</span>
			</div>
			<div>
				<span class="kt-label">Status</span>
				<span class="kt-meta-value">
					<span class="kt-status" :class="`is-${plan.header?.badge_kind || 'draft'}`">{{ plan.header?.badge }}</span>
				</span>
			</div>
			<div v-if="plan.accepted_submission_number">
				<span class="kt-label">Accepted submission</span>
				<span class="kt-meta-value">{{ plan.accepted_submission_number }}</span>
			</div>
			<div v-if="plan.is_correction && plan.candidate_submission_number">
				<span class="kt-label">Correction submission</span>
				<span class="kt-meta-value">{{ plan.candidate_submission_number }}</span>
			</div>
		</div>

		<!-- U05-CORRECTION — the correction notice leads, before the table it
		     affects. -->
		<div v-if="plan.is_correction" class="kt-notice is-warning" data-testid="pln-dpp-correction-notice">
			<svg class="kt-notice-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
				<path d="M12 3l9 16H3z"></path><path d="M12 10v4M12 17h.01"></path>
			</svg>
			<div class="kt-notice-body">Your plan needs a correction</div>
		</div>

		<div v-if="plan.update_notice" class="kt-notice is-warning" data-testid="pln-dpp-update-notice">
			<svg class="kt-notice-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
				<path d="M12 3l9 16H3z"></path><path d="M12 10v4M12 17h.01"></path>
			</svg>
			<div class="kt-notice-body">
				<strong>{{ plan.update_notice.title }}</strong>
				<p>{{ plan.update_notice.text }}</p>
			</div>
		</div>

		<!-- U02-CLOSED — the draft stays editable; only submission is closed. -->
		<div v-if="closedNotice" class="kt-notice is-warning" data-testid="pln-dpp-closed">
			<svg class="kt-notice-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
				<path d="M12 3l9 16H3z"></path><path d="M12 10v4M12 17h.01"></path>
			</svg>
			<div class="kt-notice-body">{{ closedNotice }}</div>
		</div>

		<!-- Summary strip. The Author's cost label says "entered so far" because
		     that is what it is: no complete departmental total exists yet. -->
		<div class="kt-kpi-row" data-testid="pln-dpp-summary">
			<div class="kt-kpi-card">
				<div class="kt-kpi-value">{{ summary.requirements }}</div>
				<div class="kt-kpi-sub">Requirements</div>
			</div>
			<div class="kt-kpi-card">
				<div class="kt-kpi-value">{{ summary.cost }}</div>
				<div class="kt-kpi-sub">{{ summary.cost_label }}</div>
			</div>
			<div class="kt-kpi-card" :class="{ 'is-attention': summary.attention }">
				<div class="kt-kpi-value">{{ summary.third }}</div>
				<div class="kt-kpi-sub">{{ summary.third_label }}</div>
			</div>
		</div>

		<h3 class="kt-card-title">Requirements</h3>
		<table class="kt-table pln-dpp-table" data-testid="pln-dpp-table">
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
				<template v-for="row in entries" :key="row.entry_id">
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
							<a
								v-if="row.action"
								href="#"
								data-testid="pln-dpp-row-action"
								@click.prevent="onRowAction(row)"
							>{{ row.action }}</a>
							<span v-else>—</span>
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
							<span class="kt-label">What needs to change?</span>
							<span>{{ issue.correction || issue.problem }}</span>
						</td>
					</tr>
				</template>
				<tr v-if="!entries.length">
					<td colspan="7" class="kt-muted" data-testid="pln-dpp-empty">No requirements yet.</td>
				</tr>
			</tbody>
		</table>

		<div v-if="plan.mutable" class="pln-dpp-add">
			<button type="button" class="kt-btn kt-btn-ghost" data-testid="pln-dpp-add" @click="$emit('add-direct')">
				Add a requirement
			</button>
		</div>

		<!-- U05-CORRECTION's "For your next departmental update": named, and
		     deliberately without an add action — the correction comes first. -->
		<template v-if="plan.is_correction">
			<h3 class="kt-card-title">For your next departmental update</h3>
			<p class="kt-muted" data-testid="pln-dpp-next-update">
				Finish this correction first. New requirements belong in the next update.
			</p>
		</template>

		<!-- Certification: the HoD's, on the complete plan, on this page. -->
		<div v-if="certification.show" class="kt-card kt-blueprint pln-certification" data-testid="pln-dpp-certification">
			<i class="kt-corner tl"></i><i class="kt-corner tr"></i>
			<i class="kt-corner bl"></i><i class="kt-corner br"></i>
			<div class="kt-card-title">Certification</div>
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

		<!-- Action area, after all decision content. -->
		<div class="pln-footer" data-testid="pln-dpp-footer">
			<button type="button" class="kt-btn kt-btn-secondary" data-testid="pln-dpp-back" @click="$emit('back')">
				Back
			</button>
			<div class="pln-footer-right">
				<!-- The Author is told who submits, rather than shown a control
				     they cannot use (§10.4). -->
				<p v-if="plan.submit_hint" class="kt-muted" data-testid="pln-dpp-submit-hint">{{ plan.submit_hint }}</p>
				<p v-else-if="certification.show && !certified" class="kt-muted" data-testid="pln-dpp-certify-hint">
					Confirm the certification to submit this plan.
				</p>
				<button
					v-if="plan.mutable"
					type="button"
					class="kt-btn kt-btn-secondary"
					data-testid="pln-dpp-save"
					:disabled="pending"
					@click="$emit('save-draft')"
				>
					Save draft
				</button>
				<button
					v-if="plan.can_submit"
					type="button"
					class="kt-btn kt-btn-primary"
					data-testid="pln-dpp-submit"
					:disabled="pending || !certified"
					@click="$emit('submit')"
				>
					{{ plan.is_correction ? "Resubmit departmental plan" : "Submit departmental plan" }}
				</button>
				<button
					v-if="plan.can_create_update"
					type="button"
					class="kt-btn kt-btn-primary"
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
			<button type="button" class="kt-btn kt-btn-primary" @click="$emit('open-task', plan.open_task.route)">
				{{ plan.open_task.label }}
			</button>
		</div>
	</div>
</template>

<script setup>
import { computed } from "vue";

const props = defineProps({
	plan: { type: Object, default: () => ({}) },
	pending: Boolean,
	certified: Boolean,
	errorSummary: String,
});

const emit = defineEmits([
	"view-accepted-needs",
	"add-direct",
	"open-entry",
	"restore-entry",
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
const isHod = computed(() => props.plan.access === "hod");

const heading = computed(() => {
	const department = context.value.department_name || context.value.department || "your department";
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

const closedNotice = computed(() => {
	const window = context.value.window || {};
	if (window.state !== "Closed" || !props.plan.mutable || props.plan.is_correction) return "";
	return "Initial submissions are closed. You can keep editing this draft, but it cannot be submitted now.";
});

function onRowAction(row) {
	if (row.action === "Include in this year's departmental plan") {
		emit("restore-entry", row);
		return;
	}
	emit("open-entry", row);
}
</script>
