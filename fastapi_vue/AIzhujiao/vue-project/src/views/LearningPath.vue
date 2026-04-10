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
          placeholder="请输入您的学习目标（例如：掌握 Python 基础）"
        />
      </div>

      <!-- 学习水平 -->
      <div class="form-section">
        <label class="section-title">🎯 学习水平</label>
        <select v-model="form.level" class="lp-input">
          <option value="入门">入门 (0-1年)</option>
          <option value="进阶">进阶 (1-3年)</option>
          <option value="专家">专家 (3年以上)</option>
        </select>
      </div>

      <!-- 学习天数 -->
      <div class="form-section">
        <label class="section-title">📅 计划天数</label>
        <input
          v-model.number="form.days"
          type="number"
          class="lp-input"
          placeholder="请输入计划完成天数"
        />
      </div>

      <!-- 背景与计划输入 (关键修改点) -->
      <div class="form-section">
        <label class="section-title">☰ 学习背景与计划</label>
        <div class="textarea-wrapper">
          <!-- 绑定字段已改为 background_plan -->
          <textarea
            v-model="form.background_plan"
            class="lp-textarea"
            placeholder="请描述您的基础情况或学习计划..."
          ></textarea>
          <span class="word-count">{{ form.background_plan.length }} 字</span>
        </div>
      </div>

      <!-- 生成按钮 -->
      <button class="generate-btn" @click="generate" :disabled="loading">
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
        <button class="copy-btn" @click="copyPath" :disabled="!currentPath.length">
          复制
        </button>
        <button class="save-btn" @click="savePath" :disabled="!currentPath.length">
          保存
        </button>
      </div>

      <div class="result-content">
        <!-- 加载状态 -->
        <div v-if="loading" class="loading-state">
          <div class="spinner"></div>
          <p>AI 正在为您规划中...</p>
        </div>

        <!-- 结果展示 (关键修改点) -->
        <!-- 使用 v-else-if 替代 v-else，确保 tasks 为空数组时不显示错误 -->
        <div v-else-if="currentPath.length" class="path-display">
          <!-- 遍历 path_tasks 数据 -->
          <div
            v-for="(task, idx) in currentPath"
            :key="task.task_id || idx"
            class="path-item"
          >
            <!-- 显示任务顺序 -->
            <div class="step-index">{{ task.task_order || idx + 1 }}</div>
            <div class="step-content">
              <!-- 显示任务名称 -->
              <h4 class="task-name">{{ task.task_name }}</h4>
              <!-- 显示任务描述 -->
              <p class="task-desc">{{ task.task_description }}</p>
            </div>
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
      <button class="refresh-btn" @click="getPaths" :disabled="historyLoading">
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
          :key="record.path_id"
          class="table-row"
        >
          <div class="table-cell">{{ record.path_id }}</div>
          <div class="table-cell truncate" :title="record.goal">
            {{ record.goal }}
          </div>
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
import { ref, reactive, onMounted } from 'vue'
import api from '../api/index' // 引入 API 模块

// --- 用户状态 ---
const userStr = localStorage.getItem('user_info')
const user = userStr ? JSON.parse(userStr) : null
const userId = user?.user_id

if (!userId) {
  console.warn('未检测到用户登录，请先登录')
}

// --- 领域数据 ---
const domains = [
  { key: 'career', label: '职业技能', icon: '💻' },
  { key: 'language', label: '语言学习', icon: '🈯' },
  { key: 'academic', label: '学术研究', icon: '⚗️' },
  { key: 'hobby', label: '兴趣爱好', icon: '🎨' },
  { key: 'exam', label: '考试备考', icon: '📘' },
  { key: 'other', label: '其他领域', icon: '...' },
]

// --- 表单数据 (关键修改) ---
// 字段名已从 background 改为 background_plan
const form = reactive({
  domain: 'other',
  goal: '',
  level: '入门',
  days: 30,
  background_plan: '', // 对应数据库 path_tasks 的输入字段
})

// --- 状态管理 ---
// 修改数据结构：currentPath 现在存储从后端获取的 path_tasks 列表
const currentPath = ref([]) // 改为数组，用于存储任务对象
const loading = ref(false)

// --- 生成路径逻辑 (关键修改) ---
const generate = async () => {
  if (!userId) {
    alert('请先登录')
    return
  }
  if (!form.goal) {
    alert('请输入学习目标')
    return
  }

  loading.value = true
  // 清空上一次的结果
  currentPath.value = []

  try {
    // 构建符合后端要求的数据结构
    const generateData = {
      user_id: userId,
      domain: form.domain,
      level: form.level,
      goal: form.goal,
      background_plan: form.background_plan, // 关键：字段名必须是 background_plan
      // 注意：如果后端 generate 接口不需要 days，可以不传，或者后端需适配
    }

    // 调用后端 API
    const response = await api.generatePath(generateData)

    // 假设后端返回格式为 { success: true, data: { tasks: [...] } }
    // 或者直接返回 tasks 数组
    if (response.data && Array.isArray(response.data)) {
      // 直接赋值给 currentPath (即 path_tasks 数据)
      currentPath.value = response.data
    } else if (response.data?.tasks && Array.isArray(response.data.tasks)) {
      // 如果后端返回的是包含 tasks 字段的对象
      currentPath.value = response.data.tasks
    } else {
      currentPath.value = [{ task_name: '提示', task_description: 'AI 未返回有效数据，请重试。' }]
    }
  } catch (error) {
    console.error('API 请求失败:', error)
    alert('生成失败：' + (error.response?.data?.detail || error.message || '网络错误'))
    currentPath.value = [{ task_name: '错误', task_description: '生成过程中发生错误。' }]
  } finally {
    loading.value = false
  }
}

