<!-- PLN-UI-09 Plan Item editor (§12.8), rendering PLN-DES-09 (single source)
     and PLN-DES-09A (combined) from the same read model and screen: the
     source card(s) are read-only, only title/description/Strategic
     Objective/aggregation reason (combined only) and the seven schedule
     dates are editable. No source edit, method selector or actual dates. -->
<template>
	<div class="pln-editor">
		<p class="kt-page-kicker">{{ item.header?.eyebrow }}</p>
		<h1 class="kt-page-title">{{ item.header?.title }}</h1>
		<p class="pln-quiet-ref">{{ item.header?.reference_line }}</p>
		<div class="pln-badges">
			<span class="kt-status is-draft">{{ item.header?.item_state_badge }}</span>
			<span class="kt-status is-pending">{{ item.header?.finance_state_badge }}</span>
		</div>

		<div
			v-if="item.source_correction_required"
			class="pln-notice is-critical"
			data-testid="ppi-source-correction"
		>
			<p class="pln-notice-title">Source correction required</p>
			<p>
				A departmental source changed. Dissolve this Plan Item and re-form it
				from the current source before continuing.
			</p>
		</div>

		<div v-if="errorSummary" class="pln-notice is-critical" role="alert" data-testid="ppi-error">
			<p class="pln-notice-title">This command could not be completed</p>
			<p>{{ errorSummary }}</p>
		</div>

		<!-- single source -->
		<div
			v-if="!item.combined"
			class="kt-card kt-blueprint pln-card-pad"
			data-testid="ppi-source"
		>
			<i class="kt-corner tl"></i><i class="kt-corner tr"></i>
			<i class="kt-corner bl"></i><i class="kt-corner br"></i>
			<div class="kt-card-title">Departmental source</div>
			<div class="pln-field-grid" v-if="source">
				<div class="pln-ro-field"><label>Department</label><div class="pln-val">{{ source.department }}</div></div>
				<div class="pln-ro-field"><label>Source origin</label><div class="pln-val">{{ source.source_origin }}</div></div>
				<div class="pln-ro-field"><label>Departmental plan</label><div class="pln-val">{{ source.departmental_plan_line }}</div></div>
				<div class="pln-ro-field" v-if="source.need_reference_line">
					<label>Accepted Need</label><div class="pln-val">{{ source.need_reference_line }}</div>
				</div>
				<div class="pln-ro-field"><label>Quantity</label><div class="pln-val">{{ source.quantity_display }}</div></div>
				<div class="pln-ro-field"><label>Required by</label><div class="pln-val">{{ source.required_by_display }}</div></div>
				<div class="pln-ro-field"><label>Budget Line</label><div class="pln-val">{{ source.budget_line }}</div></div>
				<div class="pln-ro-field"><label>Planned value</label><div class="pln-val">{{ source.amount_display }}</div></div>
			</div>
		</div>

		<!-- combined sources -->
		<div
			v-else
			class="kt-card kt-blueprint pln-card-pad"
			data-testid="ppi-sources"
		>
			<i class="kt-corner tl"></i><i class="kt-corner tr"></i>
			<i class="kt-corner bl"></i><i class="kt-corner br"></i>
			<div class="kt-card-title">Departmental sources</div>
			<table class="pln-table">
				<thead>
					<tr>
						<th>Requirement</th><th>Department</th><th>Source origin</th>
						<th class="pln-num">Quantity</th><th>Required by</th>
						<th>Budget Line</th><th class="pln-num">Amount</th>
					</tr>
				</thead>
				<tbody>
					<tr v-for="(row, idx) in item.sources" :key="idx">
						<td>{{ row.requirement }}</td>
						<td>{{ row.department }}</td>
						<td>{{ row.source_origin }}</td>
						<td class="pln-num">{{ row.quantity_display }}</td>
						<td>{{ row.required_by_display }}</td>
						<td>{{ row.budget_line }}</td>
						<td class="pln-num">{{ row.amount_display }}</td>
					</tr>
				</tbody>
			</table>
			<p class="pln-table-caption">{{ item.sources_caption }}</p>
		</div>

		<!-- procurement package -->
		<div class="kt-card kt-blueprint pln-card-pad" data-testid="ppi-package">
			<i class="kt-corner tl"></i><i class="kt-corner tr"></i>
			<i class="kt-corner bl"></i><i class="kt-corner br"></i>
			<div class="kt-card-title">Procurement package</div>
			<div class="pln-field-grid">
				<div class="pln-field" style="grid-column: 1 / -1">
					<label for="ppi-title">Plan Item title</label>
					<input id="ppi-title" class="kt-input" data-testid="ppi-title" v-model="form.title" />
				</div>
				<div class="pln-field" style="grid-column: 1 / -1">
					<label for="ppi-description">Procurement description</label>
					<textarea
						id="ppi-description" class="kt-input" data-testid="ppi-description"
						v-model="form.description"
					></textarea>
				</div>
				<div class="pln-ro-field">
					<label>Requirement type</label><div class="pln-val">{{ item.item?.requirement_type }}</div>
				</div>
				<div class="pln-field">
					<label for="ppi-objective">Strategic Objective</label>
					<select id="ppi-objective" class="kt-input" data-testid="ppi-objective" v-model="form.strategic_objective">
						<option value="">Select…</option>
						<option v-for="row in item.strategic_objectives" :key="row.id" :value="row.id">
							{{ row.title }}
						</option>
					</select>
				</div>
				<div class="pln-ro-field" style="grid-column: 1 / -1" v-if="item.item?.objective_path">
					<label>Objective path</label><div class="pln-val">{{ item.item.objective_path }}</div>
				</div>
				<div class="pln-ro-field"><label>Procurement method</label><div class="pln-val">{{ item.item?.procurement_method }}</div></div>
				<div class="pln-field" style="grid-column: 1 / -1" v-if="item.combined">
					<label for="ppi-aggregation">Aggregation reason</label>
					<textarea
						id="ppi-aggregation" class="kt-input" data-testid="ppi-aggregation"
						v-model="form.aggregation_reason"
					></textarea>
				</div>
			</div>
		</div>

		<!-- planned schedule -->
		<div class="kt-card kt-blueprint pln-card-pad" data-testid="ppi-schedule">
			<i class="kt-corner tl"></i><i class="kt-corner tr"></i>
			<i class="kt-corner bl"></i><i class="kt-corner br"></i>
			<div class="kt-card-title">Planned schedule</div>
			<div class="pln-field-grid">
				<div class="pln-field" v-for="field in SCHEDULE_FIELDS" :key="field.key">
					<label :for="`ppi-${field.key}`">{{ field.label }}</label>
					<input
						:id="`ppi-${field.key}`" type="date" class="kt-input"
						:data-testid="`ppi-${field.key}`"
						v-model="form[field.key]"
					/>
				</div>
			</div>
		</div>

		<div class="pln-footer-bar">
			<div>
				<button class="kt-btn kt-btn-ghost" @click="$emit('back')">Back to Annual Plan</button>
				<button
					v-if="item.mutable"
					class="kt-btn kt-btn-ghost"
					data-testid="ppi-dissolve"
					:disabled="pending"
					@click="$emit('dissolve')"
				>
					Dissolve Plan Item
				</button>
			</div>
			<div class="pln-footer-actions">
				<button
					v-if="item.mutable"
					class="kt-btn kt-btn-secondary"
					data-testid="ppi-save"
					:disabled="pending"
					@click="$emit('save', { ...form })"
				>
					Save draft
				</button>
				<button
					v-if="item.mutable && item.header?.finance_state_badge !== 'Confirmed'"
					class="kt-btn kt-btn-primary"
					data-testid="ppi-request-finance"
					:disabled="pending"
					@click="$emit('request-finance')"
				>
					Request Finance confirmation
				</button>
			</div>
		</div>
	</div>
