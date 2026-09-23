<!-- PLN-CHG-001 v1.24 §10.8 — the purchase editor (U09), ported from
     Artboards-U09.dc.html.

     This is the screen v1.22 cut hardest, and the cut is the point. The first
     view is Purchase details, Included requirements, Estimated cost,
     Procurement approach and Dates — the decisions the Planner actually makes.
     Strategy provenance, classification provenance, rule evidence and the
     milestone table go into one collapsed Supporting details.

     What must never appear as an ordinary business field: "Procedure —
     Planning example", resolver support or status, Rule version, Source check.
     A blocking configuration problem is replaced by one plain issue and the
     responsible recovery action (PLN22-AC-005). Blank, None, Not applicable,
     Single lot and Lot count 1 are omitted rather than displayed to prove the
     values exist (PLN22-AC-006).

     A material issue is never moved into Supporting details. -->
<template>
	<div>
		<div class="kt-page">
			<!-- The artboard's own head: the title, then one scope line naming
			     the purchase, its Plan Version and its state. This used to be a
			     three-cell `.kt-meta-row` of labelled facts, which the board
			     never draws here and which read as the screen's first section
			     rather than as the record's identity. -->
			<div class="kt-page-head">
				<div>
					<h1 class="kt-page-title" data-testid="ppi-title">{{ item.header?.title }}</h1>
					<div class="kt-page-scope" data-testid="ppi-context">
						<span>{{ item.plan_item_id }}</span>
						<span v-if="versionNumber">· Plan Version {{ versionNumber }}</span>
						<span class="kt-status" :class="item.is_active ? 'is-live' : 'is-draft'">{{ statusLabel }}</span>
					</div>
				</div>
			</div>

			<!-- Current material issues, immediately below the context and never
			     inside a disclosure. -->
			<div
				v-for="notice in notices"
				:key="notice.kind"
				class="kt-notice"
				:class="notice.kind === 'scope_locked' || notice.kind === 'correction_hold' ? 'is-critical' : 'is-warning'"
				data-testid="ppi-notice"
			>
				<svg class="kt-notice-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
					<path d="M12 3l9 16H3z"></path><path d="M12 10v4M12 17h.01"></path>
				</svg>
				<div class="kt-notice-body">
					<strong>{{ notice.heading }}</strong>
					<p>{{ notice.text }}</p>
				</div>
			</div>
			<div v-for="blocker in visibleBlockers" :key="blocker.message" class="kt-notice is-critical" data-testid="ppi-blocker">
				<svg class="kt-notice-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
					<path d="M12 3l9 16H3z"></path><path d="M12 10v4M12 17h.01"></path>
				</svg>
				<div class="kt-notice-body">{{ blocker.message }}</div>
			</div>

			<!-- 1. Purchase details -->
			<div class="kt-region">
				<h2>Purchase details</h2>
				<!-- The artboard's own form column: one field per line, a real
				     gap between them and a reading width. -->
				<div class="pln-form-column">
					<div class="kt-field" :class="flagged('title')">
						<label for="ppi-title-input" class="kt-label">Title</label>
						<input id="ppi-title-input" class="kt-input" data-testid="ppi-title-input" :value="draft.title" :disabled="!item.mutable" @input="onField('title', $event.target.value)">
					</div>
					<div class="kt-field" :class="flagged('description')">
						<label for="ppi-description" class="kt-label">Description</label>
						<textarea id="ppi-description" class="kt-input" rows="3" data-testid="ppi-description" :value="draft.description" :disabled="!item.mutable" @input="onField('description', $event.target.value)"></textarea>
					</div>
				</div>
				<div class="pln-summary-line">
					<!-- Derived from the included requirements; not editable here, and
					     Plan horizon is a fixed literal so it is not shown at all. -->
					<span class="kt-muted" data-testid="ppi-summary-line">{{ item.summary_line }}</span>
					<a href="#" class="kt-btn kt-btn-ghost" data-testid="ppi-view-classification" @click.prevent="$emit('view-classification')">View classification details</a>
				</div>
			</div>

			<!-- 2. Included requirements -->
			<div class="kt-region">
				<h2>Included requirements</h2>
				<table class="kt-table" data-testid="ppi-sources">
					<thead>
						<tr>
							<th>Requirement</th><th>Department</th><th class="is-num">Quantity</th>
							<th>Unit</th><th>Required by</th><th class="is-num">Allocation</th>
						</tr>
					</thead>
					<tbody>
						<tr v-for="row in sources" :key="row.requirement + row.department" data-testid="ppi-source-row">
							<td>{{ row.requirement }}</td>
							<td>{{ row.department }}</td>
							<td class="is-num">{{ row.quantity_number }}</td>
							<td>{{ row.unit_label }}</td>
							<td>{{ row.required_by_display }}</td>
							<td class="is-num">{{ row.amount_display }}</td>
						</tr>
					</tbody>
				</table>
				<div v-if="item.combined" class="pln-summary-line" data-testid="ppi-combined">
					<span>
						<span class="kt-tag kt-tag-neutral">Combined purchase</span>
						<span class="kt-muted">{{ item.aggregation_reason_preview }}</span>
					</span>
					<a href="#" data-testid="ppi-read-reason" @click.prevent="fullReason = !fullReason">Read full reason</a>
				</div>
				<p v-if="fullReason" class="kt-muted" data-testid="ppi-full-reason">{{ item.identity?.aggregation_reason }}</p>
			</div>

			<!-- 3. Estimated cost -->
			<div class="kt-region">
				<h2>Estimated cost</h2>
				<!-- The amount is derived from the included requirements, so it
				     reads as a fact; what the Planner writes — the basis and its
				     supporting document — are ordinary fields beneath it. All
				     three used to share one `.kt-meta-row`, which bottom-aligned
				     a two-line textarea against a one-line figure, sized every
				     control by its content and rendered the document reference
				     in the heading typeface (measured live, 23 Sep 2026). -->
				<div class="pln-fact">
					<span class="kt-label">Planned amount (KES)</span>
					<span class="kt-meta-value" data-testid="ppi-planned-value">{{ item.planned_value_display }}</span>
				</div>
				<div class="pln-form-column pln-region-gap">
					<div v-if="item.mutable" class="kt-field" :class="flagged('estimate_basis')">
						<label for="ppi-estimate-basis" class="kt-label">Estimate basis</label>
						<textarea
							id="ppi-estimate-basis"
							class="kt-input"
							rows="2"
							data-testid="ppi-estimate-basis"
							:value="draft.estimate_basis"
							@input="onField('estimate_basis', $event.target.value)"
						></textarea>
						<div class="kt-field-hint">What the estimate is based on, and what it includes.</div>
					</div>
					<div v-else class="kt-group">
						<span class="kt-label">Estimate basis</span>
						<p class="kt-muted" style="margin: 2px 0 0">
							{{ item.estimate_basis_preview }}
							<a href="#" data-testid="ppi-read-basis" @click.prevent="fullBasis = !fullBasis">Read full basis</a>
						</p>
					</div>
					<!-- §10.8 — shown only when an actual accessible record exists. -->
					<div v-if="item.mutable" class="kt-field pln-field-320" :class="flagged('estimate_basis_reference')">
						<label for="ppi-basis-reference" class="kt-label">Supporting document</label>
						<input
							id="ppi-basis-reference"
							class="kt-input"
							data-testid="ppi-basis-reference"
							:value="draft.estimate_basis_reference"
							@input="onField('estimate_basis_reference', $event.target.value)"
						>
					</div>
					<div v-else-if="draft.estimate_basis_reference" class="pln-fact">
						<span class="kt-label">Supporting document</span>
						<span class="kt-meta-value">{{ draft.estimate_basis_reference }}</span>
					</div>
				</div>
				<p v-if="fullBasis" class="kt-muted" data-testid="ppi-full-basis">{{ classification.estimate_basis }}</p>
			</div>

			<!-- 4. Procurement approach -->
			<div class="kt-region">
				<h2>Procurement approach</h2>
				<!-- §10.16 C03/C04 — the board states the blocked setting before the
				     field it blocks, not after the whole grid: a Planner reads why
				     the method they already chose no longer resolves before meeting
				     what now looks like an empty control (found live 23 Sep 2026 —
				     the panel sat after every field in this section, including ones
				     it has nothing to do with). Never resolver mechanics, and the
				     setup control only for an actor who actually holds setup access. -->
				<MissingSettingPanel v-for="(panel, index) in missingSettings" :key="index" :panel="panel" />
				<!-- The artboard's paired 320px controls. These were wrapped in a
				     `.kt-meta-row` — a bottom-aligned row built for short read-only
				     facts — which stretched each control to its content and left
				     the condition inputs and the designation at different
				     heights. -->
				<div class="pln-field-grid">
					<div class="kt-field" :class="flagged('procurement_method')">
						<label for="ppi-method" class="kt-label">Procurement method</label>
						<select id="ppi-method" class="kt-input" data-testid="ppi-method" :value="draft.procurement_method" :disabled="!item.mutable" @change="onField('procurement_method', $event.target.value)">
							<option value="">Select a procurement method</option>
							<option v-for="method in classification.admissible_methods || []" :key="method" :value="method">{{ method }}</option>
						</select>
					</div>
					<!-- Shown only when the Planner must choose one or one is set;
					     "None" is never displayed to prove the field exists. -->
					<div v-if="showReservation" class="kt-field" :class="flagged('reservation_category')">
						<label for="ppi-reservation" class="kt-label">Planned designation</label>
						<select id="ppi-reservation" class="kt-input" data-testid="ppi-reservation" :value="draft.reservation_category" :disabled="!item.mutable" @change="onField('reservation_category', $event.target.value)">
							<option value="">Select a designation</option>
							<option v-for="option in preference.reservation_categories || []" :key="option" :value="option">{{ option }}</option>
						</select>
					</div>
					<!-- §10.8 — a condition-specific input appears only when the chosen
					     method actually requires the Planner to supply it. A method
					     whose conditions are facts about the purchase asks nothing. -->
					<div
						v-for="condition in declarableConditions"
						:key="condition.condition_id"
						class="kt-field pln-condition"
						:data-testid="`ppi-condition-${condition.condition_id}`"
					>
						<label :for="`ppi-evidence-${condition.condition_id}`" class="kt-label">
							{{ condition.required_evidence || condition.description }}
						</label>
						<input
							:id="`ppi-evidence-${condition.condition_id}`"
							class="kt-input"
							:data-testid="`ppi-evidence-${condition.condition_id}`"
							:value="conditionEvidence[condition.condition_id]?.evidence_reference || ''"
							:disabled="!item.mutable"
							@input="onEvidence(condition.condition_id, 'evidence_reference', $event.target.value)"
						>
						<!-- Only where the rule names someone who has to authorise it. -->
						<template v-if="condition.authorisation_actor">
							<label :for="`ppi-authorisation-${condition.condition_id}`" class="kt-label">
								{{ condition.authorisation_actor }} authorisation
							</label>
							<input
								:id="`ppi-authorisation-${condition.condition_id}`"
								class="kt-input"
								:data-testid="`ppi-authorisation-${condition.condition_id}`"
								:value="conditionEvidence[condition.condition_id]?.authorisation_reference || ''"
								:disabled="!item.mutable"
								@input="onEvidence(condition.condition_id, 'authorisation_reference', $event.target.value)"
							>
						</template>
						<div class="kt-field-hint" :data-testid="`ppi-condition-result-${condition.condition_id}`">
							{{ condition.result }}<template v-if="condition.statutory_reference"> · {{ condition.statutory_reference }}</template>
						</div>
					</div>
					<!-- Only for an applicable county entity, and only when it changes
					     the item decision. -->
					<div v-if="preference.county_control_available" class="kt-field">
						<label class="kt-label">County requirement</label>
						<label class="kt-checkbox">
							<input type="checkbox" data-testid="ppi-county" :checked="draft.county_resident_reservation" :disabled="!item.mutable" @change="onField('county_resident_reservation', $event.target.checked)">
							<span class="box"></span>Reserved for county residents
						</label>
					</div>
					<!-- Only when the Planner chooses multiple lots or must resolve a
					     lotting issue; Single lot and Lot count 1 are omitted. -->
					<div v-if="showLotting" class="kt-field" :class="flagged('lot_count')">
						<label for="ppi-lots" class="kt-label">Lots</label>
						<input id="ppi-lots" class="kt-input" type="number" min="2" data-testid="ppi-lot-count" :value="draft.lot_count" :disabled="!item.mutable" @input="onField('lot_count', $event.target.value)">
					</div>
				</div>
				<button
					v-if="!showReservation && item.mutable"
					type="button"
					class="kt-btn kt-btn-ghost"
					data-testid="ppi-add-reservation"
					@click="forceReservation = true"
				>
					Add a planned designation
				</button>
			</div>

			<!-- 5. Dates -->
			<div class="kt-region">
				<!-- U09-INVALID-SCHEDULE — the blocking problem and its recovery
				     action sit beside the dates they are about. -->
				<div v-if="saveBlocked" class="kt-notice is-critical" style="margin-bottom: var(--kt-space-4)">
					<svg class="kt-notice-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
						<circle cx="12" cy="12" r="10"></circle><path d="M12 8v5"></path><path d="M12 16h.01"></path>
					</svg>
					<div style="flex: 1">
						<div class="kt-notice-body">{{ boundaryText }}</div>
						<button
							type="button"
							class="kt-btn kt-btn-secondary"
							style="margin-top: var(--kt-space-3)"
							data-testid="ppi-review-dates"
							@click="scrollToDates"
						>
							Review dates
						</button>
					</div>
				</div>
				<h2>Dates</h2>
				<!-- The board draws these four as one band. Two of them are the
				     Planner's own entries and two are derived from them, so the
				     entries are fields and the results are facts — on one grid,
				     top-aligned, rather than a flex row that bottom-aligned a
				     hint-bearing input against a bare figure. -->
				<div class="pln-field-grid pln-dates-grid">
					<div class="kt-field" :class="flagged('baseline_invitation_date')">
						<label for="ppi-invitation" class="kt-label">Target invitation date</label>
						<input id="ppi-invitation" class="kt-input" type="date" data-testid="ppi-invitation" :value="draft.baseline_invitation_date" :disabled="!item.mutable" @input="onField('baseline_invitation_date', $event.target.value)">
					</div>
					<div class="kt-field" :class="flagged('estimated_delivery_period_days')">
						<label for="ppi-delivery" class="kt-label">Expected delivery period</label>
						<input id="ppi-delivery" class="kt-input" type="number" min="0" data-testid="ppi-delivery-days" :value="draft.estimated_delivery_period_days" :disabled="!item.mutable" @input="onField('estimated_delivery_period_days', $event.target.value)">
						<div class="kt-field-hint">Calendar days</div>
					</div>
					<div class="pln-fact">
						<span class="kt-label">Expected completion</span>
						<span class="kt-meta-value" data-testid="ppi-completion">{{ baseline.estimated_completion_display || "—" }}</span>
					</div>
					<div class="pln-fact">
						<span class="kt-label">Departmental deadline</span>
						<span class="kt-meta-value" data-testid="ppi-deadline">{{ deadlineDisplay }}</span>
					</div>
				</div>
				<!-- Said once. When the deadline cannot be met the critical notice
				     above already says so and offers the recovery action, so
				     repeating the same sentence here left the page stating one
				     problem twice (U09-INVALID-SCHEDULE draws the notice alone). -->
				<p
					v-if="baseline.estimated_completion_display && !saveBlocked"
					class="pln-boundary"
					data-testid="ppi-boundary"
				>
					<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
						<path d="M20 6 9 17l-5-5"></path>
					</svg>
					{{ boundaryText }}
				</p>
				<div class="pln-region-gap">
					<a href="#" class="kt-btn kt-btn-ghost" data-testid="ppi-view-dates" @click.prevent="supporting = true">View calculated dates</a>
				</div>
			</div>

			<!-- 6. Supporting details — one level, closed by default. -->
			<details class="kt-disclosure" :open="supporting" data-testid="ppi-supporting">
				<summary class="kt-disclosure-head">
					<div class="kt-disclosure-title-row">
						<span class="kt-disclosure-title">Supporting details</span>
						<!-- The board's own chip: what is inside, so the disclosure can
						     stay closed without hiding what it holds. -->
						<span class="kt-tag kt-tag-neutral">Strategy, classification, rule evidence, milestone calculations</span>
					</div>
					<svg class="kt-disclosure-chevron" :class="{ 'is-open': supporting }" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
						<path d="M6 9l6 6 6-6"></path>
					</svg>
				</summary>
				<div class="kt-disclosure-body pln-supporting">
					<div class="kt-field pln-field-480">
						<label for="ppi-objective" class="kt-label">Strategy</label>
						<select id="ppi-objective" class="kt-input" data-testid="ppi-objective" :value="draft.strategic_objective" :disabled="!item.mutable" @change="onField('strategic_objective', $event.target.value)">
							<option value="">Select a strategic objective</option>
							<option v-for="objective in classification.strategic_objectives || []" :key="objective.id" :value="objective.id">{{ objective.title }}</option>
						</select>
						<div v-if="classification.objective_path" class="kt-field-hint" data-testid="ppi-objective-path">{{ classification.objective_path }}</div>
					</div>

					<div class="pln-fact">
						<span class="kt-label">Classification provenance</span>
						<span class="kt-meta-value" data-testid="ppi-classification-provenance">
							{{ item.identity?.requirement_type }} / {{ item.identity?.procurement_category }}
						</span>
					</div>

					<!-- Only where a rule actually resolved. Clearing the method
					     left this heading standing over nothing (live, 23 Sep
					     2026); §10.16 replaces an unresolved rule with the
					     missing-setting panel, not with an empty section. -->
					<div v-if="methodProfile.profile || methodProfile.verification_status" class="kt-meta-row" data-testid="ppi-rule-evidence">
						<div v-if="methodProfile.profile">
							<span class="kt-label">Applicable rule</span>
							<span class="kt-meta-value">{{ methodProfile.profile }}</span>
						</div>
						<div v-if="methodProfile.verification_status">
							<span class="kt-label">Source check</span>
							<span class="kt-meta-value">{{ methodProfile.verification_status }}</span>
						</div>
					</div>

					<div>
						<h4 class="kt-label">Calculated dates</h4>
						<!-- A table of dashes states nothing. Until the Planner sets
						     the target invitation date there is no schedule to show. -->
						<table v-if="hasCalculatedDates" class="kt-table pln-region-gap" data-testid="ppi-milestones">
							<thead><tr><th>Milestone</th><th>Baseline date</th></tr></thead>
							<tbody>
								<tr v-for="row in baseline.rows || []" :key="row.milestone">
									<td>{{ row.label }}</td>
									<td>{{ row.date_display }}</td>
								</tr>
							</tbody>
						</table>
						<p v-else class="kt-muted" data-testid="ppi-milestones-empty">
							Set the target invitation date to calculate the milestone dates.
						</p>
					</div>
				</div>
			</details>

			<p v-if="errorSummary" class="pln-error-summary" data-testid="ppi-error">{{ errorSummary }}</p>

			<div class="pln-footer" data-testid="ppi-footer">
				<button
					v-if="item.mutable && !item.scope_lock?.locked"
					type="button"
					class="kt-btn kt-btn-secondary kt-danger"
					data-testid="ppi-remove"
					:disabled="pending"
					@click="$emit('remove')"
				>
					Remove purchase
				</button>
				<span v-else></span>
				<div class="pln-footer-right">
					<button type="button" class="kt-btn kt-btn-secondary" data-testid="ppi-back" @click="$emit('back')">
						Back to annual plan
					</button>
					<button
						v-if="item.mutable"
						type="button"
						class="kt-btn kt-btn-primary"
						data-testid="ppi-save"
						:disabled="pending || saveBlocked"
						@click="$emit('save', draft)"
					>
						Save draft
					</button>
				</div>
			</div>
		</div>
	</div>
