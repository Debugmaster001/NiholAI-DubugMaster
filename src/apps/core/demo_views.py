"""Public, no-storage synthetic-document screening. Not an official taxonomy approval.

This local deterministic prototype works when the LLM API is disabled. It deliberately
reports 'candidate' rather than silently assuming all unspecified exclusions absent.
"""
from __future__ import annotations

from hashlib import sha256
from io import BytesIO
from time import perf_counter
import json

from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_POST
from django.views.decorators.cache import never_cache
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.enums import TA_LEFT
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer
from xml.sax.saxutils import escape

from src.apps.dashboard.prototype_rules import analyze_docs, VERSION, SOURCE

MAX_BYTES = 6 * 1024 * 1024
MAX_FILES = 5


def demo(request):
    return render(request, 'core/demo.html')


def _read_inputs(request):
    typed = (request.POST.get('text') or '').strip()
    if len(typed) > 120_000:
        raise ValueError('Kiritilgan matn juda uzun (120 000 belgidan oshmasin)')
    uploads = request.FILES.getlist('documents')
    if len(uploads) > MAX_FILES:
        raise ValueError('Bir vaqtda 5 tagacha fayl yuklash mumkin')
    docs = []
    dig = sha256()
    if typed:
        docs.append({'name': 'Kiritilgan matn', 'pages': [{'page': 1, 'text': typed}]})
        dig.update(typed.encode('utf8'))
    for uploaded in uploads:
        name = uploaded.name.rsplit('/',1)[-1].rsplit('\\',1)[-1]
        if uploaded.size > MAX_BYTES:
            raise ValueError(f'{name}: fayl 6 MB dan katta')
        data = uploaded.read(MAX_BYTES + 1)
        if len(data) > MAX_BYTES:
            raise ValueError(f'{name}: fayl 6 MB dan katta')
        dig.update(data)
        suffix = name.lower().rsplit('.', 1)[-1]
        if suffix == 'txt':
            try: content = data.decode('utf-8-sig')
            except UnicodeDecodeError: raise ValueError(f'{name}: TXT UTF-8 formatida bo‘lishi kerak')
            pages = [{'page': 1, 'text': content[:120000]}]
        elif suffix == 'pdf':
            try:
                from pypdf import PdfReader
                reader = PdfReader(BytesIO(data))
                if len(reader.pages) > 35: raise ValueError(f'{name}: 35 betdan oshmasin')
                pages = [{'page': i+1,'text': (p.extract_text() or '')[:12000]}
                         for i, p in enumerate(reader.pages)]
            except ValueError: raise
            except Exception: raise ValueError(f'{name}: PDF matnini o‘qib bo‘lmadi')
        else:
            raise ValueError(f'{name}: ochiq demoda faqat TXT va matnli PDF qo‘llanadi')
        docs.append({'name': name, 'pages': pages})
    if not docs:
        raise ValueError('Matn kiriting yoki PDF/TXT fayl yuklang')
    return docs, dig.hexdigest()[:16]


def _run(request):
    docs, digest = _read_inputs(request)
    start = perf_counter()
    result = analyze_docs(docs)
    result.update(input_sha256=digest, elapsed_ms=round(1000*(perf_counter()-start), 1),
                  document_count=len(docs), review_status='NEEDS_HUMAN_REVIEW',
                  engine='LOCAL_RULES_NO_LLM')
    return result


@require_POST
@never_cache
def analyze(request):
    try:
        result = _run(request)
    except ValueError as e:
        return JsonResponse({'error': str(e)}, status=400)
    response = JsonResponse(result, json_dumps_params={'ensure_ascii':False})
    response['Cache-Control'] = 'no-store'
    return response


@require_POST
@never_cache
def report(request):
    try:
        r = _run(request)
    except ValueError as e:
        return JsonResponse({'error': str(e)}, status=400)
    buf = BytesIO()
    story = []
    import os
    font = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
    if os.path.exists(font):
        if 'DejaVu' not in pdfmetrics.getRegisteredFontNames():
            pdfmetrics.registerFont(TTFont('DejaVu', font))
        font_name='DejaVu'
    else: font_name='Helvetica'
    sty = getSampleStyleSheet()
    sty['Normal'].fontName=font_name
    sty['Normal'].fontSize=9
    sty['Normal'].leading=14
    sty['Title'].fontName=font_name
    sty['Heading2'].fontName=font_name
    def line(value): story.append(Paragraph(escape(str(value)),sty['Normal']));story.append(Spacer(1,9))
    story.append(Paragraph('NIHOL AI · DubugMaster',sty['Title']))
    line('Prototip / auditga tayyorlash uchun skrining; yakuniy qaror emas')
    line('Natija: '+r['verdict']+' — '+r['reason'])
    line('Tekshirilgan fayllar: '+str(r['document_count']))
    line('Kirish ma’lumoti SHA-256 (qisqartirilgan): '+r['input_sha256'])
    line('Qoidalar versiyasi: '+r['policy_version'])
    line('Stop-faktorlar: '+str(r['stop_count'])+' | yashil mezonlar: '+str(r['green_count']))
    story.append(Paragraph('Hujjat sahifalaridan dalillar',sty['Heading2']))
    for h in r['evidence']+r['cautions']:
        line(f"{h['rule_id']} · {h['label']} — {h['filename']} (sahifa {h['page']})")
        line('Dalil: '+h['quote'][:380])
        if h.get('note'):line('Ogohlantirish: '+h['note'])
    if not r['evidence'] and not r['cautions']:
        line('Dalil topilmadi, qo‘shimcha hujjat kerak.')
    story.append(Paragraph('Inson tekshiruvi',sty['Heading2']))
    line('Holat: KUTILMOQDA. Bank mutaxassisi hujjat va taksonomiya bandlarini tasdiqlashi kerak.')
    line('Muhim: '+r['disclaimer'])
    line('Manba haqida: '+SOURCE)
    SimpleDocTemplate(buf,pagesize=A4,rightMargin=42,leftMargin=42).build(story)
    response=HttpResponse(buf.getvalue(),content_type='application/pdf')
    response['Content-Disposition']='attachment; filename="NiholAI_DubugMaster_Review.pdf"'
    response['Cache-Control']='no-store'
    return response


def health(request):
    return JsonResponse({'status':'ok','name':'Nihol AI','team':'DubugMaster','policy_version':VERSION,
                        'public_demo':'local rules; no confidential data'})
