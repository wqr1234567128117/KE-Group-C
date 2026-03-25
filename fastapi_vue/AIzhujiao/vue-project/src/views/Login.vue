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

const form = reactive({
  username: '',
  password: '',
  real_name: '',
  major: ''
})

const handleSubmit = async () => {
  errorMsg.value = ''
  try {
    let res
    if (isRegister.value) {
      // 注册
      res = await api.register(form)
      alert(res.data.message + ', 请登录')
      isRegister.value = false
    } else {
      // 登录
      res = await api.login(form.username, form.password)
      // 保存用户信息
      const userInfo = {
        user_id: res.data.user_id,
        token: res.data.token,
        username: form.username
      }
      localStorage.setItem('user_info', JSON.stringify(userInfo))
      router.push('/')
    }
  } catch (err) {
    errorMsg.value = err.response?.data?.detail || '操作失败，请检查输入'
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