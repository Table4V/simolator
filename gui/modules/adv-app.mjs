new Vue({
    el: "#app",
    components: {
        'ptw': httpVueLoader('modules/SlimPTW.vue'),
        'display-ptws': httpVueLoader('modules/DisplayPTWs.vue'),
    },
    data: {
        name: "",
        walksets: [],
        results: [],
        code: `{
    // comments
    mode: 48, // Sv48
    // Sample JSON for running test cases
    memory_size: 0x3000000000, // 192 GB
    test_cases: [
        {
            repeats: 4,
            ptes: [
                {},
                {},
                {},
                {
                    attributes: {
                        // Set the flags (RSW, DAGUXWRV) probabilistically on the PTE
                        G: 0.5, // Float for probabilities
                        U: 1, // 0 - 1 aren't probabilities
                        X: 0.5, // Float for probabilities
                        W: 0, // 0 - 1 aren't probabilities
                        R: 1, // 0 - 1 aren't probabilities
                    },
                },
            ],
        },
        {
            repeats: 4,
            ptes: [
                {},
                {
                    // PTE entry -- set the address
                    address: 0xcafebabe0,
                },
                {},
            ],
        },
        {
            repeats: 4,
            ptes: [
                {
                    // PTE entry -- set the address
                    // If you use a list where a number is needed, it'll choose at random
                    address: [0xdeadbeef0, 0xcafebabe0],
                },
                {},
                {},
            ],
        },
        {
            repeats: 2,
            // Specifying an entire path
            ptes: [
                { address: 0x00001452876690 },
                { address: 0x000011fd18ccb8 },
                { address: 0x000027960d1f80 },
                { address: 0x0000264afd7c28 },
            ],
        },
        {
            repeats: 2,
            // SATP + VA = exact same path
            satp: { ppn: 0xb00ffff000 },
            va: 0xf00fb00f,
        },
        {
            repeats: 4,
            same_va_pa: 1,
        },
        {
            repeats: 2,
            same_va_pa: 1,
            aliasing: 1,
        },
        {
            satp: { ppn: 0xb00ffff000 },
            va: 0xf00ff0000,
        },
        {
            satp: { ppn: 0xb00ffff000 },
            va: 0xf00ff0008,
        },
        {
            repeats: 5,
            reuse_pte: 1,
        },
    ],
}`
    },
    methods: {
        process() {
            console.log('Processing data');
            fetch('/api/json5', {
                method: 'POST', // or 'PUT'
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ 'code': this.code }),
            }).then(response => response.json()).then(data => {
                this.results.push(data);
                this.walksets.push(data.walks);
            })
            // console.log(this.results);
        },
        drop(ev) {
            console.log('File(s) dropped');
            // Prevent default behavior (Prevent file from being opened)
            ev.preventDefault();
            var file = ev.dataTransfer.files[0];
            var self = this;
            file.text().then(text => self.code = text);
        },
        download_code() {
            var blob = new Blob([this.code], {type: "text/plain;charset=utf-8"});
            saveAs(blob, "code.json5");
        },
        download_results() {
            var blob = new Blob([JSON.stringify(this.results, null, 4)], {type: "application/json;charset=utf-8"});
            saveAs(blob, "results.json");
        },

    },
    // mounted() {
    //     var dropArea = this.$refs.left_col;
    //     console.log('Droparea registered');
    //     dropArea.addEventListener('drop', (event) => {
    //         console.log('dropped');
    //         event.stopPropagation();
    //         event.preventDefault();
    //         const fileList = event.dataTransfer.files;
    //         console.log(fileList);
    //     });
    // },
});