<template>
  <div class="progress-container">
    <h2>📊 学习进度</h2>

    <div v-if="stats" class="stats-grid">
      <div class="card">
        <h3>任务进度</h3>
        <p>{{ stats.completed_tasks }} / {{ stats.total_tasks }}</p>
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

    <div class="actions">
      <h3>今日打卡</h3>
      <input type="date" v-model="checkInForm.date" />
      <input type="number" v-model.number="checkInForm.hours" placeholder="学习时长" />
      <button @click="doCheckIn">打卡</button>
    </div>

    <div class="tasks">
      <h3>任务管理 (示例)</h3>
      <div class="task-item">
        <span>接入数据库</span>
        <button @click="updateTask('接入数据库', 'completed')">标记完成</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import api from '../api/index'

const user = JSON.parse(localStorage.getItem('user_info'))
const userId = user?.user_id
const stats = ref(null)
const checkInForm = reactive({ date: new Date().toISOString().split('T')[0], hours: 1 })

onMounted(() => {
  if(userId) loadStats()
})

const loadStats = async () => {
  const res = await api.getProgress(userId)
  stats.value = res.data
}

const doCheckIn = async () => {
  await api.checkIn(userId, checkInForm.date, checkInForm.hours)
  alert('打卡成功')
  loadStats()
}

const updateTask = async (name, status) => {
  await api.updateTask(userId, name, status)
  alert('任务已更新')
  loadStats()
}
</script>

<style scoped>
.progress-container { max-width: 800px; margin: 20px auto; }
.stats-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; margin-bottom: 30px; }
.card { border: 1px solid #ddd; padding: 15px; text-align: center; border-radius: 8px; }
progress { width: 100%; }
.actions, .tasks { margin-top: 20px; padding: 15px; border: 1px solid #eee; }
.task-item { display: flex; justify-content: space-between; padding: 10px 0; border-bottom: 1px solid #eee; }
</style>