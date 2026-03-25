<template>
  <div class="path-container">
    <h2>🎯 学习路径规划</h2>
    <div class="form-box">
      <input v-model="form.goal" placeholder="学习目标 (如：完成知识工程课程项目)" />
      <select v-model="form.level">
        <option value="初学者">初学者</option>
        <option value="进阶者">进阶者</option>
        <option value="专家">专家</option>
      </select>
      <input type="number" v-model.number="form.time" placeholder="每周可用时间 (小时)" />
      <button @click="generate">生成路径</button>
    </div>

    <div v-if="currentPath" class="result-box">
      <h3>为您生成的路径：</h3>
      <ul>
        <li v-for="(step, idx) in currentPath" :key="idx">{{ step }}</li>
      </ul>
    </div>

    <div v-if="savedPath" class="saved-box">
      <h3>当前保存的路径：</h3>
      <ul>
        <li v-for="(step, idx) in savedPath" :key="idx">{{ step }}</li>
      </ul>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import api from '../api/index'

const user = JSON.parse(localStorage.getItem('user_info'))
const userId = user?.user_id

const form = reactive({ goal: '', level: '初学者', time: 8 })
const currentPath = ref(null)
const savedPath = ref(null)

onMounted(() => {
  if(userId) loadSavedPath()
})

const generate = async () => {
  try {
    const res = await api.generatePath(userId, form.goal, form.level, form.time)
    currentPath.value = res.data.path
  } catch (e) { alert('生成失败') }
}

const loadSavedPath = async () => {
  try {
    const res = await api.getPath(userId)
    if(res.data.path) savedPath.value = res.data.path
  } catch (e) {}
}
</script>

<style scoped>
.path-container { max-width: 600px; margin: 20px auto; }
.form-box { display: flex; gap: 10px; margin-bottom: 20px; flex-wrap: wrap; }
input, select { padding: 8px; flex: 1; }
button { padding: 8px 15px; background: #42b983; color: white; border: none; cursor: pointer; }
.result-box, .saved-box { background: #f0f0f0; padding: 15px; border-radius: 5px; margin-top: 20px; }
</style>