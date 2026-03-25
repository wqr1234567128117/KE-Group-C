<script setup>
import { ref } from 'vue'
// 如果以后需要路由跳转逻辑，可以在这里导入 useRouter
// import { useRouter } from 'vue-router'
// const router = useRouter()
</script>

<template>
  <div class="home-container">
    <!-- 头部欢迎区 -->
    <header class="hero-section">
      <div class="hero-content">
        <h1 class="title">🚀 智能助教系统</h1>
        <p class="subtitle">
          基于 AI 技术的智能助手，为您提供精准、高效的问答服务。<br>
          无论是技术问题、生活咨询还是创意灵感，随时为您解答。
        </p>

        <!-- 主要行动按钮 -->
        <div class="action-buttons">
          <router-link to="/smart-qa" class="btn-primary">
            <span class="icon">🤖</span> 开始智能问答
          </router-link>

          <!-- 可选：添加一个次要按钮，比如“了解更多” -->
          <!-- <a href="https://vuejs.org/" target="_blank" class="btn-secondary">
            查看文档
          </a> -->
        </div>
      </div>

      <!-- 装饰性背景元素（可选） -->
      <div class="hero-decoration">
        <div class="circle c1"></div>
        <div class="circle c2"></div>
      </div>
    </header>

    <!-- 特性展示区 (可选，增加页面丰富度) -->
    <section class="features-section">
      <div class="feature-card">
        <div class="icon-box">⚡</div>
        <h3>极速响应</h3>
        <p>毫秒级回复，无需漫长等待。</p>
      </div>
      <div class="feature-card">
        <div class="icon-box">🧠</div>
        <h3>智能理解</h3>
        <p>深度语义分析，懂你所问。</p>
      </div>
      <div class="feature-card">
        <div class="icon-box">🛡️</div>
        <h3>安全可靠</h3>
        <p>数据加密传输，保护隐私。</p>
      </div>
    </section>

    <footer class="home-footer">
      <p>&copy; 2026 SmartQA System. All rights reserved.</p>
    </footer>
  </div>
</template>

<style scoped>
/* 整体容器 */
.home-container {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
  color: #333;
}

/* 英雄区域 (Hero Section) */
.hero-section {
  position: relative;
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  text-align: center;
  padding: 40px 20px;
  overflow: hidden;
}

.hero-content {
  position: relative;
  z-index: 2;
  max-width: 800px;
  animation: fadeIn Up 0.8s ease-out;
}

.title {
  font-size: 3.5rem;
  font-weight: 800;
  color: #2c3e50;
  margin-bottom: 20px;
  letter-spacing: -1px;
  text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
}

.subtitle {
  font-size: 1.25rem;
  color: #555;
  line-height: 1.6;
  margin-bottom: 40px;
  max-width: 600px;
  margin-left: auto;
  margin-right: auto;
}

/* 按钮样式 */
.action-buttons {
  display: flex;
  gap: 20px;
  justify-content: center;
  flex-wrap: wrap;
}

.btn-primary {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  padding: 16px 32px;
  background: linear-gradient(90deg, #42b983 0%, #35495e 100%);
  color: white;
  text-decoration: none;
  border-radius: 50px;
  font-size: 1.1rem;
  font-weight: bold;
  box-shadow: 0 4px 15px rgba(66, 185, 131, 0.4);
  transition: all 0.3s ease;
}

.btn-primary:hover {
  transform: translateY(-3px);
  box-shadow: 0 8px 25px rgba(66, 185, 131, 0.6);
}

.btn-primary .icon {
  font-size: 1.4rem;
}

/* 特性卡片区域 */
.features-section {
  display: flex;
  justify-content: center;
  gap: 30px;
  padding: 60px 20px;
  background-color: white;
  flex-wrap: wrap;
}

.feature-card {
  background: #fff;
  padding: 30px;
  border-radius: 15px;
  box-shadow: 0 10px 30px rgba(0,0,0,0.05);
  width: 250px;
  text-align: center;
  transition: transform 0.3s ease;
  border: 1px solid #eee;
}

.feature-card:hover {
  transform: translateY(-10px);
}

.icon-box {
  font-size: 3rem;
  margin-bottom: 15px;
}

.feature-card h3 {
  margin: 10px 0;
  color: #2c3e50;
}

.feature-card p {
  color: #7f8c8d;
  font-size: 0.95rem;
  line-height: 1.5;
}

/* 页脚 */
.home-footer {
  text-align: center;
  padding: 20px;
  color: #7f8c8d;
  font-size: 0.9rem;
  background-color: rgba(255,255,255,0.5);
}

/* 背景装饰圆圈 */
.hero-decoration {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
  z-index: 1;
}

.circle {
  position: absolute;
  border-radius: 50%;
  opacity: 0.1;
}

.c1 {
  width: 300px;
  height: 300px;
  background: #42b983;
  top: -50px;
  right: -50px;
}

.c2 {
  width: 200px;
  height: 200px;
  background: #35495e;
  bottom: 50px;
  left: -50px;
}

/* 动画定义 */
@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(30px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* 移动端适配 */
@media (max-width: 768px) {
  .title {
    font-size: 2.5rem;
  }
  .subtitle {
    font-size: 1rem;
  }
  .features-section {
    flex-direction: column;
    align-items: center;
  }
  .feature-card {
    width: 100%;
    max-width: 300px;
  }
}
</style>