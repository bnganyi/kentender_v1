<!-- NDS-UI-03 need editor (§12.3) — NDS-DES-03 create, NDS-DES-04 returned
     correction, NDS-DES-08 accepted update draft and NDS-DES-15's department
     choice are the same editor over the same six values; only the masthead,
     notice, context and footer differ. -->
<template>
	<div class="kt-panel-lg" style="max-width: 700px">
		<h3 style="margin: 0">{{ heading }}</h3>
		<div v-if="reference" style="display: flex; gap: var(--kt-space-3); align-items: center; margin: 6px 0 0">
			<span class="kt-label">{{ reference }}</span>
			<span class="kt-status" :class="statusClass">{{ statusLabel }}</span>
			<span v-if="revisionNote" class="text-muted" style="font-size: 12px">{{ revisionNote }}</span>
		</div>
		<p v-else class="text-muted" style="font-size: 13px; margin: 6px 0 0">{{ lede }}</p>

		<!-- NDS-DES-04 "What needs to change" — the immutable return reason. -->
		<div v-if="returnReason" class="kt-notice is-warning" style="margin-top: var(--kt-space-4)">
			<div class="kt-notice-body">
				<strong>What needs to change</strong><br />
				{{ returnReason.reason }}
				<div style="display: flex; gap: var(--kt-space-6); margin-top: var(--kt-space-3); font-size: 12px">
					<div><strong style="color: var(--kt-color-text)">Returned by</strong> {{ returnReason.actor_label }}</div>
					<div><strong style="color: var(--kt-color-text)">Returned at</strong> {{ returnReason.occurred_label }}</div>
				</div>
			</div>
		</div>

		<!-- NDS-DES-08 — the accepted source remains in effect while a proposed
		     update is being drafted. -->
		<div v-if="mode === 'successor'" class="kt-notice is-info" style="margin-top: var(--kt-space-4)">
			<div class="kt-notice-body">
				The previously accepted requirement remains in effect until these changes are
				accepted.
			</div>
		</div>

		<div
			v-if="errorSummary"
			ref="errorEl"
			class="kt-notice is-critical"
			style="margin-top: var(--kt-space-4)"
			role="alert"
			tabindex="-1"
		>
			<div class="kt-notice-body">{{ errorSummary }}</div>
		</div>

		<!-- §11.1 — read-only Department/Financial year, except NDS-DES-15's
		     same-form selector when this Author has more than one eligible
		     department and none is chosen yet. -->
		<div class="kt-panel" style="margin-top: var(--kt-space-4)">
			<div class="kt-meta-row">
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
					<span class="kt-meta-value" style="font-size: 14px">{{
						context.organisation_unit_label || context.organisation_unit || ""
					}}</span>
				</div>
				<div>
					<span class="kt-label">Financial year</span>
					<span class="kt-meta-value" style="font-size: 14px">{{
						context.financial_year_label || context.financial_year || ""
					}}</span>
				</div>
			</div>
		</div>

		<!-- §11.1 six-field arrangement: title/description/expected result full
		     width, quantity+unit side by side, required by on its own row. -->
		<div style="display: flex; flex-direction: column; gap: var(--kt-space-4); margin-top: var(--kt-space-4)">
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
				<div class="text-muted" style="font-size: 12.5px; margin-top: 4px">
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
				<div class="text-muted" style="font-size: 12.5px; margin-top: 4px">Describe what is needed.</div>
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
				<div class="text-muted" style="font-size: 12.5px; margin-top: 4px">
					What will the department be able to do when this need is met?
				</div>
			</div>
			<div style="display: grid; grid-template-columns: 1fr 1fr; gap: var(--kt-space-4)">
				<div class="field" style="margin: 0">
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
					<div class="text-muted" style="font-size: 12.5px; margin-top: 4px">
						Enter the total quantity needed.
					</div>
					<div v-if="inputErrors.indicative_quantity" class="kt-field-error" data-testid="nds-quantity-error">
						{{ inputErrors.indicative_quantity }}
					</div>
				</div>
				<div class="field" style="margin: 0">
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
					<div class="text-muted" style="font-size: 12.5px; margin-top: 4px">
						Select the unit that describes the quantity.
					</div>
				</div>
			</div>
			<div class="field" style="max-width: 340px">
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
				<div class="text-muted" style="font-size: 12.5px; margin-top: 4px">When does the department need it?</div>
				<div v-if="inputErrors.required_by_date" class="kt-field-error" data-testid="nds-required-by-error">
					{{ inputErrors.required_by_date }}
				</div>
			</div>
		</div>

		<!-- NDS-DES-04 History — collapsed, revision timeline. -->
		<div v-if="history.length" class="kt-disclosure" style="margin-top: var(--kt-space-4)">
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

		<!-- §11.1 form footer — destructive action at the far left; primary
		     action right-aligned. Draft/Returned use Withdraw need; Create/
		     successor use Cancel/Cancel update. -->
		<div
			style="display: flex; justify-content: space-between; margin-top: var(--kt-space-6); padding-top: var(--kt-space-4); border-top: 1px solid var(--kt-color-divider)"
		>
			<button
				class="kt-btn kt-btn-secondary kt-danger"
				data-testid="nds-editor-cancel"
				:disabled="pending"
				@click="$emit('cancel')"
			>
				{{ cancelLabel }}
			</button>
			<div style="display: flex; gap: var(--kt-space-2)">
				<button
					class="kt-btn kt-btn-secondary"
					data-testid="nds-save-draft"
					:disabled="pending || departmentRequired"
					@click="guardedEmit('save')"
				>
					{{ saveLabel }}
				</button>
				<button
					class="kt-btn kt-btn-primary"
					data-testid="nds-submit"
					:disabled="pending || departmentRequired"
					@click="guardedEmit('submit')"
				>
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
	inputErrors.indicative_quantity =
		quantityEl.value && quantityEl.value.validity.badInput
			? "Indicative quantity must be a number."
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

const HEADINGS = {
	create: "Create a departmental need",
	draft: () => props.revision?.title || "Departmental need",
	correct: () => props.revision?.title || "Departmental need",
	successor: "Update accepted need",
};
const LEDES = {
	create: "Describe one requirement for your department. Your Head of Department will review it for procurement planning.",
};

const reference = computed(() => (props.mode === "create" ? "" : props.need?.need_reference || ""));
const heading = computed(() => {
	const entry = HEADINGS[props.mode] || HEADINGS.create;
	return typeof entry === "function" ? entry() : entry;
});
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
