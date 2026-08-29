<!-- NDS-UI-03 need editor (§12.3) — NDS-DES-03 create, NDS-DES-04 returned
     correction and NDS-DES-08 accepted update draft are the same editor over
     the same six values; only the masthead, notice and footer differ. -->
<template>
	<div style="padding-bottom: 24px">
		<div style="display: flex; align-items: center; gap: 12px; margin-bottom: 8px">
			<h1 class="kt-record-title">{{ heading }}</h1>
			<StatusPill :label="statusLabel" />
		</div>
		<p class="kt-page-lede" style="margin: 0 0 24px">{{ lede }}</p>

		<!-- §12.3 — the returned editor shows the immutable return reason. -->
		<div
			v-if="returnReason"
			class="kt-card kt-blueprint"
			style="margin-bottom: 16px; padding: 18px 24px"
		>
			<i class="kt-corner tl"></i><i class="kt-corner tr"></i>
			<i class="kt-corner bl"></i><i class="kt-corner br"></i>
			<div class="kt-card-title" style="margin-bottom: 8px">Returned for correction</div>
			<p style="margin: 0 0 8px; font-size: 14.5px">{{ returnReason.reason }}</p>
			<div style="font-size: 13px; color: var(--color-neutral-600)">
				{{ returnReason.actor_label }} · {{ returnReason.occurred_label }}
			</div>
		</div>

		<div
			v-if="errorSummary"
			ref="errorEl"
			class="kt-error-summary"
			role="alert"
			tabindex="-1"
		>
			{{ errorSummary }}
		</div>

		<ContextCard :items="contextItems" />

		<div class="kt-card kt-blueprint" style="margin-bottom: 16px; padding: 20px 24px">
			<i class="kt-corner tl"></i><i class="kt-corner tr"></i>
			<i class="kt-corner bl"></i><i class="kt-corner br"></i>
			<div class="kt-card-title" style="margin-bottom: 16px">Requirement</div>
			<div class="kt-field" style="margin-bottom: 16px">
				<label for="nds-title">Title</label>
				<input id="nds-title" ref="titleEl" data-testid="nds-title" class="kt-input" type="text" v-model="form.title" />
				<div v-if="fieldErrors.title" class="kt-field-error">{{ fieldErrors.title }}</div>
			</div>
			<div class="kt-field" style="margin-bottom: 16px">
				<label for="nds-description">Description</label>
				<textarea id="nds-description" data-testid="nds-description" class="kt-input" v-model="form.description"></textarea>
			</div>
			<div class="kt-field" style="margin-bottom: 0">
				<label for="nds-result">Expected operational result</label>
				<textarea
					id="nds-result"
					data-testid="nds-result"
					class="kt-input"
					v-model="form.expected_operational_result"
				></textarea>
				<div style="font-size: 12.5px; color: var(--color-neutral-600); margin-top: 6px">
					Describe the practical result the department expects after this requirement is
					met.
				</div>
			</div>
		</div>

		<div class="kt-card kt-blueprint" style="padding: 20px 24px">
			<i class="kt-corner tl"></i><i class="kt-corner tr"></i>
			<i class="kt-corner bl"></i><i class="kt-corner br"></i>
			<div class="kt-card-title" style="margin-bottom: 16px">Quantity and timing</div>
			<div style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 16px">
				<div class="kt-field" style="margin: 0">
					<label for="nds-quantity">Indicative quantity</label>
					<input
						id="nds-quantity"
						data-testid="nds-quantity"
						class="kt-input"
						type="number"
						min="0"
						step="0.001"
						v-model="form.indicative_quantity"
					/>
				</div>
				<div class="kt-field" style="margin: 0">
					<label for="nds-unit">Unit</label>
					<!-- §12.3 — options come from the governed active catalogue. -->
					<select id="nds-unit" data-testid="nds-unit" class="kt-input" v-model="form.unit">
						<option value="">Select a unit</option>
						<option v-for="unit in units" :key="unit.name" :value="unit.name">
							{{ unit.unit_label }}
						</option>
					</select>
				</div>
			</div>
			<div class="kt-field" style="margin: 0; max-width: 340px">
				<label for="nds-required-by">Required by</label>
				<input
					id="nds-required-by"
					data-testid="nds-required-by"
					class="kt-input"
					type="date"
					v-model="form.required_by_date"
				/>
			</div>
		</div>

		<div class="kt-page-footer">
			<button class="kt-btn kt-btn-ghost" data-testid="nds-editor-cancel" :disabled="pending" @click="$emit('cancel')">
				{{ cancelLabel }}
			</button>
			<div style="display: flex; gap: 12px">
				<button class="kt-btn kt-btn-secondary" data-testid="nds-save-draft" :disabled="pending" @click="$emit('save', form)">
					Save draft
				</button>
				<button class="kt-btn kt-btn-primary" data-testid="nds-submit" :disabled="pending" @click="$emit('submit', form)">
					{{ submitLabel }}
				</button>
			</div>
		</div>
	</div>
</template>

<script setup>
import { computed, nextTick, reactive, ref, watch } from "vue";
import ContextCard from "./ContextCard.vue";
import StatusPill from "./StatusPill.vue";

const props = defineProps({
	mode: { type: String, default: "create" }, // create | correct | successor
	version: { type: Object, default: () => ({}) },
	context: { type: Object, default: () => ({}) },
	units: { type: Array, default: () => [] },
	returnReason: { type: Object, default: null },
	errorSummary: { type: String, default: "" },
	fieldErrors: { type: Object, default: () => ({}) },
	pending: Boolean,
});
defineEmits(["save", "submit", "cancel"]);

const errorEl = ref(null);
const titleEl = ref(null);

const form = reactive({
	title: "",
	description: "",
	expected_operational_result: "",
	indicative_quantity: "",
	unit: "",
	required_by_date: "",
});

watch(
	() => props.version,
	(version) => {
		form.title = version?.title || "";
		form.description = version?.description || "";
		form.expected_operational_result = version?.expected_operational_result || "";
		form.indicative_quantity =
			version?.indicative_quantity == null ? "" : version.indicative_quantity;
		form.unit = version?.unit || "";
		form.required_by_date = version?.required_by_date
			? String(version.required_by_date).slice(0, 10)
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
	create: "Create need",
	draft: "Edit need",
	correct: "Correct need",
	successor: "Update accepted need",
};
const LEDES = {
	create: "Describe one requirement your department expects to include in procurement planning.",
	draft: "Describe one requirement your department expects to include in procurement planning.",
	correct: "Correct the requirement and resubmit it for departmental review.",
	successor:
		"Propose an update to the accepted need. The accepted version stays current until this update is accepted.",
};

const heading = computed(() => HEADINGS[props.mode] || HEADINGS.create);
const lede = computed(() => LEDES[props.mode] || LEDES.create);
const statusLabel = computed(() =>
	props.mode === "create" ? "New" : props.version?.version_status || "Draft"
);
const submitLabel = computed(() =>
	["create", "draft"].includes(props.mode) ? "Submit for review" : "Resubmit for review"
);
const cancelLabel = computed(() => (props.mode === "successor" ? "Cancel update" : "Cancel"));

const contextItems = computed(() => [
	{ label: "Procuring Entity", value: props.context.procuring_entity_label || props.context.procuring_entity || "" },
	{ label: "Department", value: props.context.organisation_unit_label || props.context.organisation_unit || "" },
	{ label: "Financial Year", value: props.context.financial_year_label || props.context.financial_year || "" },
]);

defineExpose({ focusTitle: () => titleEl.value?.focus() });
</script>
