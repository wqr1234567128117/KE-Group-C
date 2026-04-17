<template>
  <div class="progress-page">
    <div class="progress-shell">
      <section class="hero-card">
        <div class="hero-left">
          <div class="hero-badge">📈 学习进度</div>
          <h2 class="hero-title">阶段 — 任务点 — 题目</h2>
        </div>

        <div class="hero-right">
          <label class="selector-label">选择学习路径</label>
          <select
            v-model="selectedPathId"
            class="path-select"
            :disabled="loadingPaths || !pathOptions.length"
            @change="onPathChange"
          >
            <option v-if="!pathOptions.length" value="">暂无学习路径</option>
            <option
              v-for="path in pathOptions"
              :key="path.path_id"
              :value="path.path_id"
            >
              {{ formatPathOption(path) }}
            </option>
          </select>
        </div>
      </section>

      <section class="overview-grid" v-if="selectedPath">
        <div class="overview-card path-meta-card">
          <div class="overview-title">当前路径</div>
          <div class="path-goal">{{ selectedPath.goal || '未命名学习路径' }}</div>
          <div class="meta-tags">
            <span class="meta-tag">领域：{{ formatDomain(selectedPath.domain) }}</span>
            <span class="meta-tag">水平：{{ selectedPath.level || '未设置' }}</span>
            <span class="meta-tag">当前阶段：{{ selectedPath.status || currentStageName }}</span>
          </div>
          <p class="background-text">
            {{ selectedPath.background_plan || '暂无学习背景与计划说明。' }}
          </p>
        </div>

        <div class="overview-card compact-card">
          <div class="overview-title">阶段数</div>
          <div class="overview-value">{{ totalStages }}</div>
        </div>

        <div class="overview-card compact-card">
          <div class="overview-title">任务点进度</div>
          <div class="overview-value">{{ completedTasks }} / {{ totalTasks }}</div>
          <div class="overview-desc">已完成 / 总任务点</div>
        </div>

        <div class="overview-card compact-card">
          <div class="overview-title">完成率</div>
          <div class="overview-value">{{ completionRate }}%</div>
          <div class="mini-progress">
            <div class="mini-progress-bar" :style="{ width: `${completionRate}%` }"></div>
          </div>
        </div>

      </section>

      <section class="content-card">
        <div class="content-header">
          <div>
            <h3 class="content-title">📚 学习结构总览</h3>
          </div>
          <div class="content-stats" v-if="selectedPath">
            <span>{{ totalStages }} 个阶段</span>
            <span>{{ totalTasks }} 个任务点</span>
          </div>
        </div>

        <div v-if="loadingDetail" class="status-view">正在加载学习进度...</div>
        <div v-else-if="!selectedPathId" class="status-view">请先选择一个学习路径。</div>
        <div v-else-if="!displayStages.length" class="status-view">当前路径暂无阶段与任务数据。</div>

        <div v-else class="content-scroll">
          <div
            v-for="stage in displayStages"
            :key="stage.progress_id || `stage-${stage.progress_order}`"
            class="stage-card"
          >
            <div class="stage-top">
              <div>
                <div class="stage-order">阶段 {{ stage.progress_order || 1 }}</div>
                <h4 class="stage-title">{{ stage.progress_name || '未命名阶段' }}</h4>
                <p class="stage-desc">
                  {{ stage.progress_description || '暂无阶段说明。' }}
                </p>
              </div>
              <div class="stage-summary">
                <span>{{ getCompletedTaskCount(stage.tasks) }}/{{ stage.tasks.length }} 已完成</span>
              </div>
            </div>

            <div class="task-list">
              <div
                v-for="task in stage.tasks"
                :key="task.task_id || `${stage.progress_id}-${task.order_no}`"
                class="task-card"
                :class="task.is_completed ? 'task-card--done' : 'task-card--todo'"
              >
                <div class="task-top">
                  <div class="task-index">任务点 {{ task.order_no || 1 }}</div>
                  <span class="task-state" :class="task.is_completed ? 'done' : 'todo'">
                    {{ task.is_completed ? '已完成' : '未完成' }}
                  </span>
                </div>

                <div class="task-name-row">
                  <span class="task-icon">{{ task.is_completed ? '✅' : '🟣' }}</span>
                  <h5 class="task-name">{{ task.task_name || '未命名任务点' }}</h5>
                </div>

                <p class="task-desc">
                  {{ task.description || task.task_description || '暂无任务说明。' }}
                </p>

                <div class="question-box">
                  <div class="question-head">
                    <span>📝 题目</span>
                    <span class="question-count">
                      {{ Array.isArray(task.questions) ? task.questions.length : 0 }} 题
                    </span>
                  </div>

                  <template v-if="Array.isArray(task.questions) && task.questions.length">
                    <div
                      v-for="(question, qIndex) in task.questions"
                      :key="question.question_id || `question-${task.task_id || task.order_no}-${qIndex}`"
                      class="question-item"
                    >
                      <span class="question-dot"></span>
                      <div class="question-main">
                        <div class="question-text">
                          {{ qIndex + 1 }}. {{ question.question_text || question.title || '未命名题目' }}
                        </div>
                        <div class="question-meta" v-if="question.correct_answer || question.user_answer">
                          <span v-if="question.correct_answer">参考答案：{{ question.correct_answer }}</span>
                          <span v-if="question.user_answer">我的作答：{{ question.user_answer }}</span>
                        </div>
                      </div>
                    </div>
                  </template>

                  <div v-else class="question-empty">
                    当前任务点暂无题目。
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import api from '../api/index'

