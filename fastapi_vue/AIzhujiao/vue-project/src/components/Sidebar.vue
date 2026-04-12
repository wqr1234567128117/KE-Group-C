<!-- vue-project/src/components/Sidebar.vue -->
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
      <!-- 1. 最近对话 (由父组件通过 props 传入) -->
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

          <!-- 操作按钮 -->
          <div
            v-if="!isCollapsed"
            class="action-btn"
            @click.stop="toggleMenu(item.id, $event)"
          >
            <Icon icon="ph:dots-three-bold" />
          </div>
        </div>
      </div>

      <!-- 2. 热门问题 (API 获取) -->
      <div class="section hot-questions-section">
        <div class="group-title">🔥 热门问题</div>
        <div
          v-for="(item, index) in hotQuestions"
          :key="'hot-' + index"
          class="recommend-item"
          @click="handleSelectRecommend(item.question_content)"
        >
          <span class="item-text">{{ item.question_content }}</span>
          <span class="item-count">{{ item.click_count }}</span>
        </div>
      </div>

      <!-- 3. 推荐问题 (API 获取) -->
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

    <!-- 全局菜单弹窗 -->
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
    <!-- ✅ 修改 5: 新增：内联重命名输入框 (直接放在 body 后面，利用 fixed 定位) -->
    <div 
      v-if="isRenamingInline" 
      class="inline-rename-input" 
      :class="{ 'force-float': isRenamingInline }"
      :style="menuStyle" 
      @click.stop
    >
      <ElInput
        ref="renameInputRef"
        v-model="renameInputValue"
        size="small"
        @keyup.enter="confirmRenameInline"
        @blur="cancelRenameInline" 
      />
      <!-- 可选：添加确定/取消按钮，或者只靠回车/失焦 -->
      <!-- <ElButton size="small" @click="confirmRenameInline">确定</ElButton> -->
    </div>
  </div>
</template>

<script setup>
import { defineProps, defineEmits, ref, nextTick, onMounted } from 'vue';
import { Icon } from '@iconify/vue';
import api from '../api/index'; // 引入统一封装的 API
import { ElDialog, ElInput, ElButton } from 'element-plus'


// ---------- Props & Emits ----------
const props = defineProps({
  history: { type: Array, required: true },
  currentChatId: { type: [String, Number], required: true }, // 兼容 String 类型的 ID
  modelValue: { type: Boolean, default: false },
});

const emit = defineEmits(['update:modelValue', 'new-chat', 'select-chat', 'rename-chat', 'pin-chat', 'share-chat', 'delete-chat', 'select-recommend']);

// ---------- 状态 ----------
const isCollapsed = ref(props.modelValue);
const activeMenuId = ref(null);
const menuStyle = ref({ top: '0px', left: '0px' });

// 数据状态
const hotQuestions = ref([]);
const recommendedQuestions = ref([]);

// --- 新增：重命名相关的状态 ---
const isRenamingInline = ref(false); // 标记是否正在内联编辑
const renameInputValue = ref('');
const renamingTargetId = ref(null);

// ---------- 生命周期 ----------
onMounted(() => {
  fetchSidebarData();
  document.addEventListener('click', handleOutsideClick);
});

// ---------- 方法 ----------

// 1. 获取侧边栏数据
const fetchSidebarData = async () => {
  try {
    // 并行请求两个接口
    const [hotRes, recRes] = await Promise.all([
      api.getHotQuestions(),
      api.getSuggestions()
    ]);

    // 映射热门问题
    // 假设后端返回结构: [{question_content: "...", click_count: 100}, ...]
    // hotQuestions.value = hotRes.data; 
    hotQuestions.value = hotRes.data.map(item => ({
      question_content: item.question || '暂无问题',
      click_count: item.count || 0
    }));

    // 映射推荐问题
    // 假设后端返回结构: ["问题A", "问题B", ...]
    recommendedQuestions.value = recRes.data;

  } catch (error) {
    console.error('获取侧边栏数据失败:', error);
    // 可以在这里设置默认值，防止界面空白
    hotQuestions.value = [];
    recommendedQuestions.value = [];
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

const handleRename = async () => {
  const targetId = activeMenuId.value;
  if (!targetId) return;

  // 1. 找到当前标题
  const targetItem = props.history.find(item => item.id === targetId);
  const currentTitle = targetItem ? targetItem.title || targetItem.session_title : '';
  
  // 2. 初始化内联编辑状态
  renameInputValue.value = currentTitle;
  renamingTargetId.value = targetId;
  isRenamingInline.value = true; // 显示输入框

  // 3. 关闭原来的右键菜单，因为我们现在要在旁边显示输入框
  activeMenuId.value = null;

  // 4. 等待 DOM 更新，聚焦输入框
  await nextTick();
  if (renameInputRef.value) {
    renameInputRef.value.focus();
  }
};

// --- 修改 3: 新增 confirmRenameInline ---
const confirmRenameInline = () => {
  // if (renamingTargetId.value) {
  //   emit('rename-chat', renamingTargetId.value, renameInputValue.value);
  // }
  if (renamingTargetId.value && renameInputValue.value.trim()) {
    emit('rename-chat', renamingTargetId.value, renameInputValue.value.trim());
  }
  // 重置状态
  isRenamingInline.value = false;
  renamingTargetId.value = null;
};

// --- 修改 4: 新增 cancelRenameInline ---
const cancelRenameInline = () => {
  isRenamingInline.value = false;
  renamingTargetId.value = null;
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
/* 样式保持不变，仅做微调以适配新内容 */
.sidebar-container {
  width: 280px;
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

.scroll-area::-webkit-scrollbar {
  display: none;
}
.inline-rename-input {
  position: absolute;
  z-index: 9999; /* 修改点：大幅提升层级，确保盖住右侧组件 */
  
  /* 其他原有样式保持不变 */
  background-color: #1f1f1f;
  border: 1px solid #444;
  border-radius: 8px;
  padding: 6px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.5);
  width: 200px;
}


.inline-rename-input.force-float {
  position: fixed !important; 
  z-index: 99999 !important;  
  
  /* 视觉美化 */
  background-color: #1f1f1f;
  border: 1px solid #444;
  border-radius: 8px;
  padding: 6px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.8); 
  width: auto;
  
}

/* 穿透修改 Element Plus 样式，确保输入框透明 */
.inline-rename-input ::v-deep(.el-input__wrapper) {
  background-color: transparent !important;
  box-shadow: none !important;
  border: none;
  padding: 0;
}

/* 文字颜色白色 */
.inline-rename-input ::v-deep(input) {
  color: #000000;
}
</style>