</template>

<script setup>
import { computed, reactive, watch } from "vue";

const props = defineProps({
	item: { type: Object, default: () => ({}) },
	pending: Boolean,
	errorSummary: String,
});

defineEmits(["save", "dissolve", "back", "request-finance"]);

const SCHEDULE_FIELDS = [
	{ key: "invitation_date", label: "Invitation or advertisement" },
	{ key: "bid_opening_date", label: "Bid opening" },
	{ key: "evaluation_completion_date", label: "Evaluation completion" },
	{ key: "award_approval_date", label: "Tender award approval" },
	{ key: "award_notification_date", label: "Notification of award" },
	{ key: "contract_signing_date", label: "Contract signing" },
	{ key: "delivery_completion_date", label: "Delivery or implementation completion" },
];

const source = computed(() => (props.item.sources || [])[0] || null);

function blank() {
	const schedule = {};
	for (const field of SCHEDULE_FIELDS) schedule[field.key] = "";
	return {
		title: "", description: "", strategic_objective: "", aggregation_reason: "", ...schedule,
	};
}

const form = reactive(blank());

function hydrate() {
	const fields = blank();
	Object.assign(fields, {
		title: props.item.item?.title || "",
		description: props.item.item?.description || "",
		strategic_objective: props.item.item?.strategic_objective || "",
		aggregation_reason: props.item.item?.aggregation_reason || "",
	});
	for (const field of SCHEDULE_FIELDS) {
		fields[field.key] = props.item.schedule?.[field.key] || "";
	}
	Object.assign(form, fields);
}

watch(() => props.item.plan_item_id, hydrate, { immediate: true });
</script>
