# BOSHLASH — Nihol AI / DubugMaster (Windows)

## 1. Asl sayt dizaynini saqlamoqchi bo‘lsangiz — shu papkadan foydalaning

Python **3.11** o‘rnatilgan kompyuterda, ZIP faylini oddiy papkaga chiqaring va PowerShell oching.

```powershell
cd "C:\Users\user\Desktop\NiholAI_DubugMaster_Django"
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
python manage.py migrate
python manage.py runserver
```

`http://127.0.0.1:8000` — asosiy sayt; `http://127.0.0.1:8000/demo/` — hakamlar sinov sahifasi. **Yuqoridagi `cd` manzilini o‘zingizdagi papka manziliga moslang.** `.env` ichida SECRET_KEY ni xavfsiz qiymatga almashtiring. Gemini kaliti bo‘lmasa ham `/demo/` ishlaydi (qoidalar bilan). Original Gemini tahlili uchun maxfiy `GEMINI_API_KEYS` kerak.

## 2. GitHub

- github.com → New repository → `NiholAI-DubugMaster` → Public → Create.
- Repozitoriyga faqat *shu jildning ichidagi* fayllarni yuklang; `.env` va `.venv` hech qachon yuklanmasin.
- GitHub’da `.env`, `db.sqlite3` yo‘qligiga ishonch hosil qiling.

## 3. Railway

- railway.com → New Project → Deploy from GitHub Repo → `NiholAI-DubugMaster`.
- Service → Variables → `SECRET_KEY` (tasodifiy uzoq kalit), `DEBUG=False`, `ALLOWED_HOSTS=.up.railway.app,.railway.app`.
- Service → Settings → Networking → Generate Domain.
- Ommaviy `https://...up.railway.app/demo/`ni mobil telefonda va boshqa laptopda tekshiring.
- Agar authenticated dashboard ma’lumotlari saqlansin desangiz Railway Postgres ulang va `DATABASE_URL` sozlang.
- GitHub repository URL, jonli URL va tayyor PPTX/PDF taqdimotni finalga yuboring.

**Zarur ogohlantirish:** oldingi arxivdan qolgan `.env`dagi kalitlarni internetga chiqarmang. Agar ular biror joyda oshkor bo‘lgan bo‘lsa, ularni yangilang. Oldingi kod qayerdan kelgani `docs/PROVENANCE.md`da oshkor qilingan — final davomida yaratildi deb noto‘g‘ri ta’kidlamang. Rejalashtirilgan on-prem AI modeli hali qurilmagan.

## 4. Tez va xavfsiz zaxira variant

Agar asl Django saytida deployment muammo bersa, `NiholAI_DubugMaster_Offline_Demo.zip`ni alohida repo qilib Railway'ga joylang. Uning avtomatik testlari shu yerda ishlatildi, lekin u asl saytdagi dashboard bilan bir xil dizayn/funksiyani takrorlamaydi.
