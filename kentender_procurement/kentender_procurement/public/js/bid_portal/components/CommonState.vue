<script setup>
// BDS-CHG-001 v0.8 §10.17 BDS-DES-16 — one common state replacing the
// affected content surface: the catalogue's heading, message and one action
// (bid_submission/common_states.json, the same file the server reads). The
// caller names the state, gives the figures its message names (the deadline,
// a correlation, a receipt) and where the action leads; `inline` draws it in
// place of one part of a page rather than the whole page. `retry` uses the
// state's retry action (Try confirmation again) when the server permits one.
import { computed } from "vue";
import catalogue from "../../../../bid_submission/common_states.json";

const props = defineProps({
	state: { type: String, required: true },
	figures: { type: Object, default: () => ({}) },
	actionHref: { type: String, default: "" },
	inline: { type: Boolean, default: false },
	retry: { type: Boolean, default: false },
});
const emit = defineEmits(["action"]);

const STATES = Object.fromEntries(catalogue.states.map((entry) => [entry.key, entry]));
const entry = computed(() => STATES[props.state] || STATES["page-not-found"]);
const message = computed(() => (entry.value.message || "").replace(/\{(\w+)\}/g, (_match, name) => (props.figures[name] ?? "").toString()));
const action = computed(() => (props.retry && entry.value.retry_action) || entry.value.action || "");
</script>

<template>
	<div v-if="inline" class="kt-notice is-critical bds-state-inline" role="alert" :data-testid="'bds-state-' + state">
		<svg class="kt-notice-icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="10" /><path d="M12 8v4M12 16h.01" /></svg>
		<div class="kt-notice-body">
			<strong>{{ __(entry.heading) }}</strong>
			<div v-if="message">{{ message }}</div>
			<div v-if="action" class="bds-state-action">
				<a v-if="actionHref" class="btn btn-secondary" :href="actionHref">{{ __(action) }}</a>
				<button v-else type="button" class="btn btn-secondary" @click="emit('action')">{{ __(action) }}</button>
			</div>
		</div>
	</div>
	<div v-else class="kt-page bds-state" :data-testid="'bds-state-' + state">
		<h1 class="bds-state-heading">{{ __(entry.heading) }}</h1>
		<p v-if="message" class="bds-state-message">{{ message }}</p>
		<div v-if="action" class="bds-state-action">
			<a v-if="actionHref" class="btn btn-secondary" :href="actionHref">{{ __(action) }}</a>
			<button v-else type="button" class="btn btn-secondary" @click="emit('action')">{{ __(action) }}</button>
		</div>
	</div>
</template>
