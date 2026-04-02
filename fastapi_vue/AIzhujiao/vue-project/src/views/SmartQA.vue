<script setup>
import { ref, computed } from 'vue';
import Sidebar from '../components/Sidebar.vue';
import ChatWindow from '../components/ChatWindow.vue';

// ---------- 虚拟对话数据 ----------
// 对话列表（模拟历史记录）
const chatHistory = ref([
  { id: 1, title: '方剂数据字段映射优化', time: '2023-10-27' },
  { id: 2, title: '修改中医知识库代码', time: '2023-10-26' },
  { id: 3, title: '针灸知识库分级授权与语义检索', time: '2023-10-25' },
]);

// 当前选中的对话ID（默认为第一个对话）
const currentChatId = ref(chatHistory.value[0]?.id || null);

// 对话内容映射（模拟每个对话的消息记录）
const chatContents = ref({
  1: [
    { role: 'assistant', content: '你好！关于“方剂数据字段映射优化”，请问需要我帮你分析哪些字段？' },
    { role: 'user', content: '帮我梳理一下“方剂名称”和“药材组成”的映射逻辑。' },
  ],
  2: [
    { role: 'assistant', content: '关于“中医知识库代码修改”，请提供具体需求或代码片段，我会帮你分析。' },
  ],
  3: [
    { role: 'assistant', content: '“针灸知识库分级授权与语义检索”的需求已收到，需要我帮你设计权限模型吗？' },
  ],
});

// 当前对话的内容（根据 currentChatId 动态获取）
const currentChatContent = computed(() => {
  return chatContents.value[currentChatId.value] || [];
});

// 侧边栏折叠状态
const isSidebarCollapsed = ref(false);

// ---------- 事件处理 ----------
// 新建对话
const handleNewChat = () => {
  const newId = Date.now(); // 用时间戳生成唯一ID
  chatHistory.value.unshift({
    id: newId,
    title: `新对话 ${chatHistory.value.length + 1}`,
    time: new Date().toLocaleDateString(),
  });
  currentChatId.value = newId;
  // 新对话默认无内容
  chatContents.value[newId] = [];
};

// 切换对话
const handleSelectChat = (id) => {
  currentChatId.value = id;
};

// 发送消息（模拟对话更新）
const handleSendMessage = (message) => {
  if (!currentChatId.value) return;
  // 向当前对话的消息列表中添加新消息
  chatContents.value[currentChatId.value].push({
    role: 'user',
    content: message,
  });
  // 模拟AI回复（实际场景可替换为接口调用）
  setTimeout(() => {
    chatContents.value[currentChatId.value].push({
      role: 'assistant',
      content: `这是对“${message}”的回复（模拟AI响应）`,
    });
  }, 1000);
};

// 重命名对话
const handleRenameChat = (id) => {
  const newName = prompt('请输入新的对话标题:');
  if (newName) {
    const chat = chatHistory.value.find(c => c.id === id);
    if (chat) {
      chat.title = newName;
    }
  }
};

// 置顶对话
const handlePinChat = (id) => {
  const index = chatHistory.value.findIndex(c => c.id === id);
  if (index > -1) {
    // 从当前位置移除并添加到数组开头
    const [pinnedChat] = chatHistory.value.splice(index, 1);
    chatHistory.value.unshift(pinnedChat);
  }
};

// 分享对话（模拟）
const handleShareChat = (id) => {
  alert(`正在生成对话 ${id} 的分享链接...`);
};

// 删除对话
const handleDeleteChat = (id) => {
  if (confirm('确定要删除这个对话吗？')) {
    // 从历史列表中移除
    chatHistory.value = chatHistory.value.filter(c => c.id !== id);
    // 从内容映射中移除
    delete chatContents.value[id];

    // 如果删除的是当前选中的对话，切换到剩下的第一个对话或null
    if (currentChatId.value === id) {
      currentChatId.value = chatHistory.value[0]?.id || null;
    }
  }
};
</script>

<template>
  <div class="smart-qa-container">
    <!-- 修改点：
         1. 去掉标签末尾的 '/'
         2. 添加缺失的事件绑定
         3. 在标签后显式添加 </Sidebar> 闭合标签
    -->
    <Sidebar
      :history="chatHistory"
      :current-chat-id="currentChatId"
      @new-chat="handleNewChat"
      @select-chat="handleSelectChat"
      @rename-chat="handleRenameChat"
      @pin-chat="handlePinChat"
      @share-chat="handleShareChat"
      @delete-chat="handleDeleteChat"
      @select-recommend="handleSelectRecommend"
      v-model:collapsed="isSidebarCollapsed"
    ></Sidebar>

    <ChatWindow
      :class="{'main-content-collapsed': isSidebarCollapsed}"
      :chat-content="currentChatContent"
      @send-message="handleSendMessage"
    />
  </div>
</template>

<style scoped>
.smart-qa-container {
  display: flex;
  height: 100vh;
  background-color: #f5f5f5;
}
</style>