<template>
  <div class="lp-container">
    <!-- 左侧：配置区域 -->
    <div class="lp-sidebar">
      <div class="lp-header">
        <h3>学习配置</h3>
        <div class="header-actions">
          <span class="points-badge">🍞 1 积分</span>
          <button class="icon-btn" @click="handleReset" title="重置">↺ 重置</button>
        </div>
      </div>

      <!-- 学习领域选择 -->
      <div class="form-section">
        <label class="section-title">🎓 学习领域</label>
        <div class="domain-grid">
          <div
            v-for="item in domains"
            :key="item.key"
            class="domain-card"
            :class="{ active: form.domain === item.key }"
            @click="form.domain = item.key"
          >
            <span class="domain-icon">{{ item.icon }}</span>
            <span class="domain-label">{{ item.label }}</span>
          </div>
        </div>
      </div>

      <!-- 学习目标输入 -->
      <div class="form-section">
        <label class="section-title">🎯 学习目标</label>
        <input
          v-model="form.goal"
          class="lp-input"
          placeholder="请输入您的学习目标"
        />
      </div>
      <div class="form-section">
        <label class="section-title">🎯 学习水平</label>
        <input
          v-model="form.goal"
          class="lp-input"
          placeholder="请输入您的当前水平"
        />
      </div>
      <div class="form-section">
        <label class="section-title">🎯 学习天数</label>
        <input
          v-model="form.goal"
          class="lp-input"
          placeholder="请输入您的学习目标天数"
        />
      </div>

      <!-- 背景与计划输入 -->
      <div class="form-section">
        <label class="section-title">☰ 学习背景与计划</label>
        <div class="textarea-wrapper">
          <textarea
            v-model="form.background"
            class="lp-textarea"
            placeholder="请描述您的基础情况或学习计划..."
          ></textarea>
          <span class="word-count">{{ form.background.length }} 字</span>
        </div>
      </div>

      <!-- 生成按钮 -->
      <button class="generate-btn" @click="generate">
        快速生成
      </button>
      <button class="generate-btn" @click="goToCustomize">
          个性化定制
       </button>
    </div>

    <!-- 右侧：结果展示区域 -->
    <div class="lp-main">
      <div class="result-header">
        <h3 class="result-title">✨ 生成的学习路径</h3>
        <button
          class="copy-btn"
          @click="copyPath"
          :disabled="!currentPath"
        >
          复制
        </button>
        <button>
          保存
        </button>
      </div>

      <div class="result-content">
        <!-- 加载状态 -->
        <div v-if="loading" class="loading-state">
          <div class="spinner"></div>
          <p>PROCESSING...</p>
        </div>

        <!-- 结果展示 -->
        <div v-else-if="currentPath" class="path-display">
          <div
            v-for="(step, idx) in currentPath"
            :key="idx"
            class="path-item"
          >
            <div class="step-index">{{ idx + 1 }}</div>
            <div class="step-content">{{ step }}</div>
          </div>
        </div>

        <!-- 初始空状态 -->
        <div v-else class="empty-state">
          <p>请在左侧配置学习参数以生成路径</p>
        </div>
      </div>

      <!-- 底部评分 -->
      <div class="result-footer">
        <div class="rating">
          <span>用户评分</span>
          <div class="stars">★★★★★</div>
          <span class="score">4.7 / 5.0</span>
        </div>
        <div class="user-count">👥 16 人已评价</div>
      </div>
    </div>

  </div>
  <!-- 历史记录区域 -->
<div class="history-section">
  <div class="history-header">
    <h3>📜 历史学习路径</h3>
    <button class="refresh-btn" @click="fetchHistory" :disabled="historyLoading">
      🔄 刷新记录
    </button>
  </div>
  <div class="history-table-container">
    <!-- 表格头部 -->
    <div class="table-header-grid">
      <div class="table-cell">ID</div>
      <div class="table-cell">学习目标</div>
      <div class="table-cell">领域</div>
      <div class="table-cell">生成时间</div>
      <div class="table-cell">操作</div>
    </div>
    <!-- 表格内容 -->
    <div class="table-body">
      <div v-if="historyLoading" class="loading-row">
        <div class="spinner"></div> 正在加载历史记录...
      </div>
      <div v-else-if="learningHistory.length === 0" class="empty-row">
        暂无历史记录
      </div>
      <div
        v-for="record in learningHistory"
        :key="record.id"
        class="table-row"
      >
        <div class="table-cell">{{ record.id }}</div>
        <div class="table-cell truncate" :title="record.goal">{{ record.goal }}</div>
        <div class="table-cell">
          <span class="domain-tag">{{ getDomainLabel(record.domain) }}</span>
        </div>
        <div class="table-cell">{{ formatDate(record.created_at) }}</div>
        <div class="table-cell">
          <button class="action-btn view" @click="viewPath(record)">查看</button>
          <button class="action-btn delete" @click="deletePath(record.id)">删除</button>
        </div>
      </div>
    </div>
  </div>
