"""Prototype, versioned policy: NOT an official legal taxonomy certification.

Rule family names and 9 green activities were informed by the user-provided
NovdAI founder brief; 12 policy exclusions are prototype screening signals.
Mapping to Cabinet Resolution 561 requires specialist legal validation.
"""
from dataclasses import dataclass
import re
from typing import Optional

VERSION = 'nih-2026-10-11-demo-v1'
SOURCE = 'Prototype signals inspired by provided founder brief; independently validate against Uzbekistan VM 561 (2023) https://lex.uz/docs/6644013'

@dataclass(frozen=True)
class Rule:
    id: str
    title: str
    keywords: tuple[str, ...]
    type: str

BLOCKED = [
    Rule('S01','Qurol va o‘q-dori',('qurol ishlab','o‘q-dori','harbiy qurol','ammunition manufactur','weapons manufactur','производство оружия'),'stop'),
    Rule('S02','Alkogol ishlab chiqarish',('aroq ishlab','vino ishlab','pivo ishlab','alkogol ishlab','alcohol produc','beer brewery','производство алкоголя'),'stop'),
    Rule('S03','Tamaki mahsulotlari',('tamaki ishlab','sigaret ishlab','tobacco manufactur','cigarette factor','производство табака'),'stop'),
    Rule('S04','Qimor faoliyati',('qimor','kazino','casino','gambling','букмекер','казино'),'stop'),
    Rule('S05','Yadro elektr ishlab chiqarish',('atom elektr stansiya','yadro energiya','nuclear power plant','атомная электростанция'),'stop'),
    Rule('S06','Radioaktiv materiallar',('uran qazib','radioaktiv modda','radioactive material','добыча урана'),'stop'),
    Rule('S07','Asbest bilan faoliyat',('asbest ishlab','asbest sot','asbestos manufactur','асбест производ'),'stop'),
    Rule('S08','Ko‘mir qazib olish',('ko‘mir qazib','coal mining','добыча угля'),'stop'),
    Rule('S09','Ko‘mir elektr stansiyasi',('ko‘mir yoqiladigan','coal-fired power','угольная электростанция'),'stop'),
    Rule('S10','Neft qazib olish',('neft qazib','oil extraction','oil drilling','добыча нефти'),'stop'),
    Rule('S11','Gaz qazib olish uskunalari',('gaz qazib olish uskun','gas drilling equipment','оборудование для добычи газа'),'stop'),
    Rule('S12','Xavfli chiqindilarni noqonuniy tashlash',('noqonuniy xavfli chiqindi tash','illegal hazardous waste dumping','незаконный сброс опасных отходов'),'stop'),
]
GREEN = [
    Rule('G01','Shamol energetikasi',('shamol elektr','shamol turbina','wind turbine','wind farm','ветровая электростанция'),'green'),
    Rule('G02','Quyosh energetikasi',('quyosh panel','quyosh elektr','fotoelektr','solar panel','solar power','солнечная электростанция','солнечные панели'),'green'),
    Rule('G03','Geotermal energetika',('geotermal','geothermal','геотермальн'),'green'),
    Rule('G04','Gidroenergetika',('gidroelektr','hydropower','hydroelectric','гидроэлектростанция'),'green'),
    Rule('G05','Qayta tiklanuvchi isitish',('qayta tiklanuvchi isitish','renewable heating','solar heating','возобновляемое отопление'),'green'),
    Rule('G06','Kam emissiyali transport',('elektromobil','elektr avtobus','electric bus','electric vehicle','электробус','электромобиль','cng bus','lng bus'),'green'),
    Rule('G07','Nol emissiyali temir yo‘l',('elektr lokomotiv','zero-emission railway','electric locomotive','электровоз'),'green'),
    Rule('G08','Motorsiz transport infratuzilmasi',('velosiped yo‘lak','velosiped yolak','cycle lane','bicycle infrastructure','велодорожк'),'green'),
    Rule('G09','Bino energiya tejamkorligi >=20%',('bino energiya samarador','building energy efficiency','энергоэффективность здания'),'green'),
]

NEGATIONS=('emas','mavjud emas','yo‘q',"yo'q",'shug‘ullanmaydi',"shug'ullanmaydi",'ishlab chiqarilmay','faoliyat olib bormaydi','taqiqlangan','without ','not involved','not used','не производ','отсутствует','не ведет')


