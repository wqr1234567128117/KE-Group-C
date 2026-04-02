<template>
  <div :class="['sidebar-container', { 'collapsed': isCollapsed }]">
    <!-- 折叠按钮 -->
    <div class="toggle-btn" @click="toggleCollapse">
      <Icon :icon="isCollapsed ? 'ph:arrow-right-bold' : 'ph:arrow-left-bold'" />
    </div>

    <!-- 新对话按钮 -->
    <div class="new-chat-btn" @click="handleNewChat">
      <Icon icon="ph:plus-bold" />
      <span v-if="!isCollapsed">新对话</span>
    </div>

    <!-- 滚动区域 -->
    <div class="scroll-area" v-if="!isCollapsed">
      <!-- 1. 最近对话 (原有逻辑) -->
      <div class="section">
        <div class="group-title">最近对话</div>
        <div
          v-for="item in history"
          :key="item.id"
          class="history-item"
          :class="{ 'active': item.id === currentChatId }"
          @click="handleSelectChat(item.id)"
        >
          <Icon icon="ph:chat-bold" />
          <span class="item-title">{{ item.title }}</span>
          <span class="item-time">{{ item.time }}</span>

          <!-- 只有在未折叠状态下，且鼠标悬停或菜单激活时显示操作按钮 -->
          <div
            v-if="!isCollapsed"
            class="action-btn"
            @click.stop="toggleMenu(item.id, $event)"
          >
            <Icon icon="ph:dots-three-bold" />
          </div>
        </div>
      </div>

      <!-- 2. 热门问题 (新增) -->
      <div class="section hot-questions-section">
        <div class="group-title">🔥 热门问题</div>
        <div
          v-for="(item, index) in hotQuestions"
          :key="'hot-' + index"
          class="recommend-item"
          @click="handleSelectRecommend(item.question)"
        >
          <span class="item-text">{{ item.question }}</span>
          <span class="item-count">{{ item.count }}</span>
        </div>
      </div>

      <!-- 3. 推荐问题 (新增) -->
      <div class="section recommended-section">
        <div class="group-title">💡 推荐问题</div>
        <div
          v-for="(q, index) in recommendedQuestions"
          :key="'rec-' + index"
          class="recommend-item"
          @click="handleSelectRecommend(q)"
        >
          <span class="item-text">{{ q }}</span>
        </div>
      </div>
    </div>

    <!-- 全局菜单弹窗 (保持原有逻辑) -->
    <div
      v-if="activeMenuId !== null"
      class="context-menu"
      :style="menuStyle"
      @click.stop
    >
      <div class="menu-item" @click="handleRename">
        <Icon icon="ph:pencil-bold" />
        <span>重命名</span>
      </div>
      <div class="menu-item" @click="handlePin">
        <Icon icon="ph:push-pin-bold" />
        <span>置顶</span>
      </div>
      <div class="menu-item" @click="handleShare">
        <Icon icon="ph:share-fat" />
        <span>分享</span>
      </div>
      <div class="menu-item danger" @click="handleDelete">
        <Icon icon="ph:trash-bold" />
        <span>删除</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { defineProps, defineEmits, ref, onMounted } from 'vue';
import { Icon } from '@iconify/vue';
// 假设你有 axios，如果没有可以使用 fetch 或你项目中的 request 实例
import axios from 'axios';

// ---------- Props & Emits ----------
const props = defineProps({
  history: { type: Array, required: true },
  currentChatId: { type: Number, required: true },
  modelValue: { type: Boolean, default: false },
});

const emit = defineEmits(['update:modelValue', 'new-chat', 'select-chat', 'rename-chat', 'pin-chat', 'share-chat', 'delete-chat', 'select-recommend']);

// ---------- 状态 ----------
const isCollapsed = ref(props.modelValue);
const activeMenuId = ref(null);
const menuStyle = ref({ top: '0px', left: '0px' });

// 新增状态：热门与推荐数据
const hotQuestions = ref([]);
const recommendedQuestions = ref([]);

// ---------- 生命周期 ----------
onMounted(() => {
  // 组件挂载后获取侧边栏数据
  fetchSidebarData();
  document.addEventListener('click', handleOutsideClick);
});

// ---------- 方法 ----------

// 1. 获取侧边栏数据 (热门/推荐)
const fetchSidebarData = async () => {
  try {
    // 模拟后端调用，请替换为真实的 API
    // const hotRes = await axios.get('/api/hot-questions');
    // const recRes = await axios.get('/api/recommended-questions');

    // 这里使用模拟数据演示
    hotQuestions.value = [
      { question: '方剂数据字段如何映射？', count: '1.2k' },
      { question: '中医知识库代码修改建议', count: '856' },
      { question: '针灸分级授权模型设计', count: '430' }
    ];

    recommendedQuestions.value = [
      '帮我梳理一下药材组成的映射逻辑',
      '设计一个权限模型',
      '分析这段代码的潜在Bug'
    ];

  } catch (error) {
    console.error('获取侧边栏数据失败:', error);
  }
};

