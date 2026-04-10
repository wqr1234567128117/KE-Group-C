<script setup>
import { ref, watch, nextTick } from 'vue';

// --- Props 接收 (如果父组件传递历史记录) ---
const props = defineProps({
  chatContent: {
    type: Array,
    default: () => []
  }
});

// --- 状态管理 ---
// 注意：为了防止混淆，我们统一使用 inputMessage
const inputMessage = ref('');
const isSending = ref(false);
const isHomeworkMode = ref(false);
const bottomAnchor = ref(null);

// --- 事件定义 ---
// 定义向父组件发送消息的事件
const emit = defineEmits(['send-message']);

// --- 方法 ---

// 切换作业模式
const toggleHomeworkMode = () => {
  isHomeworkMode.value = !isHomeworkMode.value;
};

// 发送消息处理
const handleSend = async () => {
  // 1. 获取输入框内容并校验
  // 注意：这里修正了变量名，统一使用 inputMessage
  const text = inputMessage.value.trim(); 
  if (!text || isSending.value) return;

  // 2. 重置发送状态
  isSending.value = true;

  try {
    // 3. 调用父组件逻辑 (发送用户消息)
    // 这里将内容和模式传给父组件处理
    await emit('send-message', { 
      content: text, 
      isHomework: isHomeworkMode.value 
    });

    // 4. 清空输入框，准备下一次输入
    inputMessage.value = '';
    
  } catch (error) {
    console.error('消息发送失败:', error);
    // 这里可以添加 UI 提示，但通常在父组件处理错误
  } finally {
    isSending.value = false;
  }
};

// --- 自动滚动 ---
// 监听 DOM 变化，自动滚动到底部
watch(() => props.chatContent, async () => {
  await nextTick();
  if (bottomAnchor.value) {
    bottomAnchor.value.scrollIntoView({ behavior: 'smooth' });
  }
}, { immediate: true });
</script>

<template>
  <main class="chat-window">
    <!-- 顶部导航栏 -->
    <header class="chat-header">
      <div class="header-left">
        <div class="model-selector">
          <span>智能助教问答</span>
          <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <polyline points="6 9 12 15 18 9"></polyline>
          </svg>
        </div>
      </div>
      <div class="header-right">
        <button class="btn">下载电脑版</button>
        <button class="btn">API 服务</button>
        <div class="theme-toggle">🌙</div>
      </div>
    </header>

    <!-- 聊天内容区 -->
    <section class="chat-content">
      <!-- 欢迎页或聊天记录列表 -->
      <!-- 注意：这里使用 v-if 判断 props.chatContent，确保父子数据同步 -->
      <div v-if="props.chatContent.length === 0" class="welcome-screen">
        <h1>你好，我是助教AI</h1>
        
        <!-- 输入区域 (欢迎页专用) -->
        
        
        <div class="quick-actions">
          <span>任务助理</span>
          <span>深度思考</span>
          <span>深度研究</span>
          <span>代码</span>
          <span>图像</span>
          <span>更多</span>
        </div>
      </div>

      <!-- 消息列表 -->
      <!-- 这里渲染父组件传入的 chatContent -->
      <div class="messages-list">
        <div 
          v-for="(msg, index) in props.chatContent" 
          :key="index" 
          class="message-item" 
          :class="[msg.role, { 'message-error': msg.error }]"
        >
          <!-- 头像 -->
          <div class="avatar">
            {{ msg.role === 'user' ? '👤' : '🤖' }}
          </div>

          <!-- 内容盒子 -->
          <div class="content-box">
            <div class="content" v-text="msg.content"></div>
            <!-- 错误提示 -->
            <div class="error-tip" v-if="msg.error">
              ❌ {{ msg.content }}
            </div>
          </div>
        </div>
        
        <!-- 滚动锚点 -->
        <div ref="bottomAnchor"></div>
      </div>
    </section>

    <!-- 底部快捷功能 -->
    <footer class="chat-footer">
      <div class="input-area">
          <input 
            type="text" 
            v-model="inputMessage" 
            @keyup.enter="handleSend" 
            placeholder="向助教AI提问" 
            :disabled="isSending" 
          />
          <button 
            class="send-btn" 
            @click="handleSend" 
            :disabled="isSending || !inputMessage.trim()"
          >
            {{ isSending ? '发送中...' : '发送' }}
          </button>
          <button 
            class="homework-btn" 
            :class="{ active: isHomeworkMode }" 
            @click="toggleHomeworkMode"
          >
            {{ isHomeworkMode ? '普通模式' : '作业辅导' }}
          </button>
      </div>
      
    </footer>
  </main>
