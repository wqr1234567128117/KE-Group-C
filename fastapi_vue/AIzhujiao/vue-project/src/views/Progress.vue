<template>
  <div class="progress-container">
    <!-- 1. 顶部路径选择 -->
    <div class="header-section">
      <h2>📊 学习进度追踪</h2>
      <div class="path-selector">
        <label>选择学习路径：</label>
        <select v-model="selectedPathId" @change="onPathChange">
          <option v-for="path in pathOptions" :key="path.id" :value="path.id">
            {{ path.name }}
          </option>
        </select>
      </div>
    </div>

    <!-- 2. 统计概览 (保留原有功能) -->
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

    <!-- 3. 详细任务列表 (核心修改部分) -->
    <div class="curriculum-tree" v-if="currentPathData">
      <h3>📚 当前路径任务详情</h3>

      <!-- 循环展示阶段 -->
      <div v-for="stage in currentPathData.stages" :key="stage.id" class="stage-block">
        <div class="stage-header">
          <h4>{{ stage.name }}</h4>
          <span class="stage-desc">{{ stage.description }}</span>
        </div>

        <div class="tasks-list">
          <!-- 循环展示任务点 -->
          <div
            v-for="task in stage.tasks"
            :key="task.id"
            class="task-item"
            :class="getTaskStatusClass(task.status)"
          >
            <!-- 任务点头部 -->
            <div class="task-header">
              <div class="task-title">
                <!-- 状态图标 -->
                <span class="status-icon">
                  {{ getStatusIcon(task.status) }}
                </span>
                <span>{{ task.name }}</span>
              </div>
              <span class="task-badge">{{ task.status_text }}</span>
            </div>

            <!-- 任务点对应的题目列表 -->
            <div class="questions-list">
              <div v-for="question in task.questions" :key="question.id" class="question-item">
                <span class="q-icon">📝</span>
                <span class="q-title">{{ question.title }}</span>
                <span class="q-difficulty" :class="question.difficulty">{{ question.difficulty }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 底部打卡区域 -->
    <div class="actions">
      <h3>今日打卡</h3>
      <input type="date" v-model="checkInForm.date" />
      <input type="number" v-model.number="checkInForm.hours" placeholder="学习时长" />
      <button @click="doCheckIn">提交打卡</button>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
// import api from '../api/index' // 实际项目中请引入你的 API 模块

// --- 模拟数据 (实际开发中请从后端 API 获取) ---
const pathOptions = [
  { id: 1, name: 'Java 后端开发工程师' },
  { id: 2, name: 'Vue3 前端开发专家' },
  { id: 3, name: 'Python 数据分析' }
]

// 模拟的当前路径详细数据
const mockPathData = {
  id: 1,
  name: 'Java 后端开发工程师',
  stages: [
    {
      id: 101,
      name: '第一阶段：Java 基础',
      description: '掌握语法、面向对象编程',
      tasks: [
        {
          id: 1001,
          name: '环境搭建与 Hello World',
          status: 'completed', // 状态：completed, current, pending
          status_text: '已完成',
          questions: [
            { id: 1, title: 'JDK 安装配置检查', difficulty: 'easy' },
            { id: 2, title: '第一个 Java 程序', difficulty: 'easy' }
          ]
        },
        {
          id: 1002,
          name: '面向对象核心概念',
          status: 'current',
          status_text: '进行中',
          questions: [
            { id: 3, title: '封装、继承、多态理解', difficulty: 'medium' },
            { id: 4, title: '类与对象的设计练习', difficulty: 'medium' }
          ]
        },
        {
          id: 1003,
          name: '集合框架与异常处理',
          status: 'pending',
          status_text: '未开始',
          questions: [
            { id: 5, title: 'ArrayList 与 LinkedList', difficulty: 'hard' }
          ]
        }
      ]
    },
    {
      id: 102,
      name: '第二阶段：数据库与 SQL',
      description: 'MySQL 基础与高级查询',
      tasks: [
        {
          id: 1004,
          name: 'SQL 基础语法',
          status: 'pending',
          status_text: '未开始',
          questions: [
            { id: 6, title: 'SELECT 语句练习', difficulty: 'medium' }
          ]
        }
      ]
    }
  ]
}

// --- 状态定义 ---
const user = JSON.parse(localStorage.getItem('user_info'))
const userId = user?.user_id
const stats = ref(null)
const selectedPathId = ref(1)
const currentPathData = ref(null) // 存储当前选中的路径详情

const checkInForm = reactive({
  date: new Date().toISOString().split('T')[0],
  hours: 1
})

// --- 生命周期 ---
onMounted(() => {
  if(userId) {
    loadStats()
    loadPathDetail(selectedPathId.value)
  }
})

// --- 方法 ---

// 模拟加载统计数据
const loadStats = async () => {
  // const res = await api.getProgress(userId)
  // stats.value = res.data
  // 模拟数据
  stats.value = { completed_tasks: 5, total_tasks: 20, study_hours: 12, check_in_days: 3 }
}

// 模拟加载路径详情
const loadPathDetail = async (pathId) => {
  // const res = await api.getPathDetail(pathId)
  // currentPathData.value = res.data
  currentPathData.value = mockPathData
}

const onPathChange = () => {
  // 切换路径时重新加载数据
  loadPathDetail(selectedPathId.value)
}

const doCheckIn = async () => {
  // await api.checkIn(userId, checkInForm.date, checkInForm.hours)
  alert('打卡成功')
  loadStats()
}

// --- 样式辅助函数 ---

// 根据状态返回 CSS 类名
const getTaskStatusClass = (status) => {
  if (status === 'completed') return 'status-completed'
  if (status === 'current') return 'status-current'
  return 'status-pending'
}

// 根据状态返回图标
const getStatusIcon = (status) => {
  if (status === 'completed') return '✅'
  if (status === 'current') return '▶️'
  return '⏸️'
}

</script>

<style scoped>
/* 基础布局 */
.progress-container { max-width: 900px; margin: 20px auto; font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; color: #333; }
h2, h3, h4 { margin-top: 0; }

/* 顶部选择器 */
.header-section { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.path-selector select { padding: 8px 12px; border-radius: 4px; border: 1px solid #ddd; font-size: 14px; width: 250px; }

/* 统计卡片 */
.stats-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; margin-bottom: 30px; }
.card { border: 1px solid #eee; padding: 20px; text-align: center; border-radius: 12px; background: #fff; box-shadow: 0 2px 8px rgba(0,0,0,0.05); }
progress { width: 100%; height: 8px; border-radius: 4px; margin-top: 10px; }
progress::-webkit-progress-bar { background-color: #f0f0f0; border-radius: 4px; }
progress::-webkit-progress-value { background-color: #42b983; border-radius: 4px; }

/* 课程树结构 */
.curriculum-tree { margin-top: 30px; }
.stage-block { margin-bottom: 25px; border: 1px solid #e0e0e0; border-radius: 8px; overflow: hidden; background: #fafafa; }

/* 阶段头部 */
.stage-header { background: #f5f5f5; padding: 15px 20px; border-bottom: 1px solid #e0e0e0; }
.stage-header h4 { margin: 0; font-size: 18px; color: #2c3e50; }
.stage-desc { font-size: 12px; color: #7f8c8d; display: block; margin-top: 5px; }

/* 任务列表 */
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

/* 任务头部 */
.task-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }
.task-title { display: flex; align-items: center; font-weight: bold; font-size: 16px; }
.status-icon { margin-right: 10px; font-size: 18px; }
.task-badge { font-size: 12px; padding: 4px 8px; border-radius: 4px; background: #eee; }

/* 题目列表 */
.questions-list { margin-top: 15px; padding-top: 15px; border-top: 1px dashed #eee; }
.question-item { display: flex; align-items: center; padding: 8px 10px; margin-bottom: 5px; background: #f9f9f9; border-radius: 4px; font-size: 14px; }
.q-icon { margin-right: 8px; }
.q-title { flex: 1; }
.q-difficulty { font-size: 12px; padding: 2px 6px; border-radius: 3px; color: #fff; }
.q-difficulty.easy { background: #42b983; }
.q-difficulty.medium { background: #f39c12; }
.q-difficulty.hard { background: #e74c3c; }

/* --- 状态样式区分 (核心需求) --- */

/* 已完成状态 */
.status-completed { border-left: 4px solid #42b983; opacity: 0.8; }
.status-completed .task-title { color: #42b983; }
.status-completed .task-badge { background: #e8f8f5; color: #42b983; }

/* 进行中状态 */
.status-current { border-left: 4px solid #3498db; box-shadow: 0 4px 12px rgba(52, 152, 219, 0.15); transform: scale(1.01); }
.status-current .task-title { color: #3498db; }
.status-current .task-badge { background: #ebf5fb; color: #3498db; }

/* 未开始状态 */
.status-pending { border-left: 4px solid #bdc3c7; opacity: 0.6; filter: grayscale(1); }
.status-pending .task-title { color: #7f8c8d; }
.status-pending .task-badge { background: #f4f4f4; color: #95a5a6; }

/* 底部打卡 */
.actions { margin-top: 30px; padding: 20px; border: 1px solid #eee; border-radius: 8px; background: #fff; }
input { padding: 8px; margin-right: 10px; border: 1px solid #ddd; border-radius: 4px; }
button { padding: 8px 20px; background: #42b983; color: white; border: none; border-radius: 4px; cursor: pointer; }
button:hover { background: #369970; }
</style>