import json
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.config import get_settings
from app.services.ark_client import ArkTutorClient
from app.services.ppt_parser import extract_ppt_texts
from app.services.presets import PRESET_PROMPTS, COURSE_NAME

BASE_DIR = Path(__file__).resolve().parent.parent

app = FastAPI(title='KE Tutor System', version='3.0.0')
app.mount('/static', StaticFiles(directory=str(BASE_DIR / 'static')), name='static')
templates = Jinja2Templates(directory=str(BASE_DIR / 'templates'))


def parse_question_texts(raw_json: str) -> list[str]:
    if not raw_json.strip():
        return []
    try:
        data = json.loads(raw_json)
        if isinstance(data, list):
            return [str(x) for x in data]
    except Exception:
        pass
    return [raw_json]


@app.get('/', response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(
        'index.html',
        {'request': request, 'presets': PRESET_PROMPTS, 'course_name': COURSE_NAME},
    )


@app.get('/ppt-summary', response_class=HTMLResponse)
async def ppt_summary_page(request: Request):
    return templates.TemplateResponse(
        'ppt_summary.html',
        {'request': request, 'course_name': COURSE_NAME},
    )


@app.get('/api/health')
async def health_check():
    settings = get_settings()
    return {
        'code': 200,
        'message': 'ok',
        'model': settings.ark_model,
        'has_api_key': bool(settings.ark_api_key),
    }


@app.post('/api/solve-batch')
async def solve_batch(
    question_texts_json: str = Form(default='[]'),
    extra_requirement: str = Form(default=''),
    preset_key: str = Form(default='general_ke'),
    images: list[UploadFile] | None = File(default=None),
):
    settings = get_settings()
    if not settings.ark_api_key:
        raise HTTPException(status_code=500, detail='未配置 ARK_API_KEY，请先在 .env 中填写')

    question_texts = [q.strip() for q in parse_question_texts(question_texts_json) if q and str(q).strip()]
    if len(question_texts) > settings.max_text_question_count:
        raise HTTPException(status_code=400, detail=f'文本题目最多 {settings.max_text_question_count} 个')

    files = [f for f in (images or []) if f and f.filename]
    if not question_texts and not files:
        raise HTTPException(status_code=400, detail='题目文本和图片不能同时为空')
    if len(files) > settings.max_image_count:
        raise HTTPException(status_code=400, detail=f'最多上传 {settings.max_image_count} 张图片')

    parsed_images: list[tuple[bytes, str, str | None]] = []
    for file in files:
        if file.content_type and not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail=f'仅支持图片文件：{file.filename}')
        file_bytes = await file.read()
        if len(file_bytes) > settings.max_image_size_mb * 1024 * 1024:
            raise HTTPException(status_code=400, detail=f'单张图片不能超过 {settings.max_image_size_mb}MB：{file.filename}')
        parsed_images.append((file_bytes, file.filename or 'image.png', file.content_type))

    try:
        solver = ArkTutorClient()
        result = solver.solve_batch(
            question_texts=question_texts,
            extra_requirement=extra_requirement,
            preset_key=preset_key,
            images=parsed_images,
        )
        return {'code': 200, 'message': 'success', 'data': result.model_dump()}
    except HTTPException:
        raise
    except Exception as exc:
        return JSONResponse(status_code=500, content={'code': 500, 'message': 'model_call_failed', 'detail': str(exc)})


@app.post('/api/summarize-ppt')
async def summarize_ppt(
    ppt_file: UploadFile = File(...),
    extra_requirement: str = Form(default=''),
):
    settings = get_settings()
    if not settings.ark_api_key:
        raise HTTPException(status_code=500, detail='未配置 ARK_API_KEY，请先在 .env 中填写')
    if not ppt_file.filename.lower().endswith('.pptx'):
        raise HTTPException(status_code=400, detail='目前仅支持 .pptx 文件')

    file_bytes = await ppt_file.read()
    if len(file_bytes) > settings.max_ppt_size_mb * 1024 * 1024:
        raise HTTPException(status_code=400, detail=f'PPT 文件不能超过 {settings.max_ppt_size_mb}MB')

    try:
        slides = extract_ppt_texts(file_bytes)
        solver = ArkTutorClient()
        result = solver.summarize_ppt(ppt_name=ppt_file.filename, slides=slides, extra_requirement=extra_requirement)
        return {
            'code': 200,
            'message': 'success',
            'data': result.model_dump(),
            'meta': {'slide_count': len(slides), 'extracted_slides': slides},
        }
    except HTTPException:
        raise
    except Exception as exc:
        return JSONResponse(status_code=500, content={'code': 500, 'message': 'ppt_summary_failed', 'detail': str(exc)})
