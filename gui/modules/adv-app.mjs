
import { examples } from './examples.mjs';

new Vue({
    el: "#app",
    components: {
        'slim-ptw': httpVueLoader('modules/SlimPTW.vue' + "?h=" + Math.random().toString(16)),
        'display-ptws': httpVueLoader('modules/DisplayPTWs.vue' + "?h=" + Math.random().toString(16)),
        "ptw-viewer": httpVueLoader("modules/ExpandingPTW.vue" + "?h=" + Math.random().toString(16))
    },
    data: {
        name: "",
        show_error: false,
        error_message: "",
        examples: examples,
        // walksets: [],
        results: [],
        code: ""
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
                if (data.error) {
                    this.error_message = data.error;
                    this.show_error = true;
                    return;
                }
                this.results.push(data);
                // console.log(this.results);
                // this.walksets.push(data.walks);
            })
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
            var blob = new Blob([this.code], { type: "text/plain;charset=utf-8" });
            saveAs(blob, "code.json5");
        },
        download_results() {
            var blob = new Blob([JSON.stringify(this.results, null, 4)], { type: "application/json;charset=utf-8" });
            saveAs(blob, "results.json");
        },
        prettify() {
            this.code = js_beautify(this.code, { brace_style: 'none,preserve-inline' });
        },
    },
    mounted() {
        this.code = this.examples[0].data;
    },
});