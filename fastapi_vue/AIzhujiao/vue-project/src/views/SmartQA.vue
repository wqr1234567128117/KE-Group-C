<template>
  <div class="smart-qa-container">
    <h1>🤖 智能问答助手</h1>

    <div class="chat-box">
      <div v-for="(msg, index) in messages" :key="index"
           :class="['message', msg.role === 'user' ? 'user-msg' : 'bot-msg']">
        <strong>{{ msg.role === 'user' ? '你' : 'AI' }}:</strong>
        <p>{{ msg.content }}</p>
      </div>
    </div>

    <div class="input-area">
      <textarea
        v-model="userInput"
        placeholder="请输入你的问题..."
        @keyup.enter="sendMessage"
        :disabled="loading"
      ></textarea>
      <button @click="sendMessage" :disabled="loading || !userInput.trim()">
        {{ loading ? '思考中...' : '发送' }}
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import axios from 'axios'

const userInput = ref('')
const messages = ref([
  { role: 'bot', content: '你好！我是你的智能助手，请问有什么可以帮你？' }
])
const loading = ref(false)

const sendMessage = async () => {
  if (!userInput.value.trim() || loading.value) return

  const question = userInput.value.trim()
  messages.value.push({ role: 'user', content: question })
  userInput.value = ''
  loading.value = true

  try {
    // 调用后端 API（假设部署在 http://localhost:8000）
    const response = await axios.post('http://localhost:8000/api/ask', {
      question: question
    })

    messages.value.push({
      role: 'bot',
      content: response.data.answer || '抱歉，我暂时无法回答这个问题。'
    })
  } catch (error) {
    console.error('请求失败:', error)
    messages.value.push({
      role: 'bot',
      content: '❌ 网络错误或服务器未响应，请稍后再试。'
    })
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.smart-qa-container {
  max-width: 800px;
  margin: 40px auto;
  padding: 20px;
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
}

h1 {
  text-align: center;
  color: #333;
  margin-bottom: 30px;
}

.chat-box {
  height: 400px;
  overflow-y: auto;
  border: 1px solid #ddd;
  border-radius: 8px;
  padding: 15px;
  background-color: #f9f9f9;
  margin-bottom: 20px;
}

.message {
  margin: 10px 0;
  padding: 10px 15px;
  border-radius: 8px;
  max-width: 80%;
}

.user-msg {
  background-color: #e3f2fd;
  align-self: flex-end;
  margin-left: auto;
}

.bot-msg {
  background-color: #f1f8e9;
  align-self: flex-start;
}

.input-area {
  display: flex;
  gap: 10px;
}

textarea {
  flex: 1;
  padding: 12px;
  border: 1px solid #ccc;
  border-radius: 6px;
  resize: none;
  height: 60px;
  font-size: 14px;
}

button {
  padding: 12px 24px;
  background-color: #4CAF50;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-weight: bold;
  transition: background 0.3s;
}

button:hover:not(:disabled) {
  background-color: #45a049;
}

button:disabled {
  background-color: #cccccc;
  cursor: not-allowed;
}
</style>