# Nihol AI · DubugMaster

**Mode: STARTUP | WIUT Hackathon 2026 · FinTech / AI in Finance**

Uzbek-first green-finance document screening. This repository adapts the **user-supplied ESG_Hackathon_MVP** Django application. The original site structure, admin dashboard, authentication, multilingual interface, optional Gemini document-analysis pipeline and PDF output are retained and renamed. The final-stage team's contributions are documented in `docs/PROVENANCE.md`. **Do not misrepresent the imported material as code newly written during the final.**

## What a judge can test (no account, no API key)

Open `/demo/` from the public homepage. Paste a new synthetic project description or upload a **text PDF / UTF-8 TXT**, press *Tekshirish*, inspect page/quote/rule evidence, then click *PDF hisobotni olish*. Results are recomputed from submitted documents, not pre-recorded responses. The demonstrator uses a **local, deterministic, keyword-based screening model**, not a hosted LLM. The user-facing result is `GREEN_CANDIDATE`, `NOT_GREEN`, `REVIEW_REQUIRED`, or `NO_DATA`. A green *candidate* still needs a specialist's approval. The demo never uploads documents to Gemini, logs source text or stores submitted files.

The main authenticated `/dashboard/` preserves the user-supplied Gemini analysis and original UI. **That AI mode needs `GEMINI_API_KEYS`** and is not the same inference path as the public offline screening demo. The original full-system view needs further production hardening and integration testing.

## Start locally (Windows PowerShell)

Prerequisites: **Python 3.11**, internet to install Python dependencies, and the unzipped project directory.

```powershell
cd path\to\NiholAI_DubugMaster_Django
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Edit `.env`: set `SECRET_KEY` to a strong random string; leave `GEMINI_API_KEYS` blank to use the API-free public demo. **Never publish `.env`.**

```powershell
python manage.py migrate --noinput
python manage.py runserver
```

Open `http://127.0.0.1:8000/demo/` for the judge demo. The site root `/` shows the original rebranded design. Login/register and full authenticated dashboard are also available. To enable the original Gemini branch, put your own `GEMINI_API_KEYS` in `.env`. **Do not upload real bank customer data to an external API.**

Tests (local pure-Python rule tests work even without Django installation):

```powershell
python -m unittest discover -s tests -v
python -m tests.eval_synthetic
```

## GitHub + Railway (publicly reachable)

1. Create a **new PUBLIC GitHub repository** `NiholAI-DubugMaster` with only this directory, without the original RAR, `.env`, `db.sqlite3`, ZIP, video showing real people, or any private bank data.
2. Push with `git init`, `git add .`, `git commit -m "Nihol AI final prototype"`, `git branch -M main`, `git remote add origin <YOUR_REPOSITORY_URL>`, and `git push -u origin main`.
3. Railway → **New Project → Deploy from GitHub repo** → select that exact public repository.
4. Railway Variables: `SECRET_KEY=<random long unique value>`, `DEBUG=False`, `ALLOWED_HOSTS=.up.railway.app,.railway.app`, and (if provided) `DATABASE_URL=<Railway PostgreSQL connection string>`. For the **public local rules demo**, no Gemini key is required. If enabling original AI, add `GEMINI_API_KEYS` privately.
5. Use the included `railway.json` and `nixpacks.toml`. The start command migrates and launches Gunicorn, with no fabricated analysis seeding.
6. Railway service → Settings → Networking → **Generate Domain**. Verify `/api/health/`, `/demo/`, POST a NEW synthetic input, and download the PDF report. Only then submit the real public URL.
7. Put your actual **public GitHub URL + deployed URL** into the hackathon dashboard, along with the deck. Check the code-freeze commit at the deadline.

Deployment notes: use Railway PostgreSQL for persistent authenticated analyses; ephemeral SQLite is **not** suitable for long-lived deployments. `RAILWAY_PUBLIC_DOMAIN` is supported for CSRF / allowed hosts. External Bootstrap/CDN visual assets mean production frontend is not fully air-gapped; host/vendor these in a real on-prem build.

## Architecture and limitations

- **Prototype public:** browser → Django `/api/demo/analyze/` → `pypdf` text extraction → local `prototype_rules.py` (12 configurable stop rules, 9 green checks, limited negation handling) → source page and quote → PDF; no API network call, no database persistence.
- **Existing optional branch:** authenticated uploader → Google Gemini fact extraction → `constants.compute_verdict()` → Django DB → PDF/report. This optional path invokes an external API; it is not suitable for confidential bank material without approvals.
- **Production perimeter design (NOT implemented):** ingress/auth → AV + OCR → on-prem document processor → on-prem LLM or rules extractor → versioned taxonomy decision engine → secured PostgreSQL/object storage → signed audit event → risk officer confirmation → PDF; no external API or CDN; KMS/RBAC/retention schedule required.
- **Known failure cases:** low-quality scans/images not supported in public rules demo; negation, mixed projects, nuanced contextual semantics, legal thresholds and project-wide exclusion completeness require human review; exact rule-to-taxonomy legal mapping requires expert sign-off. The public demo intentionally does not show speculative ESG scores.

## Evaluation, evidence and economics

`tests/eval_synthetic.py` has **18 synthetic labelled scenarios** and checks all programmatic outcomes; this is developer-written smoke coverage **not a real-world validation set**. At authoring time, all 18 matched the stated synthetic labels, with rule-only median around **0.038 ms** in one restricted machine; these numbers exclude upload, PDF processing, database, networking and model inference. Re-run benchmarks on your deployed server and record genuine results before presenting.

Illustrative pilot assumptions only: 100 cases/month, 45 minutes baseline triage versus 10 minutes assisted triage (to be measured), analyst cost $8/hour, hosting $50/month, pilot integration/training $3,200. Potential time saved = `100 × (45–10) / 60 = 58.3h/month`, gross cost saved ≈ `$467/month`, net after hosting ≈ `$417/month`, simple estimated payback **~7.7 months**. Not bank-verified ROI. External Gemini usage, if enabled, has additional variable usage-based charges (estimate with real token counts).

See `docs/DATA_SOURCES_AND_LICENSES.md`, `docs/PROVENANCE.md`, `docs/SECURITY_AND_TEST_PLAN.md` and `docs/DEFENCE_SCRIPT_UZ.md`.

## Ethical use and disclosure

Use *synthetic/non-identifying inputs only* in the public hackathon demo. The imported project was supplied by the user, not proven to have been built entirely during the final: disclose exactly what was reused. The rule catalogue is a prototype approximation, not an officially certified implementation of Cabinet of Ministers Resolution **No. 561, 25 October 2023**. The public site must not imply a bank endorsement, current pilots, protected data, or quantified accuracy without evidence.
