<!-- PLN-CHG-001 v1.23 §10.7 — Add selected requirements (U08), ported from
     U08.dc.html.

     Three things in this order: what was selected, how it should be added, and
     what that will produce. The selection itself was already made on the plan
     behind this panel, so it is shown here as fact, not re-offered as
     checkboxes — re-picking here would let the panel disagree with the rows
     highlighted behind it.

     Combining is the consequential choice, so the reason for it is asked here,
     where the Planner is holding it, rather than left to be discovered later as
     a readiness blocker in the purchase editor. There is no partial quantity
     control and no implicit combining. -->
<template>
	<div class="kt-dialog-backdrop" data-testid="pln-form-dialog">
		<div class="kt-dialog pln-form-dialog" role="dialog" aria-modal="true" aria-labelledby="pln-form-title">
			<div id="pln-form-title" class="kt-dialog-title" data-testid="pln-form-title">How should these requirements be added?</div>

			<!-- U08-DUPLICATE/INCOMPLETE — a named source and its concrete
			     problem, above the choice. There is nothing to add, so nothing
			     offers to add it. -->
			<div v-if="blocked" class="kt-notice is-critical" data-testid="pln-form-blocked">
				<svg class="kt-notice-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
					<path d="M18 6L6 18M6 6l12 12"></path>
				</svg>
				<div class="kt-notice-body">{{ blocked }}</div>
			</div>

			<template v-else>
				<table class="kt-table" data-testid="pln-form-sources">
					<thead>
						<tr>
							<th>Requirement</th><th>Department</th>
							<th class="is-num">Quantity</th><th>Unit</th><th class="is-num">Estimated cost</th>
						</tr>
					</thead>
					<tbody>
						<tr v-for="row in entries" :key="row.dpp_entry" data-testid="pln-form-source-row">
							<td>
								{{ row.title }}
								<div class="kt-muted pln-row-ref">{{ row.entry_id }}</div>
							</td>
							<td>{{ row.department }}</td>
							<td class="is-num">{{ row.quantity_number }}</td>
							<td>{{ row.unit_label }}</td>
							<td class="is-num">{{ row.amount_display }}</td>
						</tr>
					</tbody>
				</table>

				<!-- U08-INCOMPATIBLE — said before the choice, so the disabled
				     option reads as explained rather than broken. -->
				<div v-if="!combinable" class="kt-notice is-warning" data-testid="pln-form-incompatible">
					<svg class="kt-notice-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
						<path d="M12 3l9 16H3z"></path><path d="M12 10v4M12 17h.01"></path>
					</svg>
					<div class="kt-notice-body">{{ incompatibleText }}</div>
				</div>

				<!-- U08's own segmented toggle (`.seg`/`.seg-opt`), not two bare
				     radio labels — same component Tenders already ported under
				     `.kt-tnd .tnd-seg[-opt]`; this is the Planning-scoped copy. -->
				<div v-if="entries.length > 1" class="pln-seg" role="radiogroup" aria-label="How should these requirements be added?">
					<label class="pln-seg-opt">
						<input type="radio" value="each" v-model="mode" data-testid="pln-form-mode-each">
						Keep separate
					</label>
					<label class="pln-seg-opt" :class="{ 'is-disabled': !combinable }">
						<input
							type="radio"
							value="combined"
							v-model="mode"
							:disabled="!combinable"
							data-testid="pln-form-mode-combined"
						>
						Combine into one purchase
					</label>
				</div>

				<template v-if="effectiveMode === 'combined'">
					<div class="kt-field">
						<label for="pln-form-reason" class="kt-label">Reason for combining</label>
						<textarea
							id="pln-form-reason"
							class="kt-input"
							rows="3"
							data-testid="pln-form-reason"
							v-model="reason"
						></textarea>
						<div class="kt-field-hint">20–500 characters.</div>
					</div>
					<div class="kt-field">
						<label for="pln-form-title-input" class="kt-label">Purchase title</label>
						<input id="pln-form-title-input" class="kt-input" data-testid="pln-form-title-input" v-model="combinedTitle">
					</div>
				</template>

				<!-- What the choice will actually produce. -->
				<div class="kt-card pln-form-preview" data-testid="pln-form-preview">
					<div class="kt-meta-row">
						<div>
							<span class="kt-label">Purchases</span>
							<span class="kt-meta-value" data-testid="pln-form-purchases">{{ purchases }}</span>
						</div>
						<template v-if="effectiveMode === 'combined'">
							<div>
								<span class="kt-label">Total quantity</span>
								<span class="kt-meta-value">{{ totalQuantityDisplay }}</span>
							</div>
							<div>
								<span class="kt-label">Estimated cost</span>
								<span class="kt-meta-value">{{ totalCostDisplay }}</span>
							</div>
							<div>
								<span class="kt-label">Purchase title</span>
								<span class="kt-meta-value" data-testid="pln-form-preview-title">{{ combinedTitle }}</span>
							</div>
						</template>
					</div>
					<!-- Keeping them separate produces one purchase per source,
					     each with its own scope; the rows say so. -->
					<table v-if="effectiveMode === 'each'" class="kt-table" data-testid="pln-form-preview-rows">
						<tbody>
							<tr v-for="row in entries" :key="row.dpp_entry">
								<td>{{ row.title }}</td>
								<td class="is-num">{{ row.quantity_number }} {{ row.unit_label }}</td>
								<td class="is-num">{{ row.amount_display }}</td>
							</tr>
						</tbody>
					</table>
				</div>
			</template>

			<p v-if="error" class="pln-dialog-error" role="alert" data-testid="pln-form-error">{{ error }}</p>

			<div class="kt-dialog-actions">
				<button type="button" class="kt-btn kt-btn-secondary" :disabled="pending" @click="$emit('cancel')">Cancel</button>
				<button
					v-if="!blocked"
					type="button"
					class="kt-btn kt-btn-primary"
					data-testid="pln-form-confirm"
					:disabled="pending || !canAdd"
					@click="confirm"
				>
					Add to plan
				</button>
			</div>
		</div>
	</div>
