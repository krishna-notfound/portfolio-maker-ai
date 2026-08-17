# AI-Assisted Portfolio Generator

This project is an end-to-end Streamlit application that transforms raw, unstructured resume text into a complete, structured portfolio website. It leverages the **Google Gemini API** (`gemini-2.5-flash`) for intelligent data extraction and parsing.

## Features

- **Automated Parsing**: Extracts Name, Contact Info, Summary, Education, Experience, Projects, Skills, and Achievements from unstructured text.
- **Privacy First (PII Masking)**: Uses regular expressions to detect and redact sensitive information (like SSNs and Credit Card numbers) *before* sending data to the AI model.
- **Deterministic JSON Output**: Uses advanced prompt engineering and API configurations to guarantee the model returns strictly formatted JSON.
- **Hallucination Detection**: Includes a post-processing algorithm to verify that the extracted skills and links actually appear in the original text, flagging any potential AI fabrications.
- **Live Preview & Export**: Generates a responsive HTML/CSS template with a live preview and one-click download.

## Setup & Installation

1. **Clone the repository** (or download the files):
   Ensure you have `app.py` in your working directory.

2. **Install dependencies**:
   You need Python 3.9+ installed. Install the required libraries using pip:
   ```bash
   pip install streamlit google-genai
   ```

3. **Get a Gemini API Key**:
   Visit [Google AI Studio](https://aistudio.google.com/app/apikey) to generate a free API key.

4. **Run the application**:
   ```bash
   streamlit run app.py
   ```

## Technical Details

### 1. Privacy Pre-processing (Masking)
Before sending the user's resume to the Gemini API, the text is passed through a `mask_pii()` function. This function uses Python's `re` (regex) library to identify patterns that look like Social Security Numbers (e.g., `XXX-XX-XXXX`) or 16-digit credit card numbers. It replaces these matches with `[REDACTED SSN]` or `[REDACTED CC]`, ensuring sensitive data never leaves the user's machine.

### 2. Prompt Engineering & Deterministic JSON
To reliably power our Streamlit UI and HTML generator, we need structured data, not conversational text. 
We achieve this by:
- Defining a strict Expected JSON Structure within the system prompt.
- Explicitly instructing the model *not* to include markdown wrappers (like ` ```json `).
- Setting `response_mime_type="application/json"` in the `GenerateContentConfig` of the `google-genai` SDK. This forces the Gemini model to output purely valid JSON.

### 3. Hallucination Check Logic
Large Language Models sometimes "hallucinate" or infer information that wasn't explicitly stated. For example, if the resume says "Web Development", the AI might hallucinate specific skills like "HTML" or "CSS".
Our `check_hallucinations()` function performs a basic safety check:
1. It converts the original raw text to lowercase.
2. It iterates through the arrays of extracted `Skills` and `Links` provided by the API.
3. If an extracted skill or link substring is *not* found in the original text, it flags it as a potential hallucination and alerts the user in the UI.

## File Structure
- `app.py`: The main Streamlit application containing UI, API logic, and HTML generation.
- `README.md`: This documentation file.
