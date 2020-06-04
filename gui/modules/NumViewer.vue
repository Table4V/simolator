<template>
    <span>
        <span v-b-tooltip.hover :title="value.toString(2)" class="numview">{{ value.toString(16) }}</span>
    </span>
</template>

<script>
module.exports = {
    name: 'num-viewer',
    props: ['value']
}
</script>


<style scoped>

.numview {
    text-decoration: underline dotted black;
}

</style>