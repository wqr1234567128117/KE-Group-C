<template>
  <div class="progress-container">
    <!-- 1. 顶部路径选择 -->
    <div class="header-section">
      <h2>📊 学习进度追踪</h2>
      <div class="path-selector">
        <label>选择学习路径：</label>
        <select v-model="selectedPathId" @change="onPathChange">
          <option v-for="path in pathOptions" :key="path.path_id" :value="path.path_id">
            {{ path.goal }} ({{ path.domain }})
          </option>
        </select>
      </div>
    </div>

    <!-- 2. 统计概览 -->
    <div v-if="stats" class="stats-grid">
      <div class="card">
        <h3>总体进度</h3>
        <div class="progress-text">{{ stats.completed_tasks }} / {{ stats.total_tasks }} 任务</div>
        <progress :value="stats.completed_tasks" :max="stats.total_tasks"></progress>
      </div>
      <div class="card">
        <h3>总时长</h3>
        <p>{{ stats.study_hours }} 小时</p>
      </div>
      <div class="card">
        <h3>打卡天数</h3>
        <p>{{ stats.check_in_days }} 天</p>
      </div>
    </div>

    <!-- 3. 详细任务列表 -->
    <div class="curriculum-tree" v-if="displayStages.length > 0">
      <h3>📚 当前路径任务详情</h3>

      <!-- 循环展示阶段 (Progress) -->
      <div v-for="stage in displayStages" :key="stage.progress_id" class="stage-block">
        <div class="stage-header">
          <h4>{{ stage.progress_name }}</h4>
          <span class="stage-desc">{{ stage.progress_description }}</span>
        </div>

        <div class="tasks-list">
          <!-- 循环展示任务点 (Task) -->
          <div
            v-for="task in stage.tasks"
            :key="task.task_id"
            class="task-item"
            :class="getTaskStatusClass(task.is_completed)"
          >
            <!-- 任务点头部 -->
            <div class="task-header">
              <div class="task-title">
                <!-- 状态图标 -->
                <span class="status-icon">
                  {{ getStatusIcon(task.is_completed) }}
                </span>
                <span>{{ task.task_name }}</span>
              </div>
              <span class="task-badge">
                {{ task.is_completed ? '已完成' : '进行中' }}
              </span>
            </div>

            <!-- 任务点对应的题目列表 -->
            <!-- 注意：这里为了展示，我们直接从API获取题目，或者假设后端在详情里返回了题目 -->
            <!-- 由于后端API /api/learning-path/detail 目前可能不包含深层题目数据，这里仅展示任务 -->
            <div class="questions-list" v-if="false">
              <!-- 实际项目中，你可能需要点击任务时调用 /api/tasks/{id}/questions 来懒加载题目 -->
              <div class="question-item">
                <span class="q-icon">📝</span>
                <span class="q-title">该任务包含题目（需点击进入详情页查看）</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div v-else-if="selectedPathId" class="loading">正在加载路径详情...</div>
    <div v-else class="empty">请先选择一个学习路径。</div>

    <!-- 底部打卡区域 -->
    <div class="actions">
      <h3>今日打卡</h3>
      <input type="date" v-model="checkInForm.date" />
      <input type="number" v-model.number="checkInForm.hours" placeholder="学习时长(小时)" min="0" max="24" />
      <button @click="doCheckIn">提交打卡</button>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import api from '../api/index' // 引入你修正后的 API 模块

// --- 状态定义 ---
const user = JSON.parse(localStorage.getItem('user_info'))
const userId = user?.user_id

const stats = ref(null)
const pathOptions = ref([]) // 存储从后端获取的路径列表
const selectedPathId = ref(null)

// 存储后端返回的原始详情数据
const pathDetailData = ref(null)

// 经过处理的、用于视图展示的阶段列表
const displayStages = ref([])

const checkInForm = reactive({
  date: new Date().toISOString().split('T')[0],
  hours: 1
})

// --- 生命周期 ---
onMounted(async () => {
  if (!userId) {
    alert('请先登录')
    return
  }
  await loadStats()
  await loadPathList()
  if (pathOptions.value.length > 0) {
    selectedPathId.value = pathOptions.value[0].path_id
    await loadPathDetail(selectedPathId.value)
  }
})

// --- 方法 ---

const loadStats = async () => {
  try {
    const res = await api.getProgress(userId)
    stats.value = res.data
  } catch (error) {
    console.error('加载统计失败:', error)
  }
}

const loadPathList = async () => {
  try {
    const res = await api.getPaths(userId)
    pathOptions.value = res.data
  } catch (error) {
    console.error('加载路径列表失败:', error)
  }
}