// --- 保存路径到数据库 ---
// (此处逻辑保持不变，或根据后端 save 接口调整)
const savePath = async () => {
  if (!userId || !currentPath.value.length || !form.goal) {
    alert('没有可保存的内容')
    return
  }
  try {
    // 假设后端 save 接口需要 path_data 字符串
    // 这里将任务名称拼接成字符串保存
    const pathText = currentPath.value.map(t => t.task_name).join('\n')
    
    await api.savePath({
      user_id: userId,
      goal: form.goal,
      domain: form.domain,
      path_data: pathText,
      status: 'generated'
    })
    alert('保存成功！')
    getPaths() // 保存成功后刷新历史列表
  } catch (error) {
    alert('保存失败')
  }
}

// --- 跳转逻辑 ---
const goToCustomize = () => {
  // router.push('/person-learning-path') // 需要引入 router
  alert('跳转到个性化定制页面')
}

// --- 复制功能 ---
const copyPath = () => {
  if (!currentPath.value.length) return
  // 拼接任务名称和描述
  const text = currentPath.value
    .map(t => `第${t.task_order}步: ${t.task_name}\n${t.task_description}\n`)
    .join('\n')
  navigator.clipboard.writeText(text).then(() => {
    alert('路径已复制到剪贴板')
  })
}

// --- 历史记录逻辑 (连接后端) ---
const learningHistory = ref([])
const historyLoading = ref(false)

const getPaths = async () => {
  if (!userId) return
  historyLoading.value = true
  try {
    const response = await api.getPaths(userId)
    learningHistory.value = response.data || []
  } catch (error) {
    console.error('获取历史记录失败:', error)
    alert('加载历史记录失败')
    learningHistory.value = []
  } finally {
    historyLoading.value = false
  }
}

// --- 辅助与操作函数 ---
const getDomainLabel = (key) => {
  const item = domains.find(d => d.key === key)
  return item ? item.label : '未知领域'
}

const formatDate = (isoString) => {
  if (!isoString) return '未知时间'
  const date = new Date(isoString)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

// --- 查看路径详情 (修改版) ---
const viewPath = async (record) => {
  try {
    // 1. 显示加载状态
    loading.value = true;
    
    // 2. 调用后端接口获取详细任务数据
    // 假设 record.path_id 是后端定义的唯一ID
    const response = await api.getPathDetail(record.path_id); 
    
    // 3. 数据处理
    // 假设后端返回格式为 { success: true, data: { tasks: [...] } }
    // 或者直接返回任务数组，根据实际接口调整
    if (response.data && Array.isArray(response.data)) {
      currentPath.value = response.data;
    } else if (response.data?.tasks) {
      currentPath.value = response.data.tasks;
    } else {
      // 如果接口返回数据异常，显示提示
      currentPath.value = [{ task_name: '提示', task_description: '该记录暂无详细内容' }];
    }
  } catch (error) {
    console.error('获取路径详情失败:', error);
    // 失败时也可以尝试降级处理（如解析 path_data 字段），或者直接报错
    alert('加载详情失败，请重试');
    // 降级方案：如果后端接口挂了，尝试解析数据库中保存的原始文本
    if (record.path_data) {
      currentPath.value = record.path_data.split('\n').map((line, idx) => ({
        task_order: idx + 1,
        task_name: line,
        task_description: '详细描述暂不可用'
      }));
    } else {
      currentPath.value = [];
    }
  } finally {
    loading.value = false;
    
    // 4. 滚动到视图
    document.querySelector('.lp-main').scrollIntoView({ behavior: 'smooth' });
  }
}

const deletePath = async (id) => {
  if (!confirm('确定要删除这条记录吗？')) return
  try {
    await api.deletePath(id)
    learningHistory.value = learningHistory.value.filter(item => item.id !== id)
    alert('删除成功')
  } catch (error) {
    alert('删除失败')
  }
}

// --- 重置功能 ---
const handleReset = () => {
  form.goal = ''
  form.background_plan = '' // 重置字段
  form.domain = 'other'
  form.level = '入门'
  form.days = 30
  currentPath.value = []
}

// 组件挂载后自动加载历史记录
onMounted(() => {
  if (userId) {
    getPaths()
  }
})
</script>

<style scoped>
/* (样式部分保持不变，为了节省篇幅，此处省略样式代码) */
/* 请保留你上传代码中的 <style scoped> 部分，或者使用下方提供的样式 */
/* ... (此处保留原样式的代码) ... */
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
/* 路径列表样式 (关键修改) */
.path-display {
  width: 100%;
  display: flex;
  flex-direction: column;
}
</style>