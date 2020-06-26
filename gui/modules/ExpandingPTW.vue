// Shows the SlimPTW, expands to the Tabular on click

<template>
    <b-container fluid>
        <b-card no-body class="mb-1 p-0" v-bind:class=" { 'bg-warning' : walk.error_type }">
            <!-- <b-card-header header-tag="header" class="p-1" role="tab">
                <b-button :pressed.sync="show_panel" block variant="info">{{ walks.length }} PTWs</b-button>
            </b-card-header>-->
            <!-- <b-row v-if="walk.satp.ppn != global_satp.ppn">SATP: {{ phex(walk.satp.ppn) }}</b-row> -->
            <!-- <b-row v-if="walk.satp.ppn != global_satp.ppn">
                <b-col style="text-align: center;" class="bg-info">
                    <span class="error_msg">SATP: {{ phex(walk.satp.ppn) }}</span>
                </b-col>
            </b-row> -->
            <b-row>
                <b-col cols="11">
                    <slim-ptw :walk="walk" :global_satp="global_satp"></slim-ptw>
                </b-col>
                <b-col cols="1">
                    <b-button
                        :pressed.sync="show_panel"
                        variant="info"
                    >{{ show_panel ? "Hide" : "Show" }}</b-button>
                </b-col>

                <!-- <b-col cols="1">
                    <b-button @click="show_edit = !show_edit">Edit</b-button>
                </b-col>-->
            </b-row>
            <!-- <b-collapse v-model="show_edit">
                <b-button @click="edit_walk">Apply</b-button>
                <v-jsoneditor v-model="walk"></v-jsoneditor>
            </b-collapse>-->
            <!-- <b-modal v-model="show_panel" size="xl"> -->
            <b-collapse v-model="show_panel">
                <tabular-ptw :walk="walk"></tabular-ptw>
            </b-collapse>
            <!-- </b-modal> -->
        </b-card>
    </b-container>
</template>

<script>
module.exports = {
    components: {
        "slim-ptw": httpVueLoader(
            "modules/SlimPTW.vue" + "?h=" + Math.random().toString(16)
        ),
        "tabular-ptw": httpVueLoader(
            "modules/TabularPTW.vue" + "?h=" + Math.random().toString(16)
        )
    },
    name: "ptw-viewer",
    props: ["walk", "global_satp"],
    data: function() {
        return {
            show_panel: false,
            show_edit: false,
            localdata: null
        };
    },
    methods: {
        phex(n) {
            if (n == null) return "";
            return "0x" + n.toString(16);
        }
        // edit_data() {
        //     var mod_data = this.localdata;
        //     mod_data["test_cases"] = [JSON.parse(JSON.stringify(this.localdata))];
        //     console.log("Processing edit data");
        //     fetch("/api", {
        //         method: "POST", // or 'PUT'
        //         headers: {
        //             "Content-Type": "application/json"
        //         },
        //         body: JSON.stringify(mod_data)
        //     })
        //         .then(response => response.json())
        //         .then(data => {
        //             this.results = data;
        //             this.localdata = data[0];
        //         });
        //     console.log(this.results);
        // }
    },
    mounted() {
        this.localdata = this.data;
    }
};
</script>

<style>
.walkview {
    font-family: Consolas, "Courier New", Courier, monospace;
    font-size: 10pt;
}


.error_msg {
    font-weight: bold;
}
/* .va_data {
    text-decoration: underline;
    text-decoration-style: dotted;
} */
</style>