</template>

<script setup>
import { computed, reactive, ref, watch } from "vue";
import MissingSettingPanel from "./MissingSettingPanel.vue";

const props = defineProps({
	item: { type: Object, default: () => ({}) },
	pending: Boolean,
	errorSummary: String,
});

const emit = defineEmits(["save", "remove", "back", "view-classification"]);

const EDITABLE = [
	"title",
	"description",
	"estimate_basis",
	"estimate_basis_reference",
	"procurement_method",
	"reservation_category",
	"county_resident_reservation",
	"lot_count",
	"baseline_invitation_date",
	"estimated_delivery_period_days",
	"strategic_objective",
];

function initial() {
	const identity = props.item.identity || {};
	const classification = props.item.classification || {};
	const preference = props.item.preference || {};
	const baseline = props.item.baseline || {};
	return {
		title: identity.title || "",
		description: identity.description || "",
		estimate_basis: classification.estimate_basis || "",
		estimate_basis_reference: classification.estimate_basis_reference || "",
		procurement_method: classification.procurement_method || "",
		reservation_category: preference.reservation_category || "",
		county_resident_reservation: Boolean(preference.county_resident_reservation),
		lot_count: preference.lot_count || 0,
		baseline_invitation_date: baseline.target_invitation_date || "",
		estimated_delivery_period_days: baseline.estimated_delivery_period_days ?? "",
		strategic_objective: classification.strategic_objective || "",
		// §7.2 — the rows the save command expects: one per declarable
		// condition, carrying what the Planner supplied for it.
		method_condition_evidence: ((classification.method_profile || {}).conditions || [])
			.filter((c) => c.kind !== "Known fact")
			.map((c) => ({
				condition_id: c.condition_id,
				evidence_reference: c.evidence_reference || "",
				authorisation_reference: c.authorisation_reference || "",
			})),
	};
}