def _normalize_for_search(value: str) -> str:
    """Normalize common Uzbek apostrophes and PDF Unicode variants for matching.

    Preserve character positions: all substitutions are one character to one character.
    """
    return value.lower().translate(str.maketrans({
        "‘": "'", "’": "'", "ʻ": "'", "ʼ": "'", "`": "'", "´": "'",
        "–": "-", "—": "-", "‑": "-", "−": "-",
    }))


def _find(text: str, term: str) -> Optional[tuple[int, int]]:
    normalized = _normalize_for_search(text)
    needle = _normalize_for_search(term)
    p = normalized.find(needle)
    return (p, p + len(needle)) if p >= 0 else None


def _negated(text: str, start: int, stop: int) -> bool:
    # Stop keyword in a negation sentence is ambiguous: flag as needs-review, not as clear exclusion.
    sentence_start = max(text.rfind('.',0,start),text.rfind('\n',0,start),text.rfind(';',0,start))+1
    sentence_end_candidates = [n for n in (text.find('.',stop),text.find('\n',stop),text.find(';',stop)) if n>=0]
    sentence_end = min(sentence_end_candidates) if sentence_end_candidates else len(text)
    context=text[sentence_start:sentence_end].casefold()
    return any(n in context for n in NEGATIONS)


def _energy_saving_proven(text: str) -> bool:
    # A specific magnitude is required; intentionally conservative.
    pats = [r'(?:energiya|energy|энерг)[^\n.]{0,75}?(\d+(?:[.,]\d+)?)\s*%',
            r'(\d+(?:[.,]\d+)?)\s*%[^\n.]{0,75}?(?:energiya|energy|энерг)']
    for pat in pats:
        for m in re.finditer(pat,text,flags=re.I):
            if float(m.group(1).replace(',','.')) >= 20: return True
    return False


def analyze_docs(documents: list[dict]):
    """Every document has name and pages [{page,text}]; decisions use only evidenced matches."""
    hits=[]; cautions=[]; populated=0
    for doc in documents:
        for page in doc['pages']:
            txt=page['text']; populated+=len(txt.strip())
            for rule in BLOCKED+GREEN:
                selected=None
                for word in rule.keywords:
                    found=_find(txt,word)
                    if found:
                        selected=(word,found);break
                if not selected: continue
                word,(start,end)=selected
                left=max(0,start-80); right=min(len(txt),end+100)
                evidence={'rule_id':rule.id,'label':rule.title,'kind':rule.type,
                          'filename':doc['name'],'page':page['page'],
                          'quote':txt[left:right].strip().replace('\n',' '),
                          'keyword':word,'negated':_negated(txt,start,end)}
                if rule.id=='G09' and not _energy_saving_proven(txt):
                    evidence['note']='20% yoki undan yuqori tejash dalili topilmadi'
                    cautions.append(evidence);continue
                if evidence['negated']:
                    evidence['note']='Inkor yoki cheklov mavjud; qo‘lda aniqlashtirish kerak'
                    cautions.append(evidence);continue
                hits.append(evidence)
    stops=[h for h in hits if h['kind']=='stop']
    greens=[h for h in hits if h['kind']=='green']
    # Lack of evidence that other stop factors are absent is not proof of their absence.
    # Thus 'green' is a conditional candidate with human sign-off, not an automated authorization.
    if not populated: verdict='NO_DATA'
    elif stops: verdict='NOT_GREEN'
    elif greens and not cautions: verdict='GREEN_CANDIDATE'
    else: verdict='REVIEW_REQUIRED'
    if verdict=='NOT_GREEN': reason='Istisno faoliyat haqida dalil topildi. Bank xodimi tasdiqlashi kerak.'
    elif verdict=='GREEN_CANDIDATE': reason='Yashil faoliyat belgisi topildi, lekin istisnolar yo‘qligi va boshqa talablar qo‘lda tekshiriladi.'
    elif verdict=='NO_DATA': reason='O‘qiladigan matn topilmadi. Matn/OCR yoki qo‘shimcha hujjat kerak.'
    else: reason='Dalil yetarli emas yoki qarama-qarshilik bor. Qo‘shimcha hujjat talab qilinadi.'
    return {'verdict':verdict,'reason':reason,'evidence':hits,'cautions':cautions,
            'stop_count':len({h['rule_id'] for h in stops}),
            'green_count':len({h['rule_id'] for h in greens}),
            'policy_version':VERSION,'human_approval_required':True,
            'disclaimer':'Prototip skriningi, rasmiy yashil sertifikat yoki bank kredit qarori emas.'}