</template>

<script setup>
import { computed, ref } from "vue";

const props = defineProps({
	entries: { type: Array, default: () => [] },
	pending: Boolean,
	error: String,
});

const emit = defineEmits(["confirm", "cancel"]);

const mode = ref("each");
const reason = ref("");

// U08-INCOMPATIBLE — the server supplies each source's combinable identity
// from the one rule the formation command enforces, so the choice is offered
// exactly where the command would accept it, and the reason named here is the
// difference that actually blocks it.
const DIMENSIONS = [
	["budget", "They draw on different budgets."],
	["classification", "They are different requirement types."],
	["unit", "They are measured in different units."],
	["origin", "They come from different kinds of requirement."],
];

const conflicts = computed(() =>
	DIMENSIONS.filter(
		([dimension]) => new Set(props.entries.map((row) => (row.combination_key || {})[dimension])).size > 1,
	).map(([, reason]) => reason),
);

const combinable = computed(() => props.entries.length > 1 && !conflicts.value.length);
const incompatibleText = computed(() =>
	conflicts.value.length
		? `These requirements cannot be combined. Add them as separate purchases. ${conflicts.value.join(" ")}`
		: "",
);

// One source makes one purchase; there is no second choice to make.
const effectiveMode = computed(() => (combinable.value ? mode.value : "each"));

const purchases = computed(() => (effectiveMode.value === "combined" ? 1 : props.entries.length));

// U08-DUPLICATE/INCOMPLETE — a source the plan can no longer draw on.
const blocked = computed(() => {
	const stale = props.entries.find((row) => row.unavailable_reason);
	return stale ? `${stale.title} ${stale.unavailable_reason}` : "";
});

// Quantities combine only where the unit is the same. Two units are two facts,
// and adding them would produce a number that means nothing.
const totalQuantityDisplay = computed(() => {
	const units = new Set(props.entries.map((row) => row.unit_label));
	const total = props.entries.reduce((sum, row) => sum + Number(row.quantity || 0), 0);
	if (units.size === 1) return `${total} ${[...units][0]}`;
	return props.entries.map((row) => `${row.quantity_number} ${row.unit_label}`).join(" + ");
});

const totalCostDisplay = computed(() => {
	const total = props.entries.reduce((sum, row) => sum + Number(row.indicative_amount || 0), 0);
	return `KES ${total.toLocaleString("en-KE")}`;
});

const defaultTitle = computed(() => props.entries.map((row) => row.title).join(" + ").slice(0, 160));
const combinedTitle = ref(defaultTitle.value);

const canAdd = computed(() => {
	if (!props.entries.length) return false;
	if (effectiveMode.value !== "combined") return true;
	const length = reason.value.trim().length;
	return length >= 20 && length <= 500 && Boolean(combinedTitle.value.trim());
});

function confirm() {
	emit("confirm", {
		dppEntries: props.entries.map((row) => row.dpp_entry),
		mode: effectiveMode.value,
		combinationReason: effectiveMode.value === "combined" ? reason.value.trim() : "",
		combinedTitle: effectiveMode.value === "combined" ? combinedTitle.value.trim() : "",
	});
}
</script>
