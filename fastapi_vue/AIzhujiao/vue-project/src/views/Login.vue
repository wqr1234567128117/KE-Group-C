<template>
  <div class="login-container">
    <div class="login-card">
      <div class="card-header">
        <div class="icon-wrapper">👋</div>
        <h2>{{ isRegister ? '创建新账号' : '欢迎回来' }}</h2>
        <p class="subtitle">{{ isRegister ? '加入我们，开启学习之旅' : '请登录您的账号' }}</p>
      </div>

      <form @submit.prevent="handleSubmit" class="login-form">
        <!-- 注册专用字段 -->
        <transition name="slide-fade">
          <div v-if="isRegister" class="extra-fields">
            <div class="input-group">
              <span class="input-icon">👤</span>
              <input v-model="form.real_name" placeholder="真实姓名" required />
            </div>
            <div class="input-group">
              <span class="input-icon">🎓</span>
              <input v-model="form.major" placeholder="专业" required />
            </div>
          </div>
        </transition>

        <!-- 通用字段 -->
        <div class="input-group">
          <span class="input-icon">🆔</span>
          <input v-model="form.username" placeholder="用户名" required />
        </div>
        
        <div class="input-group">
          <span class="input-icon">🔒</span>
          <input v-model="form.password" type="password" placeholder="密码" required />
        </div>

        <!-- 错误提示 -->
        <p v-if="errorMsg" class="error-message">
          <span class="error-icon">⚠️</span> {{ errorMsg }}
        </p>

        <button type="submit" class="submit-btn">
          {{ isRegister ? '立即注册' : '安全登录' }}
        </button>
      </form>

      <div class="card-footer">
        <p @click="isRegister = !isRegister" class="toggle-link">
          {{ isRegister ? '已有账号？去登录' : '没有账号？去注册' }}
        </p>
      </div>
    </div>
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
/* 容器：全屏居中，渐变背景 */
.login-container {
  min-height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  font-family: 'Helvetica Neue', Helvetica, 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', Arial, sans-serif;
  padding: 20px;
}

/* 卡片主体 */
.login-card {
  background: #ffffff;
  width: 100%;
  max-width: 420px;
  border-radius: 20px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  overflow: hidden;
  animation: fadeInUp 0.5s ease-out;
}

/* 头部区域 */
.card-header {
  padding: 40px 30px 20px;
  text-align: center;
}

.icon-wrapper {
  font-size: 3rem;
  margin-bottom: 15px;
  display: inline-block;
  animation: wave 2s infinite ease-in-out;
}

h2 {
  margin: 0;
  color: #2d3748;
  font-size: 1.8rem;
  font-weight: 700;
}

.subtitle {
  margin: 10px 0 0;
  color: #718096;
  font-size: 0.95rem;
}

/* 表单区域 */
.login-form {
  padding: 20px 30px;
}

/* 输入框组 */
.input-group {
  position: relative;
  margin-bottom: 20px;
  display: flex;
  align-items: center;
}

.input-icon {
  position: absolute;
  left: 15px;
  font-size: 1.2rem;
  pointer-events: none;
  color: #a0aec0;
  transition: color 0.3s;
}

input {
  width: 100%;
  padding: 14px 15px 14px 45px; /* 左侧留出图标位置 */
  box-sizing: border-box;
  border: 2px solid #e2e8f0;
  border-radius: 12px;
  font-size: 1rem;
  background: #f7fafc;
  transition: all 0.3s ease;
  outline: none;
  color: #2d3748;
}

input:focus {
  border-color: #667eea;
  background: #fff;
  box-shadow: 0 0 0 4px rgba(102, 126, 234, 0.1);
}

input:focus + .input-icon {
  color: #667eea;
}

/* 注册额外字段的动画容器 */
.extra-fields {
  overflow: hidden;
}

/* 按钮 */
.submit-btn {
  width: 100%;
  padding: 15px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 12px;
  font-size: 1.1rem;
  font-weight: 600;
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s;
  margin-top: 10px;
}

.submit-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 10px 20px rgba(118, 75, 162, 0.3);
}

.submit-btn:active {
  transform: translateY(0);
}

/* 底部切换 */
.card-footer {
  padding: 20px 30px;
  text-align: center;
  background: #f7fafc;
  border-top: 1px solid #e2e8f0;
}

.toggle-link {
  margin: 0;
  color: #667eea;
  cursor: pointer;
  font-size: 0.95rem;
  font-weight: 600;
  transition: color 0.2s;
}

.toggle-link:hover {
  color: #764ba2;
  text-decoration: underline;
}

/* 错误提示 */
.error-message {
  background: #fff5f5;
  color: #e53e3e;
  padding: 12px;
  border-radius: 8px;
  font-size: 0.9rem;
  margin-bottom: 20px;
  display: flex;
  align-items: center;
  border: 1px solid #feb2b2;
  animation: shake 0.4s ease-in-out;
}

.error-icon {
  margin-right: 8px;
}

/* 动画定义 */
@keyframes fadeInUp {
  from { opacity: 0; transform: translateY(30px); }
  to { opacity: 1; transform: translateY(0); }
}

@keyframes wave {
  0%, 100% { transform: rotate(0deg); }
  25% { transform: rotate(10deg); }
  75% { transform: rotate(-10deg); }
}

@keyframes shake {
  0%, 100% { transform: translateX(0); }
  25% { transform: translateX(-5px); }
  75% { transform: translateX(5px); }
}

/* 切换动画 */
.slide-fade-enter-active {
  transition: all 0.3s ease-out;
}

.slide-fade-leave-active {
  transition: all 0.2s cubic-bezier(1, 0.5, 0.8, 1);
}

.slide-fade-enter-from,
.slide-fade-leave-to {
  transform: translateY(-10px);
  opacity: 0;
}
</style>