<!-- The artboards' `card blueprint elev-sm` frame with padding 0: the shared
     .kt-card.kt-blueprint plus its four .kt-corner marks, ported once. -->
<template>
	<div class="kt-card kt-blueprint tnd-card" v-bind="$attrs">
		<i class="kt-corner tl"></i><i class="kt-corner tr"></i><i class="kt-corner bl"></i><i class="kt-corner br"></i>
		<slot />
	</div>
</template>

<script setup>
defineOptions({ inheritAttrs: false });
</script>
