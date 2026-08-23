<script setup>
defineProps({
	status: { type: String, required: true },
	tone: { type: String, default: "accent" }, // 'accent' | 'outline'
});
</script>

<template>
	<span class="kt-pp-tag" :class="`kt-pp-tag--${tone}`">{{ status }}</span>
</template>

<style scoped>
.kt-pp-tag {
	display: inline-flex;
	align-items: center;
	font-size: 11px;
	letter-spacing: 0.02em;
	padding: 3px 10px;
	border-radius: 3px;
}
.kt-pp-tag--accent {
	background: var(--ktpp-color-accent-100);
	color: var(--ktpp-color-accent-800);
}
.kt-pp-tag--outline {
	border: 1px solid var(--ktpp-color-accent);
	color: var(--ktpp-color-accent);
}
</style>
