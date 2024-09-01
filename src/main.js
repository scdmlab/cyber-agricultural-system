import './assets/main.css'

import { createApp } from 'vue'
import App from './App.vue'
import store from './store'
import 'vue-toastification/dist/index.css'
import Notifications from '@kyvg/vue3-notification'
import PrimeVue from 'primevue/config'


createApp(App)
    .use(store)
    .use(Notifications)
    .use(PrimeVue)
    .mount('#app')

store.dispatch('initializeData')
