<!-- CustomizePath.vue -->
<template>
  <div class="tutor-container">
    <div class="tutor-content">
      <h1 class="tutor-title">Your Personal <span class="highlight">Tutor</span></h1>
      <p class="subtitle">请输入您想学习的内容，我们将为您定制专属课程</p>

      <div class="input-area">
        <input
          v-model="topic"
          class="tutor-input"
          placeholder="Teach me about..."
          @keyup.enter="startChat"
        />
        <button class="start-btn" @click="startChat">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2">
            <line x1="7" y1="17" x2="17" y2="7"></line>
            <polyline points="7 7 17 7 17 17"></polyline>
          </svg>
        </button>
      </div>

      <div class="suggestions">
        <div
          v-for="(tag, index) in tags"
          :key="index"
          class="tag-item"
          @click="selectTag(tag)"
        >
          <span class="tag-icon">{{ tag.icon }}</span>
          {{ tag.label }}
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const topic = ref('')

// 推荐标签
const tags = [
  { label: 'Basketball', icon: '🏀' },
  { label: 'Machine Learning', icon: '🤖' },
  { label: 'Photography', icon: '📷' },
  { label: 'Cooking', icon: '🍳' }
]

const selectTag = (tag) => {
  topic.value = tag.label
}

const startChat = () => {
  if (!topic.value) return

  // 跳转到 LLM 交互页面，并传递话题参数
  router.push({
    name: 'LLMLearningPath',
    query: { topic: topic.value }
  })
}
</script>

<style scoped>
.tutor-container {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100vh;
  background: #fff;
}

.tutor-content {
  width: 100%;
  max-width: 600px;
  text-align: center;
  padding: 20px;
}

.tutor-title {
  font-size: 48px;
  font-weight: 700;
  margin-bottom: 10px;
  color: #1a1a1a;
}

.highlight {
  color: #2563eb; /* 蓝色高亮 */
}

.subtitle {
  color: #666;
  margin-bottom: 40px;
  font-size: 18px;
}

.input-area {
  display: flex;
  gap: 10px;
  margin-bottom: 30px;
}

.tutor-input {
  flex: 1;
  padding: 16px 20px;
  border: 1px solid #ddd;
  border-radius: 12px;
  font-size: 16px;
  outline: none;
}

.tutor-input:focus {
  border-color: #2563eb;
  box-shadow: 0 0 0 2px rgba(37, 99, 235, 0.2);
}

.start-btn {
  width: 60px;
  background: #2563eb;
  border: none;
  border-radius: 12px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.2s;
}

.start-btn:hover {
  background: #1d4ed8;
}

.suggestions {
  display: flex;
  justify-content: center;
  gap: 12px;
  flex-wrap: wrap;
}

.tag-item {
  padding: 8px 16px;
  border: 1px solid #eee;
  border-radius: 20px;
  background: #f9f9f9;
  cursor: pointer;
  font-size: 14px;
  display: flex;
  align-items: center;
  gap: 6px;
  transition: all 0.2s;
}

.tag-item:hover {
  background: #eef2ff;
  border-color: #c7d2fe;
}
</style>