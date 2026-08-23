<script setup>
defineProps({
	items: { type: Array, required: true }, // [{ label, ref }]
});
</script>

<template>
	<section class="kt-pp-mywork">
		<h3>My work</h3>
		<div class="kt-pp-mywork__list">
			<button
				v-for="item in items"
				:key="item.ref"
				type="button"
				class="kt-pp-mywork__row"
				title="Pilot — not wired to a live action"
			>
				<span>{{ item.label }}</span>
				<span class="kt-pp-mywork__ref">{{ item.ref }}</span>
			</button>
		</div>
	</section>
</template>

<style scoped>
.kt-pp-mywork {
	max-width: 620px;
}
.kt-pp-mywork h3 {
	font-size: 13px;
	letter-spacing: 0.08em;
	text-transform: uppercase;
	color: color-mix(in srgb, var(--ktpp-color-text) 60%, transparent);
	margin-bottom: 6px;
}
.kt-pp-mywork__list {
	border-top: 1px solid var(--ktpp-color-divider);
}
.kt-pp-mywork__row {
	width: 100%;
	display: flex;
	align-items: baseline;
	gap: 12px;
	padding: 10px 2px;
	border: 0;
	border-bottom: 1px solid color-mix(in srgb, var(--ktpp-color-text) 8%, transparent);
	background: transparent;
	cursor: pointer;
	text-align: left;
	font: inherit;
	color: var(--ktpp-color-text);
}
.kt-pp-mywork__row:hover {
	background: color-mix(in srgb, var(--ktpp-color-text) 4%, transparent);
}
.kt-pp-mywork__ref {
	margin-left: auto;
	font-family: var(--ktpp-font-heading);
	font-size: 12px;
	letter-spacing: 0.08em;
	color: var(--ktpp-color-accent-700);
}
</style>
