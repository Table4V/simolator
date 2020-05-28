// import Vue from 'https://cdn.jsdelivr.net/npm/vue@2.6.11/dist/vue.esm.browser.js'


new Vue({
    el: "#app",
    components: {
        'ptw': httpVueLoader('modules/PageTableWalk.vue'),
        'displayer': httpVueLoader('modules/DisplayPTWs.vue')
    },
    data: {
        name: ""
    },
    computed: {
        showAlert() {
            return this.name.length > 4 ? true : false;
        }
    }
});

