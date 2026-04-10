<script setup>
import { ref, computed, onMounted } from 'vue';
import Sidebar from '../components/Sidebar.vue';
import ChatWindow from '../components/ChatWindow.vue';
import api from '../api/index'; // 引入 API

// 1. 用户信息
const user = JSON.parse(localStorage.getItem('user_info'));
const userId = user?.user_id;

// ---------- 状态数据 ----------
const conversations = ref([]); // 会话列表
const currentSessionId = ref(null); // 当前会话ID
const chatCache = ref({}); // 聊天内容缓存

// ---------- 核心逻辑 ----------

// 1. 加载会话列表
const loadConversations = async () => {
  try {
    // 假设 api.getConversations 返回的是包含 session_id 的列表
    const res = await api.getConversations(userId);
    conversations.value = res.data.map(item => ({
      id: item.session_id,
      title: item.latest_question ? item.latest_question.substring(0, 20) : '新对话',
      time: item.latest_asked_at,
    }));

    if (conversations.value.length > 0) {
      currentSessionId.value = conversations.value[0].id;
      await loadConversationDetail(currentSessionId.value);
    }
  } catch (error) {
    console.error('加载会话列表失败:', error);
  }
};

// 2. 加载具体会话详情
const loadConversationDetail = async (sessionId) => {
  try {
    const res = await api.getConversationDetail(sessionId);
    // 注意：这里假设后端返回的数据结构，你需要根据实际接口调整
    // 假设返回的是 [{ role: 'user', content: '...' }, { role: 'assistant', content: '...' }]
    // --- 核心修复：数据映射逻辑 ---
    // 假设后端返回的是一个包含 { question, answer } 对象的数组
    // 我们需要将其映射为 ChatWindow 组件需要的 { role, content } 格式
    chatCache.value[sessionId] = res.data.map(item => [
      // 用户消息
      {
        role: 'user',
        content: item.question // 对应你要求的 question
      },
      // 助手消息
      {
        role: 'assistant',
        content: item.answer // 对应你要求的 res.data.answer
      }
    ]).flat(); // 使用 flat() 将成对的数组展平为单一的消息列表

  } catch (error) {
    console.error('加载对话详情失败:', error);
    chatCache.value[sessionId] = [{ role: 'assistant', content: '历史记录加载失败' }];
  }
};

// 3. 发送消息
const handleSendMessage = async (messageObj) => {
  const message = messageObj.content;
  const isHomework = messageObj.isHomework;

  if (!message) return;

  // 临时 Session ID (如果是新对话，暂时为 null)
  const sessionId = currentSessionId.value;

  // 1. 乐观更新：先显示用户消息
  if (!chatCache.value[sessionId]) {
    chatCache.value[sessionId] = [];
  }

  const userMessage = { role: 'user', content: message };
  chatCache.value[sessionId].push(userMessage);

  try {
    // 2. 调用 API
    let res;
    if (isHomework) {
      res = await api.getHomeworkHelp(message);
    } else {
      // 如果 sessionId 为 null，后端应自动创建新会话并返回新 ID
      res = await api.askQuestion(message, sessionId);
    }

    // 3. 处理返回的新 Session ID (如果是新对话)
    const returnedSessionId = res.data.session_id;

    if (!currentSessionId.value && returnedSessionId) {
      currentSessionId.value = returnedSessionId;

      // 将缓存的数据迁移到新的 Session ID 下
      chatCache.value[returnedSessionId] = chatCache.value[sessionId];
      delete chatCache.value[sessionId];

      // 更新侧边栏
      conversations.value.unshift({
        id: returnedSessionId,
        title: message.substring(0, 20) || '新对话',
        time: new Date().toLocaleString(),
      });
    }

    // 4. 添加 AI 回复
    const finalSessionId = currentSessionId.value; // 确保使用更新后的 ID
    const aiMessage = {
      role: 'assistant',
      content: res.data.answer || res.data.result || '（无内容）',
    };

    chatCache.value[finalSessionId].push(aiMessage);

  } catch (err) {
    console.error(err);
    const errorMsg = {
      role: 'assistant',
      content: `错误: ${err.message || '请求失败'}`,
    };
    chatCache.value[currentSessionId.value].push(errorMsg);
  }
};

// 4. 新建对话
const handleNewChat = () => {
  currentSessionId.value = null;
  // 注意：这里不需要清空 chatCache，因为我们会用 null 或新的 ID 作为 key
};

// Sidebar 事件处理
const handleSelectChat = async (chatId) => {
  currentSessionId.value = chatId;
  await loadConversationDetail(chatId);
};

const handleSelectRecommend = (question) => {
  handleSendMessage({ content: question, isHomework: false });
};

// 其他空函数防止报错
const handleRenameChat = () => {};
const handlePinChat = () => {};
const handleShareChat = () => {};
const handleDeleteChat = () => {};

// ---------- 计算属性 ----------
// 确保传给 ChatWindow 的是当前会话的内容
const currentChatContent = computed(() => {
  return chatCache.value[currentSessionId.value] || [];
});

// 侧边栏状态
const isSidebarCollapsed = ref(false);

onMounted(() => {
  loadConversations();
});
</script>

<template>
  <div class="smart-qa-container">
    <!-- 修复点 1: 修正 Sidebar 的绑定属性，使用 conversations 而不是 chatHistory -->
    <Sidebar
      :history="conversations"
      :current-chat-id="currentSessionId"
      @new-chat="handleNewChat"
      @select-chat="handleSelectChat"
      @rename-chat="handleRenameChat"
      @pin-chat="handlePinChat"
      @share-chat="handleShareChat"
      @delete-chat="handleDeleteChat"
      @select-recommend="handleSelectRecommend"
      v-model:collapsed="isSidebarCollapsed"
    />

    <!-- 修复点 2: 确保 ChatWindow 接收正确的数据 -->
    <ChatWindow
      :class="{ 'collapsed': isSidebarCollapsed }"
      :chat-content="currentChatContent"
      @send-message="handleSendMessage"
    />
  </div>
</template>

<style scoped>
.smart-qa-container {
  display: flex;
  width: 100%;
  height: 100vh; /* 核心修复：强制占满视口高度 */
  overflow: hidden; /* 防止页面整体滚动 */
  background-color: #f5f5f5;
}

/* 如果 ChatWindow 需要适应侧边栏收缩，可以在这里加样式 */
/* 但通常 ChatWindow 内部应该自己处理 flex: 1 */
</style>