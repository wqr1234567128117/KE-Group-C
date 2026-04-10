// vue-project\src\api\index.js
import axios from 'axios';

// 1. 配置基础地址
const BASE_URL = 'http://127.0.0.1:8000'; // 确保后端端口是 8000
const apiClient = axios.create({
  baseURL: BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 2. 请求拦截器 (自动注入 Token)
apiClient.interceptors.request.use(config => {
  const user = localStorage.getItem('user_info');
  if (user) {
    const { token } = JSON.parse(user);
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
  }
  return config;
});

// 3. 定义 API 接口 (已根据后端 api.py 修正)
export default {
  // --- 用户模块 ---
  login(username, password) {
    return apiClient.post('/api/login', { username, password });
  },
  register(realName, major, username, password) {
    // 注意：后端需要 real_name 和 major 字段
    return apiClient.post('/api/register', { 
      real_name: realName, 
      major, 
      username, 
      password 
    });
  },
  getUserInfo(userId) {
    return apiClient.get(`/api/users/${userId}`);
  },

  // --- 智能问答模块 ---
  // 注意：ask 接口不需要传 user_id，后端从 token 解析；需要传 session_id 来续聊
  askQuestion(question, sessionId = null) {
    return apiClient.post('/api/ask', { 
      question, 
      session_id: sessionId // 如果为空，后端会自动生成
    });
  },
  // 获取用户的所有会话列表 (用于左侧会话栏)
  getConversations(userId) {
    return apiClient.get(`/api/conversations/${userId}`);
  },
  // 获取特定会话的详细消息
  getConversationDetail(sessionId) {
    return apiClient.get(`/api/conversation/${sessionId}`);
  },
  // 获取热门问题
  getHotQuestions() {
    return apiClient.get('/api/hot-questions');
  },
  // 获取问题建议 (写死的推荐)
  getSuggestions() {
    return apiClient.get('/api/question-suggestions');
  },

  // --- 作业辅导模块 ---
  getHomeworkHelp(content) {
    return apiClient.post('/api/homework-help', { content });
  },
  // 新增：获取作业历史
  getHomeworkHistory(userId) {
    return apiClient.get(`/api/homework-history/${userId}`);
  },

  // --- 学习路径模块 ---
  generatePath(data) {
    const {
      user_id,
      domain,
      level,
      goal,
      background_plan,
    } = data

    return apiClient.post('/api/learning-path/generate', {
      user_id,
      domain,
      level,
      goal,
      background_plan,
    })
  },
  // 获取路径列表
  getPaths(userId) {
    return apiClient.get(`/api/learning-path/${userId}`);
  },
  // 获取路径详情 (包含任务)
  getPathDetail(pathId) {
    return apiClient.get(`/api/learning-path/detail/${pathId}`);
  },

  // --- 学习进度与任务模块 ---
  // 获取任务下的题目列表
  getTaskQuestions(taskId) {
    return apiClient.get(`/api/tasks/${taskId}/questions`);
  },
  // 提交题目答案
  submitAnswer(questionId, userAnswer) {
    return apiClient.post('/api/tasks/answer', { 
      question_id: questionId, 
      user_answer: userAnswer 
    });
  },
  // 学习打卡
  checkIn(date, studyHours) {
    return apiClient.post('/api/progress/check-in', { 
      date, 
      study_hours: studyHours 
    });
  },
  // 获取进度汇总
  getProgress(userId) {
    return apiClient.get(`/api/progress/${userId}`);
  },
  // 获取打卡记录 (原接口为 /api/progress/check-in/${userId}，但后端代码中未定义此接口，此处保留原样，实际可能需要调整)
  // 注意：后端代码中没有提供按用户获取打卡记录的独立接口，只有通用的 getProgress
  // 如果后端未实现，前端调用 getProgress 即可
  getCheckInRecords(userId) {
    return apiClient.get(`/api/progress/${userId}`); // 复用进度接口，或者后端需补充接口
  },
};