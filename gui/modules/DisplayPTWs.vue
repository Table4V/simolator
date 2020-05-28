<template>
    <div>
        <p>PageTableWalks:</p>
        <ptw-viewer></ptw-viewer>
        <ptw-viewer></ptw-viewer>
        <ptw-viewer></ptw-viewer>
    </div>
</template>

<script>
module.exports = {
    components: {
        "ptw-viewer": httpVueLoader("modules/PageTableWalk.vue")
    }
};
</script>

<style scoped>
</style>