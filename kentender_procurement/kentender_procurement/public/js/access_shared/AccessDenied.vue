<!-- The one "You do not have access to ..." state. The pack draws an access state as a lock spot, one heading and
     one reason on the white sheet below a 1px rule (`.kt-empty` + `.kt-spot`); the sizing is `.kt-access` in the
     generated kt_industry_tokens.css (Part 9). Every module reaches it through a copy of this file — a component
     cannot cross a bundle boundary (AGENTS.md §6.6) — and `kentender_core/tests/test_access_denied_copies.py` fails
     when a copy drifts. Change all four together: core, strategy, budget, procurement.
     It draws the state only: put it inside the page's `.kt-page` sheet, under the page rail. -->
<template>
	<div class="kt-empty kt-access" role="alert" :data-testid="testid">
		<span class="kt-spot is-neutral" aria-hidden="true">
			<svg class="kt-icon" viewBox="0 0 24 24"><rect x="3" y="11" width="18" height="11" rx="2" /><path d="M7 11V7a5 5 0 0 1 10 0v4" /></svg>
		</span>
		<h2>{{ title }}</h2>
		<p v-for="(line, index) in lines" :key="index">{{ line }}</p>
		<div v-if="actionLabel" class="kt-access-actions">
			<button type="button" class="btn btn-secondary" data-testid="kt-access-action" @click="$emit('action')">{{ actionLabel }}</button>
		</div>
	</div>
</template>

<script setup>
import { computed } from "vue";

const props = defineProps({
	heading: { type: String, required: true },
	// One paragraph, or several (the reason, then the hint). Empty entries are dropped.
	text: { type: [String, Array], default: "" },
	// Only where there is a safe place to go back to.
	actionLabel: { type: String, default: "" },
	testid: { type: String, default: "kt-access-denied" },
});
defineEmits(["action"]);

// A heading is a title, not a sentence: sources that wrote it with a full stop and sources that did not read the same.
const title = computed(() => props.heading.trim().replace(/\.$/, ""));
// The hint ("Ask your KenTender administrator ...") always stands as its own paragraph, whether a source sent it apart or run on.
const lines = computed(() =>
	(Array.isArray(props.text) ? props.text : [props.text])
		.flatMap((line) => String(line || "").split(/\s+(?=Ask your KenTender)/))
		.filter((line) => line.trim())
);
</script>