const draft = reactive(initial());
const fullReason = ref(false);
const fullBasis = ref(false);
const supporting = ref(false);
const forceReservation = ref(false);

// A quiet in-place refresh carries nothing new; re-hydrating would discard
// what the Planner has typed since.
watch(
	() => props.item,
	(item, previous) => {
		if (previous && (previous.record_version ?? null) === (item?.record_version ?? null)) return;
		Object.assign(draft, initial());
		forceReservation.value = false;
	},
);

const classification = computed(() => props.item.classification || {});
const preference = computed(() => props.item.preference || {});
const baseline = computed(() => props.item.baseline || {});
const methodProfile = computed(() => classification.value.method_profile || {});
const sources = computed(() => props.item.sources || []);
const notices = computed(() => props.item.notices || []);
const missingSettings = computed(() => props.item.missing_settings || []);

// A condition the rule states as a fact about the purchase (a value band) is
// evaluated, not declared; only the rest are asked of the Planner.
const declarableConditions = computed(() =>
	((classification.value.method_profile || {}).conditions || []).filter((c) => c.kind !== "Known fact"),
);

const conditionEvidence = computed(() =>
	Object.fromEntries((draft.method_condition_evidence || []).map((row) => [row.condition_id, row])),
);

function onEvidence(conditionId, field, value) {
	if (!props.item.mutable) return;
	const rows = draft.method_condition_evidence || [];
	const existing = rows.find((row) => row.condition_id === conditionId);
	if (existing) existing[field] = value;
	else rows.push({ condition_id: conditionId, evidence_reference: "", authorisation_reference: "", [field]: value });
	draft.method_condition_evidence = [...rows];
}
const versionNumber = computed(() => {
	const match = /Version (\d+)/.exec(props.item.header?.reference_line || "");
	return match ? match[1] : "";
});
const statusLabel = computed(() => (props.item.is_active ? "Active" : props.item.header?.item_state_badge || "Draft"));

