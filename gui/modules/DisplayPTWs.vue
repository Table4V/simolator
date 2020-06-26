<template>
    <b-container fluid class="ptwdisplayer">
        <b-card no-body class="mb-1">
            <b-card-header header-tag="header" class="p-1" role="tab">
                <b-button
                    :pressed.sync="show_panel"
                    block
                    variant="info"
                >{{ walkset.walks.length }} PTWs. SATP: {{ phex(walkset.global_satp.ppn) }}</b-button>
            </b-card-header>
            <b-collapse v-model="show_panel">
                <b-card-body class="p-0">
                    <ptw-viewer
                        v-for="(walk, index) in walkset.walks"
                        :key="index"
                        :walk="walk"
                        :global_satp="walkset.global_satp"
                    ></ptw-viewer>
                </b-card-body>
            </b-collapse>
        </b-card>
    </b-container>
</template>

<script>
module.exports = {
    components: {
        "ptw-viewer": httpVueLoader(
            "modules/ExpandingPTW.vue" + "?h=" + Math.random().toString(16)
        )
    },
    props: ["walkset", "createdJSON"],
    data: function() {
        return {
            show_panel: true
        };
    },
    methods: {
        phex(n) {
            if (n == null) return "";
            return "0x" + n.toString(16);
        }
    }
};
</script>

<style scoped>
/* .ptwdisplayer {
    width: 1400px;
} */
</style>