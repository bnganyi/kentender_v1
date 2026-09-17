<!-- PLN-CHG-001 v1.18 §9.3/§12.8 U09 Plan Item editor, ported class-for-class
     from U09 (default + CONFIG-missing method notice), U09-eligibility-lots,
     U09-schedule-expanded, U09-conditional-method, U09-feasibility-fail and
     U09-locked (one route, `/app/procurement-plan-item/{plan_item_id}`, for
     every state — §9's own table lists "scope lock" as one of this same
     screen's states, not a separate one). Five sections in the frame's own
     order: Requirement and sources, Package details, Method and eligibility,
     Reservation and structure, Baseline schedule.

     §17.4 removed concepts this row does not rebuild: Plan horizon,
     Aggregation and Lotting are read-only facts here (spec line ~1265 calls
     Plan horizon "read-only" explicitly; nothing in the frame or spec offers
     a control for any of the three) — only "Lot count" stays editable, and
     only once already "Packaged into lots". The v1.12 reservation-reason /
     highest-advantage override UI, the multi-year justification textarea and
     the county-resident checkbox are gone: "No highest-advantage ranking or
     override reason" (spec line 1265) and no v1.18 frame shows any of them. -->
<template>
	<div class="pln-editor pln-editor-wide">
		<p class="kt-page-kicker">{{ item.header?.eyebrow }}</p>
		<h1 class="kt-page-title">{{ item.header?.title }}</h1>
		<p class="pln-quiet-ref">{{ item.header?.reference_line }}</p>
		<span class="kt-status" :class="badgeClass" data-testid="ppi-badge">{{ item.header?.item_state_badge }}</span>

		<div v-if="item.source_correction_required" class="pln-notice is-critical" data-testid="ppi-source-correction">
			<p class="pln-notice-title">Source correction required</p>
			<p>
				A departmental source changed. Dissolve this Plan Item and re-form it
				from the current source before continuing.
			</p>
		</div>

		<!-- §9.7 domain notices: scope lock, correction hold -->
		<div
			v-for="notice in item.notices || []"
			:key="notice.kind"
			class="pln-notice is-attention"
			:data-testid="`ppi-notice-${notice.kind}`"
		>
			<p class="pln-notice-title">{{ notice.heading }}</p>
			<p>{{ notice.text }}</p>
			<div v-if="notice.kind === 'scope_locked'" class="pln-facts-row" style="margin-top: 8px">
				<div class="pln-fact"><span class="kt-label">Requisition</span><span class="pln-fact-val">{{ scopeLock.first_requisition }}</span></div>
				<div class="pln-fact"><span class="kt-label">Date</span><span class="pln-fact-val">{{ scopeLockSinceDisplay }}</span></div>
			</div>
		</div>

		<div v-if="errorSummary" class="pln-notice is-critical" role="alert" data-testid="ppi-error">
			<p class="pln-notice-title">This command could not be completed</p>
			<p>{{ errorSummary }}</p>
		</div>

		<!-- Requirement and sources -->
		<div class="kt-card kt-blueprint pln-card-pad" data-testid="ppi-sources">
			<i class="kt-corner tl"></i><i class="kt-corner tr"></i>
			<i class="kt-corner bl"></i><i class="kt-corner br"></i>
			<div class="kt-card-title">Requirement and sources</div>
			<table class="pln-table">
				<thead>
					<tr>
						<th>Source</th><th>Department</th>
						<th class="pln-num">Quantity</th><th>Unit</th>
						<th>Required by</th><th>Procurement Budget Line</th>
						<th class="pln-num">{{ scopeLock.locked ? "Original allowance" : "Amount" }}</th>
					</tr>
				</thead>
				<tbody>
					<tr v-for="(row, idx) in item.sources" :key="idx">
						<td>{{ row.need_reference_line || row.requirement }}</td>
						<td>{{ row.department }}</td>
						<td class="pln-num">{{ row.quantity_number }}</td>
						<td>{{ row.unit_label }}</td>
						<td>{{ row.required_by_display }}</td>
						<td>{{ row.budget_line_display }}</td>
						<td class="pln-num">{{ row.amount_display }}</td>
					</tr>
				</tbody>
			</table>
			<p v-if="item.sources_caption" class="pln-table-caption">{{ item.sources_caption }}</p>
			<p class="pln-helper-text" data-testid="ppi-price-index">{{ priceIndexLine }}</p>
		</div>

		<!-- Package details -->
		<div class="kt-card kt-blueprint pln-card-pad" data-testid="ppi-package">
			<i class="kt-corner tl"></i><i class="kt-corner tr"></i>
			<i class="kt-corner bl"></i><i class="kt-corner br"></i>
			<div class="kt-card-title">Package details</div>
			<div class="pln-field-grid">
				<div class="pln-field" style="grid-column: 1 / -1">
					<label for="ppi-title">Package title</label>
					<input id="ppi-title" type="text" class="kt-input" data-testid="ppi-title" v-model="form.title" :disabled="!item.mutable" />
				</div>
				<div class="pln-field" style="grid-column: 1 / -1">
					<label for="ppi-description">Package description</label>
					<textarea id="ppi-description" class="kt-input" rows="3" data-testid="ppi-description" v-model="form.description" :disabled="!item.mutable"></textarea>
				</div>
				<div class="pln-field" style="grid-column: 1 / -1">
					<label for="ppi-objective">Strategic Objective</label>
					<select id="ppi-objective" class="kt-input" data-testid="ppi-objective" v-model="form.strategic_objective" :disabled="!item.mutable" :aria-invalid="invalid('strategic_objective')">
						<option value="">Select…</option>
						<option v-for="row in classification.strategic_objectives || []" :key="row.id" :value="row.id">
							{{ row.reference ? `${row.reference} — ${row.title}` : row.title }}
						</option>
					</select>
					<p class="pln-helper-text">{{ objectivePath }}</p>
				</div>
				<div v-if="item.combined" class="pln-field" style="grid-column: 1 / -1">
					<label for="ppi-aggregation">Aggregation reason</label>
					<textarea id="ppi-aggregation" class="kt-input" rows="2" data-testid="ppi-aggregation" v-model="form.aggregation_reason" :disabled="!item.mutable" :aria-invalid="invalid('aggregation_reason')"></textarea>
				</div>
				<div class="pln-field" style="grid-column: 1 / -1">
					<label for="ppi-estimate-basis">Estimate basis</label>
					<textarea id="ppi-estimate-basis" class="kt-input" rows="2" data-testid="ppi-estimate-basis" v-model="form.estimate_basis" :disabled="!item.mutable" :aria-invalid="invalid('estimate_basis')"></textarea>
					<p class="pln-helper-text">The market survey used and which incidental costs are included.</p>
				</div>
				<div class="pln-field">
					<label for="ppi-estimate-basis-reference">Estimate basis reference</label>
					<input id="ppi-estimate-basis-reference" type="text" class="kt-input" data-testid="ppi-estimate-basis-reference" v-model="form.estimate_basis_reference" :disabled="!item.mutable" :aria-invalid="invalid('estimate_basis_reference')" />
				</div>
			</div>
			<div class="pln-facts-row" style="margin-top: 12px">
				<div class="pln-fact"><span class="kt-label">Quantity</span><span class="pln-fact-val">{{ item.total_quantity_display }}</span></div>
				<div class="pln-fact"><span class="kt-label">Value</span><span class="pln-fact-val">{{ item.planned_value_display }}</span></div>
			</div>
		</div>

		<!-- Method and eligibility -->
		<div v-if="!classification.reference_available" class="kt-card kt-blueprint pln-card-pad" data-testid="ppi-method-config-missing" style="border-color: var(--status-attention, #b45309)">
			<i class="kt-corner tl"></i><i class="kt-corner tr"></i>
			<i class="kt-corner bl"></i><i class="kt-corner br"></i>
			<div class="kt-card-title">Method and eligibility</div>
			<p class="pln-notice-title"><span class="kt-status is-attention">Procurement rules are not configured</span></p>
			<p>Required configuration is missing or incomplete. Draft work can continue where permitted; the affected submission is unavailable.</p>
		</div>
		<div v-else class="kt-card kt-blueprint pln-card-pad" data-testid="ppi-method-card">
			<i class="kt-corner tl"></i><i class="kt-corner tr"></i>
			<i class="kt-corner bl"></i><i class="kt-corner br"></i>
			<div class="kt-card-title">Method and eligibility</div>
			<div class="pln-facts-row" style="margin-bottom: 12px">
				<div class="pln-field">
					<label for="ppi-method">Method</label>
					<select id="ppi-method" class="kt-input" data-testid="ppi-method" v-model="form.procurement_method" :disabled="!item.mutable" :aria-invalid="invalid('procurement_method')">
						<option v-for="method in methodOptions" :key="method" :value="method">{{ method }}</option>
					</select>
				</div>
				<div class="pln-fact"><span class="kt-label">Procedure profile</span><span class="pln-fact-val">{{ procedureProfileLine }}</span></div>
				<div v-if="methodProfile.conditions?.length" class="pln-fact">
					<span class="kt-label">Conditions</span>
					<span class="kt-status" :class="methodProfile.evidence_complete ? 'is-live' : 'is-attention'">{{ methodProfile.evidence_complete ? "Complete" : "Evidence required" }}</span>
				</div>
			</div>
			<template v-if="methodProfile.conditions?.length">
				<h4 class="pln-section-label">Eligibility conditions</h4>
				<table class="pln-table" data-testid="ppi-conditions">
					<thead><tr><th>Condition</th><th>Value</th></tr></thead>
					<tbody>
						<tr v-for="row in methodProfile.conditions" :key="row.condition_id">
							<td>{{ row.description }}</td>
							<td>
								<span v-if="row.kind === 'Known fact'" class="kt-status" :class="row.result === 'Met' ? 'is-live' : 'is-critical'">{{ row.result }}</span>
								<span v-else class="kt-status" :class="row.result === 'Declared' ? 'is-live' : 'is-attention'">{{ row.result }}</span>
							</td>
						</tr>
					</tbody>
				</table>
			</template>
			<div v-for="row in declarationConditions" :key="row.condition_id" class="pln-field-grid" style="margin-top: 12px">
				<div class="pln-field" style="grid-column: 1 / -1">
					<label :for="`ppi-evidence-${row.condition_id}`">{{ (row.description || "").replace(/\.$/, "") }}</label>
					<input
						:id="`ppi-evidence-${row.condition_id}`" type="text" class="kt-input"
						:data-testid="`ppi-evidence-${row.condition_id}`"
						v-model="evidenceForm[row.condition_id].evidence_reference"
						:disabled="!item.mutable"
					/>
				</div>
				<div v-if="row.authorisation_actor" class="pln-fact">
					<span class="kt-label">Required specific authorisation</span><span class="pln-fact-val">{{ row.authorisation_actor }}</span>
				</div>
				<div v-if="row.authorisation_actor" class="pln-field">
					<label :for="`ppi-authorisation-${row.condition_id}`">Authorisation reference</label>
					<input
						:id="`ppi-authorisation-${row.condition_id}`" type="text" class="kt-input"
						:data-testid="`ppi-authorisation-${row.condition_id}`"
						v-model="evidenceForm[row.condition_id].authorisation_reference"
						:disabled="!item.mutable"
					/>
				</div>
			</div>
		</div>

		<!-- Reservation and structure -->
		<div class="kt-card kt-blueprint pln-card-pad" data-testid="ppi-preference">
			<i class="kt-corner tl"></i><i class="kt-corner tr"></i>
			<i class="kt-corner bl"></i><i class="kt-corner br"></i>
			<div class="kt-card-title">{{ preference.lotting_indicator === "Packaged into lots" ? "Structure — Packaged into lots" : "Reservation and structure" }}</div>
			<div class="pln-facts-row" style="margin-bottom: 12px">
				<div class="pln-field" style="max-width: 220px">
					<label for="ppi-reservation">Planned reservation</label>
					<select id="ppi-reservation" class="kt-input" data-testid="ppi-reservation" v-model="form.reservation_category" :disabled="!item.mutable" :aria-invalid="invalid('reservation_category')">
						<option v-for="category in reservationOptions" :key="category" :value="category">{{ category }}</option>
					</select>
				</div>
				<div class="pln-fact"><span class="kt-label">Mandatory restrictions</span><span class="pln-fact-val">{{ preference.mandatory_restrictions_line }}</span></div>
				<div class="pln-fact"><span class="kt-label">Plan horizon</span><span class="pln-fact-val">{{ preference.plan_horizon }}</span></div>
			</div>
			<div class="pln-facts-row">
				<div class="pln-fact"><span class="kt-label">Aggregation</span><span class="pln-fact-val">{{ preference.aggregation_indicator }}</span></div>
				<div class="pln-fact"><span class="kt-label">Lotting</span><span class="pln-fact-val">{{ preference.lotting_indicator }}</span></div>
				<div v-if="preference.lotting_indicator === 'Packaged into lots'" class="pln-field" style="max-width: 120px">
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
				<thead><tr><th>Milestone</th><th>Baseline</th></tr></thead>
				<tbody>
					<tr v-for="row in computedRows" :key="row.milestone" :data-testid="`ppi-baseline-${row.milestone}`">
						<td>{{ row.label }}</td>
						<td>{{ row.display }}</td>
					</tr>
				</tbody>
			</table>
			<div class="pln-facts-row" style="margin: 12px 0">
				<div class="pln-fact"><span class="kt-label">Estimated delivery / implementation period</span><span class="pln-fact-val">{{ deliveryPeriodDisplay }}</span></div>
				<div class="pln-fact"><span class="kt-label">Estimated completion</span><span class="pln-fact-val">{{ baseline.estimated_completion_display || display(computedDates.delivery_completion) }}</span></div>
				<div class="pln-fact"><span class="kt-label">Required by</span><span class="pln-fact-val">{{ requiredByDisplay }}</span></div>
				<div class="pln-fact"><span class="kt-label">Outcome</span><span class="kt-status" :class="deliveryBoundaryOk ? 'is-live' : 'is-critical'">{{ deliveryBoundaryOk ? "Within the required-by date" : "Estimated completion exceeds the required-by date" }}</span></div>
			</div>
			<p v-if="!deliveryBoundaryOk" class="pln-dialog-error" data-testid="ppi-boundary-warning">
				The computed contract signing date leaves too little time before the required-by date. Bring the target invitation date forward or shorten a period.
			</p>

			<div class="pln-disclosure">
				<button
					type="button"
					class="pln-disclosure-trigger btn btn-ghost"
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
import { formatDate } from "../data/format.js";

const props = defineProps({
	item: { type: Object, default: () => ({}) },
	pending: Boolean,
	errorSummary: String,
});

const emit = defineEmits(["save", "dissolve", "back"]);

const PERIODS = [
	{ key: "tendering_period_days", label: "Tendering", floor: "tendering_period_days" },
	{ key: "evaluation_period_days", label: "Evaluation", ceiling: "evaluation_period_days" },
	{ key: "award_approval_buffer_days", label: "Award approval buffer", assumption: true },
	{ key: "notification_buffer_days", label: "Notification buffer", assumption: true },
	{ key: "standstill_period_days", label: "Standstill", floor: "standstill_period_days" },
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

const identity = computed(() => props.item.identity || {});
const classification = computed(() => props.item.classification || {});
const methodProfile = computed(() => classification.value.method_profile || {});
const preference = computed(() => props.item.preference || {});
const baseline = computed(() => props.item.baseline || {});
const scopeLock = computed(() => props.item.scope_lock || {});
const periodsOpen = ref(false);

const badgeClass = computed(() => (props.item.is_active ? "is-live" : "is-draft"));
const scopeLockSinceDisplay = computed(() => formatDate(scopeLock.value.since));

const priceIndexLine = computed(() => (props.item.market_price_index || {}).helper || "");
const requiredByDisplay = computed(() => (props.item.sources || [])[0]?.required_by_display || "—");
const deliveryPeriodDisplay = computed(() => {
	const days = baseline.value.estimated_delivery_period_days;
	return days == null ? "—" : `${days} Calendar days`;
});

const procedureProfileLine = computed(() => {
	const profile = methodProfile.value;
	return profile.found ? `${profile.profile}, Version ${profile.version_number}` : "";
});

// §12.8 — "Do not invent universal checkboxes for every method." Evidence
// inputs render only for the Declaration-kind conditions this method's own
// profile actually names, never a generic control offered for every method.
const declarationConditions = computed(() => (methodProfile.value.conditions || []).filter((c) => c.kind !== "Known fact"));

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

const form = reactive({
	title: "",
	description: "",
	strategic_objective: "",
	aggregation_reason: "",
	estimate_basis: "",
	estimate_basis_reference: "",
	procurement_method: "",
	reservation_category: "None",
	lot_count: null,
	baseline_invitation_date: "",
	tendering_period_days: null,
	evaluation_period_days: null,
	award_approval_buffer_days: null,
	notification_buffer_days: null,
	standstill_period_days: null,
});

const evidenceForm = reactive({});

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
		estimate_basis: cls.estimate_basis || "",
		estimate_basis_reference: cls.estimate_basis_reference || "",
		procurement_method: cls.procurement_method || cls.proposed_method || "",
		reservation_category: pref.reservation_category || "None",
		lot_count: pref.lot_count || null,
		baseline_invitation_date: base.target_invitation_date || "",
	});
	for (const period of PERIODS) {
		form[period.key] = periods[period.key] || defaults[period.key] || 0;
	}
	for (const key of Object.keys(evidenceForm)) delete evidenceForm[key];
	const existing = new Map((cls.method_condition_evidence || []).map((row) => [row.condition_id, row]));
	for (const condition of (cls.method_profile || {}).conditions || []) {
		if (condition.kind === "Known fact") continue;
		const given = existing.get(condition.condition_id) || {};
		evidenceForm[condition.condition_id] = {
			evidence_reference: given.evidence_reference || "",
			authorisation_reference: given.authorisation_reference || "",
		};
	}
	periodsOpen.value = false;
}

