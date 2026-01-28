import { createRouter, createWebHashHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'
import DifyView from '../views/DifyView.vue'
import TestView from '../views/TestView.vue'

const routes = [
  { path: '/', component: HomeView },
  { path: '/dify', component: DifyView },
  { path: '/test', component: TestView }
]

const router = createRouter({
  history: createWebHashHistory(),
  routes
})

export default router