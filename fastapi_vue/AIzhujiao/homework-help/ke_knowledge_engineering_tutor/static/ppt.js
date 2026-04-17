const pptForm = document.getElementById('pptForm');
const pptDropzone = document.getElementById('pptDropzone');
const pptInput = document.getElementById('ppt_file');
const pptFileInfo = document.getElementById('pptFileInfo');
const pptStatus = document.getElementById('pptStatus');
const pptSubmitBtn = document.getElementById('pptSubmitBtn');
const pptClearBtn = document.getElementById('pptClearBtn');
const pptCopyBtn = document.getElementById('pptCopyBtn');
const pptEmptyState = document.getElementById('pptEmptyState');
const pptResult = document.getElementById('pptResult');

let selectedPpt = null;
let pptCopyText = '';

function setPptStatus(message, type = 'normal') {
  pptStatus.textContent = message;
  pptStatus.className = 'status';
  if (type === 'error') pptStatus.classList.add('error');
  if (type === 'success') pptStatus.classList.add('success');
}

function renderPptFileInfo() {
  pptFileInfo.innerHTML = '';
  if (!selectedPpt) return;
  const item = document.createElement('div');
  item.className = 'file-item';
  item.innerHTML = `
    <div class="file-name">${selectedPpt.name}</div>
    <div class="file-meta">${(selectedPpt.size / 1024 / 1024).toFixed(2)} MB</div>
    <button type="button" class="remove-file" id="removePptBtn">移除</button>
  `;
  pptFileInfo.appendChild(item);
  document.getElementById('removePptBtn').addEventListener('click', () => {
    selectedPpt = null;
    pptInput.value = '';
    renderPptFileInfo();
  });
}

function handlePptFile(file) {
  if (!file) return;
  const valid = file.name.toLowerCase().endsWith('.pptx');
  if (!valid) {
    setPptStatus('只支持 .pptx 文件。', 'error');
    return;
  }
  selectedPpt = file;
  renderPptFileInfo();
}

pptDropzone.addEventListener('click', () => pptInput.click());
pptInput.addEventListener('change', () => handlePptFile(pptInput.files[0]));
['dragenter', 'dragover'].forEach(type => {
  pptDropzone.addEventListener(type, (event) => {
    event.preventDefault();
    pptDropzone.classList.add('dragover');
  });
});
['dragleave', 'drop'].forEach(type => {
  pptDropzone.addEventListener(type, (event) => {
    event.preventDefault();
    pptDropzone.classList.remove('dragover');
  });
});
pptDropzone.addEventListener('drop', (event) => handlePptFile(event.dataTransfer.files[0]));

function renderList(id, list, ordered = false) {
  const target = document.getElementById(id);
  target.innerHTML = '';
  (list || []).forEach(item => {
    const li = document.createElement('li');
    li.textContent = item;
    target.appendChild(li);
  });
}

function renderSlideSummaries(slides) {
  const container = document.getElementById('slide_summaries');
  container.innerHTML = '';
  (slides || []).forEach(slide => {
    const card = document.createElement('div');
    card.className = 'slide-card';
    card.innerHTML = `
      <div class="slide-card-title">第${slide.slide_no}页｜${slide.title || '未命名页'}</div>
      <div class="content">${slide.summary || ''}</div>
      <ul>${(slide.knowledge_points || []).map(x => `<li>${x}</li>`).join('')}</ul>
    `;
    container.appendChild(card);
  });
}

function buildPptCopyText(data) {
  const slideLines = (data.slide_summaries || []).map(slide => {
    return `第${slide.slide_no}页 ${slide.title || ''}
摘要：${slide.summary || ''}
知识点：${(slide.knowledge_points || []).join('；')}`;
  }).join('\n\n');

  return [
    `课程主题：${data.course_theme || ''}`,
    `整体总结：${data.overall_summary || ''}`,
    `章节结构：${(data.chapter_outline || []).join('；')}`,
    `核心知识点：${(data.core_knowledge_points || []).join('；')}`,
    `易混概念：${(data.easy_confusions || []).join('；')}`,
    `复习问题：${(data.review_questions || []).join('；')}`,
    slideLines,
  ].join('\n\n');
}

pptForm.addEventListener('submit', async (event) => {
  event.preventDefault();
  if (!selectedPpt) {
    setPptStatus('请先上传一个 .pptx 文件。', 'error');
    return;
  }
  pptSubmitBtn.disabled = true;
  pptCopyBtn.disabled = true;
  setPptStatus('正在抽取 PPT 文本并生成知识点总结，请稍候…');

  const formData = new FormData();
  formData.append('ppt_file', selectedPpt);
  formData.append('extra_requirement', document.getElementById('ppt_extra_requirement').value || '');

  try {
    const response = await fetch('/api/summarize-ppt', { method: 'POST', body: formData });
    const result = await response.json();
    if (!response.ok || result.code !== 200) throw new Error(result.detail || result.message || '请求失败');
    const data = result.data;
    document.getElementById('course_theme').textContent = data.course_theme || '';
    document.getElementById('overall_summary').textContent = data.overall_summary || '';
    renderList('chapter_outline', data.chapter_outline || []);
    renderList('core_knowledge_points', data.core_knowledge_points || []);
    renderList('easy_confusions', data.easy_confusions || []);
    renderList('review_questions', data.review_questions || []);
    renderSlideSummaries(data.slide_summaries || []);
    pptEmptyState.classList.add('hidden');
    pptResult.classList.remove('hidden');
    pptCopyText = buildPptCopyText(data);
    pptCopyBtn.disabled = false;
    setPptStatus(`总结完成，共处理 ${result.meta?.slide_count || 0} 页。`, 'success');
  } catch (error) {
    setPptStatus(`发生错误：${error.message}`, 'error');
  } finally {
    pptSubmitBtn.disabled = false;
  }
});

pptCopyBtn.addEventListener('click', async () => {
  if (!pptCopyText) return;
  await navigator.clipboard.writeText(pptCopyText);
  setPptStatus('总结结果已复制。', 'success');
});

pptClearBtn.addEventListener('click', () => {
  pptForm.reset();
  selectedPpt = null;
  pptCopyText = '';
  pptCopyBtn.disabled = true;
  pptResult.classList.add('hidden');
  pptEmptyState.classList.remove('hidden');
  renderPptFileInfo();
  setPptStatus('已清空内容。');
});
