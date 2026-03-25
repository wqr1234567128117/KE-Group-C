import axios from 'axios';

// 后端基础地址
const BASE_URL = 'http://127.0.0.1:8000';

const apiClient = axios.create({
  baseURL: BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 简单拦截器：可在请求头添加 Token (虽然当前后端是演示版，预留位置)
apiClient.interceptors.request.use(config => {
  const user = localStorage.getItem('user_info');
  if (user) {
    const { token } = JSON.parse(user);
    if (token) config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export default {
  // --- 用户模块 ---
  login(username, password) {
    return apiClient.post('/api/login', { username, password });
  },
  register(userData) {
    return apiClient.post('/api/register', userData);
  },
  getUserInfo(userId) {
    return apiClient.get(`/api/users/${userId}`);
  },

  // --- 智能问答模块 ---
  askQuestion(userId, question) {
    return apiClient.post('/api/ask', { user_id: userId, question });
  },
  getHistory(userId) {
    return apiClient.get(`/api/history/${userId}`);
  },
  clearHistory(userId) {
    return apiClient.delete(`/api/history/${userId}`);
  },
  getHotQuestions() {
    return apiClient.get('/api/hot-questions');
  },
  getSuggestions() {
    return apiClient.get('/api/question-suggestions');
  },
  getHomeworkHelp(userId, question) {
    return apiClient.post('/api/homework-help', { user_id: userId, question });
  },

  // --- 学习路径模块 ---
  generatePath(userId, goal, level, time) {
    return apiClient.post('/api/learning-path/generate', {
      user_id: userId,
      goal,
      level,
      available_time_per_week: time
    });
  },
  getPath(userId) {
    return apiClient.get(`/api/learning-path/${userId}`);
  },

  // --- 学习进度模块 ---
  getProgress(userId) {
    return apiClient.get(`/api/progress/${userId}`);
  },
  checkIn(userId, date, hours) {
    return apiClient.post('/api/progress/check-in', { user_id: userId, date, study_hours: hours });
  },
  getCheckInRecords(userId) {
    return apiClient.get(`/api/progress/check-in/${userId}`);
  },
  updateTask(userId, taskName, status) {
    return apiClient.post('/api/progress/task-update', { user_id: userId, task_name: taskName, status });
  }
};