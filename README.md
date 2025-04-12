# 🤖 AI-Powered Job Screening System

An intelligent resume screening app that uses LLMs (like Mistral via Ollama) and semantic embedding models (like all-MiniLM) to automate the shortlisting process for hiring teams.

## 🚀 Features

- 📄 Upload job descriptions via CSV or plain text
- 📜 Automatically summarize JDs using the Mistral model
- 📂 Upload multiple candidate resumes (PDFs)
- 🤝 Match resumes to job roles using semantic similarity (MiniLM embeddings)
- 📤 Email shortlisted candidates directly
- 📈 Batch match all resumes to all jobs
- 📅 Schedule interview messages for shortlisted candidates

---

## 🧰 Tech Stack

- [Streamlit](https://streamlit.io/) – interactive UI
- [Ollama](https://ollama.ai/) – for local LLM inference (Mistral)
- [SentenceTransformers (MiniLM)](https://www.sbert.net/) – for semantic matching
- Python + PyPDF2 / pdfplumber for PDF parsing
- SMTP (Gmail) for sending emails
- SQLite (optional) for persistence

---

## ⚙️ Installation

```bash
git clone https://github.com/Sahil-3967/job-screening-app.git
cd job-screening-app
python -m venv venv
venv\\Scripts\\activate   # Or source venv/bin/activate (Linux/Mac)
pip install -r requirements.txt
