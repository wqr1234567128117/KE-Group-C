<template>
  <div>
    <div class="lp-container">
      <div class="lp-sidebar">
        <div class="lp-header">
          <h3>学习配置</h3>
          <button class="icon-btn" @click="handleReset" title="重置">↺ 重置</button>
        </div>

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

        <div class="form-section">
          <label class="section-title">🎯 学习目标</label>
          <input
            v-model="form.goal"
            class="lp-input"
            placeholder="请输入您的学习目标（例如：掌握 Python 基础）"
          />
        </div>

        <div class="form-section">
          <label class="section-title">📚 学习水平</label>
          <select v-model="form.level" class="lp-input">
            <option value="入门">入门 (0-1年)</option>
            <option value="进阶">进阶 (1-3年)</option>
            <option value="专家">专家 (3年以上)</option>
          </select>
        </div>

        <div class="form-section">
          <label class="section-title">☰ 学习背景与计划</label>
          <div class="textarea-wrapper">
            <textarea
              v-model="form.background_plan"
              class="lp-textarea"
              placeholder="请描述您的基础情况、当前困惑和学习计划..."
            ></textarea>
            <span class="word-count">{{ form.background_plan.length }} 字</span>
          </div>
        </div>

        <button class="generate-btn" @click="generate" :disabled="loading">
          {{ loading ? '生成中...' : '快速生成' }}
        </button>
      </div>

      <div class="lp-main">
        <div class="result-header">
          <h3 class="result-title">✨ 生成的学习路径</h3>
          <div class="result-actions">
            <button class="copy-btn" @click="copyPath" :disabled="!displayedProgresses.length">
              复制
            </button>
            <button class="save-btn" @click="savePath" :disabled="!displayedProgresses.length">
              保存
            </button>
          </div>
        </div>

        <div class="result-content">
          <div v-if="loading" class="loading-state">
            <div class="spinner"></div>
            <p>AI 正在为您规划阶段与任务点...</p>
          </div>

          <div v-else-if="displayedProgresses.length" class="path-display scrollable-panel">
            <div class="path-overview sticky-overview">
              <div class="overview-chip">
                <span class="chip-label">目标</span>
                <span class="chip-value">{{ currentPathMeta.goal || form.goal || '未填写' }}</span>
              </div>
              <div class="overview-chip">
                <span class="chip-label">领域</span>
                <span class="chip-value">{{ getDomainLabel(currentPathMeta.domain || form.domain) }}</span>
              </div>
              <div class="overview-chip">
                <span class="chip-label">水平</span>
                <span class="chip-value">{{ currentPathMeta.level || form.level || '未设置' }}</span>
              </div>
              <div class="overview-chip">
                <span class="chip-label">当前阶段</span>
                <span class="chip-value">{{ currentPathMeta.status || '未开始' }}</span>
              </div>
              <div class="overview-chip">
                <span class="chip-label">阶段数</span>
                <span class="chip-value">{{ displayedProgresses.length }}</span>
              </div>
              <div class="overview-chip">
                <span class="chip-label">任务点</span>
                <span class="chip-value">{{ totalTaskCount }}</span>
              </div>
            </div>

            <div class="progress-list">
              <div
                v-for="progress in displayedProgresses"
                :key="progress.progress_key"
                class="stage-card"
              >
                <div class="stage-header">
                  <div class="stage-badge">阶段 {{ progress.progress_order }}</div>
                  <div class="stage-heading">
                    <h4 class="stage-title">{{ progress.progress_name }}</h4>
                    <p v-if="progress.progress_description" class="stage-desc">
                      {{ progress.progress_description }}
                    </p>
                  </div>
                  <div class="stage-count">{{ progress.tasks.length }} 个任务点</div>
                </div>

                <div class="task-list">
                  <div
                    v-for="(task, taskIdx) in progress.tasks"
                    :key="task.task_id || `${progress.progress_key}-${taskIdx}`"
                    class="task-card"
                  >
                    <div class="task-order">{{ task.order_no || task.task_order || taskIdx + 1 }}</div>
                    <div class="task-main">
                      <div class="task-topline">
                        <h5 class="task-name">{{ task.task_name || `任务点 ${taskIdx + 1}` }}</h5>
                        <div class="task-tags">
                          <span class="task-tag status-tag" :class="task.is_completed ? 'done' : 'pending'">
                            {{ task.is_completed ? '已完成' : '未完成' }}
                          </span>
                        </div>
                      </div>
                      <p v-if="task.description || task.task_description" class="task-desc">
                        {{ task.description || task.task_description }}
                      </p>
                      <p v-else class="task-desc muted">暂未提供任务描述</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div v-else class="empty-state">
            <div class="empty-emoji">🧭</div>
            <p class="empty-title">请先在左侧配置学习参数</p>
            <p class="empty-tip">生成后会按“阶段—任务点”展示完整学习路径</p>
          </div>
        </div>

      </div>
    </div>

    <div class="history-section">
      <div class="history-header">
        <h3>📜 历史学习路径</h3>
        <button class="refresh-btn" @click="getPaths" :disabled="historyLoading">
          🔄 刷新记录
        </button>
      </div>

      <div class="history-table-container">
        <div class="table-header-grid">
          <div class="table-cell">ID</div>
          <div class="table-cell">学习目标</div>
          <div class="table-cell">领域</div>
          <div class="table-cell">生成时间</div>
          <div class="table-cell">操作</div>
        </div>

        <div class="table-body">
          <div v-if="historyLoading" class="loading-row">
            <div class="spinner small"></div>
            <span>正在加载历史记录...</span>
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
            <div class="table-cell truncate" :title="record.goal">{{ record.goal }}</div>
            <div class="table-cell">
              <span class="domain-tag">{{ getDomainLabel(record.domain) }}</span>
            </div>
            <div class="table-cell">{{ formatDate(record.created_at) }}</div>
            <div class="table-cell action-group">
              <button class="action-btn view" @click="viewPath(record)">查看</button>
              <button class="action-btn delete" @click="deletePath(record.path_id)">删除</button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import api from '../api/index'

