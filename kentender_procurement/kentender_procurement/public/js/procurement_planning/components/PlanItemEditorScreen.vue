<!-- PLN-UI-09 Plan Item editor (§12.8), rendering PLN-DES-09 (single source)
     and PLN-DES-09A (combined) from one read model: read-only source card or
     table, Identity, Classification and method (Objective + admissible
     method selects), Preference and structure (with the conditional
     multi-year justification and lot count), and the Baseline schedule card
     whose computed dates recalculate live from the target invitation date
     and the five governed periods behind a closed-by-default disclosure.
     No Finance action, no forecast or actual field, no source edit. -->
<template>
	<div class="pln-editor pln-editor-wide">
		<p class="kt-page-kicker">{{ item.header?.eyebrow }}</p>
		<h1 class="kt-page-title">{{ item.header?.title }}</h1>
		<p class="pln-quiet-ref">{{ item.header?.reference_line }}</p>
		<span class="kt-status is-draft" data-testid="ppi-badge">{{ item.header?.item_state_badge }}</span>

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
		<div v-if="!item.combined" class="kt-card kt-blueprint pln-card-pad" data-testid="ppi-source">
			<i class="kt-corner tl"></i><i class="kt-corner tr"></i>
			<i class="kt-corner bl"></i><i class="kt-corner br"></i>
			<div class="kt-card-title">Departmental source</div>
			<div v-if="source" class="pln-field-grid">
				<div class="pln-ro-field"><label>Department</label><div class="pln-val">{{ source.department }}</div></div>
				<div class="pln-ro-field"><label>Source origin</label><div class="pln-val">{{ source.source_origin }}</div></div>
				<div class="pln-ro-field"><label>Departmental plan</label><div class="pln-val">{{ source.departmental_plan_line }}</div></div>
				<div v-if="source.need_reference_line" class="pln-ro-field">
					<label>Accepted Need</label><div class="pln-val">{{ source.need_reference_line }}</div>
				</div>
				<div class="pln-ro-field"><label>Quantity</label><div class="pln-val">{{ source.quantity_display }}</div></div>
				<div class="pln-ro-field"><label>Required by</label><div class="pln-val">{{ source.required_by_display }}</div></div>
				<div class="pln-ro-field"><label>Procurement Budget Line</label><div class="pln-val">{{ source.budget_line_display }}</div></div>
				<div class="pln-ro-field"><label>Planned value</label><div class="pln-val">{{ item.planned_value_display }}</div></div>
			</div>
			<p class="pln-helper-text" data-testid="ppi-price-index">{{ priceIndexLine }}</p>
		</div>

		<!-- combined sources -->
		<div v-else class="kt-card kt-blueprint pln-card-pad" data-testid="ppi-sources">
			<i class="kt-corner tl"></i><i class="kt-corner tr"></i>
			<i class="kt-corner bl"></i><i class="kt-corner br"></i>
			<div class="kt-card-title">Departmental sources</div>
			<table class="pln-table">
				<thead>
					<tr>
						<th>Requirement</th><th>Department</th><th>Source origin</th>
						<th class="pln-num">Quantity</th><th>Required by</th>
						<th>Procurement Budget Line</th><th class="pln-num">Amount</th>
					</tr>
				</thead>
				<tbody>
					<tr v-for="(row, idx) in item.sources" :key="idx">
						<td>{{ row.requirement }}</td>
						<td>{{ row.department }}</td>
						<td>{{ row.source_origin }}</td>
						<td class="pln-num">{{ row.quantity_display }}</td>
						<td>{{ row.required_by_display }}</td>
						<td>{{ row.budget_line_display?.split(" — ")[0] || row.budget_line }}</td>
						<td class="pln-num">{{ row.amount_display }}</td>
					</tr>
				</tbody>
			</table>
			<p class="pln-table-caption">{{ item.sources_caption }}</p>
			<p class="pln-helper-text" data-testid="ppi-price-index">{{ priceIndexLine }}</p>
		</div>

		<!-- Identity -->
		<div class="kt-card kt-blueprint pln-card-pad" data-testid="ppi-identity">
			<i class="kt-corner tl"></i><i class="kt-corner tr"></i>
			<i class="kt-corner bl"></i><i class="kt-corner br"></i>
			<div class="kt-card-title">Identity</div>
			<div class="pln-field-grid">
				<div class="pln-field" style="grid-column: 1 / -1">
					<label for="ppi-title">Plan Item title</label>
					<input id="ppi-title" type="text" class="kt-input" data-testid="ppi-title" v-model="form.title" :disabled="!item.mutable" />
				</div>
				<div class="pln-field" style="grid-column: 1 / -1">
					<label for="ppi-description">Procurement description</label>
					<textarea id="ppi-description" class="kt-input" rows="3" data-testid="ppi-description" v-model="form.description" :disabled="!item.mutable"></textarea>
				</div>
				<div class="pln-ro-field">
					<label>Requirement type</label><div class="pln-val">{{ identity.requirement_type }}</div>
				</div>
				<div v-if="item.combined" class="pln-field" style="grid-column: 1 / -1">
					<label for="ppi-aggregation">Aggregation reason</label>
					<textarea id="ppi-aggregation" class="kt-input" rows="2" data-testid="ppi-aggregation" v-model="form.aggregation_reason" :disabled="!item.mutable" :aria-invalid="invalid('aggregation_reason')"></textarea>
				</div>
			</div>
		</div>

		<!-- Classification and method -->
		<div class="kt-card kt-blueprint pln-card-pad" data-testid="ppi-classification">
			<i class="kt-corner tl"></i><i class="kt-corner tr"></i>
			<i class="kt-corner bl"></i><i class="kt-corner br"></i>
			<div class="kt-card-title">Classification and method</div>
			<div class="pln-field-grid">
				<div class="pln-field">
					<label for="ppi-objective">Strategic Objective</label>
					<select id="ppi-objective" class="kt-input" data-testid="ppi-objective" v-model="form.strategic_objective" :disabled="!item.mutable" :aria-invalid="invalid('strategic_objective')">
						<option value="">Select…</option>
						<option v-for="row in classification.strategic_objectives || []" :key="row.id" :value="row.id">
							{{ row.reference ? `${row.reference} — ${row.title}` : row.title }}
						</option>
					</select>
				</div>
				<div class="pln-ro-field">
					<label>Objective path</label><div class="pln-val">{{ objectivePath }}</div>
				</div>
				<div class="pln-field">
					<label for="ppi-method">Procurement method</label>
					<select id="ppi-method" class="kt-input" data-testid="ppi-method" v-model="form.procurement_method" :disabled="!item.mutable" :aria-invalid="invalid('procurement_method')">
						<option v-for="method in methodOptions" :key="method" :value="method">{{ method }}</option>
					</select>
				</div>
				<div class="pln-ro-field">
					<label>Value band</label><div class="pln-val" data-testid="ppi-value-band">{{ classification.value_band }}</div>
				</div>
			</div>
		</div>

		<!-- Preference and structure -->
		<div class="kt-card kt-blueprint pln-card-pad" data-testid="ppi-preference">
			<i class="kt-corner tl"></i><i class="kt-corner tr"></i>
			<i class="kt-corner bl"></i><i class="kt-corner br"></i>
			<div class="kt-card-title">Preference and structure</div>
			<div class="pln-field-grid">
				<div class="pln-field" style="grid-column: 1 / -1">
					<label for="ppi-reservation">Preference and reservation</label>
					<select id="ppi-reservation" class="kt-input" data-testid="ppi-reservation" v-model="form.reservation_category" :disabled="!item.mutable" :aria-invalid="invalid('reservation_category')">
						<option v-for="category in reservationOptions" :key="category" :value="category">{{ category }}</option>
					</select>
					<p class="pln-helper-text">{{ preference.helper }}</p>
				</div>
				<div v-if="reasonRequired" class="pln-field" style="grid-column: 1 / -1">
					<label for="ppi-reservation-reason">Reservation reason</label>
					<textarea id="ppi-reservation-reason" class="kt-input" rows="2" data-testid="ppi-reservation-reason" v-model="form.reservation_category_reason" :disabled="!item.mutable" :aria-invalid="invalid('reservation_category_reason')"></textarea>
					<p class="pln-helper-text">Why this scheme rather than {{ preference.highest_advantage }}, the highest-advantage scheme published for this year.</p>
				</div>
				<div v-if="preference.county_control_available" class="pln-field" style="grid-column: 1 / -1">
					<label class="pln-checkbox-row">
						<input type="checkbox" data-testid="ppi-county" v-model="form.county_resident_reservation" :disabled="!item.mutable" />
						Reserved for county-resident tenderers
					</label>
				</div>
				<div class="pln-field">
					<label for="ppi-horizon">Plan horizon</label>
					<select id="ppi-horizon" class="kt-input" data-testid="ppi-horizon" v-model="form.plan_horizon" :disabled="!item.mutable">
						<option value="Single year">Single year</option>
						<option value="Multi-year">Multi-year</option>
					</select>
				</div>
				<div class="pln-field">
					<label for="ppi-aggregation-indicator">Aggregation</label>
					<select id="ppi-aggregation-indicator" class="kt-input" data-testid="ppi-aggregation-indicator" v-model="form.aggregation_indicator" :disabled="!item.mutable">
						<option value="Not aggregated">Not aggregated</option>
						<option value="Aggregated into this package">Aggregated into this package</option>
						<option value="Common-user item arrangement">Common-user item arrangement</option>
					</select>
				</div>
				<div class="pln-field">
					<label for="ppi-lotting">Lotting</label>
					<select id="ppi-lotting" class="kt-input" data-testid="ppi-lotting" v-model="form.lotting_indicator" :disabled="!item.mutable">
						<option value="Single lot">Single lot</option>
						<option value="Packaged into lots">Packaged into lots</option>
					</select>
				</div>
				<div v-if="form.plan_horizon === 'Multi-year'" class="pln-field" style="grid-column: 1 / -1">
					<label for="ppi-multi-year">Multi-year justification</label>
					<textarea id="ppi-multi-year" class="kt-input" rows="2" data-testid="ppi-multi-year" v-model="form.multi_year_justification" :disabled="!item.mutable" :aria-invalid="invalid('multi_year_justification')"></textarea>
				</div>
				<div v-if="form.lotting_indicator === 'Packaged into lots'" class="pln-field">
					<label for="ppi-lot-count">Lot count</label>
					<input id="ppi-lot-count" type="number" min="2" step="1" class="kt-input" data-testid="ppi-lot-count" v-model="form.lot_count" :disabled="!item.mutable" :aria-invalid="invalid('lot_count')" />
				</div>
			</div>
		</div>

		<!-- Baseline schedule -->
		<div class="kt-card kt-blueprint pln-card-pad" data-testid="ppi-baseline">
			<i class="kt-corner tl"></i><i class="kt-corner tr"></i>
			<i class="kt-corner bl"></i><i class="kt-corner br"></i>
			<div class="kt-card-title">Baseline schedule</div>
			<p class="pln-card-subhead">
				Computed from your target invitation date using the governed periods for this
				procurement's category and method. Locked once this Plan Version is submitted.
			</p>

			<div class="pln-field" style="max-width: 280px">
				<label for="ppi-target-date">Target invitation date</label>
				<input id="ppi-target-date" type="date" class="kt-input" data-testid="ppi-target-date" v-model="form.baseline_invitation_date" :disabled="!item.mutable || baseline.locked" :aria-invalid="invalid('baseline_invitation_date')" />
			</div>

			<table class="pln-table pln-baseline-table" style="margin-top: 16px" data-testid="ppi-baseline-table">
				<thead><tr><th>Milestone</th><th>Baseline date</th></tr></thead>
				<tbody>
					<tr v-for="row in computedRows" :key="row.milestone" :data-testid="`ppi-baseline-${row.milestone}`">
						<td>{{ row.label }}</td>
						<td>{{ row.display }}</td>
					</tr>
				</tbody>
			</table>
			<p class="pln-helper-text">
				Delivery completion is the department's own required-by date. The computed contract
				signing date must leave a reasonable delivery period before it.
			</p>
			<p v-if="!deliveryBoundaryOk" class="pln-dialog-error" data-testid="ppi-boundary-warning">
				The computed contract signing date leaves too little time before the required-by date. Bring the target invitation date forward or shorten a period.
			</p>

			<div class="pln-disclosure">
				<button
					type="button"
					class="pln-disclosure-trigger"
					data-testid="ppi-adjust-periods"
					:aria-expanded="periodsOpen ? 'true' : 'false'"
					@click="periodsOpen = !periodsOpen"
				>
					<svg class="pln-chevron" :class="{ open: periodsOpen }" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M9 6l6 6-6 6"/></svg>
					Adjust periods
				</button>
				<p v-if="!periodsOpen" class="pln-disclosure-summary" data-testid="ppi-periods-summary">{{ periodsSummary }}</p>
				<div v-else class="pln-periods-grid" data-testid="ppi-periods">
					<div v-for="period in PERIODS" :key="period.key" class="pln-field">
						<label :for="`ppi-${period.key}`">{{ period.label }}</label>
						<input :id="`ppi-${period.key}`" type="number" min="0" step="1" class="kt-input" :data-testid="`ppi-${period.key}`" v-model.number="form[period.key]" :disabled="!item.mutable || baseline.locked" :aria-invalid="invalid(period.key)" />
						<p class="pln-period-note">{{ periodNote(period) }}</p>
					</div>
				</div>
			</div>
		</div>

		<div class="pln-footer-bar">
			<div class="pln-footer-actions">
				<button type="button" class="kt-btn kt-btn-ghost" @click="$emit('back')">Back to Annual Plan</button>
				<button
					v-if="item.mutable"
					type="button"
					class="kt-btn kt-btn-secondary"
					data-testid="ppi-dissolve"
					:disabled="pending"
					@click="$emit('dissolve')"
				>
					Dissolve Plan Item
				</button>
			</div>
			<button
				v-if="item.mutable"
				type="button"
				class="kt-btn kt-btn-primary"
				data-testid="ppi-save"
				:disabled="pending"
				@click="save"
			>
				Save draft
			</button>
		</div>
	</div>
