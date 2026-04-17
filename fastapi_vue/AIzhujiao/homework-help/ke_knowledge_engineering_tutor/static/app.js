const form = document.getElementById('solveForm');
const dropzone = document.getElementById('dropzone');
const imageInput = document.getElementById('images');
const fileList = document.getElementById('fileList');
const statusBox = document.getElementById('status');
const submitBtn = document.getElementById('submitBtn');
const clearBtn = document.getElementById('clearBtn');
const copyBtn = document.getElementById('copyBtn');
const presetHelp = document.getElementById('presetHelp');
const presetKeyInput = document.getElementById('preset_key');
const questionList = document.getElementById('questionList');
const addQuestionBtn = document.getElementById('addQuestionBtn');
const emptyState = document.getElementById('emptyState');
const resultArea = document.getElementById('resultArea');
const questionTabs = document.getElementById('questionTabs');

let selectedFiles = [];
let batchResults = [];
let activeIndex = -1;
let copyText = '';

function formatFileSize(bytes) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / 1024 / 1024).toFixed(2)} MB`;
}

function setStatus(message, type = 'normal') {
  statusBox.textContent = message;
  statusBox.className = 'status';
  if (type === 'error') statusBox.classList.add('error');
  if (type === 'success') statusBox.classList.add('success');
}

function createQuestionCard(value = '') {
  const index = questionList.children.length + 1;
  const wrapper = document.createElement('div');
  wrapper.className = 'question-item';
  wrapper.innerHTML = `
    <div class="question-item-head">
      <div class="question-item-title">文本题目 ${index}</div>
      <button type="button" class="text-link remove-question">删除</button>
    </div>
    <textarea rows="4" class="question-text" placeholder="输入一个知识工程课程相关题目，例如：请比较规则推理与基于知识图谱推理的差异。">${value}</textarea>
  `;
  wrapper.querySelector('.remove-question').addEventListener('click', () => {
    wrapper.remove();
    refreshQuestionTitles();
  });
  questionList.appendChild(wrapper);
}

function refreshQuestionTitles() {
  [...questionList.querySelectorAll('.question-item')].forEach((item, idx) => {
    item.querySelector('.question-item-title').textContent = `文本题目 ${idx + 1}`;
  });
}

function syncInputFiles() {
  const dt = new DataTransfer();
  selectedFiles.forEach(file => dt.items.add(file));
  imageInput.files = dt.files;
}

function renderFileList() {
  fileList.innerHTML = '';
  if (!selectedFiles.length) return;
  selectedFiles.forEach((file, index) => {
    const item = document.createElement('div');
    item.className = 'file-item';
    item.innerHTML = `
      <div class="file-name">${file.name}</div>
      <div class="file-meta">${formatFileSize(file.size)}</div>
      <button type="button" class="remove-file" data-index="${index}">移除</button>
    `;
    fileList.appendChild(item);
  });
}

function addFiles(files) {
  for (const file of files) {
    if (!file.type.startsWith('image/')) continue;
    const exists = selectedFiles.some(f => f.name === file.name && f.size === file.size && f.lastModified === file.lastModified);
    if (!exists) selectedFiles.push(file);
  }
  syncInputFiles();
  renderFileList();
}

function getQuestionTexts() {
  return [...document.querySelectorAll('.question-text')]
    .map(el => el.value.trim())
    .filter(Boolean);
}

function renderList(targetId, list) {
  const target = document.getElementById(targetId);
  target.innerHTML = '';
  (list || []).forEach(item => {
    const li = document.createElement(targetId === 'solving_outline' ? 'li' : 'li');
    li.textContent = item;
    target.appendChild(li);
  });
}

function buildCopyText(result) {
  return [
    `识别题目：${result.recognized_question || ''}`,
    `来源：${result.source_type || ''} / ${result.source_name || ''}`,
    `直接答案：${result.direct_answer || ''}`,
    `详细解析：${result.detailed_explanation || ''}`,
    `课程关联：${result.relation_to_course || ''}`,
    `主题标签：${(result.topic_tags || []).join('，')}`,
    `解题提纲：${(result.solving_outline || []).join('；')}`,
    `关键知识点：${(result.key_points || []).join('；')}`,
    `常见混淆点：${(result.common_confusions || []).join('；')}`,
    `延伸追问：${(result.extension_questions || []).join('；')}`,
  ].join('\n\n');
}

function showResult(index) {
  if (index < 0 || index >= batchResults.length) return;
  activeIndex = index;
  const result = batchResults[index];

  document.querySelectorAll('.question-tab').forEach((tab, idx) => {
    tab.classList.toggle('active', idx === index);
  });

  document.getElementById('recognized_question').textContent = result.recognized_question || '';
  document.getElementById('source_info').textContent = `${result.source_type || ''}｜${result.source_name || ''}`;
  document.getElementById('confidence').textContent = String(result.confidence ?? '');
  document.getElementById('direct_answer').textContent = result.direct_answer || '';
  document.getElementById('detailed_explanation').textContent = result.detailed_explanation || '';
  document.getElementById('relation_to_course').textContent = result.relation_to_course || '';
  renderList('topic_tags', result.topic_tags || []);
  renderList('solving_outline', result.solving_outline || []);
  renderList('key_points', result.key_points || []);
  renderList('common_confusions', result.common_confusions || []);
  renderList('extension_questions', result.extension_questions || []);

  copyText = buildCopyText(result);
  copyBtn.disabled = false;
}

function renderTabs(results) {
  questionTabs.innerHTML = '';
  results.forEach((result, idx) => {
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'question-tab';
    btn.innerHTML = `
      <div class="question-tab-title">题目 ${idx + 1}</div>
      <div class="question-tab-sub">${(result.recognized_question || '').slice(0, 44) || '未识别题目'}...</div>
    `;
    btn.addEventListener('click', () => showResult(idx));
    questionTabs.appendChild(btn);
  });
}

fileList.addEventListener('click', (event) => {
  if (!event.target.classList.contains('remove-file')) return;
  const index = Number(event.target.dataset.index);
  selectedFiles.splice(index, 1);
  syncInputFiles();
  renderFileList();
});

dropzone.addEventListener('click', () => imageInput.click());
imageInput.addEventListener('change', () => addFiles(imageInput.files));
['dragenter', 'dragover'].forEach(type => {
  dropzone.addEventListener(type, (event) => {
    event.preventDefault();
    dropzone.classList.add('dragover');
  });
});
['dragleave', 'drop'].forEach(type => {
  dropzone.addEventListener(type, (event) => {
    event.preventDefault();
    dropzone.classList.remove('dragover');
  });
});
dropzone.addEventListener('drop', (event) => addFiles(event.dataTransfer.files));

addQuestionBtn.addEventListener('click', () => createQuestionCard(''));
createQuestionCard('');
createQuestionCard('');

document.querySelectorAll('.preset-chip').forEach(chip => {
  chip.addEventListener('click', () => {
    document.querySelectorAll('.preset-chip').forEach(c => c.classList.remove('active'));
    chip.classList.add('active');
    presetKeyInput.value = chip.dataset.key;
    presetHelp.textContent = chip.dataset.prompt;
  });
});

form.addEventListener('submit', async (event) => {
  event.preventDefault();
  submitBtn.disabled = true;
  copyBtn.disabled = true;
  setStatus('正在解析题目并调用模型，请稍候…');

  const formData = new FormData();
  formData.append('preset_key', presetKeyInput.value);
  formData.append('extra_requirement', document.getElementById('extra_requirement').value || '');
  formData.append('question_texts_json', JSON.stringify(getQuestionTexts()));
  selectedFiles.forEach(file => formData.append('images', file));

  try {
    const response = await fetch('/api/solve-batch', { method: 'POST', body: formData });
    const result = await response.json();
    if (!response.ok || result.code !== 200) throw new Error(result.detail || result.message || '请求失败');
    batchResults = result.data.results || [];
    if (!batchResults.length) throw new Error('未得到可展示的题目结果');
    emptyState.classList.add('hidden');
    resultArea.classList.remove('hidden');
    renderTabs(batchResults);
    showResult(0);
    setStatus(`解答完成，共生成 ${batchResults.length} 个题目的解析。`, 'success');
  } catch (error) {
    setStatus(`发生错误：${error.message}`, 'error');
  } finally {
    submitBtn.disabled = false;
  }
});

copyBtn.addEventListener('click', async () => {
  if (!copyText) return;
  await navigator.clipboard.writeText(copyText);
  setStatus('当前题目解析已复制。', 'success');
});

clearBtn.addEventListener('click', () => {
  form.reset();
  questionList.innerHTML = '';
  createQuestionCard('');
  createQuestionCard('');
  selectedFiles = [];
  syncInputFiles();
  renderFileList();
  batchResults = [];
  activeIndex = -1;
  copyText = '';
  copyBtn.disabled = true;
  resultArea.classList.add('hidden');
  emptyState.classList.remove('hidden');
  setStatus('已清空内容。');
  document.querySelectorAll('.preset-chip').forEach(c => c.classList.remove('active'));
  const firstChip = document.querySelector('.preset-chip');
  if (firstChip) {
    firstChip.classList.add('active');
    presetKeyInput.value = firstChip.dataset.key;
    presetHelp.textContent = firstChip.dataset.prompt;
  }
});