const toggleCollapse = () => {
  isCollapsed.value = !isCollapsed.value;
  emit('update:modelValue', isCollapsed.value);
};

const handleNewChat = () => {
  emit('new-chat');
  closeMenu();
};

const handleSelectChat = (id) => {
  emit('select-chat', id);
  closeMenu();
};

// 2. 处理点击推荐/热门问题
const handleSelectRecommend = (questionText) => {
  // 向父组件发送事件，告知用户选择了一个推荐问题
  emit('select-recommend', questionText);
};

const toggleMenu = (id, event) => {
  if (activeMenuId.value === id) {
    closeMenu();
  } else {
    activeMenuId.value = id;
    const rect = event.currentTarget.getBoundingClientRect();
    menuStyle.value = {
      top: `${rect.top}px`,
      left: `${rect.right + 5}px`,
    };
  }
};

const closeMenu = () => {
  activeMenuId.value = null;
};

const handleRename = () => {
  emit('rename-chat', activeMenuId.value);
  closeMenu();
};

const handlePin = () => {
  emit('pin-chat', activeMenuId.value);
  closeMenu();
};

const handleShare = () => {
  emit('share-chat', activeMenuId.value);
  closeMenu();
};

const handleDelete = () => {
  emit('delete-chat', activeMenuId.value);
  closeMenu();
};

const handleOutsideClick = () => {
  if (activeMenuId.value !== null) {
    closeMenu();
  }
};
</script>

<style scoped>
.sidebar-container {
  width: 280px; /* 稍微加宽以适应新内容 */
  background-color: #202123;
  color: #fff;
  display: flex;
  flex-direction: column;
  transition: width 0.3s ease;
  overflow: hidden;
  position: relative;
}

.sidebar-container.collapsed {
  width: 60px;
}

.toggle-btn {
  padding: 12px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
}

.new-chat-btn {
  padding: 10px 16px;
  margin: 0 8px 12px;
  background-color: #343541;
  border-radius: 8px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  transition: background-color 0.2s;
}

.new-chat-btn:hover {
  background-color: #40414f;
}

/* 滚动区域 */
.scroll-area {
  flex: 1;
  overflow-y: auto;
  padding-bottom: 20px;
}

.section {
  margin-bottom: 20px;
}

.group-title {
  padding: 8px 16px;
  font-size: 12px;
  color: #8a8b8f;
  text-transform: uppercase;
  font-weight: 600;
}

/* 历史记录样式 */
.history-item {
  padding: 10px 16px;
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  border-radius: 0 8px 8px 0;
  margin-right: 8px;
  font-size: 14px;
  position: relative;
}

.history-item:hover, .history-item.active {
  background-color: #343541;
}

.item-title {
  flex: 1;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.item-time {
  font-size: 12px;
  color: #8a8b8f;
  margin-left: 8px;
}

/* 推荐/热门项样式 */
.recommend-item {
  padding: 8px 16px;
  font-size: 13px;
  color: #d1d5db;
  cursor: pointer;
  display: flex;
  justify-content: space-between;
  align-items: center;
  transition: background 0.2s;
}

.recommend-item:hover {
  background-color: #2A2B32;
  color: #fff;
}

.item-count {
  font-size: 11px;
  color: #555;
  background: #2A2B32;
  padding: 2px 6px;
  border-radius: 4px;
}

/* 操作按钮 */
.action-btn {
  margin-left: auto;
  padding: 4px;
  border-radius: 4px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #8a8b8f;
}

.action-btn:hover {
  background-color: #50515c;
  color: #fff;
}

/* 菜单样式保持不变 */
.context-menu {
  position: fixed;
  width: 160px;
  background-color: #202123;
  border: 1px solid #50515c;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.5);
  z-index: 1000;
  display: flex;
  flex-direction: column;
  padding: 4px;
}

.menu-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 12px;
  font-size: 14px;
  color: #fff;
  cursor: pointer;
  border-radius: 4px;
}

.menu-item:hover {
  background-color: #343541;
}

.menu-item.danger {
  color: #ff6b6b;
}

.menu-item.danger:hover {
  background-color: rgba(255, 107, 107, 0.1);
}

/* 隐藏滚动条 */
.scroll-area::-webkit-scrollbar {
  display: none;
}
</style>