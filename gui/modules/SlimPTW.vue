<template>
    <b-container fluid class="walkview" v-bind:class=" { 'error' : error_type }">
        <b-row v-if="walk.satp.ppn != global_satp.ppn">
            <b-col style="text-align: center;">
                <span class="error_msg">SATP: {{ phex(walk.satp.ppn) }}</span>
            </b-col>
        </b-row>
        <b-row no-gutters outlined>
            <b-col>
                VA:
                <span
                    class="data_tooltip"
                    v-bind:class="{ 'reuse': va.reuse, 'same_va_pa': va.same_va_pa}"
                    v-b-tooltip
                    :title="popup_arr([va.offset].concat(va.vpn))"
                >{{ phex(va.data) }}</span>
            </b-col>
            <b-col v-for="pte of ptes" :key="pte.address">
                PTE @
                <span v-bind:class="{ 'reuse': pte.reuse }">{{ phex(pte.address) }}</span>
                <br />Data:
                <span
                    class="data_tooltip"
                    v-b-tooltip
                    :title="popup_arr(pte.ppn)"
                >{{ phex(pte.contents) }}</span>
            </b-col>
            <b-col>
                PA:
                <span
                    class="data_tooltip"
                    v-bind:class="{ 'reuse': pa.reuse, 'same_va_pa': pa.same_va_pa}"
                    v-b-tooltip
                    :title="popup_arr([pa.offset].concat(pa.ppn))"
                >{{ phex(pa.data) }}</span>
            </b-col>
        </b-row>
        <b-row v-if="error_type">
            <b-col style="text-align: center;">
                <span class="error_msg">Exception: {{ error_type }}</span>
            </b-col>
        </b-row>
    </b-container>
</template>

<script>
module.exports = {
    name: "slim-ptw",
    methods: {
        hex(n) {
            if (n == null) return '???';
            return n.toString(16);
        },
        phex(n) {
            if (n == null) return '???';
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
                var x = " ";
                if (item != null) x = item.toString(16);
                h_arr.unshift(x);
            }
            return h_arr.join(" | ");
        }
    },
    // props: ["vpn", "ppn", "ptes"]
    props: ["walk", "global_satp"],
    computed: {
        va() {
            return this.walk.va;
        },
        pa() {
            return this.walk.pa;
        },
        ptes() {
            return this.walk.ptes;
        },
        error_type() {
            return this.walk.error_type || null;
        }
    }
};
</script>

<style scoped>
.walkview {
    font-family: Consolas, "Courier New", Courier, monospace;
    font-size: 10pt;
}

.data_tooltip {
    text-decoration: underline;
    text-decoration-style: dotted;
}

.reuse {
    color: darkred;
}

.same_va_pa {
    background-color: lightskyblue;
}

.error_msg {
    font-weight: bold;
}

/* 
.error {
    background-color: orange;
} */
</style>