</div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router' // 1. 引入路由模块
import api from '../api/index'

// 模拟用户信息
const user = JSON.parse(localStorage.getItem('user_info'))
const userId = user?.user_id

// 领域选项数据
const domains = [
  { key: 'career', label: '职业技能', icon: '💻' },
  { key: 'language', label: '语言学习', icon: '🈯' },
  { key: 'academic', label: '学术研究', icon: '⚗️' },
  { key: 'hobby', label: '兴趣爱好', icon: '🎨' },
  { key: 'exam', label: '考试备考', icon: '📘' },
  { key: 'other', label: '其他领域', icon: '...' },
]

// 表单数据
const form = reactive({
  domain: 'other',
  goal: '',
  background: '',
})

const currentPath = ref(null)
const loading = ref(false)
const router = useRouter() // 2. 创建 router 实例


// 生成路径逻辑
const generate = async () => {
  if (!form.goal) {
    alert('请输入学习目标')
    return
  }

  loading.value = true
  currentPath.value = null // 清空旧结果

  try {
    // 模拟 API 调用，实际请替换为 api.generatePath
    // const res = await api.generatePath(userId, form.goal, form.domain, form.background)
    // currentPath.value = res.data.path

    // 这里仅作演示延时
    setTimeout(() => {
      currentPath.value = [
        '第一步：环境搭建与基础语法学习',
        '第二步：核心概念（变量、循环、函数）',
        '第三步：实战项目练习',
        '第四步：进阶库（如Pandas/NumPy）学习',
      ]
      loading.value = false
    }, 1500)
  } catch (e) {
    alert('生成失败，请稍后重试')
    loading.value = false
  }
}

// 重置功能
const handleReset = () => {
  form.goal = ''
  form.background = ''
  form.domain = 'other'
  currentPath = null
}

// 3. 新增：跳转函数
const goToCustomize = () => {
  router.push('/person-learning-path') // 跳转到目标路由
}

// 复制功能
const copyPath = () => {
  if (!currentPath.value) return
  const text = currentPath.value.join('\n')
  navigator.clipboard.writeText(text).then(() => {
    alert('路径已复制到剪贴板')
  })
}

// ... 之前的代码 ...

// --- 新增：历史记录相关逻辑 ---
const learningHistory = ref([]) // 存储历史记录列表
const historyLoading = ref(false) // 加载状态

// 模拟从数据库获取历史记录
const fetchHistory = async () => {
  historyLoading.value = true
  try {
    // 模拟 API 延迟
    await new Promise(resolve => setTimeout(resolve, 800))

    // 模拟数据结构，实际应从 api.fetchHistory() 获取
    // 这里假设数据包含 id, goal, domain, created_at 字段
    const mockData = [
      { id: 1, goal: 'Python 全栈开发', domain: 'career', created_at: '2024-04-01T10:00:00Z', path: currentPath.value || ['Python基础', 'Django框架', '项目部署'] },
      { id: 2, goal: '通过英语六级考试', domain: 'exam', created_at: '2024-03-28T15:30:00Z', path: ['词汇积累', '听力特训', '真题模拟'] },
    ]
    learningHistory.value = mockData
  } catch (error) {
    console.error('获取历史记录失败:', error)
    alert('加载历史记录失败')
  } finally {
    historyLoading.value = false
  }
}

// 辅助函数：根据 domain key 获取标签
const getDomainLabel = (key) => {
  const item = domains.find(d => d.key === key)
  return item ? item.label : '未知领域'
}