</template>

<style scoped>
/* --- 样式保持不变 (为了节省篇幅，这里省略样式部分，使用你原有的样式即可) --- */
/* 你的原有样式已经很完善，无需修改，请保留原样 */
.chat-window {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: #fff;
  overflow: hidden; /* 确保内部溢出被隐藏 */
  height: 100%; 
  width: 100%;
}

.chat-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 20px;
  border-bottom: 1px solid #eee;
  background: #fff;
  flex-shrink: 0; /* 防止头部被压缩 */
}

.model-selector {
  display: flex;
  align-items: center;
  font-size: 14px;
  color: #333;
  cursor: pointer;
}

.model-selector svg {
  margin-left: 4px;
}

.header-right .btn {
  background: none;
  border: 1px solid #ddd;
  padding: 4px 8px;
  margin-left: 10px;
  font-size: 12px;
  color: #333;
  cursor: pointer;
}

.theme-toggle {
  margin-left: 10px;
  cursor: pointer;
}

.chat-content {
  flex: 1;
  overflow-y: auto;
  padding: 20px 0;
}

.welcome-screen {
  text-align: center;
  color: #333;
  width: 100%;
  max-width: 700px;
  margin: 0 auto;
}

.welcome-screen h1 {
  font-size: 24px;
  font-weight: 500;
  margin-bottom: 30px;
}

.quick-actions {
  display: flex;
  gap: 10px;
  margin-top: 20px;
  justify-content: center;
  flex-wrap: wrap;
}

.quick-actions span {
  background: #fff;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  color: #555;
  cursor: pointer;
  border: 1px solid #eee;
}

/* --- 消息列表样式 --- */
.messages-list {
  padding: 0 20px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  flex: 1;
  overflow-y: auto;
}

.message-item {
  display: flex;
  gap: 12px;
  padding: 0 10px;
  align-items: flex-start;
}

.message-item.user {
  flex-direction: row-reverse;
}

.message-item.user .avatar {
  order: 2;
}

.message-item.user .content-box {
  background: #e6f4ff;
  border-radius: 12px;
  padding: 12px 16px;
  max-width: 80%;
  align-self: flex-end;
}

.message-item.assistant .content-box {
  background: #f5f5f5;
  border-radius: 12px;
  padding: 12px 16px;
  max-width: 80%;
  align-self: flex-start;
}

.avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  flex-shrink: 0;
}

.content-box {
  color: #333;
  line-height: 1.5;
  font-size: 14px;
  position: relative;
}

.error-tip {
  color: #ff4d4f;
  font-size: 12px;
  margin-top: 4px;
}

/* --- 输入区域样式 --- */
.input-area {
  display: flex;
  align-items: center;
  width: 600px;
  max-width: 90%;
  height: 52px;
  background: #fff;
  border: 1px solid #e0e0e0;
  border-radius: 26px;
  padding: 4px;
  box-shadow: 0 2px 10px rgba(0,0,0,0.05);
  margin: 0 auto 20px;
}

.input-area:focus-within {
  border-color: #1677ff;
}

.input-area input {
  flex: 1;
  border: none;
  outline: none;
  padding: 0 20px;
  font-size: 15px;
  height: 100%;
  background: transparent;
}

.send-btn {
  width: 80px;
  height: 44px;
  background: #1677ff;
  color: white;
  border: none;
  border-radius: 22px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  transition: background 0.2s;
}

.send-btn:hover:not(:disabled) {
  background: #0958d9;
}

.send-btn:disabled {
  background: #ccc;
  cursor: not-allowed;
}

/* 新增：作业辅导按钮样式 */
.homework-btn {
  height: 36px;
  padding: 0 16px;
  margin-left: 10px;
  background: transparent;
  border: 1px solid #d9d9d9;
  color: #595959;
  border-radius: 18px;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
  white-space: nowrap;
}

.homework-btn:hover {
  border-color: #1677ff;
  color: #1677ff;
}

.homework-btn.active {
  background: #e6f4ff;
  border-color: #1677ff;
  color: #1677ff;
  font-weight: 500;
}

.chat-footer {
  display: flex;
  justify-content: center;
  gap: 30px;
  padding: 15px 0;
  border-top: 1px solid #eee;
  background: #fff;
}

.footer-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  color: #555;
  font-size: 12px;
  cursor: pointer;
}

.footer-item:hover {
  color: #1677ff;
}

.footer-item svg {
  margin-bottom: 4px;
}
</style>