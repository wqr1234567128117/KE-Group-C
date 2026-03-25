<template>
  <div class="qa-layout">
    <!-- 左侧：聊天区域 -->
    <div class="chat-area">
      <div class="messages">
        <div v-for="(msg, idx) in messages" :key="idx" :class="['msg', msg.role]">
          <strong>{{ msg.role === 'user' ? '我' : '助教' }}:</strong>
          <p>{{ msg.content }}</p>
          <!-- 如果是作业辅助，显示 tips -->
          <ul v-if="msg.tips" class="tips-list">
            <li v-for="tip in msg.tips" :key="tip">{{ tip }}</li>
          </ul>
        </div>
      </div>

      <div class="input-area">
        <input v-model="question" placeholder="输入问题..." @keyup.enter="sendQuestion" />
        <button @click="sendQuestion">发送</button>
        <button @click="toggleMode" class="mode-btn">
          {{ isHomeworkMode ? '切换回普通问答' : '切换至作业辅助' }}
        </button>
      </div>
    </div>

    <!-- 右侧：辅助信息 -->
    <div class="sidebar">
      <div class="panel">
        <h3>🔥 热门问题</h3>
        <ul>
          <li v-for="item in hotQuestions" :key="item.question" @click="question = item.question">
            {{ item.question }} ({{ item.count }})
          </li>
        </ul>
      </div>

      <div class="panel">
        <h3>💡 推荐问题</h3>
        <ul>
          <li v-for="q in suggestions" :key="q" @click="question = q">{{ q }}</li>
        </ul>
      </div>

      <div class="panel">
        <h3>📜 历史记录</h3>
        <button @click="loadHistory" class="small-btn">刷新</button>
        <button @click="clearHistory" class="small-btn danger">清空</button>
        <ul class="history-list">
          <li v-for="rec in history" :key="rec.id">
            <small>{{ rec.created_at }}</small><br>
            {{ rec.question }}
          </li>
        </ul>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, reactive } from 'vue'
import api from '../api/index'

const user = JSON.parse(localStorage.getItem('user_info'))
const userId = user?.user_id

const question = ref('')
const messages = ref([])
const history = ref([])
const hotQuestions = ref([])
const suggestions = ref([])
const isHomeworkMode = ref(false)

// 初始化加载
onMounted(() => {
  if (!userId) return
  loadHistory()
  loadSidebarData()
})

const loadSidebarData = async () => {
  try {
    const [hotRes, sugRes] = await Promise.all([
      api.getHotQuestions(),
      api.getSuggestions()
    ])
    hotQuestions.value = hotRes.data
    suggestions.value = sugRes.data
  } catch (e) { console.error(e) }
}

const loadHistory = async () => {
  try {
    const res = await api.getHistory(userId)
    history.value = res.data
    // 将历史记录也渲染到消息区（可选）
  } catch (e) { console.error(e) }
}

const clearHistory = async () => {
  if(!confirm('确定清空历史吗？')) return
  await api.clearHistory(userId)
  loadHistory()
}

const sendQuestion = async () => {
  if (!question.value.trim()) return

  const qText = question.value
  messages.value.push({ role: 'user', content: qText })
  question.value = ''

  try {
    let res
    if (isHomeworkMode.value) {
      res = await api.getHomeworkHelp(userId, qText)
      messages.value.push({
        role: 'assistant',
        content: res.data.answer,
        tips: res.data.tips
      })
    } else {
      res = await api.askQuestion(userId, qText)
      messages.value.push({ role: 'assistant', content: res.data.answer })
    }
    // 发送后刷新历史
    loadHistory()
  } catch (e) {
    messages.value.push({ role: 'system', content: '请求失败，请稍后重试' })
  }
}

const toggleMode = () => {
  isHomeworkMode.value = !isHomeworkMode.value
}
</script>

<style scoped>
.qa-layout { display: flex; height: 80vh; gap: 20px; padding: 20px; }
.chat-area { flex: 3; display: flex; flex-direction: column; border: 1px solid #ccc; border-radius: 8px; }
.messages { flex: 1; overflow-y: auto; padding: 10px; background: #f9f9f9; }
.msg { margin: 10px 0; padding: 10px; border-radius: 5px; }
.msg.user { background: #e3f2fd; text-align: right; }
.msg.assistant { background: #fff; border: 1px solid #eee; }
.tips-list { background: #fff3cd; padding: 5px 15px; font-size: 0.9em; }
.input-area { display: flex; padding: 10px; border-top: 1px solid #ccc; }
.input-area input { flex: 1; padding: 8px; }
.sidebar { flex: 1; overflow-y: auto; }
.panel { margin-bottom: 20px; border: 1px solid #eee; padding: 10px; border-radius: 5px; }
.history-list { list-style: none; padding: 0; font-size: 0.85em; }
.history-list li { border-bottom: 1px solid #eee; padding: 5px 0; cursor: pointer; }
.small-btn { padding: 2px 8px; font-size: 0.8em; margin-right: 5px; }
.danger { background: #ffebee; color: red; border: 1px solid red; }
.mode-btn { margin-left: 10px; background: #ff9800; color: white; border: none; padding: 0 10px; cursor: pointer;}
</style>