const rawUser = localStorage.getItem('user_info')
let userId = null

try {
  userId = rawUser ? JSON.parse(rawUser)?.user_id : null
} catch (error) {
  console.error('解析用户信息失败:', error)
}

const pathOptions = ref([])
const selectedPathId = ref('')
const pathDetailData = ref(null)
const displayStages = ref([])
const loadingPaths = ref(false)
const loadingDetail = ref(false)

const selectedPath = computed(() => {
  return pathDetailData.value?.path || null
})

const totalStages = computed(() => displayStages.value.length)

const totalTasks = computed(() => {
  return displayStages.value.reduce((sum, stage) => sum + (stage.tasks?.length || 0), 0)
})

const completedTasks = computed(() => {
  return displayStages.value.reduce(
    (sum, stage) => sum + getCompletedTaskCount(stage.tasks),
    0,
  )
})

const completionRate = computed(() => {
  if (!totalTasks.value) return 0
  return Math.round((completedTasks.value / totalTasks.value) * 100)
})

const currentStageName = computed(() => {
  const firstUnfinished = displayStages.value.find((stage) => {
    const tasks = stage.tasks || []
    return tasks.some((task) => !task.is_completed)
  })
  return firstUnfinished?.progress_name || '暂无'
})

onMounted(async () => {
  if (!userId) {
    alert('请先登录')
    return
  }

  await loadPathList()

  if (pathOptions.value.length > 0) {
    selectedPathId.value = pathOptions.value[0].path_id
    await loadPathDetail(selectedPathId.value)
  }
})

const unwrapResponse = (response) => {
  if (!response) return null
  return response.data?.data ?? response.data ?? null
}

const sortByNumber = (list, field) => {
  return [...(list || [])].sort((a, b) => Number(a?.[field] || 0) - Number(b?.[field] || 0))
}

const normalizeQuestions = (questions) => {
  if (!Array.isArray(questions)) return []

  return questions.map((question, index) => ({
    ...question,
    question_id: question?.question_id ?? question?.id ?? `q-${index}`,
    question_text:
      question?.question_text ||
      question?.title ||
      question?.content ||
      '未命名题目',
    correct_answer: question?.correct_answer || '',
    user_answer: question?.user_answer || '',
    is_passed: Number(question?.is_passed || 0),
  }))
}