const userStr = localStorage.getItem('user_info')
const user = userStr ? JSON.parse(userStr) : null
const userId = user?.user_id

if (!userId) {
  console.warn('未检测到用户登录，请先登录')
}

const domains = [
  { key: 'career', label: '职业技能', icon: '💻' },
  { key: 'language', label: '语言学习', icon: '🈯' },
  { key: 'academic', label: '学术研究', icon: '⚗️' },
  { key: 'hobby', label: '兴趣爱好', icon: '🎨' },
  { key: 'exam', label: '考试备考', icon: '📘' },
  { key: 'other', label: '其他领域', icon: '🧩' },
]

const form = reactive({
  domain: 'other',
  goal: '',
  level: '入门',
  background_plan: '',
})

const currentPath = ref([])
const currentProgresses = ref([])
const currentPathMeta = ref({})
const loading = ref(false)
const learningHistory = ref([])
const historyLoading = ref(false)

const extractPayload = (response) => {
  return response?.data?.data ?? response?.data ?? {}
}

const extractTasks = (payload) => {
  if (Array.isArray(payload)) return payload
  if (Array.isArray(payload?.tasks)) return payload.tasks
  if (Array.isArray(payload?.path_tasks)) return payload.path_tasks
  return []
}

const normalizeTask = (task, idx) => {
  const orderNo = Number(task?.order_no ?? task?.task_order ?? task?.order ?? idx + 1)

  return {
    ...task,
    order_no: Number.isNaN(orderNo) ? idx + 1 : orderNo,
    task_order: Number.isNaN(orderNo) ? idx + 1 : orderNo,
    task_name: task?.task_name ?? task?.name ?? `任务点 ${idx + 1}`,
    description: task?.description ?? task?.task_description ?? '',
    task_description: task?.task_description ?? task?.description ?? '',
    is_completed: Boolean(task?.is_completed),
  }
}

const normalizeProgress = (progress, idx) => {
  const progressOrder = Number(progress?.progress_order ?? progress?.stage_order ?? idx + 1)
  const rawTasks = Array.isArray(progress?.tasks) ? progress.tasks : []

  return {
    ...progress,
    progress_key: `${progress?.progress_id ?? progressOrder}-${progress?.progress_name ?? progress?.stage_name ?? `阶段 ${idx + 1}`}`,
    progress_order: Number.isNaN(progressOrder) ? idx + 1 : progressOrder,
    progress_name: progress?.progress_name ?? progress?.stage_name ?? `阶段 ${idx + 1}`,
    progress_description: progress?.progress_description ?? progress?.stage_description ?? '',
    tasks: rawTasks
      .map((task, taskIdx) => normalizeTask(task, taskIdx))
      .sort((a, b) => a.order_no - b.order_no),
  }
}

