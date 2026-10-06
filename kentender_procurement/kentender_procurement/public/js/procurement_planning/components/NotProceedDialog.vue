<!-- PLN-CHG-001 v1.24 §10.4 U03-EXCLUDE, ported class-for-class from
     Artboards-U02-U05.dc.html. Confirms `SetNeedPlanningDisposition` (Do not
     proceed) for one Need-origin entry; the caller owns the actual API call,
     idempotency key and entry id. Re-diffed 22 Sep 2026 against the actual
     v1.24 U03-EXCLUDE section (this header previously cited that file from
     before it existed in the repo — see kentender_core's
     test_artboard_provenance_gate): title, fact block, field label, body
     copy and actions all match; no drift found. -->
<template>
	<div class="dialog-backdrop" data-testid="pln-not-proceed-dialog">
		<div class="dialog" style="width: 520px" role="dialog" aria-modal="true" aria-labelledby="pln-not-proceed-title">
			<div id="pln-not-proceed-title" class="dialog-title">Exclude from this year's departmental plan</div>
			<div v-if="title">
				<div style="font-weight: 600">{{ title }}</div>
				<div v-if="reference" class="kt-muted" style="font-size: 12.5px; margin-top: 2px">{{ reference }}</div>
			</div>
			<div class="pln-field">
				<label for="pln-not-proceed-reason">Reason for excluding this requirement</label>
				<textarea
					id="pln-not-proceed-reason" class="input" rows="3"
					data-testid="pln-not-proceed-reason" v-model="reason"
				></textarea>
			</div>
			<p class="kt-muted">This requirement stays on record. Its budget line and amount will be cleared from this draft.</p>
			<p v-if="error" class="pln-dialog-error" role="alert" data-testid="pln-not-proceed-error">
				{{ error }}
			</p>
			<div class="dialog-actions">
				<button class="btn btn-secondary" :disabled="pending" @click="$emit('cancel')">
					Cancel
				</button>
				<button
					class="btn btn-primary" data-testid="pln-not-proceed-confirm"
					:disabled="pending || reason.trim().length < 20"
					@click="$emit('confirm', reason.trim())"
				>
					Exclude requirement
				</button>
			</div>
		</div>
	</div>
</template>

<script setup>
import { ref } from "vue";

defineProps({
	pending: Boolean,
	error: String,
	// §10.4 U03-EXCLUDE — the requirement the exclusion applies to, so the
	// dialog says which one rather than assuming the caller's own context.
	title: { type: String, default: "" },
	reference: { type: String, default: "" },
});
defineEmits(["confirm", "cancel"]);

const reason = ref("");
</script>