watch(
	() => props.item,
	(item, previous) => {
		// An in-place refresh that returns the same item at the same record
		// version carries nothing new — re-hydrating would discard what the
		// user has typed since.
		if (
			previous &&
			(previous.plan_item_id ?? null) === (item?.plan_item_id ?? null) &&
			(previous.record_version ?? null) === (item?.record_version ?? null)
		) {
			return;
		}
		hydrate();
	},
	{ immediate: true }
);

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
		estimate_basis: form.estimate_basis,
		estimate_basis_reference: form.estimate_basis_reference,
		procurement_method: form.procurement_method,
		reservation_category: form.reservation_category,
		baseline_invitation_date: form.baseline_invitation_date,
	};
	for (const period of PERIODS) values[period.key] = Number(form[period.key]);
	if (props.item.combined) values.aggregation_reason = form.aggregation_reason;
	if (preference.value.lotting_indicator === "Packaged into lots") values.lot_count = Number(form.lot_count) || 0;
	const evidenceRows = Object.entries(evidenceForm)
		.filter(([, row]) => row.evidence_reference || row.authorisation_reference)
		.map(([condition_id, row]) => ({ condition_id, ...row }));
	if (evidenceRows.length) values.method_condition_evidence = evidenceRows;
	emit("save", values);
}
</script>
