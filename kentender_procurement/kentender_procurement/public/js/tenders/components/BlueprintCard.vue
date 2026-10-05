<!-- The artboards' `card blueprint elev-sm` frame with padding 0: the shared
     .card.blueprint plus its four .corner marks, ported once. -->
<template>
	<div class="card blueprint tnd-card" v-bind="$attrs">
		<i class="corner tl"></i><i class="corner tr"></i><i class="corner bl"></i><i class="corner br"></i>
		<slot />
	</div>
</template>

<script setup>
defineOptions({ inheritAttrs: false });
</script>
