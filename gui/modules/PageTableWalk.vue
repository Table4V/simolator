<template>
    <b-container fluid class="walkview">
        <b-row>
            <b-col>
                VA: <num-viewer :value="va.data"></num-viewer>.
                VPN: <num-viewer v-for="part of va.vpn" :value="part"></num-viewer>
                Offset: <num-viewer :value="va.offset"></num-viewer></b-col>
            <b-col
                v-for="pte of ptes"
                :key="pte.address"
            >PTE Addr: @0x{{ pte.address.toString(16) }}. ppns: {{ pte.ppn }}, flags: {{ pte.attributes }}</b-col>
            <b-col>PA: 0x{{ pa.data.toString(16) }}. PPN: {{ pa.ppn }}. Offset: 0x{{ pa.offset.toString(16) }}</b-col>
        </b-row>
    </b-container>
</template>

<script>
module.exports = {
    components: {
        "num-viewer": httpVueLoader("modules/NumViewer.vue")
    },
    name: "ptw-viewer",
    // props: ["vpn", "ppn", "ptes"],
    data: function() {
        return {
            ptes: [
                {
                    ppn: [364, 157, 109, 102434],
                    data: null,
                    address: 26711593323095336,
                    attributes: {
                        RSW: 0,
                        D: 0,
                        A: 0,
                        G: null,
                        U: 0,
                        X: 0,
                        W: 0,
                        R: 0,
                        V: 1
                    }
                },
                {
                    ppn: [129, 89, 427, 52894],
                    data: null,
                    address: 56313804408408104,
                    attributes: {
                        RSW: 0,
                        D: 0,
                        A: 0,
                        G: null,
                        U: 0,
                        X: 0,
                        W: 0,
                        R: 0,
                        V: 1
                    }
                },
                {
                    ppn: [511, 378, 122, 5423],
                    data: null,
                    address: 29079242694728008,
                    attributes: {
                        RSW: 0,
                        D: 0,
                        A: 0,
                        G: null,
                        U: 0,
                        X: 0,
                        W: 0,
                        R: 0,
                        V: 1
                    }
                },
                {
                    ppn: [366, 389, 494, 69629],
                    data: null,
                    address: 2981457570035096,
                    attributes: {
                        RSW: 0,
                        D: null,
                        A: null,
                        G: null,
                        U: null,
                        X: null,
                        W: null,
                        R: null,
                        V: 1
                    }
                }
            ],
            va: {
                data: 90990579497277,
                offset: 2365,
                vpn: [179, 297, 261, 165]
            },
            pa: {
                data: 38279478810962237,
                ppn: [366, 389, 494, 69629],
                offset: 2365
            },
            satp: {
                mode: 48,
                asid: 0,
                ppn: 6521385088646
            },
            mode: 48,
            startLevel: 3,
            endLevel: 0
        };
    }
};
</script>

<style scoped>
.walkview {
    font-family: Consolas, "Courier New", Courier, monospace;
}
</style>