// 辅助函数：格式化时间
const formatDate = (isoString) => {
  const date = new Date(isoString)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

// 操作函数：查看某条路径
const viewPath = (record) => {
  // 将历史记录填充到当前展示区
  currentPath.value = record.path
  // 可以滚动到页面上方查看
  document.querySelector('.lp-main').scrollIntoView({ behavior: 'smooth' })
}

// 操作函数：删除路径 (模拟)
const deletePath = (id) => {
  if (confirm('确定要删除这条记录吗？')) {
    learningHistory.value = learningHistory.value.filter(item => item.id !== id)
    alert('删除成功')
  }
}

// 组件挂载后自动加载一次历史记录
fetchHistory()
</script>

<style scoped>
/* 整体布局：左右分栏 */
.lp-container {
  display: flex;
  gap: 20px;
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
  background-color: #fcfcfc;
  min-height: 100vh;
}

/* 左侧侧边栏 */
.lp-sidebar {
  flex: 1;
  background: #fff;
  padding: 24px;
  border-radius: 12px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.03);
  border: 1px solid #eee;
}

.lp-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  color: #999;
  font-size: 14px;
}

.points-badge {
  background: #fff4e5;
  color: #e6a23c;
  padding: 4px 8px;
  border-radius: 6px;
  font-size: 12px;
  margin-right: 10px;
}

.icon-btn {
  background: none;
  border: none;
  color: #999;
  cursor: pointer;
  font-size: 12px;
}

/* 表单区域 */
.section-title {
  display: block;
  margin-bottom: 12px;
  font-weight: 600;
  color: #333;
  font-size: 14px;
}

/* 领域网格 */
.domain-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
  margin-bottom: 24px;
}

.domain-card {
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  padding: 16px 8px;
  text-align: center;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: #555;
  background: #fff;
}

.domain-card:hover {
  border-color: #a585ff;
  background: #f8f5ff;
}

.domain-card.active {
  border-color: #6c5ce7;
  background: #f0ebff;
  color: #5642b5;
  font-weight: 600;
  box-shadow: 0 0 0 1px #6c5ce7 inset;
}

.domain-icon {
  font-size: 20px;
}

/* 输入框样式 */
.lp-input {
  width: 100%;
  padding: 12px;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  background: #f9f9f9;
  font-size: 14px;
  box-sizing: border-box;
  margin-bottom: 24px;
  outline: none;
  transition: border 0.2s;
}

.lp-input:focus {
  border-color: #6c5ce7;
  background: #fff;
}

.textarea-wrapper {
  position: relative;
}

.lp-textarea {
  width: 100%;
  height: 120px;
  padding: 12px;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  background: #f9f9f9;
  font-size: 14px;
  box-sizing: border-box;
  resize: none;
  outline: none;
  font-family: inherit;
}

.lp-textarea:focus {
  border-color: #6c5ce7;
  background: #fff;
}

.word-count {
  position: absolute;
  bottom: 8px;
  right: 12px;
  font-size: 12px;
  color: #999;
  background: rgba(255, 255, 255, 0.8);
  padding: 0 4px;
}

