<!-- REQ-DES-12 common and access states: the state message and its safe
     recovery replace (never sit above) stale task or decision content. -->
<template>
	<div v-if="kind === 'forbidden'" class="kt-page" data-testid="req-state-forbidden">
		<AccessDenied :heading="forbidden.heading" :text="forbidden.text" />
	</div>
	<div v-else class="kt-panel-lg req-page" :data-testid="`req-state-${kind}`">
		<template v-if="kind === 'loading'">
			<div style="display: flex; flex-direction: column; gap: 10px" aria-busy="true" aria-label="Loading">
				<div class="kt-skel" style="height: 22px; width: 45%"></div>
				<div class="kt-skel" style="height: 12px; width: 75%"></div>
				<div class="kt-skel" style="height: 12px; width: 30%; margin-top: 16px"></div>
				<div class="kt-skel" style="height: 44px; width: 100%"></div>
				<div class="kt-skel" style="height: 44px; width: 100%"></div>
			</div>
		</template>
		<template v-else-if="kind === 'not-found'">
			<div style="border-top: 1px solid var(--kt-color-divider); padding-top: var(--kt-space-4)">
				<div class="req-question" style="margin: 0">Requisition not found</div>
				<div class="req-actions" style="margin-top: var(--kt-space-4)"><button type="button" class="btn btn-secondary" @click="$emit('back')">Back to Requisitions</button></div>
			</div>
		</template>
		<template v-else-if="kind === 'error'">
			<h3 style="margin: 0">Procurement Requisitions</h3>
			<p class="kt-muted req-lede" style="margin-top: 6px">Prepare and follow requests for purchases already approved in the annual plan.</p>
			<Notice tone="critical">Procurement Requisitions could not be loaded.</Notice>
			<div class="req-actions" style="margin-top: var(--kt-space-4)"><button type="button" class="btn btn-secondary" data-testid="req-try-again" @click="$emit('retry')">Try again</button></div>
		</template>
	</div>
</template>

<script setup>
import { computed } from "vue";
import AccessDenied from "../../../access_shared/AccessDenied.vue";
import Notice from "./Notice.vue";

const props = defineProps({ kind: { type: String, required: true }, message: { type: String, default: "" } });
defineEmits(["back", "retry"]);

// The server sends one exact-copy message (§13.13): the opening sentence says what is denied, the rest says why and what to do.
const forbidden = computed(() => {
	const [heading, ...rest] = props.message.split(/(?<=\.)\s+/);
	return { heading: heading || "You do not have access to Procurement Requisitions", text: rest };
});
</script>
