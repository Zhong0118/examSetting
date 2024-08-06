import "@/assets/main.css";

import { createApp } from "vue";
import App from "./App.vue";

import { createPinia } from "pinia";
// @ts-ignore
import router from "@/router/index.js";

import 'remixicon/fonts/remixicon.css';
import PrimeVue from "primevue/config";
import Aura from "@primevue/themes/aura";
import "primeicons/primeicons.css";
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
const app = createApp(App);
const pinia = createPinia();

app.use(pinia);
app.use(router);
app.use(PrimeVue, {
  theme: {
    preset: Aura,
  },
});
app.use(ElementPlus);
app.mount("#app");
