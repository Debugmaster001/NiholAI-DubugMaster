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


PDF_LANG = {
'uz': {'intro':'Prototip skriningi; yakuniy bank qarori emas','result':'Natija','docs':'Tekshirilgan fayllar','hash':'Kirish SHA-256','version':'Qoidalar versiyasi','stop':'Stop-faktorlar','green':'yashil mezonlar','evidence':'Hujjatdan dalillar','page':'sahifa','quote':'Dalil','caution':'Ogohlantirish','none':'Dalil topilmadi.','review':'Inson tekshiruvi','pending':'KUTILMOQDA: mutaxassis asl manbani tekshirishi kerak.','important':'Muhim','source':'Manba','disclaimer':'Bu prototip skriningi, yakuniy sertifikat yoki kredit qarori emas.','reason':{'NOT_GREEN':'Istisno faoliyat belgisi topildi. Mutaxassis tasdig‘i kerak.','GREEN_CANDIDATE':'Yashil faoliyat belgisi topildi. Yakuniy baholash uchun inson tekshiruvi shart.','REVIEW_REQUIRED':'Qo‘shimcha hujjatlar va tekshiruv kerak.','NO_DATA':'O‘qiladigan matn yo‘q.'}},
'en':{'intro':'Prototype screening; not a final bank decision','result':'Result','docs':'Documents screened','hash':'Input SHA-256','version':'Rule set version','stop':'Exclusion signals','green':'green criteria','evidence':'Evidence from source documents','page':'page','quote':'Evidence','caution':'Caution','none':'No supporting evidence found.','review':'Human review','pending':'PENDING: a specialist must verify source evidence.','important':'Important','source':'Source','disclaimer':'Prototype screening, not a green certificate or credit decision.','reason':{'NOT_GREEN':'An excluded activity was flagged; specialist confirmation required.','GREEN_CANDIDATE':'Green activity evidence found; human verification required.','REVIEW_REQUIRED':'Further documents and assessment required.','NO_DATA':'No readable text.'}},
'ru':{'intro':'Предварительный скрининг; не окончательное решение банка','result':'Результат','docs':'Проверено документов','hash':'Входной SHA-256','version':'Версия правил','stop':'Критерии исключения','green':'зелёные критерии','evidence':'Доказательства из документов','page':'стр.','quote':'Доказательство','caution':'Предупреждение','none':'Подтверждений не найдено.','review':'Проверка специалистом','pending':'ОЖИДАЕТСЯ: специалист должен проверить первоисточники.','important':'Важно','source':'Источник','disclaimer':'Предварительный скрининг, не зелёный сертификат и не кредитное решение.','reason':{'NOT_GREEN':'Обнаружена исключённая деятельность; требуется подтверждение специалиста.','GREEN_CANDIDATE':'Есть признаки зелёной деятельности; требуется проверка специалиста.','REVIEW_REQUIRED':'Нужны дополнительные документы и проверка.','NO_DATA':'Нет читаемого текста.'}}
}
RULE_TITLES = {'S01': {'en': 'Weapons and ammunition', 'ru': 'Оружие и боеприпасы'}, 'S02': {'en': 'Alcohol production', 'ru': 'Производство алкоголя'}, 'S03': {'en': 'Tobacco products', 'ru': 'Табачные изделия'}, 'S04': {'en': 'Gambling activities', 'ru': 'Азартные игры'}, 'S05': {'en': 'Nuclear power generation', 'ru': 'Производство атомной энергии'}, 'S06': {'en': 'Radioactive materials', 'ru': 'Радиоактивные материалы'}, 'S07': {'en': 'Asbestos-related activities', 'ru': 'Деятельность с асбестом'}, 'S08': {'en': 'Coal mining', 'ru': 'Добыча угля'}, 'S09': {'en': 'Coal-fired power generation', 'ru': 'Угольная электрогенерация'}, 'S10': {'en': 'Oil extraction', 'ru': 'Добыча нефти'}, 'S11': {'en': 'Gas extraction equipment', 'ru': 'Оборудование для добычи газа'}, 'S12': {'en': 'Illegal disposal of hazardous waste', 'ru': 'Незаконный сброс опасных отходов'}, 'G01': {'en': 'Wind energy', 'ru': 'Ветровая энергетика'}, 'G02': {'en': 'Solar energy', 'ru': 'Солнечная энергетика'}, 'G03': {'en': 'Geothermal energy', 'ru': 'Геотермальная энергетика'}, 'G04': {'en': 'Hydropower', 'ru': 'Гидроэнергетика'}, 'G05': {'en': 'Renewable heating', 'ru': 'Отопление на ВИЭ'}, 'G06': {'en': 'Low-emission transport', 'ru': 'Транспорт с низкими выбросами'}, 'G07': {'en': 'Zero-emission rail transport', 'ru': 'Железнодорожный транспорт с нулевыми выбросами'}, 'G08': {'en': 'Non-motorized transport infrastructure', 'ru': 'Инфраструктура немоторизованного транспорта'}, 'G09': {'en': 'Building energy savings ≥20%', 'ru': 'Повышение энергоэффективности здания ≥20%'}}

@require_POST
@never_cache
def report(request):
    try:
        r = _run(request)
    except ValueError as e:
        return JsonResponse({'error': str(e)}, status=400)
    lang = request.POST.get('lang', 'uz')
    if lang not in PDF_LANG: lang = 'uz'
    tr = PDF_LANG[lang]
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
    line(tr['intro'])
    line(tr['result']+': '+r['verdict']+' — '+tr['reason'][r['verdict']])
    line(tr['docs']+': '+str(r['document_count']))
    line(tr['hash']+': '+r['input_sha256'])
    line(tr['version']+': '+r['policy_version'])
    line(tr['stop']+': '+str(r['stop_count'])+' | '+tr['green']+': '+str(r['green_count']))
    story.append(Paragraph(escape(tr['evidence']),sty['Heading2']))
    for h in r['evidence']+r['cautions']:
        label = RULE_TITLES.get(h['rule_id'],{}).get(lang,h['label'])
        line(f"{h['rule_id']} · {label} — {h['filename']} ({tr['page']} {h['page']})")
        line(tr['quote']+': '+h['quote'][:380])
        if h.get('note'): line(tr['caution']+': '+h['note'])
    if not r['evidence'] and not r['cautions']: line(tr['none'])
    story.append(Paragraph(escape(tr['review']),sty['Heading2']))
    line(tr['pending'])
    line(tr['important']+': '+tr['disclaimer'])
    line(tr['source']+': '+SOURCE)
    SimpleDocTemplate(buf,pagesize=A4,rightMargin=42,leftMargin=42).build(story)
    response=HttpResponse(buf.getvalue(),content_type='application/pdf')
    response['Content-Disposition']='attachment; filename="NiholAI_DubugMaster_Review.pdf"'
    response['Cache-Control']='no-store'
    return response


def health(request):
    return JsonResponse({'status':'ok','name':'Nihol AI','team':'DubugMaster','policy_version':VERSION,
                        'public_demo':'local rules; no confidential data'})
