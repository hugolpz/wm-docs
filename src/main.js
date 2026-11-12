import './styles.css'
import { createApp } from 'vue'
import { createRouter, createWebHashHistory } from 'vue-router'
import App from './App.vue'
import { groups } from './groups.js'
import { applyTheme, initialTheme } from './theme.js'

// Light/dark: the saved choice, else light; tokens.css reads data-theme
applyTheme(initialTheme(), { persist: false })

// Hash history: Toolforge's static hosting has no fallback to index.html for deep links.
// Spendings keeps its column filters in the query string: #/wmfr?project=wikipages
const router = createRouter({
  history: createWebHashHistory(),
  routes: [
    { path: '/', name: 'home', component: () => import('./views/HomeView.vue') },
    ...groups.map((g) => ({ path: `/${g.slug}`, name: g.slug, component: g.view })),
  ],
})

createApp(App).use(router).mount('#app')
