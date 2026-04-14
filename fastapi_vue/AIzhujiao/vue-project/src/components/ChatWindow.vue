<script setup>
import { ref, watch, nextTick } from 'vue';
import { useRouter } from 'vue-router';

const props = defineProps({
  chatContent: {
    type: Array,
    default: () => []
  },
  loading: {
    type: Boolean,
    default: false,
  }
});

const router = useRouter();
const inputMessage = ref('');
const isHomeworkMode = ref(false);
const bottomAnchor = ref(null);
const currentPage = ref('qa');

const emit = defineEmits(['send-message']);

// const toggleHomeworkMode = () => {
//   isHomeworkMode.value = !isHomeworkMode.value;
// };
const toggleHomeworkMode = () => {
  router.push('/person-learning-path');
};

const handleSend = () => {
  const text = inputMessage.value.trim();
  if (!text || props.loading) return;

  emit('send-message', {
    content: text,
    isHomework: isHomeworkMode.value,
  });

  inputMessage.value = '';
};

const handlePageChange = () => {
  if (currentPage.value === 'learning-path') {
    router.push('/learning-path');
    return;
  }
  router.push('/smart-qa');
};

watch(() => props.chatContent.length, async () => {
  await nextTick();
  if (bottomAnchor.value) {
    bottomAnchor.value.scrollIntoView({ behavior: 'smooth', block: 'end' });
  }
}, { immediate: true });
</script>

<template>
  <main class="chat-window">
    <header class="chat-header">
      <div class="header-left">
        <label class="page-selector-wrap">
          <select v-model="currentPage" class="page-selector" @change="handlePageChange">
            <option value="qa">智能助教问答</option>
            <option value="learning-path">学习路径生成</option>
          </select>
        </label>
      </div>
    </header>

    <section class="chat-content">
      <div v-if="props.chatContent.length === 0" class="welcome-screen">
        <h1>你好，我是助教AI</h1>
        <p class="welcome-tip">输入问题后，我会先显示“正在思考中”，再返回正式回答。</p>

        <div class="quick-actions">
          <span>任务助理</span>
          <span>深度思考</span>
          <span>深度研究</span>
          <span>代码</span>
          <span>图像</span>
          <span>更多</span>
        </div>
      </div>

      <div class="messages-list" v-else>
        <div
          v-for="(msg, index) in props.chatContent"
          :key="index"
          class="message-item"
          :class="[msg.role, { 'message-error': msg.error, 'message-thinking': msg.thinking }]"
        >
          <div class="avatar">
            {{ msg.role === 'user' ? '👤' : '🤖' }}
          </div>

          <div class="content-box">
            <template v-if="msg.thinking">
              <div class="thinking-content">
                <span class="thinking-text">正在思考中</span>
                <span class="thinking-dots">
                  <i></i><i></i><i></i>
                </span>
              </div>
            </template>
            <div v-else class="content" v-text="msg.content"></div>
            <div class="error-tip" v-if="msg.error">
              ❌ {{ msg.content }}
            </div>
          </div>
        </div>

        <div ref="bottomAnchor"></div>
      </div>
    </section>

    <footer class="chat-footer">
      <div class="input-area">
        <input
          type="text"
          v-model="inputMessage"
          @keyup.enter="handleSend"
          placeholder="向助教AI提问"
          :disabled="props.loading"
        />
        <button
          class="send-btn"
          @click="handleSend"
          :disabled="props.loading || !inputMessage.trim()"
        >
          {{ props.loading ? '思考中...' : '发送' }}
        </button>
        <button
          class="homework-btn"
          :class="{ active: isHomeworkMode }"
          @click="toggleHomeworkMode"
          :disabled="props.loading"
        >
          {{ isHomeworkMode ? '普通模式' : '作业辅导' }}
        </button>
      </div>
    </footer>
  </main>
</template>

<style scoped>
.chat-window {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: #fff;
  overflow: hidden;
  height: 100%;
  width: 100%;
}

.chat-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 20px;
  border-bottom: 1px solid #eee;
  background: #fff;
  flex-shrink: 0;
}

.header-left {
  display: flex;
  align-items: center;
}

.page-selector-wrap {
  position: relative;
}

