import base64
import json
import mimetypes
import re
from typing import Optional

from openai import OpenAI

from app.config import get_settings
from app.models import BatchSolveResponse, QuestionItem, QuestionResult, PPTSummaryResult
from app.services.presets import COURSE_NAME, PRESET_PROMPTS


SYSTEM_PROMPT = f"""
你是{COURSE_NAME}的专用智能助教。
你的回答对象是计算机系研究生，要求：
1. 术语准确，解释严谨。
2. 优先围绕知识工程课程内容回答，不要泛化到无关学科。
3. 回答时先给结论，再给分析。
4. 尽量指出题目和课程知识框架之间的对应关系。
5. 若题目不完整，要明确说明假设。
6. 输出必须是合法 JSON，不要输出 JSON 之外的任何内容。
""".strip()


class ArkTutorClient:
    def __init__(self):
        settings = get_settings()
        self.client = OpenAI(api_key=settings.ark_api_key, base_url=settings.ark_base_url)
        self.model = settings.ark_model

    def _bytes_to_data_url(self, image_bytes: bytes, image_filename: str, image_content_type: Optional[str] = None) -> str:
        mime_type = image_content_type
        if not mime_type:
            mime_type, _ = mimetypes.guess_type(image_filename)
        if not mime_type:
            mime_type = 'image/png'
        b64 = base64.b64encode(image_bytes).decode('utf-8')
        return f'data:{mime_type};base64,{b64}'

    def _parse_json_text(self, text: str) -> dict:
        text = text.strip()
        try:
            return json.loads(text)
        except Exception:
            match = re.search(r'\{.*\}', text, re.S)
            if match:
                return json.loads(match.group(0))
            raise ValueError(f'模型返回的内容不是合法 JSON：{text[:500]}')

    def _call_json(self, prompt_text: str, image_contexts: list[tuple[bytes, str, Optional[str]]] | None = None) -> dict:
        content = [{'type': 'input_text', 'text': prompt_text}]
        for image_bytes, filename, content_type in (image_contexts or []):
            content.append({
                'type': 'input_image',
                'image_url': self._bytes_to_data_url(image_bytes, filename, content_type),
            })
        response = self.client.responses.create(
            model=self.model,
            input=[
                {'role': 'system', 'content': [{'type': 'input_text', 'text': SYSTEM_PROMPT}]},
                {'role': 'user', 'content': content},
            ],
        )
        return self._parse_json_text(response.output_text)

    def split_questions_from_images(self, images: list[tuple[bytes, str, Optional[str]]]) -> list[dict]:
        if not images:
            return []
        prompt = """
请读取输入图片中的题目内容。
要求：
1. 一张图中如果有多个题目，必须拆分成多个题目。
2. 如果图片里只有一个题目，则输出一个题目。
3. 尽量保留题干、选项、图示说明、约束条件。
4. 如果图中文字不完整，也要尽量提取，并标注“图片题目可能不完整”。

请严格输出 JSON：
{
  "questions": [
    {
      "question_id": "img1_q1",
      "source_name": "原图片文件名",
      "recognized_question": "题目文本"
    }
  ]
}
""".strip()
        payload = self._call_json(prompt, images)
        return payload.get('questions', [])

    def solve_one_question(self, question_id: str, source_type: str, source_name: str, recognized_question: str, preset_key: str, extra_requirement: str = '', image_contexts: list[tuple[bytes, str, Optional[str]]] | None = None) -> QuestionResult:
        preset_text = PRESET_PROMPTS.get(preset_key, PRESET_PROMPTS['general_ke'])['prompt']
        prompt = f"""
请解答下面这道《知识工程》课程相关题目。

【课程场景】
{COURSE_NAME}

【解题风格要求】
{preset_text}

【额外要求】
{extra_requirement.strip() or '无'}

【题目】
{recognized_question.strip()}

请严格输出 JSON：
{{
  "question_id": "{question_id}",
  "source_type": "{source_type}",
  "source_name": "{source_name}",
  "recognized_question": "",
  "topic_tags": [],
  "direct_answer": "",
  "detailed_explanation": "",
  "solving_outline": [],
  "key_points": [],
  "common_confusions": [],
  "relation_to_course": "",
  "extension_questions": [],
  "confidence": 0.0
}}
""".strip()
        payload = self._call_json(prompt, image_contexts=image_contexts)
        payload.setdefault('question_id', question_id)
        payload.setdefault('source_type', source_type)
        payload.setdefault('source_name', source_name)
        payload.setdefault('recognized_question', recognized_question)
        return QuestionResult(**payload)

    def solve_batch(self, question_texts: list[str], extra_requirement: str, preset_key: str, images: list[tuple[bytes, str, Optional[str]]]) -> BatchSolveResponse:
        normalized_questions: list[dict] = []
        index = 1
        for q in question_texts:
            text = (q or '').strip()
            if not text:
                continue
            normalized_questions.append({
                'question_id': f'text_q{index}',
                'source_type': 'text',
                'source_name': f'文本题目{index}',
                'recognized_question': text,
                'image_contexts': [],
            })
            index += 1

        image_questions = self.split_questions_from_images(images)
        for item in image_questions:
            source_name = item.get('source_name') or '图片题目'
            matched_images = [img for img in images if img[1] == source_name] or images[:1]
            normalized_questions.append({
                'question_id': item.get('question_id') or f'img_q{len(normalized_questions)+1}',
                'source_type': 'image',
                'source_name': source_name,
                'recognized_question': item.get('recognized_question', '').strip(),
                'image_contexts': matched_images,
            })

        results = []
        question_items = []
        for item in normalized_questions:
            if not item['recognized_question']:
                continue
            question_items.append(QuestionItem(
                question_id=item['question_id'],
                source_type=item['source_type'],
                source_name=item['source_name'],
                recognized_question=item['recognized_question'],
            ))
            result = self.solve_one_question(
                question_id=item['question_id'],
                source_type=item['source_type'],
                source_name=item['source_name'],
                recognized_question=item['recognized_question'],
                preset_key=preset_key,
                extra_requirement=extra_requirement,
                image_contexts=item.get('image_contexts') or None,
            )
            results.append(result)

        return BatchSolveResponse(
            course_name='知识工程',
            total_questions=len(results),
            question_list=question_items,
            results=results,
        )

    def summarize_ppt(self, ppt_name: str, slides: list[dict], extra_requirement: str = '') -> PPTSummaryResult:
        slide_text = []
        for slide in slides:
            slide_text.append(
                f"第{slide['slide_no']}页｜标题：{slide['title']}\n{slide['text'] or '（本页几乎无文本）'}"
            )
        merged = '\n\n'.join(slide_text)
        prompt = f"""
下面是一份《知识工程》课程相关 PPT 的逐页文本抽取结果，请完成课程知识点总结。

【PPT 文件名】
{ppt_name}

【额外要求】
{extra_requirement.strip() or '无'}

【逐页内容】
{merged[:24000]}

请严格输出 JSON：
{{
  "course_theme": "",
  "overall_summary": "",
  "chapter_outline": [],
  "core_knowledge_points": [],
  "easy_confusions": [],
  "review_questions": [],
  "slide_summaries": [
    {{
      "slide_no": 1,
      "title": "",
      "summary": "",
      "knowledge_points": []
    }}
  ]
}}
""".strip()
        payload = self._call_json(prompt)
        return PPTSummaryResult(**payload)
