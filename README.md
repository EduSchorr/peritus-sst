<div align="center">

# Peritus SST

### AI-assisted occupational safety report generation

**A local-first workflow for turning field evidence, documents and technical inputs into structured occupational safety reports.**

![Python](https://img.shields.io/badge/Python-20232A?style=for-the-badge&logo=python&logoColor=3776AB)
![SQLite](https://img.shields.io/badge/SQLite-20232A?style=for-the-badge&logo=sqlite&logoColor=003B57)
![Gemini](https://img.shields.io/badge/AI_Assisted-20232A?style=for-the-badge&logo=google&logoColor=8AB4F8)
![DOCX](https://img.shields.io/badge/Document_Automation-20232A?style=for-the-badge&logo=microsoftword&logoColor=2B579A)

</div>

---

## What is Peritus SST?

Peritus SST is a desktop-oriented web application created to reduce repetitive work in occupational safety and technical expert-report workflows.

The system combines **local document extraction, optional AI-assisted interpretation, structured field review, risk suggestions, evidence organization and automated DOCX generation** in one workflow.

The goal is not to replace professional judgment. It is to accelerate the mechanical parts of the process while keeping conclusions under human review.

> This repository is a **sanitized portfolio edition**. Real cases, generated reports, API keys, production databases, professional contact data and private reference documents are intentionally excluded.

## Core workflow

```text
Field notes / petitions / evidence
               │
               ▼
      Local document extraction
               │
               ▼
     Optional AI interpretation
               │
               ▼
      Structured case review
               │
        ┌──────┴──────┐
        ▼             ▼
 Risk suggestions   Questions
        │             │
        └──────┬──────┘
               ▼
     Evidence + measurements
               │
               ▼
      Professional validation
               │
               ▼
        Automated DOCX report
```

## Highlights

- Local-first case database using SQLite
- Structured review for inspection and expert-report data
- Extraction from DOCX, PDF, text and image inputs
- Optional Google Gemini-assisted document interpretation
- Local OCR support through Tesseract
- Risk suggestion engine backed by curated SST rules/catalogs
- Separation between claimant/respondent statements and documentary evidence
- Technical measurements, PPE/EPC and training records
- Question import and response organization
- Photograph classification and captions
- Automated professional DOCX generation
- Case history and dashboard
- Self-update and local launcher architecture

## Architecture

```text
┌──────────────────────────────────────────┐
│             Browser interface            │
│        HTML · CSS · JavaScript           │
└─────────────────────┬────────────────────┘
                      │ localhost
┌─────────────────────▼────────────────────┐
│              Python server               │
│ cases · OCR · settings · generation      │
└───────────────┬──────────────┬───────────┘
                │              │
       ┌────────▼───────┐ ┌────▼──────────────┐
       │ SQLite / local │ │ AI + local OCR    │
       │ case knowledge │ │ Gemini / Tesseract│
       └────────┬───────┘ └───────────────────┘
                │
       ┌────────▼────────────┐
       │ Risk & SST knowledge│
       │ catalog + rule engine│
       └────────┬────────────┘
                │
       ┌────────▼────────────┐
       │ DOCX report builder │
       └─────────────────────┘
```

## Repository structure

```text
app/
├── knowledge/              Curated SST catalog and risk rules
├── templates/              Public template guidance
├── web/                    Browser application
├── knowledge_db.py         Search/import for local SST knowledge
├── professional_docx.py    Report document generation
├── risk_engine.py          Risk suggestion logic
├── server.py               Local application server and APIs
├── lifecycle.py            Local process lifecycle helpers
├── launcher.py             Desktop/local launcher
└── self_updater.py         Update workflow

data/                      Runtime database (ignored)
documentos_gerados/        Generated reports (ignored)
```

## Running locally

### Requirements

- Python 3.11+
- Windows is recommended for the original desktop workflow
- Tesseract is optional for local OCR
- A Gemini API key is optional for AI-assisted extraction

### Install

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

pip install -r requirements.txt
python app/server.py
```

Then open the local address printed by the application (normally `http://127.0.0.1:8765`).

## AI configuration

No API key is included in this repository. When configured, the application stores the key locally in its runtime configuration and uses it only for requests initiated by the user.

For a portfolio/demo installation, run the application without an API key first and configure AI only if needed.

## Safety and professional review

Peritus SST assists with information organization and report drafting. Occupational safety conclusions depend on the actual workplace, evidence, measurements, applicable standards and professional judgment.

Generated content should always be reviewed and approved by a qualified professional before use.

## Privacy

The public portfolio edition excludes:

- real lawsuit/case records
- names of claimants, respondents or employees
- production databases
- generated client reports
- API credentials
- professional contact information
- private reference DOCX files
- local machine-specific paths

## Version

Portfolio baseline: **0.7.6 Beta**

---

<div align="center">

Built by **Eduardo Lima** · [GitHub](https://github.com/EduSchorr)

</div>