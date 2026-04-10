<template>
  <div class="home-container">
    <div class="home-card">
      <header class="header">
        <h1>欢迎回来，<span class="highlight">{{ username }}</span></h1>
        <p class="subtitle">AI助教陪你开始你的学习之旅！</p>
      </header>

      <div class="nav-grid">
        <router-link to="/smart-qa" class="nav-card">
          <div class="card-icon">🤖</div>
          <span class="card-title">智能问答</span>
          <span class="card-desc">AI 辅助解答疑惑</span>
        </router-link>
        
        <router-link to="/learning-path" class="nav-card">
          <div class="card-icon">🗺️</div>
          <span class="card-title">学习路径</span>
          <span class="card-desc">规划你的学习路线</span>
        </router-link>
        
        <router-link to="/progress" class="nav-card">
          <div class="card-icon">📈</div>
          <span class="card-title">学习进度</span>
          <span class="card-desc">查看任务与路径</span>
        </router-link>
      </div>

      <div class="footer">
        <button @click="logout" class="logout-btn">
          <span>退出登录</span>
        </button>
      </div>
    </div>
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
/* 全局容器：负责背景色和居中 */
.home-container {
  min-height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
  font-family: 'Helvetica Neue', Helvetica, 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', Arial, sans-serif;
  padding: 20px;
  box-sizing: border-box;
}

/* 主卡片 */
.home-card {
  background: #ffffff;
  width: 100%;
  max-width: 900px;
  border-radius: 20px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.1);
  padding: 50px;
  text-align: center;
  box-sizing: border-box;
  animation: fadeIn 0.6s ease-out;
}

/* 头部样式 */
.header {
  margin-bottom: 50px;
}

.avatar {
  font-size: 3rem;
  margin-bottom: 15px;
  display: inline-block;
  animation: wave 2s infinite ease-in-out;
}

h1 {
  color: #2c3e50;
  font-size: 2rem;
  margin: 0 0 10px 0;
  font-weight: 700;
}

.highlight {
  color: #42b983;
  position: relative;
  display: inline-block;
}

.subtitle {
  color: #7f8c8d;
  margin: 0;
  font-size: 1rem;
  font-weight: 400;
}

/* 网格布局 */
.nav-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 30px;
  margin-bottom: 50px;
}

/* 导航卡片样式 */
.nav-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 30px 20px;
  text-decoration: none;
  background: #f8f9fa;
  border-radius: 15px;
  border: 1px solid #e9ecef;
  transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
  position: relative;
  overflow: hidden;
}

.nav-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 15px 30px rgba(66, 185, 131, 0.15);
  border-color: #42b983;
  background: #fff;
}

.card-icon {
  font-size: 2.5rem;
  margin-bottom: 15px;
}

.card-title {
  font-size: 1.2rem;
  font-weight: 600;
  color: #2c3e50;
  margin-bottom: 8px;
  display: block;
}

.card-desc {
  font-size: 0.85rem;
  color: #95a5a6;
  font-weight: 400;
}

/* 退出按钮 */
.logout-btn {
  background: transparent;
  color: #ff5252;
  border: 1px solid #ff5252;
  padding: 12px 30px;
  font-size: 1rem;
  cursor: pointer;
  border-radius: 50px;
  transition: all 0.3s ease;
  font-weight: 500;
  outline: none;
}

.logout-btn:hover {
  background: #ff5252;
  color: white;
  box-shadow: 0 5px 15px rgba(255, 82, 82, 0.3);
}

/* 动画定义 */
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(20px); }
  to { opacity: 1; transform: translateY(0); }
}

@keyframes wave {
  0%, 100% { transform: rotate(0deg); }
  25% { transform: rotate(10deg); }
  75% { transform: rotate(-10deg); }
}

/* 响应式调整 */
@media (max-width: 600px) {
  .home-card {
    padding: 30px 20px;
  }
  
  .nav-grid {
    grid-template-columns: 1fr; /* 手机端单列显示 */
  }
  
  h1 {
    font-size: 1.5rem;
  }
}
</style>