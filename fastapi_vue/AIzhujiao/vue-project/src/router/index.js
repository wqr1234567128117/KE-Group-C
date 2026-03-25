import { createRouter, createWebHistory } from 'vue-router'
import Home from '../views/Home.vue'
import SmartQA from '../views/SmartQA.vue'
// 需要新建以下组件
import Login from '../views/Login.vue'
import LearningPath from '../views/LearningPath.vue'
import Progress from '../views/Progress.vue'

const routes = [
  { path: '/login', name: 'Login', component: Login },
  {
    path: '/',
    name: 'Home',
    component: Home,
    meta: { requiresAuth: true }
  },
  {
    path: '/smart-qa',
    name: 'SmartQA',
    component: SmartQA,
    meta: { requiresAuth: true }
  },
  {
    path: '/learning-path',
    name: 'LearningPath',
    component: LearningPath,
    meta: { requiresAuth: true }
  },
  {
    path: '/progress',
    name: 'Progress',
    component: Progress,
    meta: { requiresAuth: true }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 简单路由守卫
router.beforeEach((to, from, next) => {
  const user = localStorage.getItem('user_info')
  if (to.meta.requiresAuth && !user) {
    next('/login')
  } else {
    next()
  }
})

export default router