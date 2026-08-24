# 💼 AI Resume Portfolio Generator

> Transform your plain-text resume into a stunning, responsive personal portfolio website in seconds using **Google Gemini AI**.

[![Live App](https://img.shields.io/badge/Live%20Demo-Streamlit%20Cloud-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](https://porfolio-maker-ai-404.streamlit.app/)

[![Python 3.9+](https://img.shields.io/badge/Python-3.9+-blue.svg?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![Google GenAI](https://img.shields.io/badge/Google%20Gemini-Powered-orange.svg?style=flat-square&logo=google)](https://ai.google.dev/)
[![Streamlit App](https://img.shields.io/badge/Streamlit-Web%20UI-FF4B4B.svg?style=flat-square&logo=streamlit&logoColor=white)](https://streamlit.io/)
[![Built with Safety](https://img.shields.io/badge/Anti--Hallucination-Built--in-green.svg?style=flat-square)](#-anti-hallucination--verification)

---

## 🌐 Try It Online (No Installation Needed)

You can use the AI Portfolio Generator directly in your web browser:

👉 **[Launch Live Web App on Streamlit Cloud](https://porfolio-maker-ai-404.streamlit.app/)**

> 💡 **Bring Your Own API Key**: Enter your free [Google Gemini API Key](https://aistudio.google.com/app/apikey) in the sidebar to generate portfolios online. Your key is stored securely only for your active browser session.

---

## 🌟 Highlights & Features

- 🌐 **Dual-Mode Experience**:
  - **Modern Web UI**: Interactive Streamlit dashboard with drag-and-drop uploads, instant theme switching, live in-browser preview, and HTML download.
  - **Interactive CLI**: Terminal interface with step-by-step prompts or scriptable CLI flags.
- 🎨 **Multiple Gorgeous Templates**:
  - `classic`: Clean, timeless professional layout.
  - `compact`: Dense, space-efficient, high-signal modern layout.
  - `modern`: Stylish, contemporary card-based portfolio design.
- 🛡️ **Anti-Hallucination Guardrails**: Cross-references all extracted skills, projects, and contact links against your source resume to prevent AI fabrications.
- ⚡ **Zero-Config `.env` Loading**: Robust automatic environment loading with built-in fallbacks across all Python environments.
- 🔒 **Privacy-First**: Operates locally on your machine—your data is only sent to the Gemini API endpoint.

---

## 📁 Project Structure

```text
Portfolio_Generator/
├── 🌐 app.py               # Streamlit Web Application (interactive dashboard & live preview)
├── ⚙️ main.py              # Core engine (Gemini extraction, verification, rendering & CLI)
├── 📄 resume.txt           # Sample / input resume text file
├── 🎨 templates/           # Multi-theme HTML/CSS template engine
│   ├── classic/            # Classic portfolio layout (template.html + style.css)
│   ├── compact/            # Compact, high-density layout (template.html + style.css)
│   └── modern/             # Modern card-style layout (template.html + style.css)
├── 🌐 portfolio.html       # Generated output webpage
├── 🔐 .env.example         # Environment template for GEMINI_API_KEY
├── 📦 requirements.txt     # Python dependencies (google-genai, streamlit, python-dotenv, pytest)
├── 🧪 tests/               # Pytest test suite ensuring zero regressions
├── 📝 log.md               # Project development & change logs
└── 📖 README.md            # Documentation
```

---

## 🚀 Local Quick Start Guide

### 1. Prerequisites & Installation

Clone the repository and install the dependencies:

```bash
git clone https://github.com/krishna-notfound/portfolio-maker-ai.git
cd portfolio-maker-ai

pip install -r requirements.txt
```

### 2. Configure Your API Key

Create a `.env` file in the project root (or copy `.env.example`):

```bash
# On Windows PowerShell
Copy-Item .env.example .env
```

Add your [Google Gemini API Key](https://aistudio.google.com/app/apikey):

```env
GEMINI_API_KEY=your_actual_gemini_api_key_here
GEMINI_MODEL=gemini-3.1-flash-lite
```

---

## 💻 How to Run Locally

### Option A: 🌐 Web UI Mode (Streamlit) — *Recommended*

Launch the interactive web application on your local machine:

```bash
streamlit run app.py
```

> **What you can do in the Web UI:**
> 1. **Paste or Upload**: Type resume text directly or upload `.txt`/`.md` files.
> 2. **Choose Style**: Switch between `classic`, `compact`, and `modern` templates.
> 3. **Instant Preview**: View your rendered portfolio right inside the browser.
> 4. **One-Click Export**: Download the standalone `portfolio.html` file or open the local file URL (`file:///...`).

---

### Option B: ⌨️ Terminal / CLI Mode

#### 1. Interactive Step-by-Step CLI:
```bash
python main.py
```
*Prompts you interactively to choose a template, resume file, and output location.*


---

## 🎨 Available Templates

| Template | Style Description | Best For |
| :--- | :--- | :--- |
| **`classic`** | Traditional, elegant, top-to-bottom layout | General software engineers, corporate roles |
| **`compact`** | Grid-focused, space-conscious, high readability | Experienced developers with dense resumes |
| **`modern`** | Vibrant cards, accentuated tags, dynamic badges | Designers, frontend devs, creative tech |

---

## 🛡️ Anti-Hallucination & Verification

LLMs can sometimes invent or embellish facts. This project implements a dedicated **Verification Engine** (`verify_supported_content`):

1. **Extraction**: Gemini parses the resume into a strictly-typed JSON schema (`skills`, `experience`, `projects`, `education`, `contact`).
2. **Verification Cross-Check**: Every extracted skill, URL, and project name is verified against the original text.
3. **Flagging Report**: Any item not explicitly mentioned in the source resume is flagged in a verification warning so you can review it before publishing.

---

## 🧪 Running Tests

To run the automated unit test suite:

```bash
pytest
```

---

## 🔒 Responsible AI & Privacy

- **API Safety**: Never commit your `.env` file or expose your API key.
- **Data Privacy**: No data is logged or stored externally—processing runs locally and directly communicates only with the Gemini API.
- **Human in the Loop**: Always preview and review the generated HTML before sending it to recruiters or hosting it online.

---

## 📜 License

Distributed under the MIT License. See `LICENSE` for more information.
