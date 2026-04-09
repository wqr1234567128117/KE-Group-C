<template>
  <div class="login-container">
    <h2>{{ isRegister ? '用户注册' : '用户登录' }}</h2>

    <form @submit.prevent="handleSubmit">
      <div v-if="isRegister">
        <input v-model="form.real_name" placeholder="真实姓名" required />
        <input v-model="form.major" placeholder="专业" required />
      </div>

      <input v-model="form.username" placeholder="用户名" required />
      <input v-model="form.password" type="password" placeholder="密码" required />

      <button type="submit">{{ isRegister ? '注册' : '登录' }}</button>
    </form>

    <p @click="isRegister = !isRegister" class="toggle-link">
      {{ isRegister ? '已有账号？去登录' : '没有账号？去注册' }}
    </p>

    <p v-if="errorMsg" class="error">{{ errorMsg }}</p>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import api from '../api/index'

const router = useRouter()
const isRegister = ref(false)
const errorMsg = ref('')

// 统一使用 reactive 管理表单，但根据 isRegister 动态处理提交数据
const form = reactive({
  username: '',
  password: '',
  real_name: '', // 注册专用
  major: ''    // 注册专用
})

const handleSubmit = async () => {
  errorMsg.value = ''
  try {
    let res
    if (isRegister.value) {
      // --- 注册逻辑：需要传递 specific 字段 ---
      // 注意：根据新的 api.js，register 函数接收的是 (realName, major, username, password)
      // 请确保 api.js 中的 register 函数定义与此调用匹配（或者修改 api.js 为接收对象）
      // 这里假设 api.js 已按上一轮对话修改为接收对象 {real_name, major, username, password}
      res = await api.register(form.real_name, form.major, form.username, form.password)
      
      alert(res.data.message + '，请登录')
      isRegister.value = false
      // 可选：注册成功后清空表单中的敏感/专用信息
      form.real_name = ''
      form.major = ''
    } else {
      // --- 登录逻辑：只需要 username 和 password ---
      res = await api.login(form.username, form.password)
      
      // --- 数据存储逻辑 ---
      // 注意：后端返回的是 user_id 和 token
      // 修正：从 res.data 中提取数据（原代码逻辑正确，但需确认后端字段）
      const userInfo = {
        user_id: res.data.user_id, // 确保后端返回的是 user_id
        token: res.data.token,     // 确保后端返回的是 token
        username: form.username
      }
      localStorage.setItem('user_info', JSON.stringify(userInfo))
      router.push('/')
    }
  } catch (err) {
    console.error(err) // 方便调试
    // 修正：err.response?.data 可能是 {detail: "..."} 或 {message: "..."}
    errorMsg.value = err.response?.data?.detail || err.response?.data?.message || '操作失败，请检查输入'
  }
}
</script>

<style scoped>
/* 简单样式 */
.login-container { max-width: 400px; margin: 50px auto; padding: 20px; border: 1px solid #ddd; border-radius: 8px; }
input { display: block; width: 90%; margin: 10px 0; padding: 8px; }
button { width: 100%; padding: 10px; background: #42b983; color: white; border: none; cursor: pointer; }
.toggle-link { color: blue; cursor: pointer; text-align: center; margin-top: 10px; }
.error { color: red; text-align: center; }
</style>