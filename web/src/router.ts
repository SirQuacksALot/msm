import { createRouter, createWebHistory } from 'vue-router'
import ServerList from './views/ServerList.vue'
import ServerDetail from './views/ServerDetail.vue'
import ConsoleView from './views/Console.vue'
import FilesView from './views/Files.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', name: 'servers', component: ServerList },
    { path: '/servers/:id', name: 'server-detail', component: ServerDetail, props: true },
    { path: '/servers/:id/console', name: 'console', component: ConsoleView, props: true },
    { path: '/servers/:id/files', name: 'files', component: FilesView, props: true },
  ],
})

export default router