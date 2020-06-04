<template>
    <b-container fluid class="walkview">
        <b-row no-gutters>
            <b-col>
                <b-table-simple small outlined>
                    <b-tr>
                        <b-td variant="dark">VA</b-td>
                        <b-td colspan="4">{{ phex(va.data) }}</b-td>
                    </b-tr>
                    <b-tr>
                        <b-td colspan="4" variant="dark">VPN</b-td>
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
                <b-table-simple small outlined>
                    <b-tr>
                        <b-td variant="dark">PTE</b-td>
                        <b-td colspan="2" variant="dark">Address</b-td>
                        <b-td colspan="2">{{ phex(pte.address) }}</b-td>
                    </b-tr>
                    <b-tr>
                        <b-td
                            variant="dark"
                            v-for="n in pte.ppn.length"
                            :key="n"
                        >PPN{{ pte.ppn.length - n }}</b-td>
                        <b-td variant="dark">RSDAGUXWRV</b-td>
                    </b-tr>
                    <b-tr>
                        <b-td
                            v-for="(item, index) in pte.ppn.slice().reverse()"
                            :key="index"
                        >{{ hex(item) }}</b-td>
                        <b-td>
                            <span style="white-space:pre">{{ flagstring(pte.attributes) }}</span>
                        </b-td>
                    </b-tr>
                </b-table-simple>
            </b-col>
            <b-col>
                <b-table-simple small outlined>
                    <b-tr>
                        <b-td variant="dark">PA</b-td>
                        <b-td colspan="4">{{ phex(pa.data) }}</b-td>
                    </b-tr>
                    <b-tr>
                        <b-td
                            variant="dark"
                            v-for="n in pa.ppn.length"
                            :key="n"
                        >PPN{{ pa.ppn.length - n }}</b-td>
                        <b-td variant="dark">Offset</b-td>
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
    components: {
        "num-viewer": httpVueLoader("modules/NumViewer.vue")
    },
    name: "ptw-viewer",
    methods: {
        hex(n) {
            return n.toString(16);
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
    props: ["data"],
    computed: {
        va() {
            return this.data.va;
        },
        pa() {
            return this.data.pa;
        },
        ptes() {
            return this.data.ptes;
        }
    }
};
</script>

<style scoped>
.walkview {
    font-family: Consolas, "Courier New", Courier, monospace;
    font-size: 10pt;
}
</style>