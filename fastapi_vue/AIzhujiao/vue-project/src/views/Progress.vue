<template>
  <div class="progress-page">
    <div class="progress-shell">
      <section class="hero-card">
        <div class="hero-left">
          <div class="hero-badge">📈 学习进度</div>
          <h2 class="hero-title">阶段 — 任务点 — 题目</h2>
        </div>

        <div class="hero-right">
          <label class="selector-label">选择学习路径</label>
          <select
            v-model="selectedPathId"
            class="path-select"
            :disabled="loadingPaths || !pathOptions.length"
            @change="onPathChange"
          >
            <option v-if="!pathOptions.length" value="">暂无学习路径</option>
            <option
              v-for="path in pathOptions"
              :key="path.path_id"
              :value="path.path_id"
            >
              {{ formatPathOption(path) }}
            </option>
          </select>
        </div>
      </section>

      <section class="overview-grid" v-if="selectedPath">
        <div class="overview-card path-meta-card">
          <div class="overview-title">当前路径</div>
          <div class="path-goal">{{ selectedPath.goal || '未命名学习路径' }}</div>
          <div class="meta-tags">
            <span class="meta-tag">领域：{{ formatDomain(selectedPath.domain) }}</span>
            <span class="meta-tag">水平：{{ selectedPath.level || '未设置' }}</span>
            <span class="meta-tag">当前阶段：{{ currentStageName || selectedPath.status || '暂无' }}</span>
          </div>
          <p class="background-text">
            {{ selectedPath.background_plan || '暂无学习背景与计划说明。' }}
          </p>
        </div>

        <div class="overview-card compact-card">
          <div class="overview-title">阶段数</div>
          <div class="overview-value">{{ totalStages }}</div>
        </div>

        <div class="overview-card compact-card">
          <div class="overview-title">任务点进度</div>
          <div class="overview-value">{{ completedTasks }} / {{ totalTasks }}</div>
          <div class="overview-desc">已完成 / 总任务点</div>
        </div>

        <div class="overview-card compact-card">
          <div class="overview-title">完成率</div>
          <div class="overview-value">{{ completionRate }}%</div>
          <div class="mini-progress">
            <div class="mini-progress-bar" :style="{ width: `${completionRate}%` }"></div>
          </div>
        </div>
      </section>

      <section class="content-card">
        <div class="content-header">
          <div>
            <h3 class="content-title">📚 学习结构总览</h3>
          </div>
          <div class="content-stats" v-if="selectedPath">
            <span>{{ totalStages }} 个阶段</span>
            <span>{{ totalTasks }} 个任务点</span>
            <span>{{ totalQuestions }} 道题目</span>
          </div>
        </div>

        <div v-if="loadingDetail" class="status-view">正在加载学习进度...</div>
        <div v-else-if="!selectedPathId" class="status-view">请先选择一个学习路径。</div>
        <div v-else-if="!displayStages.length" class="status-view">当前路径暂无阶段与任务数据。</div>

        <div v-else class="content-scroll">
          <div
            v-for="stage in displayStages"
            :key="stage.progress_id || `stage-${stage.progress_order}`"
            class="stage-card"
          >
            <div class="stage-top">
              <div>
                <div class="stage-order">阶段 {{ stage.progress_order || 1 }}</div>
                <h4 class="stage-title">{{ stage.progress_name || '未命名阶段' }}</h4>
                <p class="stage-desc">
                  {{ stage.progress_description || '暂无阶段说明。' }}
                </p>
              </div>
              <div class="stage-summary-wrap">
                <div class="stage-summary">
                  <span>{{ getCompletedTaskCount(stage.tasks) }}/{{ stage.tasks.length }} 已完成</span>
                </div>
                <div class="stage-summary light">
                  <span>{{ getStageAnsweredCount(stage.tasks) }}/{{ getStageQuestionCount(stage.tasks) }} 已作答</span>
                </div>
              </div>
            </div>

            <div class="task-list">
              <div
                v-for="task in stage.tasks"
                :key="task.task_id || `${stage.progress_id}-${task.order_no}`"
                class="task-card"
                :class="isTaskCompleted(task) ? 'task-card--done' : 'task-card--todo'"
              >
                <div class="task-top">
                  <div class="task-index">任务点 {{ task.order_no || 1 }}</div>
                  <div class="task-top-right">
                    <span class="task-question-summary">
                      {{ getAnsweredQuestionCount(task.questions) }}/{{ getQuestionCount(task.questions) }} 已作答
                    </span>
                    <span class="task-state" :class="isTaskCompleted(task) ? 'done' : 'todo'">
                      {{ isTaskCompleted(task) ? '已完成' : '未完成' }}
                    </span>
                  </div>
                </div>

                <div class="task-name-row">
                  <span class="task-icon">{{ isTaskCompleted(task) ? '✅' : '🟣' }}</span>
                  <h5 class="task-name">{{ task.task_name || '未命名任务点' }}</h5>
                </div>

                <p class="task-desc">
                  {{ task.description || task.task_description || '暂无任务说明。' }}
                </p>

                <div class="question-box">
                  <div class="question-head">
                    <span>📝 题目</span>
                    <span class="question-count">
                      {{ getQuestionCount(task.questions) }} 题
                    </span>
                  </div>

                  <template v-if="Array.isArray(task.questions) && task.questions.length">
                    <button
                      v-for="(question, qIndex) in task.questions"
                      :key="question.question_id || `question-${task.task_id || task.order_no}-${qIndex}`"
                      type="button"
                      class="question-item"
                      :class="getQuestionCardClass(question)"
                      @click="openQuestionDialog(stage, task, question, qIndex)"
                    >
                      <div class="question-item-left">
                        <span class="question-no">{{ qIndex + 1 }}</span>
                      </div>

                      <div class="question-main">
                        <div class="question-top-line">
                          <span class="question-type-tag">
                            {{ getQuestionTypeLabel(question) }}
                          </span>
                          <span class="question-status-tag" :class="getQuestionStatusClass(question)">
                            {{ getQuestionStatusText(question) }}
                          </span>
                        </div>

                        <div class="question-text line-clamp-2">
                          {{ getQuestionStem(question) || question.question_text || '未命名题目' }}
                        </div>

                        <div class="question-meta">
                          <span v-if="hasUserAnswered(question)">
                            我的作答：{{ question.user_answer }}
                          </span>
                          <span v-if="hasUserAnswered(question)">
                            参考答案：{{ getDisplayCorrectAnswer(question) }}
                          </span>
                          <span v-else>
                            点击进入作答
                          </span>
                        </div>
                      </div>

                      <div class="question-action">
                        <span>{{ hasUserAnswered(question) ? '查看作答' : '去作答' }}</span>
                      </div>
                    </button>
                  </template>

                  <div v-else class="question-empty">
                    当前任务点暂无题目。
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>
    </div>

    <div
      v-if="dialogVisible && activeQuestion"
      class="answer-dialog-mask"
      @click.self="closeQuestionDialog"
    >
      <div class="answer-dialog">
        <div class="answer-dialog-header">
          <div>
            <div class="answer-dialog-badge">{{ activeQuestionTypeLabel }}</div>
            <h3 class="answer-dialog-title">
              {{ activeTask?.task_name || '任务题目' }}
            </h3>
            <p class="answer-dialog-subtitle">
              第 {{ activeQuestionIndex + 1 }} 题
            </p>
          </div>
          <button type="button" class="dialog-close-btn" @click="closeQuestionDialog">×</button>
        </div>

        <div class="answer-dialog-body">
          <div class="dialog-section">
            <div class="dialog-label">题目内容</div>
            <div class="dialog-question-card">
              <div class="dialog-question-text">
                {{ activeQuestionStem }}
              </div>
            </div>
          </div>

          <div class="dialog-section" v-if="activeQuestionOptions.length">
            <div class="dialog-label">选项作答</div>
            <div class="option-list" v-if="!activeQuestionLocked">
              <button
                v-for="option in activeQuestionOptions"
                :key="`${activeQuestion.question_id}-${option.label}`"
                type="button"
                class="option-item"
                :class="{ active: selectedOptionLabel === option.label }"
                @click="selectOption(option)"
              >
                <span class="option-label">{{ option.label }}</span>
                <span class="option-text">{{ option.text }}</span>
              </button>
            </div>

            <div class="answer-result-card" v-else>
              <div class="answer-result-row">
                <span class="answer-result-key">我的答案</span>
                <span class="answer-result-value">{{ activeQuestion.user_answer || '未作答' }}</span>
              </div>
              <div class="answer-result-row">
                <span class="answer-result-key">参考答案</span>
                <span class="answer-result-value">{{ getDisplayCorrectAnswer(activeQuestion) }}</span>
              </div>
              <div class="answer-result-row" v-if="showJudgeResult(activeQuestion)">
                <span class="answer-result-key">判题结果</span>
                <span
                  class="judge-chip"
                  :class="Number(activeQuestion.is_passed) === 1 ? 'pass' : 'fail'"
                >
                  {{ Number(activeQuestion.is_passed) === 1 ? '回答正确' : '回答错误' }}
                </span>
              </div>
              <div class="answer-result-row" v-else>
                <span class="answer-result-key">判题结果</span>
                <span class="judge-chip pending">待判定</span>
              </div>
            </div>
          </div>

          <div class="dialog-section" v-else>
            <div class="dialog-label">文本作答</div>
            <template v-if="!activeQuestionLocked">
              <textarea
                v-model="draftTextAnswer"
                class="answer-textarea"
                placeholder="请输入你的答案"
                rows="6"
              ></textarea>
              <p class="dialog-hint">
                当前题目未解析出客观选项，已自动切换为文本作答模式。
              </p>
            </template>

            <div v-else class="answer-result-card">
              <div class="answer-result-row align-start">
                <span class="answer-result-key">我的答案</span>
                <span class="answer-result-value multi-line">{{ activeQuestion.user_answer || '未作答' }}</span>
              </div>
              <div class="answer-result-row align-start">
                <span class="answer-result-key">参考答案</span>
                <span class="answer-result-value multi-line">{{ getDisplayCorrectAnswer(activeQuestion) }}</span>
              </div>
              <div class="answer-result-row" v-if="showJudgeResult(activeQuestion)">
                <span class="answer-result-key">判题结果</span>
                <span
                  class="judge-chip"
                  :class="Number(activeQuestion.is_passed) === 1 ? 'pass' : 'fail'"
                >
                  {{ Number(activeQuestion.is_passed) === 1 ? '回答正确' : '回答错误' }}
                </span>
              </div>
              <div class="answer-result-row" v-else>
                <span class="answer-result-key">判题结果</span>
                <span class="judge-chip pending">待判定</span>
              </div>
            </div>
          </div>

          <div v-if="dialogMessage" class="dialog-toast" :class="dialogMessageType">
            {{ dialogMessage }}
          </div>
        </div>

        <div class="answer-dialog-footer">
          <button type="button" class="dialog-btn secondary" @click="closeQuestionDialog">
            {{ activeQuestionLocked ? '关闭' : '取消' }}
          </button>
          <button
            v-if="!activeQuestionLocked"
            type="button"
            class="dialog-btn primary"
            :disabled="saveDisabled || savingAnswer"
            @click="saveCurrentAnswer"
          >
            {{ savingAnswer ? '保存中...' : '保存作答' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import api from '../api/index'

const rawUser = localStorage.getItem('user_info')
let userId = null

try {
  userId = rawUser ? JSON.parse(rawUser)?.user_id : null
} catch (error) {
  console.error('解析用户信息失败:', error)
}

const pathOptions = ref([])
const selectedPathId = ref('')
const pathDetailData = ref(null)
const displayStages = ref([])
const loadingPaths = ref(false)
const loadingDetail = ref(false)

const dialogVisible = ref(false)
const activeStage = ref(null)
const activeTask = ref(null)
const activeQuestion = ref(null)
const activeQuestionIndex = ref(0)
const selectedOptionLabel = ref('')
const draftTextAnswer = ref('')
const savingAnswer = ref(false)
const dialogMessage = ref('')
const dialogMessageType = ref('success')

const selectedPath = computed(() => pathDetailData.value?.path || null)

const totalStages = computed(() => displayStages.value.length)

const totalTasks = computed(() => {
  return displayStages.value.reduce((sum, stage) => sum + (stage.tasks?.length || 0), 0)
})

const totalQuestions = computed(() => {
  return displayStages.value.reduce((sum, stage) => {
    return sum + (stage.tasks || []).reduce((taskSum, task) => taskSum + getQuestionCount(task.questions), 0)
  }, 0)
})

const completedTasks = computed(() => {
  return displayStages.value.reduce(
    (sum, stage) => sum + getCompletedTaskCount(stage.tasks),
    0,
  )
})

const completionRate = computed(() => {
  if (!totalTasks.value) return 0
  return Math.round((completedTasks.value / totalTasks.value) * 100)
})

const currentStageName = computed(() => {
  const firstUnfinished = displayStages.value.find((stage) => {
    const tasks = stage.tasks || []
    return tasks.some((task) => !isTaskCompleted(task))
  })
  return firstUnfinished?.progress_name || '暂无'
})

const activeQuestionParsed = computed(() => {
  if (!activeQuestion.value) {
    return { stem: '', options: [] }
  }
  return parseQuestionContent(activeQuestion.value.question_text)
})

const activeQuestionStem = computed(() => {
  return activeQuestionParsed.value.stem || activeQuestion.value?.question_text || ''
})

const activeQuestionOptions = computed(() => {
  return activeQuestionParsed.value.options || []
})

const activeQuestionTypeLabel = computed(() => {
  if (!activeQuestion.value) return '题目'
  return activeQuestionOptions.value.length ? '选择题' : '文本题'
})

const activeQuestionLocked = computed(() => {
  return hasUserAnswered(activeQuestion.value)
})

const saveDisabled = computed(() => {
  if (!activeQuestion.value) return true
  if (activeQuestionOptions.value.length) {
    return !selectedOptionLabel.value
  }
  return !normalizeText(draftTextAnswer.value)
})

onMounted(async () => {
  if (!userId) {
    alert('请先登录')
    return
  }

  await loadPathList()

  if (pathOptions.value.length > 0) {
    selectedPathId.value = pathOptions.value[0].path_id
    await loadPathDetail(selectedPathId.value)
  }
})

const unwrapResponse = (response) => {
  if (!response) return null
  return response.data?.data ?? response.data ?? null
}

const sortByNumber = (list, field) => {
  return [...(list || [])].sort((a, b) => Number(a?.[field] || 0) - Number(b?.[field] || 0))
}

const normalizeText = (value) => {
  return String(value || '').replace(/\s+/g, ' ').trim()
}

const parseQuestionContent = (questionText) => {
  const raw = String(questionText || '').replace(/\r/g, '')
  const lines = raw
    .split('\n')
    .map((item) => item.trim())
    .filter(Boolean)

  if (!lines.length) {
    return { stem: '', options: [] }
  }

  const optionRegex = /^(?:选项)?([A-Z])\s*[\.、:：]\s*(.+)$/i
  const firstOptionIndex = lines.findIndex((line) => optionRegex.test(line))

  if (firstOptionIndex === -1) {
    return {
      stem: raw.trim(),
      options: [],
    }
  }

  const stem = lines.slice(0, firstOptionIndex).join('\n').trim()
  const optionLines = lines.slice(firstOptionIndex)
  const options = optionLines
    .map((line) => {
      const match = line.match(optionRegex)
      if (!match) return null
      return {
        label: String(match[1] || '').toUpperCase(),
        text: match[2] || '',
      }
    })
    .filter(Boolean)

  return {
    stem: stem || raw.trim(),
    options,
  }
}

const extractOptionLabel = (value) => {
  const text = normalizeText(value)
  if (!text) return ''

  const matched = text.match(/(?:选项)?\s*([A-Z])(?:\s*[\.、:：]|$)/i)
  return matched?.[1]?.toUpperCase() || ''
}

const hasJudgeableCorrectAnswer = (question) => {
  const correctAnswer = normalizeText(question?.correct_answer)
  if (!correctAnswer) return false
  return correctAnswer !== '(待判定)'
}

const compareAnswerWithCorrect = (userAnswer, correctAnswer) => {
  const userText = normalizeText(userAnswer)
  const correctText = normalizeText(correctAnswer)
  if (!userText || !correctText || correctText === '(待判定)') return 0

  const userLabel = extractOptionLabel(userText)
  const correctLabel = extractOptionLabel(correctText)

  if (userLabel && correctLabel) {
    return userLabel === correctLabel ? 1 : 0
  }

  return userText === correctText ? 1 : 0
}

const normalizeQuestions = (questions) => {
  if (!Array.isArray(questions)) return []

  return questions.map((question, index) => ({
    ...question,
    question_id: question?.question_id ?? question?.id ?? `q-${index}`,
    question_text:
      question?.question_text ||
      question?.title ||
      question?.content ||
      '未命名题目',
    correct_answer: question?.correct_answer || '',
    user_answer: question?.user_answer || '',
    is_passed: Number(question?.is_passed || 0),
  }))
}

const buildTaskIndex = (tasks) => {
  const byId = new Map()
  const byName = new Map()

  ;(tasks || []).forEach((task, index) => {
    const normalizedTask = {
      ...task,
      order_no: Number(task?.order_no || task?.task_order || index + 1),
      description: task?.description || task?.task_description || '',
      questions: normalizeQuestions(task?.questions),
    }

    if (task?.task_id != null) {
      byId.set(String(task.task_id), normalizedTask)
    }

    const taskName = task?.task_name || task?.title || ''
    if (taskName) {
      byName.set(taskName, normalizedTask)
    }
  })

  return { byId, byName }
}

const mergeTaskWithFlatData = (task, taskIndex, fallbackOrder = 1) => {
  const taskIdKey = task?.task_id != null ? String(task.task_id) : null
  const taskName = task?.task_name || task?.title || ''
  const flatTask =
    (taskIdKey ? taskIndex.byId.get(taskIdKey) : null) ||
    (taskName ? taskIndex.byName.get(taskName) : null) ||
    null

  const merged = {
    ...task,
    ...(flatTask || {}),
  }

  merged.order_no = Number(merged?.order_no || merged?.task_order || fallbackOrder)
  merged.description = merged?.description || merged?.task_description || ''
  merged.questions = normalizeQuestions(merged?.questions)

  return merged
}

const normalizeStagesFromDetail = (detail) => {
  const progresses = Array.isArray(detail?.progresses) ? detail.progresses : []
  const flatTasks = Array.isArray(detail?.tasks) ? detail.tasks : []
  const taskIndex = buildTaskIndex(flatTasks)

  if (progresses.length) {
    return sortByNumber(progresses, 'progress_order').map((progress) => {
      const nestedTasks = Array.isArray(progress?.tasks) ? progress.tasks : []

      if (nestedTasks.length) {
        return {
          ...progress,
          tasks: sortByNumber(nestedTasks, 'order_no').map((task, index) =>
            mergeTaskWithFlatData(task, taskIndex, index + 1),
          ),
        }
      }

      const progressTasks = flatTasks.filter((task) => {
        if (task?.progress_id == null) return false
        return String(task.progress_id) === String(progress.progress_id)
      })

      return {
        ...progress,
        tasks: sortByNumber(progressTasks, 'order_no').map((task, index) =>
          mergeTaskWithFlatData(task, taskIndex, index + 1),
        ),
      }
    })
  }

  if (flatTasks.length) {
    return [
      {
        progress_id: 'default-stage',
        progress_order: 1,
        progress_name: detail?.path?.status || '学习阶段',
        progress_description: detail?.path?.goal || '当前学习路径的任务点列表',
        tasks: sortByNumber(flatTasks, 'order_no').map((task, index) =>
          mergeTaskWithFlatData(task, taskIndex, index + 1),
        ),
      },
    ]
  }

  return []
}

const loadPathList = async () => {
  loadingPaths.value = true
  try {
    const res = await api.getPaths(userId)
    const data = unwrapResponse(res)
    pathOptions.value = Array.isArray(data) ? data : []
  } catch (error) {
    console.error('加载路径列表失败:', error)
    pathOptions.value = []
  } finally {
    loadingPaths.value = false
  }
}

const loadPathDetail = async (pathId) => {
  if (!pathId) {
    pathDetailData.value = null
    displayStages.value = []
    return
  }

  loadingDetail.value = true
  try {
    const res = await api.getPathDetail(pathId)
    const detail = unwrapResponse(res) || {}
    pathDetailData.value = detail
    displayStages.value = normalizeStagesFromDetail(detail)
  } catch (error) {
    console.error('加载路径详情失败:', error)
    pathDetailData.value = null
    displayStages.value = []
  } finally {
    loadingDetail.value = false
  }
}

const onPathChange = async () => {
  await loadPathDetail(selectedPathId.value)
}

const getCompletedTaskCount = (tasks = []) => {
  return (tasks || []).filter((task) => isTaskCompleted(task)).length
}

const getQuestionCount = (questions = []) => {
  return Array.isArray(questions) ? questions.length : 0
}

const getAnsweredQuestionCount = (questions = []) => {
  return (questions || []).filter((question) => hasUserAnswered(question)).length
}

const isTaskCompleted = (task) => {
  const questions = Array.isArray(task?.questions) ? task.questions : []
  if (questions.length > 0) {
    return questions.every((question) => hasUserAnswered(question))
  }
  return !!task?.is_completed
}

const getStageQuestionCount = (tasks = []) => {
  return (tasks || []).reduce((sum, task) => sum + getQuestionCount(task.questions), 0)
}

const getStageAnsweredCount = (tasks = []) => {
  return (tasks || []).reduce((sum, task) => sum + getAnsweredQuestionCount(task.questions), 0)
}

const hasUserAnswered = (question) => {
  return !!normalizeText(question?.user_answer)
}

const getQuestionStem = (question) => {
  return parseQuestionContent(question?.question_text).stem || question?.question_text || ''
}

const getQuestionTypeLabel = (question) => {
  return parseQuestionContent(question?.question_text).options.length ? '选择题' : '文本题'
}

const getDisplayCorrectAnswer = (question) => {
  return normalizeText(question?.correct_answer) || '暂无参考答案'
}

const showJudgeResult = (question) => {
  return hasUserAnswered(question) && hasJudgeableCorrectAnswer(question)
}

const getQuestionStatusText = (question) => {
  if (!hasUserAnswered(question)) return '未作答'
  if (!hasJudgeableCorrectAnswer(question)) return '已作答'
  return Number(question?.is_passed) === 1 ? '回答正确' : '回答错误'
}

const getQuestionStatusClass = (question) => {
  if (!hasUserAnswered(question)) return 'todo'
  if (!hasJudgeableCorrectAnswer(question)) return 'pending'
  return Number(question?.is_passed) === 1 ? 'pass' : 'fail'
}

const getQuestionCardClass = (question) => {
  return {
    'question-item--answered': hasUserAnswered(question),
    'question-item--pending': hasUserAnswered(question) && !hasJudgeableCorrectAnswer(question),
  }
}

const formatDomain = (domain) => {
  const map = {
    career: '职业发展',
    exam: '考试提升',
    hobby: '兴趣学习',
    skill: '技能训练',
  }
  return map[domain] || domain || '未设置'
}

const formatPathOption = (path) => {
  const goal = path?.goal || '未命名路径'
  const level = path?.level || '未设置水平'
  return `${goal}（${level}）`
}

const clearDialogMessage = () => {
  dialogMessage.value = ''
  dialogMessageType.value = 'success'
}

const openQuestionDialog = (stage, task, question, qIndex) => {
  activeStage.value = stage
  activeTask.value = task
  activeQuestion.value = question
  activeQuestionIndex.value = qIndex
  selectedOptionLabel.value = ''
  draftTextAnswer.value = ''
  clearDialogMessage()

  if (hasUserAnswered(question)) {
    const currentLabel = extractOptionLabel(question.user_answer)
    if (currentLabel) {
      selectedOptionLabel.value = currentLabel
    }
    draftTextAnswer.value = question.user_answer || ''
  }

  dialogVisible.value = true
}

const closeQuestionDialog = () => {
  dialogVisible.value = false
  activeStage.value = null
  activeTask.value = null
  activeQuestion.value = null
  activeQuestionIndex.value = 0
  selectedOptionLabel.value = ''
  draftTextAnswer.value = ''
  savingAnswer.value = false
  clearDialogMessage()
}

const selectOption = (option) => {
  selectedOptionLabel.value = option.label
}

const buildSelectedAnswer = () => {
  if (activeQuestionOptions.value.length) {
    const matched = activeQuestionOptions.value.find((item) => item.label === selectedOptionLabel.value)
    if (!matched) return ''
    return `${matched.label}. ${matched.text}`
  }

  return normalizeText(draftTextAnswer.value)
}

const updateLocalQuestionAnswer = ({ taskId, questionId, answer, isPassed, taskCompleted, pathStatus, currentTaskPoint }) => {
  displayStages.value.forEach((stage) => {
    ;(stage.tasks || []).forEach((task) => {
      if (String(task.task_id) !== String(taskId)) return

      ;(task.questions || []).forEach((question) => {
        if (String(question.question_id) !== String(questionId)) return
        question.user_answer = answer
        question.is_passed = Number(isPassed || 0)
      })

      if (typeof taskCompleted === 'boolean') {
        task.is_completed = taskCompleted
      } else {
        task.is_completed = isTaskCompleted(task)
      }
    })
  })

  displayStages.value = [...displayStages.value]

  if (activeQuestion.value && String(activeQuestion.value.question_id) === String(questionId)) {
    activeQuestion.value.user_answer = answer
    activeQuestion.value.is_passed = Number(isPassed || 0)
  }

  if (activeTask.value && String(activeTask.value.task_id) === String(taskId)) {
    activeTask.value.is_completed = typeof taskCompleted === 'boolean'
      ? taskCompleted
      : isTaskCompleted(activeTask.value)
  }

  if (pathDetailData.value?.path) {
    if (pathStatus) {
      pathDetailData.value.path.status = pathStatus
    }
    if (currentTaskPoint !== undefined) {
      pathDetailData.value.path.current_task_point = currentTaskPoint
    }
    pathDetailData.value = {
      ...pathDetailData.value,
      path: { ...pathDetailData.value.path },
    }
  }
}

const submitAnswerToBackend = async (payload) => {
  const requestBody = {
    user_id: payload?.user_id ?? userId,
    question_id: Number(payload?.question_id),
    user_answer: payload?.user_answer ?? '',
  }

  if (typeof api.post === 'function') {
    return unwrapResponse(await api.post('/api/tasks/answer', requestBody))
  }

  if (typeof api.saveTaskAnswer === 'function') {
    return unwrapResponse(await api.saveTaskAnswer(requestBody))
  }

  if (typeof api.submitTaskAnswer === 'function') {
    return unwrapResponse(await api.submitTaskAnswer(requestBody))
  }

  if (typeof api.submitAnswer === 'function') {
    if (api.submitAnswer.length >= 2) {
      return unwrapResponse(await api.submitAnswer(requestBody.question_id, requestBody.user_answer, requestBody.user_id))
    }
    return unwrapResponse(await api.submitAnswer(requestBody))
  }

  throw new Error('未找到可用的题目作答接口方法')
}

const saveCurrentAnswer = async () => {
  if (!activeQuestion.value || !activeTask.value) return

  const finalAnswer = buildSelectedAnswer()
  if (!finalAnswer) {
    dialogMessageType.value = 'error'
    dialogMessage.value = '请先完成作答再保存。'
    return
  }

  const isPassed = hasJudgeableCorrectAnswer(activeQuestion.value)
    ? compareAnswerWithCorrect(finalAnswer, activeQuestion.value.correct_answer)
    : 0

  const payload = {
    user_id: userId,
    path_id: selectedPathId.value,
    progress_id: activeStage.value?.progress_id,
    task_id: activeTask.value.task_id,
    question_id: activeQuestion.value.question_id,
    user_answer: finalAnswer,
    is_passed: isPassed,
  }

  savingAnswer.value = true
  clearDialogMessage()

  try {
    const result = (await submitAnswerToBackend(payload)) || {}

    updateLocalQuestionAnswer({
      taskId: activeTask.value.task_id,
      questionId: activeQuestion.value.question_id,
      answer: result.user_answer || finalAnswer,
      isPassed: result.is_passed ?? isPassed,
      taskCompleted: typeof result.task_is_completed === 'boolean' ? result.task_is_completed : undefined,
      pathStatus: result.path_status,
      currentTaskPoint: result.current_task_point,
    })

    dialogMessageType.value = 'success'
    dialogMessage.value = hasJudgeableCorrectAnswer(activeQuestion.value)
      ? (isPassed === 1 ? '保存成功，回答正确。' : '保存成功，已完成判题。')
      : '保存成功，当前题目参考答案待判定。'
  } catch (error) {
    console.error('保存题目作答失败:', error)
    dialogMessageType.value = 'error'
    dialogMessage.value = '保存失败，请稍后重试。'
  } finally {
    savingAnswer.value = false
  }
}
</script>

<style scoped>
.progress-page {
  min-height: 100vh;
  padding: 28px;
  background: #fcfcff;
}

.progress-shell {
  max-width: 1280px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.hero-card,
.overview-card,
.content-card {
  background: #fff;
  border: 1px solid #ece9ff;
  box-shadow: 0 10px 30px rgba(108, 92, 231, 0.06);
}

.hero-card {
  display: flex;
  justify-content: space-between;
  gap: 24px;
  align-items: flex-start;
  padding: 24px 28px;
  border-radius: 24px;
}

.hero-left {
  flex: 1;
}

.hero-badge {
  display: inline-flex;
  align-items: center;
  padding: 6px 12px;
  border-radius: 999px;
  background: rgba(127, 86, 217, 0.12);
  color: #7f56d9;
  font-size: 13px;
  font-weight: 700;
}

.hero-title {
  margin: 14px 0 0;
  font-size: 30px;
  color: #2b2340;
}

.hero-right {
  width: 320px;
  flex-shrink: 0;
}

.selector-label {
  display: block;
  margin-bottom: 10px;
  font-size: 13px;
  color: #625b76;
  font-weight: 600;
}

.path-select {
  width: 100%;
  height: 46px;
  padding: 0 14px;
  border-radius: 14px;
  border: 1px solid #ddd4ff;
  background: #fff;
  font-size: 14px;
  color: #2f2840;
  outline: none;
  transition: all 0.2s ease;
}

.path-select:focus {
  border-color: #8b5cf6;
  box-shadow: 0 0 0 4px rgba(139, 92, 246, 0.12);
}

.overview-grid {
  display: grid;
  grid-template-columns: 2fr repeat(3, 1fr);
  gap: 16px;
}

.overview-card {
  border-radius: 20px;
  padding: 20px;
}

.path-meta-card {
  min-height: 156px;
}

.overview-title {
  font-size: 13px;
  color: #7a7391;
  font-weight: 700;
}

.path-goal,
.overview-value {
  margin-top: 12px;
  color: #2b2340;
  font-weight: 800;
}

.path-goal {
  font-size: 24px;
  line-height: 1.4;
}

.overview-value {
  font-size: 30px;
  line-height: 1;
}

.meta-tags {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  margin-top: 14px;
}

.meta-tag {
  padding: 6px 10px;
  border-radius: 999px;
  background: #f3efff;
  color: #6d4cc0;
  font-size: 12px;
  font-weight: 700;
}

.background-text,
.overview-desc,
.stage-desc,
.task-desc,
.question-empty,
.status-view,
.dialog-hint {
  color: #6f6885;
}

.background-text {
  margin: 14px 0 0;
  font-size: 13px;
  line-height: 1.7;
}

.compact-card {
  display: flex;
  flex-direction: column;
  justify-content: center;
  min-height: 156px;
}

.overview-desc {
  margin-top: 10px;
  font-size: 12px;
}

.mini-progress {
  margin-top: 14px;
  height: 8px;
  border-radius: 999px;
  background: #ebe7fb;
  overflow: hidden;
}

.mini-progress-bar {
  height: 100%;
  border-radius: inherit;
  background: linear-gradient(90deg, #8b5cf6 0%, #6d4cc0 100%);
}

.content-card {
  border-radius: 24px;
  padding: 22px;
}

.content-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
  margin-bottom: 18px;
}

.content-title {
  margin: 0;
  font-size: 22px;
  color: #2b2340;
}

.content-stats {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.content-stats span {
  padding: 8px 12px;
  border-radius: 999px;
  background: #f4f1ff;
  color: #6d4cc0;
  font-size: 12px;
  font-weight: 700;
}

.content-scroll {
  max-height: 640px;
  overflow-y: auto;
  padding-right: 8px;
}

.content-scroll::-webkit-scrollbar {
  width: 8px;
}

.content-scroll::-webkit-scrollbar-thumb {
  border-radius: 999px;
  background: rgba(139, 92, 246, 0.32);
}

.content-scroll::-webkit-scrollbar-track {
  background: rgba(139, 92, 246, 0.08);
  border-radius: 999px;
}

.stage-card {
  border: 1px solid #ece6ff;
  border-radius: 22px;
  padding: 20px;
  background: linear-gradient(180deg, #ffffff 0%, #fcfbff 100%);
}

.stage-card + .stage-card {
  margin-top: 16px;
}

.stage-top {
  display: flex;
  justify-content: space-between;
  gap: 20px;
  align-items: flex-start;
  margin-bottom: 18px;
}

.stage-order {
  display: inline-flex;
  padding: 5px 10px;
  border-radius: 999px;
  background: rgba(139, 92, 246, 0.12);
  color: #7f56d9;
  font-size: 12px;
  font-weight: 800;
}

.stage-title {
  margin: 12px 0 8px;
  font-size: 22px;
  color: #2e2646;
}

.stage-desc {
  margin: 0;
  font-size: 13px;
  line-height: 1.7;
}

.stage-summary-wrap {
  display: flex;
  flex-direction: column;
  gap: 8px;
  align-items: flex-end;
}

.stage-summary {
  padding: 10px 14px;
  border-radius: 14px;
  background: #ffffff;
  border: 1px solid #ece6ff;
  font-size: 12px;
  font-weight: 700;
  color: #6d4cc0;
  white-space: nowrap;
}

.stage-summary.light {
  background: #faf8ff;
  color: #7a7391;
}

.task-list {
  display: grid;
  gap: 14px;
}

.task-card {
  border-radius: 18px;
  padding: 16px;
  background: #fff;
  border: 1px solid #efeafc;
  box-shadow: 0 10px 24px rgba(108, 76, 192, 0.05);
}

.task-card--done {
  border-left: 5px solid #22c55e;
}

.task-card--todo {
  border-left: 5px solid #8b5cf6;
}

.task-top,
.question-head,
.task-name-row,
.question-top-line,
.answer-result-row {
  display: flex;
  align-items: center;
}

.task-top,
.question-head,
.answer-result-row {
  justify-content: space-between;
  gap: 12px;
}

.task-top-right {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
  justify-content: flex-end;
}

.task-index {
  font-size: 12px;
  font-weight: 800;
  color: #7a7391;
}

.task-question-summary {
  font-size: 12px;
  font-weight: 700;
  color: #746c8f;
  padding: 5px 10px;
  border-radius: 999px;
  background: #f7f4ff;
}

.task-state {
  padding: 5px 10px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 800;
}

.task-state.done {
  background: rgba(34, 197, 94, 0.12);
  color: #15803d;
}

.task-state.todo {
  background: rgba(139, 92, 246, 0.12);
  color: #7f56d9;
}

.task-name-row {
  gap: 10px;
  margin-top: 12px;
}

.task-icon {
  font-size: 18px;
}

.task-name {
  margin: 0;
  font-size: 17px;
  color: #2f2840;
}

.task-desc {
  margin: 12px 0 0;
  font-size: 13px;
  line-height: 1.8;
}

.question-box {
  margin-top: 16px;
  padding: 14px;
  border-radius: 16px;
  background: #faf8ff;
  border: 1px dashed #dfd4ff;
}

.question-head {
  margin-bottom: 12px;
  font-size: 13px;
  color: #5f5874;
  font-weight: 700;
}

.question-count {
  color: #8b5cf6;
}

.question-item {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 14px;
  border-radius: 14px;
  background: #fff;
  border: 1px solid #eee8ff;
  text-align: left;
  cursor: pointer;
  transition: all 0.2s ease;
}

.question-item:hover {
  border-color: #cdb9ff;
  box-shadow: 0 12px 24px rgba(139, 92, 246, 0.08);
  transform: translateY(-1px);
}

.question-item + .question-item {
  margin-top: 10px;
}

.question-item--answered {
  background: linear-gradient(180deg, #ffffff 0%, #fcfbff 100%);
}

.question-item--pending {
  border-style: dashed;
}

.question-item-left {
  flex-shrink: 0;
}

.question-no {
  width: 34px;
  height: 34px;
  border-radius: 50%;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: #f3efff;
  color: #7f56d9;
  font-size: 13px;
  font-weight: 800;
}

.question-main {
  display: flex;
  flex-direction: column;
  gap: 8px;
  min-width: 0;
  flex: 1;
}

.question-top-line {
  gap: 8px;
  justify-content: flex-start;
  flex-wrap: wrap;
}

.question-type-tag,
.question-status-tag,
.answer-dialog-badge,
.judge-chip {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 4px 10px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 700;
}

.question-type-tag,
.answer-dialog-badge {
  background: #f3efff;
  color: #7f56d9;
}

.question-status-tag.todo {
  background: #f5f5fb;
  color: #7a7391;
}

.question-status-tag.pending,
.judge-chip.pending {
  background: rgba(250, 204, 21, 0.16);
  color: #a16207;
}

.question-status-tag.pass,
.judge-chip.pass {
  background: rgba(34, 197, 94, 0.14);
  color: #15803d;
}

.question-status-tag.fail,
.judge-chip.fail {
  background: rgba(239, 68, 68, 0.12);
  color: #dc2626;
}

.question-text {
  font-size: 13px;
  color: #443c59;
  line-height: 1.65;
  word-break: break-word;
}

.question-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  font-size: 12px;
  color: #8a83a3;
}

.question-action {
  flex-shrink: 0;
  color: #7f56d9;
  font-size: 12px;
  font-weight: 700;
}

.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.question-empty {
  padding: 12px;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.9);
  font-size: 13px;
  line-height: 1.7;
}

.status-view {
  padding: 56px 16px;
  text-align: center;
  font-size: 14px;
}

.answer-dialog-mask {
  position: fixed;
  inset: 0;
  z-index: 1000;
  background: rgba(24, 18, 41, 0.4);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
}

.answer-dialog {
  width: min(760px, 100%);
  max-height: 88vh;
  overflow: hidden;
  background: #fff;
  border-radius: 24px;
  border: 1px solid #ebe4ff;
  box-shadow: 0 28px 80px rgba(43, 35, 64, 0.22);
  display: flex;
  flex-direction: column;
}

.answer-dialog-header {
  padding: 22px 24px 18px;
  border-bottom: 1px solid #f0ebff;
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}

.answer-dialog-title {
  margin: 12px 0 6px;
  font-size: 22px;
  color: #2f2840;
}

.answer-dialog-subtitle {
  margin: 0;
  font-size: 13px;
  color: #8a83a3;
}

.dialog-close-btn {
  width: 38px;
  height: 38px;
  border: none;
  border-radius: 12px;
  background: #f6f3ff;
  color: #6d4cc0;
  font-size: 24px;
  line-height: 1;
  cursor: pointer;
}

.answer-dialog-body {
  padding: 22px 24px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.dialog-section {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.dialog-label {
  font-size: 13px;
  color: #6f6885;
  font-weight: 700;
}

.dialog-question-card,
.answer-result-card {
  border-radius: 18px;
  background: #fbfaff;
  border: 1px solid #ede7ff;
  padding: 16px;
}

.dialog-question-text {
  font-size: 15px;
  line-height: 1.8;
  color: #3a334d;
  white-space: pre-wrap;
}

.option-list {
  display: grid;
  gap: 10px;
}

.option-item {
  width: 100%;
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 14px 16px;
  border-radius: 16px;
  border: 1px solid #e8e1ff;
  background: #fff;
  cursor: pointer;
  text-align: left;
  transition: all 0.2s ease;
}

.option-item:hover {
  border-color: #cdb9ff;
  background: #faf7ff;
}

.option-item.active {
  border-color: #8b5cf6;
  box-shadow: 0 0 0 4px rgba(139, 92, 246, 0.12);
  background: #fbf8ff;
}

.option-label {
  width: 28px;
  height: 28px;
  flex-shrink: 0;
  border-radius: 50%;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: #f3efff;
  color: #7f56d9;
  font-size: 13px;
  font-weight: 800;
}

.option-text {
  color: #403752;
  font-size: 14px;
  line-height: 1.7;
}

.answer-textarea {
  width: 100%;
  resize: vertical;
  min-height: 140px;
  padding: 14px 16px;
  border-radius: 16px;
  border: 1px solid #ddd4ff;
  outline: none;
  font-size: 14px;
  color: #352d49;
  line-height: 1.7;
  transition: all 0.2s ease;
  box-sizing: border-box;
}

.answer-textarea:focus {
  border-color: #8b5cf6;
  box-shadow: 0 0 0 4px rgba(139, 92, 246, 0.12);
}

.dialog-hint {
  margin: 0;
  font-size: 12px;
}

.answer-result-row + .answer-result-row {
  margin-top: 12px;
}

.answer-result-row.align-start {
  align-items: flex-start;
}

.answer-result-key {
  flex-shrink: 0;
  min-width: 72px;
  color: #746c8f;
  font-size: 13px;
  font-weight: 700;
}

.answer-result-value {
  flex: 1;
  color: #352d49;
  font-size: 14px;
  line-height: 1.7;
  text-align: right;
}

.answer-result-value.multi-line {
  white-space: pre-wrap;
}

.dialog-toast {
  border-radius: 14px;
  padding: 12px 14px;
  font-size: 13px;
  font-weight: 700;
}

.dialog-toast.success {
  background: rgba(34, 197, 94, 0.12);
  color: #15803d;
}

.dialog-toast.error {
  background: rgba(239, 68, 68, 0.12);
  color: #dc2626;
}

.answer-dialog-footer {
  padding: 16px 24px 22px;
  border-top: 1px solid #f0ebff;
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

.dialog-btn {
  min-width: 108px;
  height: 44px;
  padding: 0 18px;
  border-radius: 14px;
  border: none;
  font-size: 14px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.2s ease;
}

.dialog-btn.secondary {
  background: #f5f3ff;
  color: #6d4cc0;
}

.dialog-btn.primary {
  background: linear-gradient(90deg, #8b5cf6 0%, #7c3aed 100%);
  color: #fff;
}

.dialog-btn:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

@media (max-width: 1100px) {
  .overview-grid {
    grid-template-columns: 1fr 1fr;
  }

  .path-meta-card {
    grid-column: 1 / -1;
  }
}

@media (max-width: 820px) {
  .progress-page {
    padding: 16px;
  }

  .hero-card,
  .content-header,
  .stage-top {
    flex-direction: column;
  }

  .hero-right {
    width: 100%;
  }

  .overview-grid {
    grid-template-columns: 1fr;
  }

  .content-scroll {
    max-height: none;
  }

  .stage-summary-wrap {
    width: 100%;
    align-items: stretch;
  }

  .task-top,
  .task-top-right,
  .answer-result-row {
    align-items: flex-start;
  }

  .task-top,
  .task-top-right,
  .answer-result-row,
  .answer-dialog-footer {
    flex-direction: column;
  }

  .question-item {
    flex-direction: column;
    align-items: flex-start;
  }

  .question-action {
    width: 100%;
  }

  .answer-dialog-mask {
    padding: 12px;
  }

  .answer-dialog-header,
  .answer-dialog-body,
  .answer-dialog-footer {
    padding-left: 16px;
    padding-right: 16px;
  }

  .answer-result-value {
    text-align: left;
  }

  .dialog-btn {
    width: 100%;
  }
}
</style>
