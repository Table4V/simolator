<template>
    <b-container fluid class="ptwdisplayer">
        <b-card no-body class="mb-1">
            <b-card-header header-tag="header" class="p-1" role="tab">
                <b-button :pressed.sync="show_panel" block variant="info">{{ walks.length }} PTWs</b-button>
            </b-card-header>
            <b-collapse v-model="show_panel">
                <b-card-body class="p-0">
                    <ptw-viewer v-for="(result, index) in walks" :key="index" :data="result"></ptw-viewer>
                </b-card-body>
            </b-collapse>
        </b-card>
    </b-container>
</template>

<script>
module.exports = {
    components: {
        "ptw-viewer": httpVueLoader("modules/ExpandingPTW.vue")
    },
    props: ["walks", "createdJSON"],
    data: function() {
        return {
            show_panel: true
        };
    }
};
</script>

<style scoped>

/* .ptwdisplayer {
    width: 1400px;
} */

</style>