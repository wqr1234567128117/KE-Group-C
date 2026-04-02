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
      <div class="welcome-screen">
        <h1>你好，我是助教AI</h1>

        <!-- 输入区域：包含输入框、发送按钮、作业辅导按钮 -->
        <div class="input-area">
          <input
            type="text"
            v-model="inputMessage"
            @keyup.enter="handleSend"
            placeholder="向助教AI提问"
          />

          <!-- 发送按钮 -->
          <button class="send-btn" @click="handleSend">发送</button>

          <!-- 新增：作业辅导切换按钮 -->
          <button
            class="homework-btn"
            :class="{ active: isHomeworkMode }"
            @click="toggleHomeworkMode"
          >
            {{ isHomeworkMode ? '普通模式' : '作业辅导' }}
          </button>
        </div>

        <div class="quick-actions">
          <span>任务助理</span>
          <span>深度思考</span>
          <span>深度研究</span>
          <span>代码</span>
          <span>图像</span>
          <span>更多</span>
        </div>
      </div>
    </section>

    <!-- 底部快捷功能 -->
    <footer class="chat-footer">
      <div class="footer-item">
        <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3z"></path>
          <path d="M19 10v2a7 7 0 0 1-14 0v-2"></path>
        </svg>
        <span>录音</span>
      </div>
      <div class="footer-item">
        <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M21.44 11.05l-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48"></path>
        </svg>
        <span>PPT</span>
      </div>
      <div class="footer-item">
        <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <polygon points="23 7 16 12 23 17 23 7"></polygon>
          <rect x="1" y="5" width="15" height="14" rx="2" ry="2"></rect>
        </svg>
        <span>音视频</span>
      </div>
      <div class="footer-item">
        <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
          <polyline points="14 2 14 8 20 8"></polyline>
        </svg>
        <span>文档</span>
      </div>
      <div class="footer-item">
        <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
          <line x1="9" y1="3" x2="9" y2="21"></line>
          <line x1="15" y1="3" x2="15" y2="21"></line>
          <line x1="3" y1="9" x2="21" y2="9"></line>
          <line x1="3" y1="15" x2="21" y2="15"></line>
        </svg>
        <span>发现</span>
      </div>
    </footer>
  </main>
</template>

<script setup>
import { ref } from 'vue';

// 定义 Props 和 Emits
const props = defineProps({
  isSidebarCollapsed: Boolean
});
const emit = defineEmits(['send-message', 'update:homework-mode']);

// 输入框内容
const inputMessage = ref('');

// 作业辅导模式状态 (默认 false)
const isHomeworkMode = ref(false);

// 切换作业辅导模式
const toggleHomeworkMode = () => {
  isHomeworkMode.value = !isHomeworkMode.value;
  // 向父组件通知模式变更
  emit('update:homework-mode', isHomeworkMode.value);
};

// 发送消息
const handleSend = () => {
  if (!inputMessage.value.trim()) return;

  // 发送消息事件，携带当前是否为作业辅导模式
  emit('send-message', {
    content: inputMessage.value,
    isHomework: isHomeworkMode.value
  });

  inputMessage.value = '';
};
</script>

<style scoped>
.chat-window {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: #fff;
  overflow: hidden;
}

/* --- 顶部和底部样式保持不变 --- */
.chat-header { /* ...原有样式... */ display: flex; justify-content: space-between; align-items: center; padding: 10px 20px; border-bottom: 1px solid #eee; background: #fff; }
.model-selector { display: flex; align-items: center; font-size: 14px; color: #333; cursor: pointer; }
.model-selector svg { margin-left: 4px; }
.header-right .btn { background: none; border: 1px solid #ddd; padding: 4px 8px; margin-left: 10px; font-size: 12px; color: #333; cursor: pointer; }
.theme-toggle { margin-left: 10px; cursor: pointer; }

.chat-content {
  flex: 1;
  display: flex;
  justify-content: center;
  align-items: center;
  flex-direction: column;
  background: radial-gradient(circle at center, #f9f9f9 0%, #eef0f3 100%);
  padding-bottom: 40px; /* 增加底部间距 */
}
.welcome-screen { text-align: center; color: #333; width: 100%; max-width: 700px; }
.welcome-screen h1 { font-size: 24px; font-weight: 500; margin-bottom: 30px; }
.quick-actions { display: flex; gap: 10px; margin-top: 20px; justify-content: center; flex-wrap: wrap; }
.quick-actions span { background: #fff; padding: 4px 8px; border-radius: 4px; font-size: 12px; color: #555; cursor: pointer; border: 1px solid #eee; }

.chat-footer { /* ...原有样式... */ display: flex; justify-content: center; gap: 30px; padding: 15px 0; border-top: 1px solid #eee; background: #fff; }
.footer-item { display: flex; flex-direction: column; align-items: center; color: #555; font-size: 12px; cursor: pointer; }
.footer-item:hover { color: #1677ff; }
.footer-item svg { margin-bottom: 4px; }

/* --- 修改后的输入区域样式 --- */
.input-area {
  display: flex;
  align-items: center;
  width: 600px; /* 稍微加宽以适应按钮 */
  max-width: 90%;
  height: 52px;
  background: #fff;
  border: 1px solid #e0e0e0; /* 灰色边框 */
  border-radius: 26px; /* 胶囊形状 */
  padding: 4px; /* 内部间距，让按钮和输入框分开 */
  box-shadow: 0 2px 10px rgba(0,0,0,0.05);
  transition: border-color 0.2s;
}

.input-area:focus-within {
  border-color: #1677ff; /* 聚焦时变蓝 */
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
  background: #1677ff; /* 蓝色背景 */
  color: white;
  border: none;
  border-radius: 22px; /* 按钮圆角 */
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  transition: background 0.2s;
}

.send-btn:hover {
  background: #0958d9;
}

/* 新增：作业辅导按钮样式 */
.homework-btn {
  height: 36px;
  padding: 0 16px;
  margin-left: 10px; /* 与发送按钮的间距 */
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

/* 激活状态样式 */
.homework-btn.active {
  background: #e6f4ff; /* 浅蓝背景 */
  border-color: #1677ff;
  color: #1677ff;
  font-weight: 500;
}
</style>