</template>

<script setup>
import { computed, reactive, ref, watch } from "vue";

const props = defineProps({
	item: { type: Object, default: () => ({}) },
	pending: Boolean,
	errorSummary: String,
});

const emit = defineEmits(["save", "dissolve", "back"]);

const PERIODS = [
	{ key: "tendering_period_days", label: "Tendering period", floor: "tendering_period_days" },
	{ key: "evaluation_period_days", label: "Evaluation period", ceiling: "evaluation_period_days" },
	{ key: "award_approval_buffer_days", label: "Award approval buffer", assumption: true },
	{ key: "notification_buffer_days", label: "Notification buffer", assumption: true },
	{ key: "standstill_period_days", label: "Standstill period", floor: "standstill_period_days" },
];

const MILESTONES = [
	["invitation", "Invitation or advertisement"],
	["bid_opening", "Bid opening"],
	["evaluation_completion", "Evaluation completion"],
	["award_approval", "Tender award approval"],
	["award_notification", "Notification of award"],
	["contract_signing", "Contract signing"],
	["delivery_completion", "Delivery or implementation completion"],
];

const MIN_IMPLEMENTATION_ALLOWANCE_DAYS = 7;

const source = computed(() => (props.item.sources || [])[0] || null);
const identity = computed(() => props.item.identity || {});
const classification = computed(() => props.item.classification || {});
const preference = computed(() => props.item.preference || {});
const baseline = computed(() => props.item.baseline || {});
const periodsOpen = ref(false);