.page-selector {
  appearance: none;
  min-width: 168px;
  height: 38px;
  padding: 0 36px 0 14px;
  border: 1px solid #d9d9d9;
  border-radius: 10px;
  background: linear-gradient(135deg, #ffffff 0%, #f8f5ff 100%);
  color: #333;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  outline: none;
}

.page-selector-wrap::after {
  content: '⌄';
  position: absolute;
  right: 12px;
  top: 50%;
  transform: translateY(-52%);
  color: #6f42c1;
  pointer-events: none;
  font-size: 16px;
}

.chat-content {
  flex: 1;
  overflow-y: auto;
  padding: 20px 0;
  background: linear-gradient(180deg, #fafafa 0%, #ffffff 100%);
}

.welcome-screen {
  text-align: center;
  color: #333;
  width: 100%;
  max-width: 700px;
  margin: 0 auto;
  padding: 24px 20px;
}

.welcome-screen h1 {
  font-size: 28px;
  font-weight: 600;
  margin-bottom: 12px;
}

.welcome-tip {
  color: #666;
  font-size: 14px;
  margin-bottom: 28px;
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
  padding: 8px 12px;
  border-radius: 999px;
  font-size: 12px;
  color: #555;
  cursor: pointer;
  border: 1px solid #eee;
}

.messages-list {
  padding: 0 20px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  flex: 1;
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
  border-radius: 14px;
  padding: 12px 16px;
  max-width: min(80%, 760px);
  align-self: flex-end;
}

.message-item.assistant .content-box {
  background: #f5f5f5;
  border-radius: 14px;
  padding: 12px 16px;
  max-width: min(80%, 760px);
  align-self: flex-start;
}

.message-item.message-thinking .content-box {
  background: #f7f3ff;
  border: 1px solid #ebe2ff;
}

.avatar {
  width: 34px;
  height: 34px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  flex-shrink: 0;
  background: #fff;
  box-shadow: 0 2px 8px rgba(0,0,0,0.06);
}

.content-box {
  color: #333;
  line-height: 1.7;
  font-size: 14px;
  position: relative;
  box-shadow: 0 4px 14px rgba(0,0,0,0.04);
}

.content {
  white-space: pre-wrap;
  word-break: break-word;
}

.thinking-content {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  color: #6f42c1;
  font-weight: 500;
}

.thinking-dots {
  display: inline-flex;
  gap: 4px;
}

.thinking-dots i {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #6f42c1;
  display: block;
  animation: dotPulse 1.2s infinite ease-in-out;
}

.thinking-dots i:nth-child(2) {
  animation-delay: 0.2s;
}

.thinking-dots i:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes dotPulse {
  0%, 80%, 100% {
    transform: scale(0.7);
    opacity: 0.5;
  }
  40% {
    transform: scale(1);
    opacity: 1;
  }
}

.error-tip {
  color: #ff4d4f;
  font-size: 12px;
  margin-top: 4px;
}

.input-area {
  display: flex;
  align-items: center;
  width: 720px;
  max-width: calc(100% - 32px);
  min-height: 56px;
  background: #fff;
  border: 1px solid #e0e0e0;
  border-radius: 28px;
  padding: 6px;
  box-shadow: 0 2px 10px rgba(0,0,0,0.05);
  margin: 0 auto 16px;
}

.input-area:focus-within {
  border-color: #6f42c1;
  box-shadow: 0 4px 16px rgba(111, 66, 193, 0.12);
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
  width: 90px;
  height: 44px;
  background: linear-gradient(135deg, #7c4dff 0%, #6f42c1 100%);
  color: white;
  border: none;
  border-radius: 22px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 600;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.send-btn:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 6px 16px rgba(111, 66, 193, 0.22);
}

.send-btn:disabled {
  background: #ccc;
  cursor: not-allowed;
  box-shadow: none;
}

.homework-btn {
  height: 38px;
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

.homework-btn:hover:not(:disabled) {
  border-color: #6f42c1;
  color: #6f42c1;
}

.homework-btn.active {
  background: #f3ecff;
  border-color: #6f42c1;
  color: #6f42c1;
  font-weight: 600;
}

.homework-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.chat-footer {
  display: flex;
  justify-content: center;
  padding: 15px 0;
  border-top: 1px solid #eee;
  background: #fff;
  flex-shrink: 0;
}
</style>
