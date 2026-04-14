<script setup>
import { ref, computed, onMounted } from 'vue';
import Sidebar from '../components/Sidebar.vue';
import ChatWindow from '../components/ChatWindow.vue';
import api from '../api/index';

const user = JSON.parse(localStorage.getItem('user_info'));
const userId = user?.user_id;

const conversations = ref([]);
const currentSessionId = ref(null);
const chatCache = ref({});
const isAwaitingResponse = ref(false);

const loadConversations = async () => {
  try {
    const res = await api.getConversations(userId);
    const list = Array.isArray(res.data) ? res.data : (res.data?.data || []);
    conversations.value = list.map(item => ({
      id: item.session_id,
      // 优先使用 session_title，为空则使用 latest_question
      title: item.session_title 
        ? item.session_title 
        : (item.latest_question ? item.latest_question.substring(0, 20) : '新对话'),
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

const loadConversationDetail = async (sessionId) => {
  try {
    const res = await api.getConversationDetail(sessionId);
    const list = Array.isArray(res.data) ? res.data : (res.data?.data || []);
    chatCache.value[sessionId] = list.map(item => [
      { role: 'user', content: item.question || '' },
      { role: 'assistant', content: item.answer || '（无内容）' }
    ]).flat().filter(msg => msg.content);
  } catch (error) {
    console.error('加载对话详情失败:', error);
    chatCache.value[sessionId] = [{ role: 'assistant', content: '历史记录加载失败', error: true }];
  }
};

const updateConversationPreview = (sessionId, questionText) => {
  const index = conversations.value.findIndex(item => item.id === sessionId);
  const preview = {
    id: sessionId,
    title: questionText.substring(0, 20) || '新对话',
    time: new Date().toLocaleString(),
  };

  if (index === -1) {
    conversations.value.unshift(preview);
  } else {
    conversations.value.splice(index, 1);
    conversations.value.unshift(preview);
  }
};

const handleSendMessage = async (messageObj) => {
  const message = messageObj.content?.trim();
  const isHomework = messageObj.isHomework;
  if (!message || isAwaitingResponse.value) return;

  const sessionId = currentSessionId.value;
  if (!chatCache.value[sessionId]) {
    chatCache.value[sessionId] = [];
  }

  chatCache.value[sessionId].push({ role: 'user', content: message });
  chatCache.value[sessionId].push({
    role: 'assistant',
    content: '正在思考中…',
    thinking: true,
  });

  isAwaitingResponse.value = true;

  try {
    let res;
    if (isHomework) {
      res = await api.getHomeworkHelp(message);
    } else {
      res = await api.askQuestion(message, sessionId);
    }

    const returnedSessionId = res.data?.session_id;

    if (!currentSessionId.value && returnedSessionId) {
      currentSessionId.value = returnedSessionId;
      chatCache.value[returnedSessionId] = chatCache.value[sessionId];
      delete chatCache.value[sessionId];
    }

    const finalSessionId = currentSessionId.value ?? sessionId;
    const messages = chatCache.value[finalSessionId] || [];
    const answer = res.data?.answer || res.data?.result || '（无内容）';
    const thinkingIndex = messages.findIndex(msg => msg.thinking);

    if (thinkingIndex !== -1) {
      messages.splice(thinkingIndex, 1, {
        role: 'assistant',
        content: answer,
      });
    } else {
      messages.push({ role: 'assistant', content: answer });
    }

    if (finalSessionId) {
      updateConversationPreview(finalSessionId, message);
    }
  } catch (err) {
    console.error(err);
    const finalSessionId = currentSessionId.value ?? sessionId;
    const messages = chatCache.value[finalSessionId] || [];
    const thinkingIndex = messages.findIndex(msg => msg.thinking);
    const errorMessage = {
      role: 'assistant',
      content: `错误: ${err?.response?.data?.detail || err.message || '请求失败'}`,
      error: true,
    };

    if (thinkingIndex !== -1) {
      messages.splice(thinkingIndex, 1, errorMessage);
    } else {
      messages.push(errorMessage);
    }
  } finally {
    isAwaitingResponse.value = false;
  }
};

const handleNewChat = () => {
  currentSessionId.value = null;
  chatCache.value[null] = [];
};

const handleSelectChat = async (chatId) => {
  currentSessionId.value = chatId;
  if (!chatCache.value[chatId]?.length) {
    await loadConversationDetail(chatId);
  }
};

const handleSelectRecommend = (question) => {
  handleSendMessage({ content: question, isHomework: false });
};

const handleRenameChat = async (chatId, newTitle) => {
  try {
    
    const response = await api.renameConversation(chatId, newTitle);
    
    const conversation = conversations.value.find(item => item.id === chatId);
    if (conversation) {
      conversation.title = newTitle.trim() ? newTitle.trim() : conversation.title; 
    }
    
    console.log('重命名成功:', response.data.message);
  } catch (error) {
    console.error('重命名失败:', error);
  }
};

const handlePinChat = () => {};
const handleShareChat = () => {};
const handleDeleteChat = async (chatId) => {
  try {
    // 1. 调用后端API删除
    // 注意：根据后端代码，接口返回格式为 { message, session_id, deleted }
    const res = await api.deleteConversation(chatId); 
    
    console.log('删除响应:', res.data);

    // 2. 更新前端状态
    // 2.1 从侧边栏列表中移除
    const index = conversations.value.findIndex(item => item.id === chatId);
    if (index !== -1) {
      conversations.value.splice(index, 1);
    }

    // 2.2 处理缓存 (如果该会话在内存中)
    if (chatCache.value[chatId]) {
      delete chatCache.value[chatId];
    }

    // 2.3 特殊逻辑：如果删除的是当前正在查看的会话
    if (currentSessionId.value === chatId) {
      // 方案：跳转到新对话 或 切换到列表中的第一个会话
      if (conversations.value.length > 0) {
        // 切换到第一个会话
        currentSessionId.value = conversations.value[0].id;
        // 尝试加载其详情（如果缓存中没有）
        if (!chatCache.value[currentSessionId.value]?.length) {
          await loadConversationDetail(currentSessionId.value);
        }
      } else {
        // 列表为空，重置为新对话状态
        currentSessionId.value = null;
        chatCache.value[null] = [];
      }
    }

    alert('会话已删除');
    
  } catch (error) {
    // 处理错误 (例如网络问题或后端报错 404)
    const errorMsg = error.response?.data?.detail || error.message;
    console.error('删除失败:', errorMsg);
    alert(`删除失败: ${errorMsg}`);
  }
};


const currentChatContent = computed(() => chatCache.value[currentSessionId.value] || []);
const isSidebarCollapsed = ref(false);

onMounted(() => {
  loadConversations();
});
</script>

<template>
  <div class="smart-qa-container">
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

    <ChatWindow
      :class="{ collapsed: isSidebarCollapsed }"
      :chat-content="currentChatContent"
      :loading="isAwaitingResponse"
      @send-message="handleSendMessage"
    />
  </div>
</template>

<style scoped>
.smart-qa-container {
  display: flex;
  width: 100%;
  height: 100vh;
  overflow: hidden;
  background-color: #f5f5f5;
}
</style>
