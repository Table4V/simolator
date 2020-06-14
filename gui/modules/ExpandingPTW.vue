// Shows the SlimPTW, expands to the Tabular on click

<template>
    <b-container fluid>
        <b-card no-body class="mb-1 p-0">
            <!-- <b-card-header header-tag="header" class="p-1" role="tab">
                <b-button :pressed.sync="show_panel" block variant="info">{{ walks.length }} PTWs</b-button>
            </b-card-header>-->
            <b-row>
                <b-col cols="11">
                    <slim-ptw :data="data"></slim-ptw>
                </b-col>
                <b-col cols="1">
                    <b-button
                        :pressed.sync="show_panel"
                        variant="info"
                    >{{ show_panel ? "Hide" : "Show" }}</b-button>
                </b-col>
            </b-row>
            <b-collapse v-model="show_panel">
                <tabular-ptw :data="data"></tabular-ptw>
            </b-collapse>
        </b-card>
    </b-container>
</template>

<script>
module.exports = {
    components: {
        "slim-ptw": httpVueLoader("modules/SlimPTW.vue"),
        "tabular-ptw": httpVueLoader("modules/TabularPTW.vue")
    },
    name: "ptw-xview",
    props: ["data"],
    data: function() {
        return {
            show_panel: false
        };
    }
};
</script>

<style>
/* .walkview {
    font-family: Consolas, "Courier New", Courier, monospace;
    font-size: 10pt;
} */

/* .va_data {
    text-decoration: underline;
    text-decoration-style: dotted;
} */
</style>