const buildProgressesFromTasks = (tasks) => {
  const groups = new Map()

  tasks
    .map((task, idx) => {
      const normalizedTask = normalizeTask(task, idx)
      const progressOrder = Number(
        task?.progress_order ?? task?.stage_order ?? task?.phase_order ?? task?.section_order ?? 1,
      )
      const safeOrder = Number.isNaN(progressOrder) ? 1 : progressOrder
      const progressName =
        task?.progress_name ??
        task?.stage_name ??
        task?.phase_name ??
        task?.section_name ??
        task?.progress ??
        task?.stage ??
        '学习阶段'
      const progressDescription =
        task?.progress_description ??
        task?.stage_description ??
        task?.phase_description ??
        task?.section_description ??
        ''

      return {
        ...normalizedTask,
        progress_order: safeOrder,
        progress_name: progressName,
        progress_description: progressDescription,
      }
    })
    .sort((a, b) => {
      if (a.progress_order !== b.progress_order) return a.progress_order - b.progress_order
      return a.order_no - b.order_no
    })
    .forEach((task) => {
      const key = `${task.progress_order}-${task.progress_name}`
      if (!groups.has(key)) {
        groups.set(key, {
          progress_key: key,
          progress_order: task.progress_order,
          progress_name: task.progress_name,
          progress_description: task.progress_description,
          tasks: [],
        })
      }
      groups.get(key).tasks.push(task)
    })

  return Array.from(groups.values()).sort((a, b) => a.progress_order - b.progress_order)
}

const displayedProgresses = computed(() => {
  if (currentProgresses.value.length) {
    return currentProgresses.value
  }
  if (currentPath.value.length) {
    return buildProgressesFromTasks(currentPath.value)
  }
  return []
})

const totalTaskCount = computed(() => {
  return displayedProgresses.value.reduce((sum, progress) => sum + progress.tasks.length, 0)
})

const applyPathResponse = (response) => {
  const payload = extractPayload(response)
  const pathMeta = payload?.path ?? payload ?? {}

  currentPathMeta.value = {
    path_id: pathMeta?.path_id,
    goal: pathMeta?.goal ?? payload?.goal ?? form.goal,
    domain: pathMeta?.domain ?? payload?.domain ?? form.domain,
    level: pathMeta?.level ?? payload?.level ?? form.level,
    status: pathMeta?.status ?? payload?.status ?? '',
    background_plan: pathMeta?.background_plan ?? payload?.background_plan ?? form.background_plan,
    created_at: pathMeta?.created_at ?? payload?.created_at ?? '',
  }

  const progresses = Array.isArray(payload?.progresses)
    ? payload.progresses.map((progress, idx) => normalizeProgress(progress, idx))
    : []

  currentProgresses.value = progresses

  if (progresses.length) {
    currentPath.value = progresses.flatMap((progress) => progress.tasks)
  } else {
    const tasks = extractTasks(payload)
    currentPath.value = Array.isArray(tasks) ? tasks.map((task, idx) => normalizeTask(task, idx)) : []
  }
}

const generate = async () => {
  if (!userId) {
    alert('请先登录')
    return
  }
  if (!form.goal.trim()) {
    alert('请输入学习目标')
    return
  }

  loading.value = true
  currentPath.value = []
  currentProgresses.value = []
  currentPathMeta.value = {}

  try {
    const response = await api.generatePath({
      user_id: userId,
      domain: form.domain,
      level: form.level,
      goal: form.goal,
      background_plan: form.background_plan,
    })

    applyPathResponse(response)

    if (!displayedProgresses.value.length) {
      alert('已生成，但暂未拿到阶段与任务点数据，请检查后端返回结构')
    }

    await getPaths()
  } catch (error) {
    console.error('API 请求失败:', error)
    alert('生成失败：' + (error.response?.data?.detail || error.message || '网络错误'))
    currentPath.value = []
    currentProgresses.value = []
  } finally {
    loading.value = false
  }
}

const savePath = () => {
  if (!displayedProgresses.value.length) {
    alert('没有可保存的路径')
    return
  }
  alert('当前路径在生成时已自动保存，无需重复保存')
}

const copyPath = async () => {
  if (!displayedProgresses.value.length) return

  const text = displayedProgresses.value
    .map((progress) => {
      const tasks = progress.tasks
        .map((task, idx) => `  ${task.order_no || idx + 1}. ${task.task_name}\n     ${task.description || task.task_description || '暂无描述'}`)
        .join('\n')

      return `【阶段${progress.progress_order}】${progress.progress_name}\n${progress.progress_description ? `${progress.progress_description}\n` : ''}${tasks}`
    })
    .join('\n\n')

  try {
    await navigator.clipboard.writeText(text)
    alert('路径已复制到剪贴板')
  } catch (error) {
    console.error('复制失败:', error)
    alert('复制失败，请手动复制')
  }
}

