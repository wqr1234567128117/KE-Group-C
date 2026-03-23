import { createRouter, createWebHistory } from 'vue-router'
import SmartQA from '../views/SmartQA.vue' // 确保路径正确

const routes = [
  {
    path: '/',
    name: 'Home',
    component: () => import('../APP.vue') // 假设已有首页
  },
  {
    path: '/smart-qa',
    name: 'SmartQA',
    component: SmartQA
  }
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes
})

export default router