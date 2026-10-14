<!-- The shared state page of the Contract Management boards (CM-CHG-001 v0.8 section 10.3), ported class for class from `CM Artboards.dc.html` (`s.isState`):
     D-ERR "This record could not be loaded." with Retry and Back to contracts, and D-DENIED "You do not have access to this contract." with Back to contracts only.
     One `.kt-empty` with a spot (is-error or is-neutral), one message and the actions, inside the page's `.kt-page` sheet under the page rail. It shows no record
     facts and offers no business action. The inline styles are the board's own. -->
<template>
	<div class="kt-empty" style="border-top: 0; padding: 72px 24px" role="alert" :data-testid="testid">
		<div v-if="tone === 'error'" class="kt-spot is-error">
			<svg class="kt-icon" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"></circle><path d="M12 8v4M12 16h.01"></path></svg>
		</div>
		<div v-else class="kt-spot is-neutral">
			<svg class="kt-icon" viewBox="0 0 24 24"><rect x="3" y="11" width="18" height="11" rx="2"></rect><path d="M7 11V7a5 5 0 0 1 10 0v4"></path></svg>
		</div>
		<p style="font-size: 17px; font-weight: 600; color: var(--color-heading)">{{ message }}</p>
		<div style="display: flex; gap: 10px">
			<button v-if="primary" type="button" class="btn btn-primary" data-testid="cm-state-primary" :disabled="busy" @click="$emit('primary')">{{ primary }}</button>
			<button v-for="label in secondary" :key="label" type="button" class="btn btn-secondary" data-testid="cm-state-secondary" @click="$emit('secondary', label)">{{ label }}</button>
		</div>
	</div>
</template>

<script setup>
defineProps({
	tone: { type: String, default: "error" }, // error | lock
	message: { type: String, required: true },
	primary: { type: String, default: "" },
	secondary: { type: Array, default: () => [] },
	busy: { type: Boolean, default: false },
	testid: { type: String, default: "cm-state" },
});
defineEmits(["primary", "secondary"]);
</script>
