<template>
    <b-container fluid class="form_input">
        <b-form @submit="emit_data">
            <b-form-row>
                <b-col>
                    Mode:
                    <b-form-select v-model="form.mode" :options="[32, 39, 48]"></b-form-select>
                </b-col>
                <b-col>
                    Memory Size:
                    <b-form-input v-model="form.memory_size"></b-form-input>
                </b-col>
                <b-col>
                    Lowest Memory Address:
                    <b-form-input v-model="form.lower_bound"></b-form-input>
                </b-col>
                <b-col>
                    Page sizes:
                    <b-form-checkbox-group v-model="form.pagesize" :options="pagesizes_available"></b-form-checkbox-group>
                </b-col>
                <b-col>
                    SATP:
                    <b-form-input v-model="form.satp.ppn" placeholder="0x123456"></b-form-input>
                </b-col>
            </b-form-row>
            <b-form-row>
                <b-col>
                    Error Probability:
                    <b-form-input v-model="form.errors.p" number placeholder="0.05"></b-form-input>
                </b-col>
                <b-col>
                    VA = PA Probability:
                    <b-form-input v-model="form.same_va_pa" number placeholder="0.05"></b-form-input>
                </b-col>
                <b-col>
                    Aliasing Probability:
                    <b-form-input v-model="form.aliasing" number placeholder="0.05"></b-form-input>
                </b-col>
                <b-col>
                    Repeats:
                    <b-form-input v-model="form.repeats" number></b-form-input>
                </b-col>
                <b-col>
                    &nbsp;
                    <!-- <b-form-group> -->
                    <b-button variant="primary" type="submit" class="form-control">Run</b-button>
                    <!-- </b-form-group> -->
                </b-col>
            </b-form-row>
        </b-form>
    </b-container>
</template>

<script>
module.exports = {
    // components: {
    //     "num-viewer": httpVueLoader("modules/NumViewer.vue")
    // },
    name: "input-creator",
    data: function() {
        return {
            form: {
                repeats: 1,
                mode: 39,
                memory_size: null,
                lower_bound: null,
                pagesize: [],
                satp: { ppn: null },
                same_va_pa: 0,
                aliasing: 0,
                errors: {
                    p: 0,
                    types: [
                        "mark_invalid",
                        "write_no_read",
                        "leaf_as_pointer",
                        "uncleared_superpage"
                    ],
                    weights: [1, 1, 1, 1]
                }
            }
        };
    },
    methods: {
        hex(n) {
            return n.toString(16);
        },
        phex(n) {
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
        emit_data(evt) {
            evt.preventDefault();
            this.$emit('emit_data', this.form);
            // console.log(JSON.stringify(this.form));
        }
    },
    // props: ["vpn", "ppn", "ptes"]
    // props: [],
    computed: {
        pagesizes_available() {
            if (this.form.mode == 32) return ["4K", "4M"];
            if (this.form.mode == 39) return ["4K", "2M", "1G"];
            if (this.form.mode == 48) return ["4K", "2M", "1G", "512G"];
            return [];
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