const priceIndexLine = computed(() => (props.item.market_price_index || {}).helper || "");

const objectivePath = computed(() => {
	const selected = (classification.value.strategic_objectives || []).find((row) => row.id === form.strategic_objective);
	return selected?.path_display || classification.value.objective_path || "";
});

// §12.8 — the eleven methods narrowed to the resolved band; the current value
// stays offered even when the band changed under it, so the refusal is visible.
const methodOptions = computed(() => {
	const admissible = classification.value.admissible_methods || [];
	const current = classification.value.procurement_method;
	return current && !admissible.includes(current) ? [current, ...admissible] : admissible;
});

const reservationOptions = computed(() => {
	const categories = preference.value.reservation_categories || [];
	return categories.includes("None") ? categories : ["None", ...categories];
});

const reasonRequired = computed(
	() => form.reservation_category && form.reservation_category !== "None" && preference.value.highest_advantage && form.reservation_category !== preference.value.highest_advantage
);

const form = reactive({
	title: "",
	description: "",
	strategic_objective: "",
	aggregation_reason: "",
	procurement_method: "",
	reservation_category: "None",
	reservation_category_reason: "",
	county_resident_reservation: false,
	plan_horizon: "Single year",
	multi_year_justification: "",
	aggregation_indicator: "Not aggregated",
	lotting_indicator: "Single lot",
	lot_count: null,
	baseline_invitation_date: "",
	tendering_period_days: null,
	evaluation_period_days: null,
	award_approval_buffer_days: null,
	notification_buffer_days: null,
	standstill_period_days: null,
});