// PLN22-AC-006 — a designation is shown when the Planner must choose one or
// one has been chosen. "None" is a real choice but not a thing to display.
const showReservation = computed(
	() => forceReservation.value || Boolean(preference.value.reservation_category) || blockerCodes.value.has("PLN_RESERVATION_REQUIRED"),
);
// Single lot and Lot count 1 are omitted; lots appear only when there are
// several or a lotting issue to resolve.
const showLotting = computed(
	() => Number(draft.lot_count) > 1 || preference.value.lotting_indicator === "Packaged into lots",
);

const blockerCodes = computed(() => new Set((props.item.blockers || []).map((b) => b.code)));
// `item_blockers` reports one blocker per incomplete field, because the fields
// are what the Planner has to fix; several of them legitimately share one
// code, and so one message. Saying the same sentence once per field stacked
// identical banners on top of each other (two live, 23 Sep 2026) and gave
// `v-for` a duplicate key. One banner per distinct sentence — the fields it
// names are marked in place instead, which is what "the highlighted purchase
// details" means.
// Schedule problems are said once, beside the dates.
const visibleBlockers = computed(() => {
	const seen = new Set();
	return (props.item.blockers || [])
		.filter(
			(b) => !["PLN_SCHEDULE_INVALID", "PLN_DELIVERY_BOUNDARY_INSUFFICIENT", "PLN_DELIVERY_PERIOD_REQUIRED", "PLN_REFERENCE_UNAVAILABLE", "PLN_RESERVATION_REQUIRED"].includes(b.code),
		)
		.filter((b) => {
			const message = b.message || b.code;
			if (seen.has(message)) return false;
			seen.add(message);
			return true;
		});
});

