<template>
  <div class="home">
    <h1>欢迎回来，{{ username }}</h1>
    <div class="nav-grid">
      <router-link to="/smart-qa" class="nav-card">🤖 智能问答</router-link>
      <router-link to="/learning-path" class="nav-card">🗺️ 学习路径</router-link>
      <router-link to="/progress" class="nav-card">📈 学习进度</router-link>
    </div>
    <button @click="logout" class="logout-btn">退出登录</button>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const user = JSON.parse(localStorage.getItem('user_info'))
const username = ref(user?.username || '用户')

const logout = () => {
  localStorage.removeItem('user_info')
  router.push('/login')
}
</script>

<style scoped>
.home { text-align: center; padding: 40px; }
.nav-grid { display: flex; justify-content: center; gap: 20px; margin: 40px 0; }
.nav-card { display: block; padding: 40px; font-size: 1.2em; text-decoration: none; color: white; background: #42b983; border-radius: 10px; width: 200px; }
.logout-btn { background: #ff5252; color: white; border: none; padding: 10px 20px; cursor: pointer; border-radius: 5px; }
</style>