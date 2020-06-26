<template>
    <b-container fluid class="walkview">
        <!-- White because of errors -->
        <b-row no-gutters >
            <b-col>
                <b-table-simple small outlined class="bg-white">
                    <b-tr>
                        <b-td variant="dark">VA</b-td>
                        <b-td :colspan="va.vpn.length">{{ phex(va.data) }}</b-td>
                    </b-tr>
                    <b-tr>
                        <b-td :colspan="va.vpn.length" variant="dark">VPN</b-td>
                        <!-- <b-td -->
                            <!-- variant="dark"
                            v-for="n in va.vpn.length"
                            :key="n"
                        > -->
                        <!-- VPN{{ va.vpn.length - n }} -->
                        <!-- </b-td> -->
                        <b-td variant="dark">Off</b-td>
                    </b-tr>
                    <b-tr>
                        <b-td
                            v-for="(item, index) in va.vpn.slice().reverse()"
                            :key="index"
                        >{{ hex(item) }}</b-td>
                        <b-td>{{hex(va.offset)}}</b-td>
                    </b-tr>
                </b-table-simple>
            </b-col>
            <b-col v-for="pte of ptes" :key="pte.address">
                <b-table-simple small outlined class="bg-white">
                    <b-tr>
                        <b-td variant="dark">PTE</b-td>
                        <b-td :colspan="pte.ppn.length">{{ phex(pte.address) }}</b-td>
                    </b-tr>
                    <b-tr>
                        <b-td variant="dark" :colspan="pte.ppn.length">PPN</b-td>
                        <!-- <b-td
                            variant="dark"
                            v-for="n in pte.ppn.length"
                            :key="n"
                        >PPN{{ pte.ppn.length - n }}</b-td> -->
                        <b-td variant="dark" style="text-align: right">RSDAGUXWRV</b-td>
                    </b-tr>
                    <b-tr>
                        <b-td
                            v-for="(item, index) in pte.ppn.slice().reverse()"
                            :key="index"
                        >{{ hex(item) }}</b-td>
                        <b-td style="text-align: right">
                            <span style="white-space:pre">{{ flagstring(pte.attributes) }}</span>
                        </b-td>
                    </b-tr>
                </b-table-simple>
            </b-col>
            <b-col>
                <b-table-simple small outlined class="bg-white">
                    <b-tr>
                        <b-td variant="dark">PA</b-td>
                        <b-td :colspan="pa.ppn.length">{{ phex(pa.data) }}</b-td>
                    </b-tr>
                    <b-tr>
                        <b-td variant="dark" :colspan="pa.ppn.length">PPN</b-td>
                        <!-- <b-td
                            variant="dark"
                            v-for="n in pa.ppn.length"
                            :key="n"
                        >PPN{{ pa.ppn.length - n }}</b-td> -->
                        <b-td variant="dark">Off</b-td>
                    </b-tr>
                    <b-tr>
                        <b-td
                            v-for="(item, index) in pa.ppn.slice().reverse()"
                            :key="index"
                        >{{ hex(item) }}</b-td>
                        <b-td>{{ hex(pa.offset) }}</b-td>
                    </b-tr>
                </b-table-simple>
            </b-col>
        </b-row>
    </b-container>
</template>

<script>
module.exports = {
    // components: {
    //     "num-viewer": httpVueLoader("modules/NumViewer.vue")
    // },
    name: "tabular-ptw",
    methods: {
        hex(n) {
            return n.toString(16) || '???';
        },
        phex(n) {
            return "0x" + n.toString(16);
        },
        flagstring(attrs) {
            var s = '00';
            for (var flag of 'DAGUXWRV') {
                var c = attrs[flag];
                if (c == null) c = ' ';
                s += c;
            }
            return s;
        }
    },
    // props: ["vpn", "ppn", "ptes"]
    props: ["walk"],
    computed: {
        va() {
            return this.walk.va;
        },
        pa() {
            return this.walk.pa;
        },
        ptes() {
            return this.walk.ptes;
        }
    }
};
</script>

<style scoped>
.walkview {
    font-family: Consolas, "Courier New", Courier, monospace;
    font-size: 10pt;
}


.table-sm td, .table-sm th {
    padding: 0.1rem;
}
</style>