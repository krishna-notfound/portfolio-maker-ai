# Codex Work Log

## 2026-08-21

### Request

Implement the student project brief for an AI-Assisted Resume Portfolio Generator.

### Actions Planned

- Replace the Streamlit-first project with a required file-based Python workflow.
- Add a decision folder for planning notes.
- Add root `log.md` and `task.md` for Codex activity and task tracking.
- Add tests before production implementation.

### Actions Performed

- Added a pytest suite for the expected CLI behavior before creating `main.py`.
- Implemented `main.py` with resume reading, cleaning, validation, Gemini prompt construction, JSON parsing, data normalization, verification, HTML generation, and CLI error handling.
- Added `template.html`, `style.css`, `resume.txt`, `requirements.txt`, `.env.example`, and generated sample `portfolio.html`.
- Replaced the Streamlit app entry with a compatibility wrapper around the CLI.
- Rewrote README for setup, workflow, testing, responsible AI, and GitHub submission requirements.
- Added `pytest.ini` so the documented `pytest` command imports `main.py` consistently.
- Added required tests for missing API key and simulated Gemini API failure.

### Approximate Codex Output

- Wrote roughly 530 lines across Python, tests, HTML, CSS, Markdown, and sample resume/output files.

### Safety Notes

- No real API key was added.
- `.env` remains ignored.
- The sample resume uses fictional contact details.
- Any prompt-injection-like text inside a resume is treated as resume content only by the Gemini prompt.

### Debugging Pass

- Investigated a real Gemini run that failed with `503 UNAVAILABLE` and an SDK AFC warning.
- Added retry handling for temporary Gemini 503, unavailable, and high-demand errors.
- Changed the Gemini call path to prefer `Chat.send_message` when available, with `Models.generate_content` only as a fallback for simpler fake clients.
- Fixed the CLI process exit code by using `sys.exit(main())`.
- Fixed normalization for Gemini list items returned as objects, such as project dictionaries with `name`, `description`, and `technologies`.
- Verified `python main.py` with the configured local API key; it generated `portfolio.html` and reported no unsupported content.

### Interactive CLI Tool Pass

- Analyzed full project architecture, data flows, anti-hallucination checks, and template system.
- Added interactive terminal prompt feature to `main.py`:
  - Interactively lists available templates (`classic`, `compact`, `modern`).
  - Prompts user for template choice by index number or name with default fallback.
  - Prompts user for custom resume input path and output HTML path.
- Maintained full non-interactive fallback when CLI flags are provided or `--non-interactive` flag is used.
- Added unit tests for interactive prompts (`prompt_template_choice`, `prompt_text_file`, `interactive_prompt_args`) in `tests/test_main.py`.

### Streamlit Web UI Pass

- Created `app.py` to provide a full Streamlit Web UI wrapping CLI functionalities.
- Added `streamlit` dependency to `requirements.txt`.
- Enhanced `run()` in `main.py` to accept direct `resume_text` in addition to `resume_path`.
- Built interactive Streamlit UI features:
  - Sidebar for API Key input (pre-filled from `.env`), Gemini Model selector, and Template dropdown.
  - Resume input options (direct text area or file upload `.txt`/`.md`).
  - Output HTML filename configuration.
  - One-click portfolio generation with spinner status.
  - Direct local portfolio URI link (`file:///...`) for easy browser opening.
  - HTML file download button and live iframe preview inside Streamlit.
  - Verification & anti-hallucination report alerts.


