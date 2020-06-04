// import Vue from 'https://cdn.jsdelivr.net/npm/vue@2.6.11/dist/vue.esm.browser.js'


new Vue({
    el: "#app",
    components: {
        'ptw': httpVueLoader('modules/SlimPTW.vue'),
        'display-ptws': httpVueLoader('modules/DisplayPTWs.vue'),
        'input-creator': httpVueLoader('modules/InputCreator.vue')
    },
    data: {
        name: "",
        walksets: [],
        results: [],
    },
    computed: {
        // showAlert() {
        //     return this.name.length > 4 ? true : false;
        // },
    },
    mounted() {
        // fetch('/api', {
        //     method: 'POST', // or 'PUT'
        //     headers: {
        //         'Content-Type': 'application/json',
        //     },
        //     body: JSON.stringify(this.sample_data),
        // })
        //     .then(response => response.json()).then(data => {
        //         this.results = data;
        //         this.walksets.push(data.walks);
        //     })
        // console.log(this.results);
    },
    methods: {
        process(formdata) {
            console.log('Processing form data');
            fetch('/api', {
                method: 'POST', // or 'PUT'
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(formdata),
            })
                .then(response => response.json()).then(data => {
                    // this.results = data;
                    this.walksets.push(data.walks);
                })
            console.log(this.results);
        },
    }
});

// Example POST method implementation:
function postData(url = '', data = {}) {
    // Default options are marked with *
    fetch(url, {
        method: 'POST', // or 'PUT'
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
    })
        .then(response => response.json()).then(data => {
            return data;
        }) // parses JSON response into native JavaScript objects
}