const buildTaskIndex = (tasks) => {
  const byId = new Map()
  const byName = new Map()

  ;(tasks || []).forEach((task, index) => {
    const normalizedTask = {
      ...task,
      order_no: Number(task?.order_no || task?.task_order || index + 1),
      description: task?.description || task?.task_description || '',
      questions: normalizeQuestions(task?.questions),
    }

    if (task?.task_id != null) {
      byId.set(String(task.task_id), normalizedTask)
    }

    const taskName = task?.task_name || task?.title || ''
    if (taskName) {
      byName.set(taskName, normalizedTask)
    }
  })

  return { byId, byName }
}

const mergeTaskWithFlatData = (task, taskIndex, fallbackOrder = 1) => {
  const taskIdKey = task?.task_id != null ? String(task.task_id) : null
  const taskName = task?.task_name || task?.title || ''
  const flatTask =
    (taskIdKey ? taskIndex.byId.get(taskIdKey) : null) ||
    (taskName ? taskIndex.byName.get(taskName) : null) ||
    null

  const merged = {
    ...task,
    ...(flatTask || {}),
  }

  merged.order_no = Number(merged?.order_no || merged?.task_order || fallbackOrder)
  merged.description = merged?.description || merged?.task_description || ''
  merged.questions = normalizeQuestions(merged?.questions)

  return merged
}

const normalizeStagesFromDetail = (detail) => {
  const progresses = Array.isArray(detail?.progresses) ? detail.progresses : []
  const flatTasks = Array.isArray(detail?.tasks) ? detail.tasks : []
  const taskIndex = buildTaskIndex(flatTasks)

  if (progresses.length) {
    return sortByNumber(progresses, 'progress_order').map((progress) => {
      const nestedTasks = Array.isArray(progress?.tasks) ? progress.tasks : []

      if (nestedTasks.length) {
        return {
          ...progress,
          tasks: sortByNumber(nestedTasks, 'order_no').map((task, index) =>
            mergeTaskWithFlatData(task, taskIndex, index + 1),
          ),
        }
      }

      const progressTasks = flatTasks.filter((task) => {
        if (task?.progress_id == null) return false
        return String(task.progress_id) === String(progress.progress_id)
      })

      return {
        ...progress,
        tasks: sortByNumber(progressTasks, 'order_no').map((task, index) =>
          mergeTaskWithFlatData(task, taskIndex, index + 1),
        ),
      }
    })
  }

  if (flatTasks.length) {
    return [
      {
        progress_id: 'default-stage',
        progress_order: 1,
        progress_name: detail?.path?.status || '学习阶段',
        progress_description: detail?.path?.goal || '当前学习路径的任务点列表',
        tasks: sortByNumber(flatTasks, 'order_no').map((task, index) =>
          mergeTaskWithFlatData(task, taskIndex, index + 1),
        ),
      },
    ]
  }

  return []
}

const loadPathList = async () => {
  loadingPaths.value = true
  try {
    const res = await api.getPaths(userId)
    const data = unwrapResponse(res)
    pathOptions.value = Array.isArray(data) ? data : []
  } catch (error) {
    console.error('加载路径列表失败:', error)
    pathOptions.value = []
  } finally {
    loadingPaths.value = false
  }
}

const loadPathDetail = async (pathId) => {
  if (!pathId) {
    pathDetailData.value = null
    displayStages.value = []
    return
  }

  loadingDetail.value = true
  try {
    const res = await api.getPathDetail(pathId)
    const detail = unwrapResponse(res) || {}
    pathDetailData.value = detail
    displayStages.value = normalizeStagesFromDetail(detail)
  } catch (error) {
    console.error('加载路径详情失败:', error)
    pathDetailData.value = null
    displayStages.value = []
  } finally {
    loadingDetail.value = false
  }
}

const onPathChange = async () => {
  await loadPathDetail(selectedPathId.value)
}

const getCompletedTaskCount = (tasks = []) => {
  return (tasks || []).filter((task) => !!task?.is_completed).length
}

const formatDomain = (domain) => {
  const map = {
    career: '职业发展',
    exam: '考试提升',
    hobby: '兴趣学习',
    skill: '技能训练',
  }
  return map[domain] || domain || '未设置'
}

const formatPathOption = (path) => {
  const goal = path?.goal || '未命名路径'
  const level = path?.level || '未设置水平'
  return `${goal}（${level}）`
}
</script>

