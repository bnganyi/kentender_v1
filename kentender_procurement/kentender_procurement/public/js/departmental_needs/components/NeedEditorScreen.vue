<!-- NDS-UI-03 need editor (§12.3) — NDS-DES-03 create, NDS-DES-04 returned
     correction, NDS-DES-08 accepted update draft and NDS-DES-15's department
     choice are the same editor over the same six values; only the masthead,
     notice, context and footer differ. The NDS-DES-14 QUANTITY-ERROR/
     CLOSED-EDITOR/PARTIAL-SUBMIT/SUBMIT-UNKNOWN boundary states and
     NDS-DES-15-MULTIPLE/SINGLE/PERSISTED are ported class-for-class from
     NDS Artboards.dc.html. -->
<template>
	<div class="kt-page">
		<div>
			<h1 class="kt-page-title">{{ headingTitle }}</h1>
			<!-- Only "successor" has a fixed action-name heading separate from
			     the requirement's own business name (NDS-DES-08); draft/correct
			     mode's heading IS the business name (NDS-DES-04/15-PERSISTED),
			     so repeating it here would show the same text twice. -->
			<div v-if="mode === 'successor'" style="font-family: var(--kt-font-heading); font-weight: 600; font-size: 21px; margin-top: 10px">{{ businessName }}</div>
			<div v-if="reference" style="display: flex; align-items: center; gap: 12px; margin-top: 6px">
				<span class="text-muted" style="font-size: 13px">{{ reference }}</span>
				<span class="kt-status" :class="statusClass">{{ statusLabel }}</span>
				<span v-if="revisionNote" class="text-muted" style="font-size: 12px">{{ revisionNote }}</span>
			</div>
			<p v-else class="kt-page-desc" style="max-width: 760px">{{ lede }}</p>
		</div>

		<!-- NDS-DES-04 "What needs to change" — the immutable return reason. -->
		<div v-if="returnReason" class="kt-notice is-warning" style="max-width: 860px">
			<svg class="kt-notice-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3"/><path d="M12 9v4"/><path d="M12 17h.01"/></svg>
			<div class="kt-notice-body">
				<div style="font-family: var(--kt-font-heading); font-weight: 600; font-size: 16px; text-transform: uppercase; letter-spacing: 0.02em">
					What needs to change
				</div>
				<p style="margin: 8px 0 0">{{ returnReason.reason }}</p>
				<p class="text-muted" style="margin: 10px 0 0; font-size: 12px">
					Returned by {{ returnReason.actor_label }} · {{ returnReason.occurred_label }}
				</p>
			</div>
		</div>

		<!-- NDS-DES-08 — the accepted source remains in effect while a proposed
		     update is being drafted. -->
		<div v-if="mode === 'successor'" class="kt-notice" style="max-width: 860px">
			<div class="kt-notice-body">
				The previously accepted requirement remains in effect until these changes are
				accepted.
			</div>
		</div>

		<div v-if="errorSummary" ref="errorEl" class="kt-notice is-critical" style="max-width: 860px" role="alert" tabindex="-1" data-testid="nds-error-summary">
			<div class="kt-notice-body">{{ errorSummary }}</div>
		</div>

		<!-- NDS-DES-14-PARTIAL-SUBMIT — the draft itself was saved (it now has a
		     real reference) even though the submit that followed was refused;
		     the saved reference stays reachable here rather than only in a
		     banner nobody can act on. §8.4 "Save succeeds, Submit fails" applies
		     to every refusal, showing its actual reason: intake closing in
		     between gets the closed-editor explanation and keeps Submit
		     disabled; any other reason (a missing field, a Required-by date
		     outside the year) leaves Submit enabled for the corrected retry. -->
		<div v-if="partialSubmit" class="kt-notice is-warning" style="max-width: 860px" data-testid="nds-partial-submit">
			<div class="kt-notice-body">
				<div style="font-weight: 600; color: var(--kt-color-text)">Your draft was saved, but it was not submitted.</div>
				<p v-if="partialSubmit.intake_closed" style="margin: 6px 0 0">New submissions are closed. You can save changes to this draft and submit if submissions reopen.</p>
				<p v-else style="margin: 6px 0 0" data-testid="nds-partial-submit-reason">{{ partialSubmit.reason }}</p>
				<div class="kt-meta-row is-tight" style="gap: 28px; margin-top: 14px">
					<div><span class="kt-label">Reference</span><span class="kt-meta-value">{{ partialSubmit.need_reference }}</span></div>
					<div><span class="kt-label">Revision</span><span class="kt-meta-value">{{ partialSubmit.revision_number }}</span></div>
				</div>
			</div>
		</div>

		<!-- NDS-DES-14-SUBMIT-UNKNOWN — a network-level failure with no
		     interpretable server answer (frappeCall's `ambiguous` flag): the
		     caller genuinely cannot tell whether the command was received, so
		     writes stay disabled until the next real load rather than offering
		     a second submission that could double it. -->
		<div v-if="submitUnknown" class="kt-notice" style="max-width: 860px" data-testid="nds-submit-unknown">
			<div class="kt-notice-body">We could not confirm whether submission succeeded. Checking the existing request…</div>
		</div>

		<!-- §11.4 — CREATE mode offers the same-form Department choice in a
		     compact ownership row over a hairline rule, not a card; every other
		     mode's Department/FY are already fixed and read as a plain
		     orientation line instead (NDS-DES-04/08). -->
		<div
			v-if="mode === 'create'"
			style="display: grid; grid-template-columns: 360px 200px; gap: 24px; align-items: end; max-width: 860px; padding-bottom: 20px; border-bottom: 1px solid var(--kt-color-divider)"
		>
			<div v-if="departmentChoices.length > 1" class="field" style="margin: 0">
				<label class="kt-label" for="nds-department">Department</label>
				<select
					id="nds-department"
					data-testid="nds-department"
					class="kt-input"
					:value="selectedDepartment"
					@change="$emit('select-department', $event.target.value)"
				>
					<option value="" disabled>Select department</option>
					<option v-for="row in departmentChoices" :key="row.organisation_unit" :value="row.organisation_unit">
						{{ row.organisation_unit_label }}
					</option>
				</select>
			</div>
			<div v-else>
				<span class="kt-label">Department</span>
				<div style="font-family: var(--kt-font-heading); font-weight: 600; font-size: 18px; margin-top: 4px">{{
					context.organisation_unit_label || context.organisation_unit || ""
				}}</div>
			</div>
			<div>
				<span class="kt-label">Financial year</span>
				<div style="font-family: var(--kt-font-heading); font-weight: 600; font-size: 18px; margin-top: 4px">{{
					context.financial_year_label || context.financial_year || ""
				}}</div>
			</div>
		</div>
		<!-- NDS-DES-15-PERSISTED — a fixed department/year context reads as a
		     labelled `kt-meta-row`, the same established live vocabulary
		     already used for the create-mode single-department context above
		     and elsewhere in this module (WorkspaceScreen.vue's closed notice,
		     NeedDetailScreen.vue's terminal decision), not the mockup's own
		     unlabelled inline text. -->
		<div v-else class="kt-meta-row is-tight" style="gap: 40px; max-width: 860px; padding-bottom: 20px; border-bottom: 1px solid var(--kt-color-divider)">
			<div><span class="kt-label">Department</span><span class="kt-meta-value">{{ context.organisation_unit_label || context.organisation_unit || "" }}</span></div>
			<div><span class="kt-label">Financial year</span><span class="kt-meta-value">{{ context.financial_year_label || context.financial_year || "" }}</span></div>
		</div>

		<!-- §11.1 six-field arrangement (single-sheet migration): one open
		     column, 860px measure — title, description and expected result
		     each their own full-width row; quantity/unit share a row; required
		     by follows on its own. -->
		<div style="max-width: 860px; display: flex; flex-direction: column; gap: 20px">
			<div class="field">
				<label class="kt-label" for="nds-title">Requirement title</label>
				<input
					id="nds-title"
					ref="titleEl"
					data-testid="nds-title"
					class="kt-input"
					type="text"
					v-model="form.title"
				/>
				<div class="text-muted" style="font-size: 12px; margin-top: 5px">
					Give the requirement a short, recognisable name.
				</div>
				<div v-if="fieldErrors.title" class="kt-field-error">{{ fieldErrors.title }}</div>
			</div>
			<div class="field">
				<label class="kt-label" for="nds-description">Description</label>
				<textarea
					id="nds-description"
					data-testid="nds-description"
					class="kt-input"
					rows="2"
					v-model="form.description"
				></textarea>
				<div class="text-muted" style="font-size: 12px; margin-top: 5px">Describe what is needed.</div>
			</div>
			<div class="field">
				<label class="kt-label" for="nds-result">Expected result</label>
				<textarea
					id="nds-result"
					data-testid="nds-result"
					class="kt-input"
					rows="2"
					v-model="form.expected_operational_result"
				></textarea>
				<div class="text-muted" style="font-size: 12px; margin-top: 5px">
					What will the department be able to do when this need is met?
				</div>
			</div>
			<div style="display: grid; grid-template-columns: 200px 260px; gap: 20px">
				<div class="field">
					<label class="kt-label" for="nds-quantity">Quantity</label>
					<input
						id="nds-quantity"
						ref="quantityEl"
						data-testid="nds-quantity"
						class="kt-input"
						type="number"
						min="0"
						step="0.001"
						v-model="form.indicative_quantity"
						@input="inputErrors.indicative_quantity = ''"
					/>
					<div class="text-muted" style="font-size: 12px; margin-top: 5px">
						Enter the total quantity needed.
					</div>
					<div v-if="inputErrors.indicative_quantity" class="kt-field-error" data-testid="nds-quantity-error">
						{{ inputErrors.indicative_quantity }}
					</div>
				</div>
				<div class="field">
					<label class="kt-label" for="nds-unit">Unit</label>
					<div style="display: flex; gap: 8px; align-items: center">
						<select id="nds-unit" data-testid="nds-unit" class="kt-input" v-model="form.unit" style="flex: 1">
							<option value="">Select a unit</option>
							<option v-for="unit in units" :key="unit.name" :value="unit.name">
								{{ unit.unit_label }}
							</option>
						</select>
						<button
							type="button"
							class="kt-btn kt-btn-secondary"
							style="white-space: nowrap"
							data-testid="nds-unit-new"
							@click="createUnit"
						>
							+ New
						</button>
					</div>
					<div class="text-muted" style="font-size: 12px; margin-top: 5px">
						Select the unit that describes the quantity.
					</div>
				</div>
			</div>
			<div class="field" style="max-width: 260px">
				<label class="kt-label" for="nds-required-by">Required by</label>
				<input
					id="nds-required-by"
					ref="requiredByEl"
					data-testid="nds-required-by"
					class="kt-input"
					type="date"
					v-model="form.required_by_date"
					@input="inputErrors.required_by_date = ''"
				/>
				<div class="text-muted" style="font-size: 12px; margin-top: 5px">When does the department need it?</div>
				<div v-if="inputErrors.required_by_date" class="kt-field-error" data-testid="nds-required-by-error">
					{{ inputErrors.required_by_date }}
				</div>
			</div>
		</div>

		<!-- NDS-DES-04 History — collapsed, revision timeline. -->
		<div v-if="history.length" class="kt-disclosure" style="max-width: 860px">
			<div class="kt-disclosure-head" @click="historyOpen = !historyOpen">
				<div class="kt-disclosure-title-row"><span class="kt-disclosure-title">History</span></div>
				<svg
					class="kt-disclosure-chevron"
					:class="{ 'is-open': historyOpen }"
					width="16"
					height="16"
					viewBox="0 0 24 24"
					fill="none"
					stroke="currentColor"
					stroke-width="1.5"
				><path d="M6 9l6 6 6-6" /></svg>
			</div>
			<div v-if="historyOpen" class="kt-disclosure-body">
				<div class="kt-timeline">
					<div v-for="(item, index) in history" :key="index" class="kt-timeline-row">
						<div class="kt-timeline-dot-col">
							<i class="kt-timeline-dot" :class="item.dotClass"></i>
							<i v-if="index < history.length - 1" class="kt-timeline-line"></i>
						</div>
						<div class="kt-timeline-item">
							<div class="kt-timeline-item-title">{{ item.title }}</div>
							<div class="kt-timeline-item-meta">{{ item.meta }}</div>
						</div>
					</div>
				</div>
			</div>
		</div>

		<!-- NDS-DES-14-CLOSED-EDITOR — a not-yet-submitted Draft's own Submit
		     needs intake Open (NDS-BR-002/003); a Returned correction's
		     resubmission does not (the version was already submitted before
		     close), so this note and the Submit disable below apply to "draft"
		     mode only, never "correct". -->
		<p
			v-if="mode === 'draft' && submissionClosed"
			style="margin: 0; font-size: 14px; color: var(--kt-color-neutral-800); max-width: 860px"
			data-testid="nds-submission-closed-note"
		>
			New submissions are closed. You can save changes to this draft and submit if submissions reopen.
		</p>

		<!-- §11.4/§11.5/§11.9 footer — CREATE has no destructive action, so
		     Cancel joins Save/Submit as one right-aligned group. Every other
		     mode separates its destructive-or-quieter cancel action to the far
		     left; only "Withdraw need" (an accepted/submitted revision's real
		     withdrawal) is danger-styled — "Cancel update"/"Cancel" discard an
		     unaccepted draft and stay plain secondary. -->
		<div
			v-if="mode === 'create'"
			style="display: flex; justify-content: flex-end; gap: 12px; padding-top: 20px; border-top: 1px solid var(--kt-color-divider); max-width: 860px"
		>
			<button class="kt-btn kt-btn-secondary" data-testid="nds-editor-cancel" :disabled="pending" @click="$emit('cancel')">
				{{ cancelLabel }}
			</button>
			<button class="kt-btn kt-btn-secondary" data-testid="nds-save-draft" :disabled="pending || departmentRequired || submitUnknown" @click="guardedEmit('save')">
				{{ saveLabel }}
			</button>
			<button class="kt-btn kt-btn-primary" data-testid="nds-submit" :disabled="pending || departmentRequired || !!partialSubmit?.intake_closed || submitUnknown" @click="guardedEmit('submit')">
				{{ submitLabel }}
			</button>
		</div>
		<div
			v-else
			style="display: flex; justify-content: space-between; align-items: center; gap: 12px; padding-top: 20px; border-top: 1px solid var(--kt-color-divider); max-width: 860px"
		>
			<button
				class="kt-btn kt-btn-secondary"
				:class="{ 'kt-danger': cancelLabel === 'Withdraw need' }"
				data-testid="nds-editor-cancel"
				:disabled="pending"
				@click="$emit('cancel')"
			>
				{{ cancelLabel }}
			</button>
			<div style="display: flex; gap: 12px">
				<button class="kt-btn kt-btn-secondary" data-testid="nds-save-draft" :disabled="pending || departmentRequired" @click="guardedEmit('save')">
					{{ saveLabel }}
				</button>
				<button class="kt-btn kt-btn-primary" data-testid="nds-submit" :disabled="pending || departmentRequired || (mode === 'draft' && submissionClosed) || !!partialSubmit?.intake_closed || submitUnknown" @click="guardedEmit('submit')">
					{{ submitLabel }}
				</button>
			</div>
		</div>
	</div>
</template>

<script setup>
import { computed, nextTick, reactive, ref, watch } from "vue";
import { quickCreate } from "../../nds_shared/composables/quickCreate.js";
import { formatDate, formatInstant } from "../data/format.js";

const props = defineProps({
	mode: { type: String, default: "create" }, // create | draft | correct | successor
	need: { type: Object, default: () => ({}) },
	revision: { type: Object, default: () => ({}) },
	context: { type: Object, default: () => ({}) },
	// NDS-DES-15-MULTIPLE — every eligible department, offered only while
	// creating and none is chosen yet; empty otherwise (read-only context).
	departmentChoices: { type: Array, default: () => [] },
	selectedDepartment: { type: String, default: "" },
	units: { type: Array, default: () => [] },
	returnReason: { type: Object, default: null },
	history: { type: Array, default: () => [] },
	errorSummary: { type: String, default: "" },
	fieldErrors: { type: Object, default: () => ({}) },
	pending: Boolean,
	// NDS-DES-14-CLOSED-EDITOR — whether Needs submission is currently closed;
	// only "draft" mode's own Submit is gated by it (see the footer's disabled
	// binding for why "correct" is exempt).
	submissionClosed: Boolean,
	// NDS-DES-14-PARTIAL-SUBMIT — { need_reference, revision_number } once a
	// create-mode save succeeded but the submit that followed it did not.
	partialSubmit: { type: Object, default: null },
	// NDS-DES-14-SUBMIT-UNKNOWN — a network-level failure with no
	// interpretable server answer; writes stay disabled until the next load.
	submitUnknown: Boolean,
});
const emit = defineEmits(["save", "submit", "cancel", "unit-created", "select-department"]);

async function createUnit() {
	const doc = await quickCreate("UOM");
	if (!doc) return;
	form.unit = doc.name;
	emit("unit-created", { name: doc.name, unit_label: doc.uom_name });
}

const errorEl = ref(null);
const titleEl = ref(null);
const requiredByEl = ref(null);
const quantityEl = ref(null);
const historyOpen = ref(false);

// A native date or number input holding unparseable text keeps the text
// visible but reports value "" — submitting would silently drop what the
// user typed (e.g. 31/09/2026) and the server would answer "…is required.",
// pointing at a field that looks filled in. Surface the real problem instead.
const inputErrors = reactive({ required_by_date: "", indicative_quantity: "" });

// NDS-DES-15-MULTIPLE — Save/Submit stay disabled until the required choice
// is made; no invented default and no separate Continue dialog.
const departmentRequired = computed(
	() => props.departmentChoices.length > 1 && !props.selectedDepartment
);

function guardedEmit(event) {
	if (departmentRequired.value) return;
	inputErrors.required_by_date =
		requiredByEl.value && requiredByEl.value.validity.badInput
			? "Required by must be a real calendar date."
			: "";
	// NDS-DES-14-QUANTITY-ERROR — NDS-AC-005 forbids a quantity of 0; checked
	// client-side (no modal, no round trip) exactly like the badInput checks
	// above, and only once badInput itself is ruled out.
	inputErrors.indicative_quantity =
		quantityEl.value && quantityEl.value.validity.badInput
			? "Indicative quantity must be a number."
			: form.indicative_quantity !== "" && Number(form.indicative_quantity) <= 0
				? "Enter a quantity greater than zero."
				: "";
	const invalid = inputErrors.required_by_date
		? requiredByEl.value
		: inputErrors.indicative_quantity
			? quantityEl.value
			: null;
	if (invalid) {
		invalid.focus();
		return;
	}
	emit(event, form);
}

const form = reactive({
	title: "",
	description: "",
	expected_operational_result: "",
	indicative_quantity: "",
	unit: "",
	required_by_date: "",
});

const FORM_SOURCE_FIELDS = [
	"name",
	"revision_number",
	"title",
	"description",
	"expected_operational_result",
	"indicative_quantity",
	"unit",
	"required_by_date",
];
let hydratedFrom = null;

watch(
	() => props.revision,
	(revision) => {
		// An in-place refresh that returns the same content carries nothing
		// new — re-hydrating would discard what the user has typed since.
		const signature = JSON.stringify(FORM_SOURCE_FIELDS.map((field) => revision?.[field] ?? null));
		if (signature === hydratedFrom) return;
		hydratedFrom = signature;
		form.title = revision?.title || "";
		form.description = revision?.description || "";
		form.expected_operational_result = revision?.expected_operational_result || "";
		form.indicative_quantity =
			revision?.indicative_quantity == null ? "" : revision.indicative_quantity;
		form.unit = revision?.unit || "";
		form.required_by_date = revision?.required_by_date
			? String(revision.required_by_date).slice(0, 10)
			: "";
	},
	{ immediate: true, deep: true }
);

// §12.3 — a business-rule error moves focus to the summary.
watch(
	() => props.errorSummary,
	async (message) => {
		if (!message) return;
		await nextTick();
		errorEl.value?.focus();
	}
);

// §11.4/§11.9 — CREATE/successor headings are a fixed action name, with the
// requirement's own business name as a second line for every other mode
// (matching NDS-DES-04/08's own `<h1>`/name split); "draft"/"correct" have no
// fixed action name of their own, so the business name IS the heading.
const HEADINGS = {
	create: "Create a departmental need",
	successor: "Update accepted need",
};
const LEDES = {
	create: "Describe one requirement for your department. Your Head of Department will review it for procurement planning.",
};

const reference = computed(() => (props.mode === "create" ? "" : props.need?.need_reference || ""));
const businessName = computed(() => props.revision?.title || "Departmental need");
const headingTitle = computed(() => HEADINGS[props.mode] || businessName.value);
const lede = computed(() => LEDES[props.mode] || "");

const STATUS_CLASSES = {
	Draft: "is-draft",
	Returned: "is-attention",
	"Accepted for planning": "is-live",
};
const statusLabel = computed(() => {
	if (props.mode === "successor") return "Draft update";
	return props.revision?.revision_status || "Draft";
});
const statusClass = computed(() => STATUS_CLASSES[statusLabel.value] || "is-draft");
const revisionNote = computed(() => {
	if (props.mode === "successor") {
		return `Proposed revision ${props.revision?.revision_number || ""} · Accepted revision ${(props.revision?.revision_number || 1) - 1}`;
	}
	if (props.mode === "correct") return `Revision ${props.revision?.revision_number || ""}`;
	return "";
});

const submitLabel = computed(() => {
	if (props.mode === "correct") return "Resubmit for review";
	if (props.mode === "successor") return "Submit update for review";
	return "Submit for review";
});
// §11.5/§11.16 — a continuing Draft or a returned correction "Save changes";
// a brand new form or a proposed update "Save draft".
const saveLabel = computed(() =>
	["draft", "correct"].includes(props.mode) ? "Save changes" : "Save draft"
);
const cancelLabel = computed(() => {
	if (props.mode === "successor") return "Cancel update";
	if (["draft", "correct"].includes(props.mode)) return "Withdraw need";
	return "Cancel";
});

defineExpose({ focusTitle: () => titleEl.value?.focus() });
</script>
