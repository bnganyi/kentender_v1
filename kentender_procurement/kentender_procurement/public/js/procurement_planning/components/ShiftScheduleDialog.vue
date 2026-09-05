<!-- PLN-DES-14A "Shift schedule from here" (§12.12): a 640px modal with the
     new forecast date for the chosen milestone, the server-computed proposed
     shift for every later not-yet-actual milestone (every row pre-included,
     independently uncheckable, never independently editable), one shared
     reason and Cancel / Confirm shift. No baseline or actual-date control. -->
<template>
	<div class="kt-dialog-backdrop" data-testid="pln-shift-dialog">
		<div class="kt-dialog" role="dialog" aria-modal="true" aria-labelledby="pln-shift-title">
			<div id="pln-shift-title" class="kt-dialog-title">Shift schedule from here — {{ milestoneLabel }}</div>
			<p class="pln-dialog-context">
				Changing {{ milestoneLabel }} recalculates every later milestone by the same number of days.
				Deselect any row you do not want to change.
			</p>

			<div class="pln-field">
				<label for="pln-shift-date">New forecast date for {{ milestoneLabel }}</label>
				<input
					id="pln-shift-date"
					type="date"
					class="kt-input"
					data-testid="pln-shift-date"
					:value="newDate"
					@change="$emit('date-change', $event.target.value)"
				/>
			</div>

			<table class="pln-table pln-shift-table">
				<thead><tr><th></th><th>Milestone</th><th>Current forecast</th><th>Proposed forecast</th></tr></thead>
				<tbody>
					<tr v-for="row in rows" :key="row.milestone" :data-testid="`pln-shift-row-${row.milestone}`">
						<td>
							<input
								type="checkbox"
								:data-testid="`pln-shift-include-${row.milestone}`"
								:checked="included.has(row.milestone)"
								:disabled="row.is_anchor"
								@change="toggle(row.milestone)"
							/>
						</td>
						<td>{{ row.label }}</td>
						<td>{{ display(row.current_forecast) }}</td>
						<td>{{ display(row.proposed_forecast) }}</td>
					</tr>
				</tbody>
			</table>
			<p v-if="!rows.length" class="pln-dialog-lede">Choose a new forecast date to see the proposed shift.</p>

			<div class="pln-field" style="margin-top: 16px">
				<label for="pln-shift-reason">Reason</label>
				<textarea id="pln-shift-reason" class="kt-input" rows="3" data-testid="pln-shift-reason" v-model="reason"></textarea>
			</div>

			<p v-if="error" class="pln-dialog-error" role="alert" data-testid="pln-shift-error">{{ error }}</p>

			<div class="kt-dialog-actions">
				<button type="button" class="kt-btn kt-btn-secondary" :disabled="pending" @click="$emit('cancel')">Cancel</button>
				<button
					type="button"
					class="kt-btn kt-btn-primary"
					data-testid="pln-shift-confirm"
					:disabled="pending || !rows.length || reason.trim().length < 20 || reason.trim().length > 500"
					@click="$emit('confirm', { included_milestones: [...included].filter((m) => rows.some((r) => r.milestone === m)), reason: reason.trim() })"
				>
					Confirm shift
				</button>
			</div>
		</div>
	</div>
</template>

<script setup>
import { reactive, ref, watch } from "vue";

const props = defineProps({
	milestoneLabel: String,
	newDate: String,
	// the server's preview rows (§8.2 PreviewForecastCascade); the dialog never computes dates itself
	rows: { type: Array, default: () => [] },
	pending: Boolean,
	error: String,
});

defineEmits(["date-change", "confirm", "cancel"]);

const reason = ref("");
const included = reactive(new Set());

// every proposed row starts included; a fresh preview re-includes what it proposes
watch(
	() => props.rows,
	(rows) => {
		for (const row of rows) if (!included.has(row.milestone)) included.add(row.milestone);
	},
	{ immediate: true }
);

function toggle(milestone) {
	if (included.has(milestone)) included.delete(milestone);
	else included.add(milestone);
}

const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
function display(iso) {
	if (!iso) return "—";
	const [y, m, d] = iso.split("-").map(Number);
	return `${d} ${MONTHS[m - 1]} ${y}`;
}
</script>
