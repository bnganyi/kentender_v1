<!-- Shared loading / load-error / not-found (§11.3 TPR_NOT_FOUND: "Tender not
     found", an unauthorised read looks exactly like a missing record) / Forbidden states (KT-STD-001 §3A.2: a
     page-load denial is an inline state, never a modal; nothing else painted
     first). -->
<template>
	<div v-if="loading" class="kt-card kt-blueprint" style="padding: 0; overflow: hidden" :data-testid="`${prefix}-loading`">
		<i class="kt-corner tl"></i><i class="kt-corner tr"></i><i class="kt-corner bl"></i><i class="kt-corner br"></i>
		<div v-for="row in 3" :key="row" class="tpr-skel-row">
			<div class="kt-skel" style="width: 72%"></div>
			<div class="kt-skel" style="width: 52%"></div>
			<div class="kt-skel" style="width: 44%"></div>
		</div>
	</div>
	<div v-else-if="error" class="kt-card kt-blueprint tpr-state-card" :data-testid="`${prefix}-error`">
		<i class="kt-corner tl"></i><i class="kt-corner tr"></i><i class="kt-corner bl"></i><i class="kt-corner br"></i>
		<h3>Tender Preparation could not be loaded.</h3>
		<p>Try again. If the problem continues, quote the support reference shown below.</p>
		<button type="button" class="kt-btn kt-btn-secondary" @click="$emit('reload')">Try again</button>
		<p class="tpr-support-ref">Support reference: {{ supportRef }}</p>
	</div>
	<div v-else-if="notFound" class="kt-card kt-blueprint tpr-state-card" :data-testid="`${prefix}-not-found`">
		<i class="kt-corner tl"></i><i class="kt-corner tr"></i><i class="kt-corner bl"></i><i class="kt-corner br"></i>
		<h3>Tender not found.</h3>
		<p>The record is absent or not visible to you.</p>
		<button type="button" class="kt-btn kt-btn-secondary" @click="$emit('home')">Return to workspace</button>
	</div>
	<div v-else-if="forbidden" class="kt-card kt-blueprint tpr-state-card" :data-testid="`${prefix}-forbidden`">
		<i class="kt-corner tl"></i><i class="kt-corner tr"></i><i class="kt-corner bl"></i><i class="kt-corner br"></i>
		<h3>{{ forbidden.heading }}</h3>
		<p>{{ forbidden.text }}</p>
	</div>
</template>

<script setup>
defineProps({ loading: Boolean, error: String, supportRef: String, forbidden: Object, notFound: Boolean, prefix: { type: String, default: "tpr" } });
defineEmits(["reload", "home"]);
</script>