function hydrate() {
	const item = props.item || {};
	const ident = item.identity || {};
	const cls = item.classification || {};
	const pref = item.preference || {};
	const base = item.baseline || {};
	const periods = base.periods || {};
	const defaults = base.defaults || {};
	Object.assign(form, {
		title: ident.title || "",
		description: ident.description || "",
		strategic_objective: cls.strategic_objective || "",
		aggregation_reason: ident.aggregation_reason || "",
		procurement_method: cls.procurement_method || cls.proposed_method || "",
		reservation_category: pref.reservation_category || "None",
		reservation_category_reason: pref.reservation_category_reason || "",
		county_resident_reservation: !!pref.county_resident_reservation,
		plan_horizon: pref.plan_horizon || "Single year",
		multi_year_justification: pref.multi_year_justification || "",
		aggregation_indicator: pref.aggregation_indicator || (item.combined ? "Aggregated into this package" : "Not aggregated"),
		lotting_indicator: pref.lotting_indicator || "Single lot",
		lot_count: pref.lot_count || null,
		baseline_invitation_date: base.target_invitation_date || "",
	});
	for (const period of PERIODS) {
		form[period.key] = periods[period.key] || defaults[period.key] || 0;
	}
	periodsOpen.value = false;
}

watch(() => props.item, hydrate, { immediate: true });

