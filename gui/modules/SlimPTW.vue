<template>
    <b-container fluid class="walkview">
        <b-row no-gutters outlined>
            <b-col>
                VA:
                <span
                    class="va_data"
                    v-b-tooltip
                    :title="popup_arr([va.offset].concat(va.vpn))"
                >{{ phex(va.data) }}</span>
            </b-col>
            <b-col v-for="pte of ptes" :key="pte.address">
                PTE @ {{ phex(pte.address) }}
                <br />Data:
                <span
                    class="va_data"
                    v-b-tooltip
                    :title="popup_arr(pte.ppn)"
                >{{ phex(pte.contents) }}</span>
            </b-col>
            <b-col>
                PA:
                <span
                    class="va_data"
                    v-b-tooltip
                    :title="popup_arr([pa.offset].concat(pa.ppn))"
                >{{ phex(pa.data) }}</span>
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
            if (n == null) return '';
            return n.toString(16);
        },
        phex(n) {
            if (n == null) return '';
            return "0x" + n.toString(16);
        },
        flagstring(attrs) {
            var s = "00";
            for (var flag of "DAGUXWRV") {
                var c = attrs[flag];
                if (c == null) c = " ";
                s += c;
            }
            return s;
        },
        popup_arr(arr) {
            var h_arr = [];
            for (item of arr) {
                var x = ' ';
                if (item != null) x =  item.toString(16);
                h_arr.unshift(x);
            }
            return h_arr.join(" | ");
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

.va_data {
    text-decoration: underline;
    text-decoration-style: dotted;
}
</style>