const loadPathDetail = async (pathId) => {
  try {
    const res = await api.getPathDetail(pathId)
    pathDetailData.value = res.data

    // 核心逻辑：将后端返回的扁平 progresses/tasks 映射为视图需要的树状结构
    // 后端返回的 LearningPathDetailResponse 包含 .progresses 和 .tasks
    // 我们需要把 tasks 按 progress_id 归组到 progresses 中
    const progresses = res.data.progresses || []
    const allTasks = res.data.tasks || []

    // 将任务按 progress_id 分组
    const tasksByProgress = {}
    allTasks.forEach(task => {
      if (!tasksByProgress[task.progress_id]) {
        tasksByProgress[task.progress_id] = []
      }
      tasksByProgress[task.progress_id].push(task)
    })

    // 组合最终展示数据
    displayStages.value = progresses.map(progress => ({
      ...progress,
      tasks: tasksByProgress[progress.progress_id] || []
    }))

  } catch (error) {
    console.error('加载路径详情失败:', error)
  }
}

const onPathChange = () => {
  if (selectedPathId.value) {
    loadPathDetail(selectedPathId.value)
  }
}

const doCheckIn = async () => {
  try {
    await api.checkIn(checkInForm.date, checkInForm.hours)
    alert('打卡成功！')
    loadStats() // 刷新统计数据
  } catch (error) {
    alert('打卡失败: ' + error.message)
  }
}

// --- 样式辅助函数 ---
const getTaskStatusClass = (isCompleted) => {
  if (isCompleted) return 'status-completed'
  return 'status-current' // 假设未完成的任务显示为“进行中”样式
}

const getStatusIcon = (isCompleted) => {
  return isCompleted ? '✅' : '▶️'
}
</script>

<style scoped>
/* 样式保持不变，沿用你提供的美观样式 */
.progress-container { max-width: 900px; margin: 20px auto; font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; color: #333; }
h2, h3, h4 { margin-top: 0; }

.header-section { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.path-selector select { padding: 8px 12px; border-radius: 4px; border: 1px solid #ddd; font-size: 14px; width: 250px; }

.stats-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; margin-bottom: 30px; }
.card { border: 1px solid #eee; padding: 20px; text-align: center; border-radius: 12px; background: #fff; box-shadow: 0 2px 8px rgba(0,0,0,0.05); }
progress { width: 100%; height: 8px; border-radius: 4px; margin-top: 10px; }
progress::-webkit-progress-bar { background-color: #f0f0f0; border-radius: 4px; }
progress::-webkit-progress-value { background-color: #42b983; border-radius: 4px; }

.curriculum-tree { margin-top: 30px; }
.stage-block { margin-bottom: 25px; border: 1px solid #e0e0e0; border-radius: 8px; overflow: hidden; background: #fafafa; }

.stage-header { background: #f5f5f5; padding: 15px 20px; border-bottom: 1px solid #e0e0e0; }
.stage-header h4 { margin: 0; font-size: 18px; color: #2c3e50; }
.stage-desc { font-size: 12px; color: #7f8c8d; display: block; margin-top: 5px; }

.tasks-list { padding: 10px; }
.task-item {
  padding: 15px;
  margin-bottom: 10px;
  border-radius: 6px;
  border: 1px solid transparent;
  background: #fff;
  transition: all 0.3s ease;
}
.task-item:last-child { margin-bottom: 0; }

.task-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }
.task-title { display: flex; align-items: center; font-weight: bold; font-size: 16px; }
.status-icon { margin-right: 10px; font-size: 18px; }
.task-badge { font-size: 12px; padding: 4px 8px; border-radius: 4px; background: #eee; }

.questions-list { margin-top: 15px; padding-top: 15px; border-top: 1px dashed #eee; }
.question-item { display: flex; align-items: center; padding: 8px 10px; margin-bottom: 5px; background: #f9f9f9; border-radius: 4px; font-size: 14px; }
.q-icon { margin-right: 8px; }
.q-title { flex: 1; }
.q-difficulty { font-size: 12px; padding: 2px 6px; border-radius: 3px; color: #fff; }
.q-difficulty.easy { background: #42b983; }
.q-difficulty.medium { background: #f39c12; }
.q-difficulty.hard { background: #e74c3c; }

/* 状态样式区分 */
.status-completed { border-left: 4px solid #42b983; opacity: 0.8; }
.status-completed .task-title { color: #42b983; }
.status-completed .task-badge { background: #e8f8f5; color: #42b983; }

.status-current { border-left: 4px solid #3498db; box-shadow: 0 4px 12px rgba(52, 152, 219, 0.15); transform: scale(1.01); }
.status-current .task-title { color: #3498db; }
.status-current .task-badge { background: #ebf5fb; color: #3498db; }

.status-pending { border-left: 4px solid #bdc3c7; opacity: 0.6; filter: grayscale(1); }
.status-pending .task-title { color: #7f8c8d; }
.status-pending .task-badge { background: #f4f4f4; color: #95a5a6; }

.actions { margin-top: 30px; padding: 20px; border: 1px solid #eee; border-radius: 8px; background: #fff; }
input { padding: 8px; margin-right: 10px; border: 1px solid #ddd; border-radius: 4px; }
button { padding: 8px 20px; background: #42b983; color: white; border: none; border-radius: 4px; cursor: pointer; }
button:hover { background: #369970; }

.loading, .empty { text-align: center; color: #666; padding: 20px; }
</style>