<style scoped>
.progress-page {
  min-height: 100vh;
  padding: 28px;
  background: #fcfcff;
}

.progress-shell {
  max-width: 1280px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.hero-card,
.overview-card,
.content-card {
  background: #fff;
  border: 1px solid #ece9ff;
  box-shadow: 0 10px 30px rgba(108, 92, 231, 0.06);
}

.hero-card {
  display: flex;
  justify-content: space-between;
  gap: 24px;
  align-items: flex-start;
  padding: 24px 28px;
  border-radius: 24px;
}

.hero-left {
  flex: 1;
}

.hero-badge {
  display: inline-flex;
  align-items: center;
  padding: 6px 12px;
  border-radius: 999px;
  background: rgba(127, 86, 217, 0.12);
  color: #7f56d9;
  font-size: 13px;
  font-weight: 700;
}

.hero-title {
  margin: 14px 0 0;
  font-size: 30px;
  color: #2b2340;
}

.hero-right {
  width: 320px;
  flex-shrink: 0;
}

.selector-label {
  display: block;
  margin-bottom: 10px;
  font-size: 13px;
  color: #625b76;
  font-weight: 600;
}

.path-select {
  width: 100%;
  height: 46px;
  padding: 0 14px;
  border-radius: 14px;
  border: 1px solid #ddd4ff;
  background: #fff;
  font-size: 14px;
  color: #2f2840;
  outline: none;
  transition: all 0.2s ease;
}

.path-select:focus {
  border-color: #8b5cf6;
  box-shadow: 0 0 0 4px rgba(139, 92, 246, 0.12);
}

.overview-grid {
  display: grid;
  grid-template-columns: 2fr repeat(3, 1fr);
  gap: 16px;
}

.overview-card {
  border-radius: 20px;
  padding: 20px;
}

.path-meta-card {
  min-height: 156px;
}

.overview-title {
  font-size: 13px;
  color: #7a7391;
  font-weight: 700;
}

.path-goal,
.overview-value {
  margin-top: 12px;
  color: #2b2340;
  font-weight: 800;
}

.path-goal {
  font-size: 24px;
  line-height: 1.4;
}

.overview-value {
  font-size: 30px;
  line-height: 1;
}

.meta-tags {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  margin-top: 14px;
}

.meta-tag {
  padding: 6px 10px;
  border-radius: 999px;
  background: #f3efff;
  color: #6d4cc0;
  font-size: 12px;
  font-weight: 700;
}

.background-text,
.overview-desc,
.stage-desc,
.task-desc,
.question-empty,
.status-view {
  color: #6f6885;
}

.background-text {
  margin: 14px 0 0;
  font-size: 13px;
  line-height: 1.7;
}

.compact-card {
  display: flex;
  flex-direction: column;
  justify-content: center;
  min-height: 156px;
}

.overview-desc {
  margin-top: 10px;
  font-size: 12px;
}

.mini-progress {
  margin-top: 14px;
  height: 8px;
  border-radius: 999px;
  background: #ebe7fb;
  overflow: hidden;
}

.mini-progress-bar {
  height: 100%;
  border-radius: inherit;
  background: linear-gradient(90deg, #8b5cf6 0%, #6d4cc0 100%);
}

.content-card {
  border-radius: 24px;
  padding: 22px;
}

.content-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
  margin-bottom: 18px;
}

.content-title {
  margin: 0;
  font-size: 22px;
  color: #2b2340;
}

.content-stats {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.content-stats span {
  padding: 8px 12px;
  border-radius: 999px;
  background: #f4f1ff;
  color: #6d4cc0;
  font-size: 12px;
  font-weight: 700;
}

.content-scroll {
  max-height: 640px;
  overflow-y: auto;
  padding-right: 8px;
}

.content-scroll::-webkit-scrollbar {
  width: 8px;
}

.content-scroll::-webkit-scrollbar-thumb {
  border-radius: 999px;
  background: rgba(139, 92, 246, 0.32);
}

.content-scroll::-webkit-scrollbar-track {
  background: rgba(139, 92, 246, 0.08);
  border-radius: 999px;
}

.stage-card {
  border: 1px solid #ece6ff;
  border-radius: 22px;
  padding: 20px;
  background: linear-gradient(180deg, #ffffff 0%, #fcfbff 100%);
}

.stage-card + .stage-card {
  margin-top: 16px;
}

.stage-top {
  display: flex;
  justify-content: space-between;
  gap: 20px;
  align-items: flex-start;
  margin-bottom: 18px;
}

.stage-order {
  display: inline-flex;
  padding: 5px 10px;
  border-radius: 999px;
  background: rgba(139, 92, 246, 0.12);
  color: #7f56d9;
  font-size: 12px;
  font-weight: 800;
}

.stage-title {
  margin: 12px 0 8px;
  font-size: 22px;
  color: #2e2646;
}

.stage-desc {
  margin: 0;
  font-size: 13px;
  line-height: 1.7;
}

.stage-summary {
  padding: 10px 14px;
  border-radius: 14px;
  background: #ffffff;
  border: 1px solid #ece6ff;
  font-size: 12px;
  font-weight: 700;
  color: #6d4cc0;
  white-space: nowrap;
}

.task-list {
  display: grid;
  gap: 14px;
}

.task-card {
  border-radius: 18px;
  padding: 16px;
  background: #fff;
  border: 1px solid #efeafc;
  box-shadow: 0 10px 24px rgba(108, 76, 192, 0.05);
}

.task-card--done {
  border-left: 5px solid #22c55e;
}

.task-card--todo {
  border-left: 5px solid #8b5cf6;
}

.task-top,
.question-head,
.task-name-row {
  display: flex;
  align-items: center;
}

.task-top,
.question-head {
  justify-content: space-between;
  gap: 12px;
}

.task-index {
  font-size: 12px;
  font-weight: 800;
  color: #7a7391;
}

.task-state {
  padding: 5px 10px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 800;
}

.task-state.done {
  background: rgba(34, 197, 94, 0.12);
  color: #15803d;
}

.task-state.todo {
  background: rgba(139, 92, 246, 0.12);
  color: #7f56d9;
}

.task-name-row {
  gap: 10px;
  margin-top: 12px;
}

.task-icon {
  font-size: 18px;
}

.task-name {
  margin: 0;
  font-size: 17px;
  color: #2f2840;
}

.task-desc {
  margin: 12px 0 0;
  font-size: 13px;
  line-height: 1.8;
}

.question-box {
  margin-top: 16px;
  padding: 14px;
  border-radius: 16px;
  background: #faf8ff;
  border: 1px dashed #dfd4ff;
}

.question-head {
  margin-bottom: 10px;
  font-size: 13px;
  color: #5f5874;
  font-weight: 700;
}

.question-count {
  color: #8b5cf6;
}

.question-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border-radius: 12px;
  background: #fff;
  border: 1px solid #eee8ff;
}

.question-item + .question-item {
  margin-top: 8px;
}

.question-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #8b5cf6;
  flex-shrink: 0;
}

.question-text {
  font-size: 13px;
  color: #443c59;
  line-height: 1.6;
}

.question-empty {
  padding: 12px;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.9);
  font-size: 13px;
  line-height: 1.7;
}

.status-view {
  padding: 56px 16px;
  text-align: center;
  font-size: 14px;
}

@media (max-width: 1100px) {
  .overview-grid {
    grid-template-columns: 1fr 1fr;
  }

  .path-meta-card {
    grid-column: 1 / -1;
  }
}

@media (max-width: 820px) {
  .progress-page {
    padding: 16px;
  }

  .hero-card,
  .content-header,
  .stage-top {
    flex-direction: column;
  }

  .hero-right {
    width: 100%;
  }

  .overview-grid {
    grid-template-columns: 1fr;
  }

  .content-scroll {
    max-height: none;
  }
}

.question-main {
  display: flex;
  flex-direction: column;
  gap: 6px;
  min-width: 0;
}

.question-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  font-size: 12px;
  color: #8a83a3;
}

</style>
