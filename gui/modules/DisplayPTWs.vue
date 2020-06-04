<template>
    <b-container fluid>
        <p>PageTableWalks:</p>
        <ptw-viewer></ptw-viewer>
        <ptw-viewer></ptw-viewer>
        <ptw-viewer></ptw-viewer>
    </b-container>
</template>

<script>
module.exports = {
    components: {
        "ptw-viewer": httpVueLoader("modules/TabularPTW.vue")
    }
};
</script>

<style scoped>
</style>