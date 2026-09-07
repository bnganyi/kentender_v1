<!-- REQ-DES-02 Start IT-equipment Requisition (§13.4), ported class-for-class
     from the artboard: a read-only "Planning source" card (identity,
     contributing departments, method, planned completion/value, plan
     horizon, Strategic Objective + full path, business need and expected
     operational result), the two-department allocation table, a static
     "Requirement product" card (always IT Equipment — no template/STD/
     profile selector, §5.9), the cross-department certification notice
     (only when more than one department contributed), and Cancel/Prepare
     Requisition actions. -->
<template>
	<div>
		<div v-if="loading" class="kt-card kt-blueprint" style="padding: 0; overflow: hidden" data-testid="req-start-loading">
			<i class="kt-corner tl"></i><i class="kt-corner tr"></i>
			<i class="kt-corner bl"></i><i class="kt-corner br"></i>
			<div v-for="row in 3" :key="row" class="req-skel-row">
				<div class="kt-skel" style="width: 72%"></div>
				<div class="kt-skel" style="width: 52%"></div>
				<div class="kt-skel" style="width: 44%"></div>
			</div>
		</div>

		<div v-else-if="error" class="kt-card kt-blueprint req-state-card" data-testid="req-start-error">
			<i class="kt-corner tl"></i><i class="kt-corner tr"></i>
			<i class="kt-corner bl"></i><i class="kt-corner br"></i>
			<h3>Procurement Requisitions could not be loaded.</h3>
			<p>Try again. If the problem continues, quote the support reference shown below.</p>
			<button type="button" class="kt-btn kt-btn-secondary" @click="$emit('reload')">Try again</button>
			<p class="req-support-ref">Support reference: {{ supportRef }}</p>
		</div>

		<div v-else-if="!detail.projection || !detail.projection.eligible" class="kt-card kt-blueprint req-state-card" data-testid="req-start-ineligible">
			<i class="kt-corner tl"></i><i class="kt-corner tr"></i>
			<i class="kt-corner bl"></i><i class="kt-corner br"></i>
			<h3>No Active Plan Items are ready for Requisition.</h3>
		</div>

		<div v-else-if="!detail.is_compatible" class="kt-card kt-blueprint req-state-card" data-testid="req-start-unsupported">
			<i class="kt-corner tl"></i><i class="kt-corner tr"></i>
			<i class="kt-corner bl"></i><i class="kt-corner br"></i>
			<h3>This Plan Item is not supported by the IT-equipment Requisition pattern.</h3>
			<button type="button" class="kt-btn kt-btn-secondary" @click="$emit('navigate', ['procurement-requisitions'])">Return to workspace</button>
		</div>

		<div v-else-if="detail.open_requisition" class="kt-card kt-blueprint req-state-card" data-testid="req-start-open-exists">
			<i class="kt-corner tl"></i><i class="kt-corner tr"></i>
			<i class="kt-corner bl"></i><i class="kt-corner br"></i>
			<h3>This Plan Item already has an open Requisition.</h3>
			<button
				v-if="canOpenExisting"
				type="button"
				class="kt-btn kt-btn-secondary"
				data-testid="req-start-open-existing"
				@click="$emit('navigate', ['procurement-requisitions', detail.open_requisition])"
			>
				Open it
			</button>
		</div>

		<template v-else>
			<h1 class="req-start-title">Prepare Requisition from approved Plan Item</h1>

			<div class="kt-card kt-blueprint req-card-pad" data-testid="req-planning-source">
				<i class="kt-corner tl"></i><i class="kt-corner tr"></i>
				<i class="kt-corner bl"></i><i class="kt-corner br"></i>
				<div class="kt-card-title">Planning source</div>
				<div class="req-source-grid">
					<div><span class="kt-eyebrow">Plan Item</span><div>{{ projection.plan_item_id }} — {{ projection.title }}</div></div>
					<div><span class="kt-eyebrow">Contributing departments</span><div>{{ detail.contributing_departments_label }}</div></div>
					<div><span class="kt-eyebrow">Procurement method</span><div>{{ projection.procurement_method }}</div></div>
					<div><span class="kt-eyebrow">Planned completion</span><div>{{ plannedCompletion }}</div></div>
					<div><span class="kt-eyebrow">Planned value</span><div>{{ plannedValue }}</div></div>
					<div>
						<span class="kt-eyebrow">Plan horizon</span>
						<div data-testid="req-plan-horizon">{{ planHorizonLine }}</div>
						<p v-if="projection.plan_horizon !== 'Single year'" class="req-source-note">
							The value above is this Plan Item's full multi-year allocation, not one year's worth.
						</p>
					</div>
				</div>
				<div class="req-source-section">
					<span class="kt-eyebrow">Strategic Objective</span>
					<div class="req-objective-id">{{ objectiveTitle ? `${projection.strategic_objective} — ${objectiveTitle}` : projection.strategic_objective }}</div>
					<div class="req-objective-path kt-muted">{{ projection.objective_path }}</div>
				</div>
				<div class="req-source-section req-source-grid">
					<div><span class="kt-eyebrow">Business need</span><div>{{ detail.business_need }}</div></div>
					<div><span class="kt-eyebrow">Expected operational result</span><div>{{ detail.expected_operational_result }}</div></div>
				</div>
			</div>

			<div class="kt-card kt-blueprint req-card-pad-tight" data-testid="req-allocations">
				<i class="kt-corner tl"></i><i class="kt-corner tr"></i>
				<i class="kt-corner bl"></i><i class="kt-corner br"></i>
				<table class="kt-table">
					<thead>
						<tr>
							<th>Contributing department</th>
							<th>Source requirement</th>
							<th class="req-num">Remaining quantity</th>
							<th class="req-num">Remaining value</th>
						</tr>
					</thead>
					<tbody>
						<tr v-for="source in projection.sources" :key="source.plan_source_allocation_id">
							<td>{{ ouLabel(source.organisation_unit) }}</td>
							<td>{{ source.title }}</td>
							<td class="req-num">{{ source.remaining_quantity }} {{ source.unit }}</td>
							<td class="req-num">{{ money(source.remaining_amount) }}</td>
						</tr>
					</tbody>
				</table>
			</div>

			<div class="kt-card kt-blueprint req-card-pad" data-testid="req-product-panel">
				<i class="kt-corner tl"></i><i class="kt-corner tr"></i>
				<i class="kt-corner bl"></i><i class="kt-corner br"></i>
				<div class="kt-card-title">Requirement product</div>
				<div class="req-product-value">IT Equipment</div>
				<p class="req-product-help kt-muted">This release supports straightforward off-the-shelf IT equipment. Complex software, integration or migration is not supported.</p>
			</div>

			<div v-if="projection.contributing_org_unit_ids.length > 1" class="req-notice" data-testid="req-cross-department-notice">
				This Requisition draws from two departments because Planning combined their Needs into one Plan Item. {{ leadDepartmentLabel }}, as the larger contributor, certifies the departmental submission.
			</div>

			<div class="req-actions">
				<button type="button" class="kt-btn kt-btn-secondary" @click="$emit('navigate', ['procurement-requisitions'])">Cancel</button>
				<!-- Read-offer parity with `prepare_it_equipment_requisition`'s own
				     gate: only a Departmental Author or Head of User Department for
				     one of this item's contributing units sees this action at all —
				     a Head of Procurement Function/Planner/Auditor can legitimately
				     reach this screen (the workspace's own "Your Requisitions" list
				     can route them here) but is never offered an action the command
				     layer would itself refuse. -->
				<button
					v-if="detail.can_prepare"
					type="button"
					class="kt-btn kt-btn-primary"
					:disabled="pending"
					data-testid="req-prepare-requisition"
					@click="$emit('prepare', planItemId)"
				>
					Prepare Requisition
				</button>
			</div>
		</template>
	</div>
</template>

<script setup>
import { computed } from "vue";
import { formatMoney, formatDate } from "../data/format.js";

const props = defineProps({
	loading: Boolean,
	error: String,
	supportRef: String,
	detail: { type: Object, default: () => ({}) },
	planItemId: String,
	pending: Boolean,
	canOpenExisting: { type: Boolean, default: true },
});

defineEmits(["reload", "navigate", "prepare"]);

const projection = computed(() => props.detail.projection || {});
const objectiveTitle = computed(() => props.detail.strategic_objective_title || "");
const plannedCompletion = computed(() => {
	const dates = projection.value.planned_dates || {};
	return formatDate(dates.delivery_completion_date || dates.completion_date);
});
const plannedValue = computed(() => money(projection.value.total_value));
const planHorizonLine = computed(() => {
	if ((projection.value.plan_horizon || "Single year") === "Single year") return "Single year";
	return `Multi-year · ${projection.value.multi_year_justification || ""}`;
});
const leadDepartmentLabel = computed(() => (props.detail.contributing_departments_label || "").split(" · ")[0] || "");

function money(amount) {
	return formatMoney(amount);
}

function ouLabel(unit) {
	return (props.detail.organisation_unit_labels || {})[unit] || unit;
}
</script>
