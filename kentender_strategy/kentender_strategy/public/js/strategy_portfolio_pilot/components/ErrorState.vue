<script setup>
const props = defineProps({
	error: { type: [Object, Error], default: null },
});
defineEmits(["retry"]);

function isPermissionError(err) {
	if (!err) return false;
	return err.exc_type === "PermissionError" || err.httpStatus === 403 || err.httpStatus === 401;
}

const message = (err) =>
	isPermissionError(err)
		? "You don't have access to this entity's portfolio."
		: "Couldn't load the strategy portfolio. Try again.";
</script>

<template>
	<div class="kt-pp-error">
		<p>{{ message(error) }}</p>
		<button type="button" class="kt-pp-btn kt-pp-btn--secondary" @click="$emit('retry')">Retry</button>
	</div>
</template>

<style scoped>
.kt-pp-error {
	padding: 54px 17px 58px;
	text-align: center;
	border: 1px solid var(--ktpp-color-divider);
}
.kt-pp-error p {
	margin: 0 0 14px;
	font-family: var(--ktpp-font-heading);
	font-size: 17px;
	color: color-mix(in srgb, var(--ktpp-color-text) 80%, transparent);
}
.kt-pp-btn {
	display: inline-flex;
	align-items: center;
	justify-content: center;
	cursor: pointer;
	font-family: var(--ktpp-font-heading);
	font-weight: var(--ktpp-font-heading-weight);
	font-size: 14px;
	padding: 7px 12px;
	border-radius: var(--ktpp-radius-md);
}
.kt-pp-btn--secondary {
	border: 1px solid var(--ktpp-color-divider);
	background: transparent;
	color: var(--ktpp-color-text);
}
.kt-pp-btn--secondary:hover {
	background: color-mix(in srgb, var(--ktpp-color-text) 7%, transparent);
}
</style>
