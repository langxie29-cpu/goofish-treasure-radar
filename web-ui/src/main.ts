import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import { i18n } from './i18n'
import './assets/main.css'

import { initializeBackend } from '@/lib/backend'
initializeBackend().then(() => {
const app = createApp(App)

app.use(router)
app.use(i18n)

app.mount('#app')

})