// --- live baseline computation (PLN-AC-115: recalculates before any save) ---

function addDays(iso, days) {
	if (!iso) return "";
	const [y, m, d] = iso.split("-").map(Number);
	const date = new Date(Date.UTC(y, m - 1, d + (Number(days) || 0)));
	return date.toISOString().slice(0, 10);
}

const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

function display(iso) {
	if (!iso) return "—";
	const [y, m, d] = iso.split("-").map(Number);
	return `${d} ${MONTHS[m - 1]} ${y}`;
}

const computedDates = computed(() => {
	const start = form.baseline_invitation_date;
	const bid = addDays(start, form.tendering_period_days);
	const evaluation = addDays(bid, form.evaluation_period_days);
	const award = addDays(evaluation, form.award_approval_buffer_days);
	const notification = addDays(award, form.notification_buffer_days);
	const signing = addDays(notification, form.standstill_period_days);
	const deliveryRow = (baseline.value.rows || []).find((r) => r.milestone === "delivery_completion");
	return {
		invitation: start,
		bid_opening: bid,
		evaluation_completion: evaluation,
		award_approval: award,
		award_notification: notification,
		contract_signing: signing,
		delivery_completion: deliveryRow?.date || "",
	};
});

const computedRows = computed(() =>
	MILESTONES.map(([milestone, label]) => ({
		milestone,
		label,
		display:
			milestone === "delivery_completion"
				? `${display(computedDates.value.delivery_completion)} · from the authorised Requisition`
				: display(computedDates.value[milestone]),
	}))
);

const deliveryBoundaryOk = computed(() => {
	const { contract_signing, delivery_completion } = computedDates.value;
	if (!contract_signing || !delivery_completion) return true; // nothing computed yet
	const gap = (Date.parse(delivery_completion) - Date.parse(contract_signing)) / 86_400_000;
	return gap >= MIN_IMPLEMENTATION_ALLOWANCE_DAYS;
});

const periodsSummary = computed(() => {
	const defaults = baseline.value.defaults || {};
	const usingDefaults = PERIODS.every((p) => Number(form[p.key]) === Number(defaults[p.key]));
	return usingDefaults ? baseline.value.defaults_line || "Using governed defaults" : "Adjusted from the governed defaults";
});

function periodNote(period) {
	const days = Number(form[period.key]) || 0;
	const floors = baseline.value.floors || {};
	const ceilings = baseline.value.ceilings || {};
	if (period.floor && floors[period.floor] != null) return `${days} days · minimum ${floors[period.floor]}`;
	if (period.ceiling && ceilings[period.ceiling] != null) return `${days} days · maximum ${ceilings[period.ceiling]}`;
	return `${days} days · governed default for this category and method, not a statutory figure`;
}

// PLN-AC-114 — a blocker names its input; the control carries aria-invalid
const invalidFields = computed(() => new Set((props.item.blockers || []).map((b) => b.field).filter(Boolean)));
function invalid(field) {
	return invalidFields.value.has(field) ? "true" : undefined;
}

function save() {
	const values = {
		title: form.title,
		description: form.description,
		strategic_objective: form.strategic_objective,
		procurement_method: form.procurement_method,
		reservation_category: form.reservation_category,
		plan_horizon: form.plan_horizon,
		aggregation_indicator: form.aggregation_indicator,
		lotting_indicator: form.lotting_indicator,
		baseline_invitation_date: form.baseline_invitation_date,
	};
	for (const period of PERIODS) values[period.key] = Number(form[period.key]);
	if (props.item.combined) values.aggregation_reason = form.aggregation_reason;
	if (reasonRequired.value) values.reservation_category_reason = form.reservation_category_reason;
	if (preference.value.county_control_available) values.county_resident_reservation = form.county_resident_reservation ? 1 : 0;
	if (form.plan_horizon === "Multi-year") values.multi_year_justification = form.multi_year_justification;
	if (form.lotting_indicator === "Packaged into lots") values.lot_count = Number(form.lot_count) || 0;
	emit("save", values);
}
</script>