/* 生成按钮 */
.generate-btn {
  width: 100%;
  padding: 14px;
  background: linear-gradient(90deg, #6c5ce7, #a585ff);
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: opacity 0.2s;
  margin-top: 10px;
}

.generate-btn:hover {
  opacity: 0.9;
}

/* 右侧主内容区 */
.lp-main {
  flex: 1.2;
  background: #fff;
  border-radius: 12px;
  border: 1px solid #eee;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  position: relative;
  min-height: 600px;
}

.result-header {
  padding: 20px 24px;
  border-bottom: 1px solid #f0f0f0;
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: #fcfcfc;
}

.result-title {
  margin: 0;
  color: #4834d4;
  font-size: 16px;
  font-weight: 600;
}

.copy-btn {
  background: #f0f0f0;
  border: 1px solid #ddd;
  padding: 6px 12px;
  border-radius: 6px;
  font-size: 12px;
  cursor: pointer;
  color: #555;
}

.copy-btn:hover {
  background: #e0e0e0;
}

/* 内容区域 */
.result-content {
  flex: 1;
  padding: 40px;
  display: flex;
  justify-content: center;
  align-items: center;
  background: #fdfdfd;
}

/* 加载动画 */
.loading-state {
  text-align: center;
  color: #6c5ce7;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 15px;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 4px solid #e0e0e0;
  border-top: 4px solid #6c5ce7;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

/* 路径列表样式 */
.path-display {
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.path-item {
  display: flex;
  align-items: flex-start;
  gap: 15px;
  background: white;
  padding: 15px;
  border-radius: 8px;
  border: 1px solid #f0f0f0;
  box-shadow: 0 2px 5px rgba(0,0,0,0.02);
}

.step-index {
  background: #6c5ce7;
  color: white;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: bold;
  flex-shrink: 0;
  margin-top: 2px;
}

.step-content {
  font-size: 14px;
  color: #333;
  line-height: 1.6;
}

.empty-state {
  color: #999;
  font-size: 14px;
}

/* 底部 */
.result-footer {
  padding: 15px 24px;
  border-top: 1px solid #f0f0f0;
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 13px;
  color: #666;
  background: #fcfcfc;
}

.stars {
  color: #f1c40f;
  margin: 0 5px;
  letter-spacing: 1px;
}

.user-count {
  background: #f0f0f0;
  padding: 4px 10px;
  border-radius: 12px;
  font-size: 12px;
}

/* 响应式调整 */
@media (max-width: 768px) {
  .lp-container {
    flex-direction: column;
  }
  .domain-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}
/* --- 历史记录样式 --- */
.history-section {
  margin-top: 30px;
  padding: 20px;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.03);
  border: 1px solid #eee;
}

.history-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid #f0f0f0;
}

.history-header h3 {
  margin: 0;
  color: #2c3e50;
  font-size: 18px;
  font-weight: 600;
}

.refresh-btn {
  padding: 6px 12px;
  background: #e0e0e0;
  border: none;
  border-radius: 6px;
  color: #333;
  cursor: pointer;
  font-size: 12px;
  transition: background 0.2s;
}

.refresh-btn:hover:not(:disabled) {
  background: #d0d0d0;
}

.refresh-btn:disabled {
  background: #f5f5f5;
  cursor: not-allowed;
  color: #aaa;
}

/* 表格布局 */
.history-table-container {
  width: 100%;
  overflow-x: auto; /* 横向滚动，防止小屏幕错位 */
  border-radius: 8px;
  overflow: hidden;
  border: 1px solid #e0e0e0;
}

.table-header-grid,
.table-row {
  display: grid;
  grid-template-columns: 0.5fr 2fr 1fr 1.5fr 1fr;
  /* 列宽比例：ID | 目标(宽) | 领域 | 时间 | 操作 */
  align-items: center;
  padding: 0 10px;
}

.table-header-grid {
  background: #f8f9fa;
  font-weight: 600;
  color: #555;
  border-bottom: 2px solid #ddd;
}

.table-cell {
  padding: 12px 8px;
  text-align: center;
  border-bottom: 1px solid #eee;
  font-size: 13px;
  color: #333;
}

/* 响应式：在小屏幕上调整列宽 */
@media (max-width: 768px) {
  .table-header-grid,
  .table-row {
    font-size: 12px;
    grid-template-columns: 1fr 2fr 1fr; /* 合并或隐藏部分列，或改为堆叠 */
  }
  /* 简单的响应式处理：让目标列不换行 */
  .truncate {
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }
}

/* 操作按钮样式 */
.action-btn {
  padding: 4px 8px;
  margin: 0 2px;
  border: none;
  border-radius: 4px;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s;
}

.action-btn.view {
  background: #6c5ce7;
  color: white;
}

.action-btn.view:hover {
  background: #5a4bd9;
}

.action-btn.delete {
  background: #ff9800;
  color: white;
}

.action-btn.delete:hover {
  background: #e68900;
}

/* 领域标签样式 */
.domain-tag {
  background: #eef2ff;
  color: #6c5ce7;
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
}

/* 加载和空状态 */
.loading-row,
.empty-row {
  grid-column: 1 / -1;
  text-align: center;
  padding: 20px;
  color: #999;
  font-size: 14px;
}

/* 旋转动画复用之前的 spinner */
.spinner {
  width: 16px;
  height: 16px;
  border: 2px solid #e0e0e0;
  border-top: 2px solid #6c5ce7;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  display: inline-block;
  margin-right: 8px;
}
</style>