const getPaths = async () => {
  if (!userId) return
  historyLoading.value = true
  try {
    const response = await api.getPaths(userId)
    const payload = extractPayload(response)
    learningHistory.value = Array.isArray(payload) ? payload : payload?.items || payload?.records || []
  } catch (error) {
    console.error('获取历史记录失败:', error)
    alert('加载历史记录失败')
    learningHistory.value = []
  } finally {
    historyLoading.value = false
  }
}

const getDomainLabel = (key) => {
  const item = domains.find((d) => d.key === key)
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
    minute: '2-digit',
  })
}

const viewPath = async (record) => {
  loading.value = true
  try {
    const response = await api.getPathDetail(record.path_id)
    applyPathResponse(response)
    currentPathMeta.value = {
      ...currentPathMeta.value,
      goal: currentPathMeta.value.goal || record.goal,
      domain: currentPathMeta.value.domain || record.domain,
    }
  } catch (error) {
    console.error('获取路径详情失败:', error)
    alert('加载详情失败，请重试')
    currentPath.value = []
    currentProgresses.value = []
  } finally {
    loading.value = false
    document.querySelector('.lp-main')?.scrollIntoView({ behavior: 'smooth' })
  }
}


const deletePath = async (pathId) => {
  // 1. 确认操作
  if (!confirm('确定要删除这条记录吗？')) return;

  try {
    // 2. 调用删除接口
    await api.deletePath(pathId);
    
    // 3. 更新前端列表
    learningHistory.value = learningHistory.value.filter((item) => item.path_id !== pathId);
    
    // 4. 提示成功
    alert('删除成功');
    
  } catch (error) {
    // 5. 错误处理
    console.error('删除失败:', error);
    alert('删除失败：' + (error.response?.data?.detail || '网络错误'));
    // 注意：如果删除失败，这里不执行过滤操作，保持列表原样
  }
}


const handleReset = () => {
  form.goal = ''
  form.background_plan = ''
  form.domain = 'other'
  form.level = '入门'
  currentPath.value = []
  currentProgresses.value = []
  currentPathMeta.value = {}
}

onMounted(() => {
  if (userId) {
    getPaths()
  }
})
</script>

<style scoped>
.lp-container {
  display: flex;
  gap: 20px;
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
  background: #fcfcff;
}

.lp-sidebar,
.lp-main,
.history-section {
  background: #fff;
  border: 1px solid #ece9ff;
  border-radius: 16px;
  box-shadow: 0 10px 30px rgba(108, 92, 231, 0.06);
}

.lp-sidebar {
  flex: 0 0 360px;
  padding: 24px;
}

