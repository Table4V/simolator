<template>
    <div>
        Page Table Walk Sv{{ mode }}:
        <ul>
            <li>VA: 0x{{ va.data.toString(16) }}. VPN: {{ va.vpn }}. Offset: 0x{{ va.offset.toString(16) }}</li>
            <li v-for="pte of ptes">PTE Addr: @0x{{ pte.address.toString(16) }}. ppns: {{ pte.ppn }}, flags: {{ pte.attributes }}</li>
            <li>PA: 0x{{ pa.data.toString(16) }}. PPN: {{ pa.ppn }}. Offset: 0x{{ pa.offset.toString(16) }}</li>
    </div>
</template>

<script>
module.exports = {
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

<style>
</style>