// The fields those blockers name, so the sentence is literally true.
const flaggedFields = computed(() => new Set((props.item.blockers || []).map((b) => b.field).filter(Boolean)));
function flagged(field) {
	return flaggedFields.value.has(field) ? "pln-field-flagged" : "";
}

// Every milestone row before the source boundary reads "—" until the Planner
// sets a target invitation date; the boundary row alone carries the
// department's own date, so it is not evidence of a calculated schedule.
const hasCalculatedDates = computed(() =>
	(baseline.value.rows || []).some((row) => !row.source_boundary && row.date_display && row.date_display !== "—"),
);

const deadlineDisplay = computed(() => {
	const row = (baseline.value.rows || []).find((r) => r.source_boundary);
	return row ? row.date_display : "—";
});

const saveBlocked = computed(() => blockerCodes.value.has("PLN_DELIVERY_BOUNDARY_INSUFFICIENT"));

const boundaryText = computed(() =>
	baseline.value.delivery_boundary_ok
		? "Expected to meet the departmental deadline"
		: "Expected completion is after the department's required date.",
);

function onField(field, value) {
	if (!EDITABLE.includes(field)) return;
	draft[field] = value;
}

function scrollToDates() {
	document.querySelector('[data-testid="ppi-invitation"]')?.scrollIntoView({ behavior: "smooth", block: "center" });
}
</script>