.lp-main {
  flex: 1;
  min-height: 640px;
  max-height: 860px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.lp-header,
.result-header,
.history-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.lp-header {
  margin-bottom: 24px;
}

.icon-btn,
.copy-btn,
.save-btn,
.refresh-btn,
.action-btn {
  border: none;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.icon-btn {
  background: #f5f3ff;
  color: #6c5ce7;
  padding: 8px 12px;
}

.form-section + .form-section {
  margin-top: 18px;
}

.section-title {
  display: block;
  margin-bottom: 10px;
  font-size: 14px;
  font-weight: 700;
  color: #352c67;
}

.domain-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
}

.domain-card {
  border: 1px solid #e7e3ff;
  border-radius: 12px;
  padding: 14px 8px;
  background: #fff;
  display: flex;
  flex-direction: column;
  gap: 6px;
  align-items: center;
  cursor: pointer;
  color: #5f5b7a;
  transition: all 0.2s ease;
}

.domain-card:hover {
  transform: translateY(-2px);
  border-color: #c9bfff;
  background: #faf8ff;
}

.domain-card.active {
  background: linear-gradient(180deg, #f6f2ff, #efe9ff);
  border-color: #7d6bff;
  box-shadow: 0 0 0 3px rgba(125, 107, 255, 0.12);
  color: #4d3fc6;
}

.domain-icon {
  font-size: 20px;
}

.domain-label {
  font-size: 13px;
  font-weight: 600;
}

.lp-input,
.lp-textarea {
  width: 100%;
  box-sizing: border-box;
  border: 1px solid #e5e2f7;
  border-radius: 12px;
  background: #fafaff;
  padding: 12px 14px;
  font-size: 14px;
  transition: border-color 0.2s ease, box-shadow 0.2s ease;
  outline: none;
}

.lp-input:focus,
.lp-textarea:focus {
  border-color: #7d6bff;
  box-shadow: 0 0 0 3px rgba(125, 107, 255, 0.1);
  background: #fff;
}

.textarea-wrapper {
  position: relative;
}

.lp-textarea {
  min-height: 130px;
  resize: vertical;
  font-family: inherit;
}

.word-count {
  position: absolute;
  right: 12px;
  bottom: 10px;
  font-size: 12px;
  color: #9b96be;
  background: rgba(255, 255, 255, 0.9);
  padding: 0 6px;
  border-radius: 999px;
}

.generate-btn {
  width: 100%;
  margin-top: 14px;
  padding: 14px 16px;
  border: none;
  border-radius: 12px;
  font-size: 15px;
  font-weight: 700;
  cursor: pointer;
  color: #fff;
  background: linear-gradient(90deg, #6c5ce7, #8f7cff);
  transition: transform 0.2s ease, opacity 0.2s ease;
}

.generate-btn:hover {
  transform: translateY(-1px);
}


.generate-btn:disabled,
.copy-btn:disabled,
.save-btn:disabled,
.refresh-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.result-header {
  padding: 20px 24px;
  border-bottom: 1px solid #f0edff;
  background: linear-gradient(180deg, #fff, #fcfbff);
}

.result-title {
  margin: 0;
  color: #4636cb;
  font-size: 18px;
}

.result-actions {
  display: flex;
  gap: 10px;
}

.copy-btn,
.save-btn,
.refresh-btn {
  padding: 9px 14px;
  font-size: 13px;
}

.copy-btn {
  background: #f3f1ff;
  color: #5545d6;
}

.save-btn,
.refresh-btn {
  background: #6c5ce7;
  color: #fff;
}

.copy-btn:hover,
.save-btn:hover,
.refresh-btn:hover,
.action-btn:hover,
.icon-btn:hover {
  filter: brightness(0.97);
}

.result-content {
  flex: 1;
  min-height: 0;
  padding: 20px 24px;
  overflow-y: auto;
  overflow-x: hidden;
  background: linear-gradient(180deg, #fcfbff 0%, #ffffff 100%);
  scrollbar-width: thin;
  scrollbar-color: #c8bfff #f4f1ff;
}

.result-content::-webkit-scrollbar {
  width: 10px;
}

.result-content::-webkit-scrollbar-track {
  background: #f4f1ff;
  border-radius: 999px;
}

.result-content::-webkit-scrollbar-thumb {
  background: linear-gradient(180deg, #c8bfff, #9f91ff);
  border-radius: 999px;
}

.scrollable-panel {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.loading-state,
.empty-state {
  min-height: 420px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  color: #6f6894;
}

.empty-emoji {
  font-size: 44px;
  margin-bottom: 10px;
}

.empty-title {
  margin: 0 0 6px;
  font-size: 18px;
  font-weight: 700;
  color: #4a3fb2;
}

.empty-tip {
  margin: 0;
  font-size: 14px;
}

.spinner {
  width: 42px;
  height: 42px;
  border: 4px solid #ebe7ff;
  border-top-color: #6c5ce7;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

.spinner.small {
  width: 20px;
  height: 20px;
  border-width: 3px;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.path-display {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.sticky-overview {
  position: sticky;
  top: -20px;
  z-index: 2;
  padding: 2px 0 14px;
  background: linear-gradient(180deg, rgba(252, 251, 255, 0.98), rgba(255, 255, 255, 0.95));
  backdrop-filter: blur(6px);
}

.path-overview {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.overview-chip {
  min-width: 120px;
  padding: 12px 14px;
  border-radius: 14px;
  border: 1px solid #ebe7ff;
  background: linear-gradient(180deg, #ffffff, #f8f6ff);
}

.chip-label {
  display: block;
  margin-bottom: 6px;
  font-size: 12px;
  color: #8a85ab;
}

.chip-value {
  display: block;
  font-size: 14px;
  font-weight: 700;
  color: #40339f;
  word-break: break-word;
}

.progress-list {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.stage-card {
  border: 1px solid #ece9ff;
  border-radius: 18px;
  background: #fff;
  overflow: hidden;
}

.stage-header {
  display: flex;
  align-items: flex-start;
  gap: 14px;
  padding: 18px 20px;
  background: linear-gradient(135deg, #f6f2ff 0%, #fcfbff 100%);
  border-bottom: 1px solid #f0edff;
}

.stage-badge {
  flex: 0 0 auto;
  min-width: 82px;
  text-align: center;
  padding: 8px 12px;
  border-radius: 999px;
  background: #6c5ce7;
  color: #fff;
  font-size: 13px;
  font-weight: 700;
}

.stage-heading {
  flex: 1;
}

.stage-title {
  margin: 0;
  font-size: 18px;
  color: #352c67;
}

.stage-desc {
  margin: 6px 0 0;
  font-size: 13px;
  line-height: 1.7;
  color: #6d688f;
}

.stage-count {
  flex: 0 0 auto;
  color: #6c5ce7;
  background: rgba(108, 92, 231, 0.08);
  padding: 8px 12px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 700;
}

.task-list {
  padding: 14px 16px 18px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.task-card {
  display: flex;
  gap: 14px;
  padding: 16px;
  border-radius: 14px;
  background: #fbfaff;
  border: 1px solid #efecff;
}

.task-order {
  flex: 0 0 34px;
  height: 34px;
  border-radius: 50%;
  background: #ece7ff;
  color: #513fd2;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 800;
}

.task-main {
  flex: 1;
  min-width: 0;
}

.task-topline {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: flex-start;
}

.task-name {
  margin: 0;
  font-size: 15px;
  color: #2f275c;
}

.task-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.task-tag {
  padding: 4px 8px;
  border-radius: 999px;
  font-size: 12px;
  white-space: nowrap;
}

.status-tag.pending {
  background: #f0ecff;
  color: #5b49d7;
}

.status-tag.done {
  background: #e9fff3;
  color: #23945d;
}

.task-desc {
  margin: 8px 0 0;
  line-height: 1.8;
  color: #655f84;
  font-size: 14px;
  white-space: pre-wrap;
}

.task-desc.muted {
  color: #a19bbd;
}

.history-section {
  max-width: 1200px;
  margin: 20px auto 0;
  padding: 20px;
}

.history-header {
  margin-bottom: 16px;
}

.history-header h3 {
  margin: 0;
  color: #352c67;
}

.history-table-container {
  border: 1px solid #f0edff;
  border-radius: 14px;
  overflow: hidden;
}

.table-header-grid,
.table-row {
  display: grid;
  grid-template-columns: 90px 2fr 1fr 1.5fr 180px;
  align-items: center;
}

.table-header-grid {
  background: #f7f5ff;
  color: #5e57a0;
  font-weight: 700;
}

.table-row {
  border-top: 1px solid #f4f2ff;
}

.table-cell {
  padding: 14px 16px;
  font-size: 14px;
  color: #4a4566;
}

.truncate {
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}

.domain-tag {
  display: inline-flex;
  align-items: center;
  padding: 4px 10px;
  border-radius: 999px;
  background: #f0ecff;
  color: #5a49d7;
  font-size: 12px;
  font-weight: 700;
}

.action-group {
  display: flex;
  gap: 8px;
}

.action-btn {
  padding: 8px 12px;
  font-size: 12px;
}

.action-btn.view {
  background: #f0ecff;
  color: #5645d7;
}

.action-btn.delete {
  background: #fff1f1;
  color: #d84e4e;
}

.loading-row,
.empty-row {
  padding: 22px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  color: #7f78a5;
}

@media (max-width: 1024px) {
  .lp-container {
    flex-direction: column;
  }

  .lp-sidebar {
    flex: none;
  }

  .lp-main {
    max-height: none;
  }

  .result-content {
    max-height: 680px;
  }

  .table-header-grid,
  .table-row {
    grid-template-columns: 70px 1.5fr 1fr 1.3fr 160px;
  }
}

@media (max-width: 768px) {
  .lp-container,
  .history-section {
    padding: 12px;
  }

  .result-header,
  .lp-header,
  .history-header,
  .stage-header,
  .task-topline {
    flex-direction: column;
    align-items: flex-start;
  }

  .result-content {
    padding: 16px;
    max-height: 72vh;
  }

  .sticky-overview {
    top: -16px;
  }

  .table-header-grid {
    display: none;
  }

  .table-row {
    display: flex;
    flex-direction: column;
    align-items: flex-start;
    padding: 10px 0;
  }

  .table-cell {
    width: 100%;
    padding: 8px 14px;
  }

  .action-group {
    padding: 0 14px 10px;
  }
}
</style>
