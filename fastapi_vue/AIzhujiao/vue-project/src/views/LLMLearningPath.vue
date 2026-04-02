<!-- LLMChat.vue -->
<template>
  <div class="chat-container">
    <!-- 左侧：对话区域 -->
    <div class="chat-main">
      <div class="chat-header">
        <h3>话题：{{ topic }}</h3>
      </div>

      <div class="messages-area">
        <!-- 模拟 AI 回复卡片 -->
        <div class="message-card">
          <div class="card-header">
            <span class="avatar">🤖</span>
            <strong>网页 #0：</strong>
            <span class="source-link">什么是机器学习（ML）？定义与示例</span>
          </div>

          <div class="card-content">
            <h2>什么是机器学习（ML）？</h2>
            <p class="date">2026年3月17日</p>
            <div class="text-body">
              <p>你好！今天，我们将学习一个非常酷的知识，叫做机器学习（ML）。</p>
              <p>机器学习是一种人工智能，帮助计算机从数据中学习，而无需明确编程。想象一下，如果你能通过展示大量图片教计算机识别不同类型的动物。这其实就是机器学习的作用！</p>
            </div>
          </div>
        </div>
      </div>

      <div class="chat-input-area">
        <input
          v-model="inputMsg"
          class="chat-input"
          placeholder="后续问题..."
          @keyup.enter="sendMsg"
        />
        <button class="send-btn" @click="sendMsg">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2">
            <line x1="7" y1="17" x2="17" y2="7"></line>
            <polyline points="7 7 17 7 17 17"></polyline>
          </svg>
        </button>
      </div>
    </div>

    <!-- 右侧：资源列表 -->
    <div class="chat-sidebar">
      <h4>资料来源：</h4>
      <div class="sources-list">
        <div
          v-for="(source, idx) in sources"
          :key="idx"
          class="source-item"
          @click="openLink(source.url)"
        >
          <h5>{{ source.title }}</h5>
          <p>{{ source.url }}</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()
const topic = ref('机器学习') // 默认或从路由获取
const inputMsg = ref('')

// 模拟资源数据
const sources = ref([
  { title: '什么是机器学习（ML）？定义与示例', url: 'https://datascience.berkeley.edu...' },
  { title: '机器学习教程 - GeeksforGeeks', url: 'https://www.geeksforgeeks.org...' },
  { title: '什么是机器学习？定义、类型与示例', url: 'https://www.coursera.org/articl...' },
  { title: '什么是机器学习（ML）？定义与示例', url: 'https://ischoolonline.berkeley.e...' },
  { title: '什么是机器学习？', url: 'https://www.oracle.com/artificia...' }
])

onMounted(() => {
  if (route.query.topic) {
    topic.value = route.query.topic
  }
})

const sendMsg = () => {
  if (!inputMsg.value) return
  // 发送逻辑...
  inputMsg.value = ''
}

const openLink = (url) => {
  window.open(url, '_blank')
}
</script>

<style scoped>
.chat-container {
  display: flex;
  height: 100vh;
  background: #fff;
}

/* 左侧主聊天区 */
.chat-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  padding: 20px;
  border-right: 1px solid #eee;
}

.chat-header {
  margin-bottom: 20px;
}

.messages-area {
  flex: 1;
  overflow-y: auto;
  padding-right: 10px;
}

.message-card {
  background: #f8f9fa;
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 20px;
  border: 1px solid #e9ecef;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 15px;
  font-size: 14px;
  color: #495057;
}

.avatar {
  font-size: 20px;
}

.source-link {
  color: #2563eb;
  font-size: 12px;
  background: #eef2ff;
  padding: 2px 6px;
  border-radius: 4px;
}

.card-content h2 {
  margin: 0 0 10px 0;
  font-size: 24px;
  color: #1a1a1a;
}

.date {
  color: #888;
  font-size: 12px;
  margin-bottom: 15px;
}

.text-body p {
  line-height: 1.6;
  color: #333;
  margin-bottom: 10px;
}

/* 输入框区域 */
.chat-input-area {
  display: flex;
  gap: 10px;
  margin-top: 20px;
}

.chat-input {
  flex: 1;
  padding: 12px 16px;
  border: 1px solid #ddd;
  border-radius: 8px;
  outline: none;
}

.send-btn {
  width: 50px;
  background: #2563eb;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
}

/* 右侧侧边栏 */
.chat-sidebar {
  width: 320px;
  padding: 20px;
  background: #fff;
  overflow-y: auto;
}

.chat-sidebar h4 {
  margin-bottom: 20px;
  font-size: 16px;
  color: #333;
}

.sources-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.source-item {
  padding: 12px;
  border: 1px solid #eee;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.source-item:hover {
  background: #f0f0f0;
  border-color: #ccc;
}

.source-item h5 {
  margin: 0 0 5px 0;
  font-size: 14px;
  color: #1a1a1a;
}

.source-item p {
  margin: 0;
  font-size: 12px;
  color: #888;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>