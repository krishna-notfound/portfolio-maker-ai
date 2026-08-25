import html
import json
import os
from collections import namedtuple
from pathlib import Path

from dotenv import load_dotenv
from google import genai

# Constants
MIN_RESUME_LENGTH = 40
DEFAULT_MODEL = "gemini-2.5-flash"
DEFAULT_TEMPLATE = "classic"
DEFAULT_TEMPLATES_DIR = Path("templates")

RunResult = namedtuple("RunResult", ["output_path", "hallucination_report"])
TemplatePaths = namedtuple("TemplatePaths", ["template", "css"])


# 1. Resume Input & Cleaning
def validate_resume_text(text):
    if len(text.strip()) < MIN_RESUME_LENGTH:
        raise ValueError("resume.txt is too short to generate a reliable portfolio.")


def clean_resume_text(text):
    return "\n".join(" ".join(line.split()) for line in text.splitlines() if line.strip())


def read_resume(path="resume.txt"):
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"{p.name} was not found. Add resume content to resume.txt and run again.")
    text = p.read_text(encoding="utf-8").strip()
    validate_resume_text(text)
    return text


# 2. Gemini AI Data Extraction
def build_prompt(cleaned_resume):
    return (
        "You are an AI resume-to-portfolio assistant.\n"
        "Use only information explicitly present in the resume text. Return JSON only, with no markdown.\n"
        'JSON format: {"name": "", "headline": "", "summary": "", "skills": [], "education": [], '
        '"experience": [], "projects": [], "achievements": [], "contact": {"email": "", "phone": "", '
        '"linkedin": "", "github": "", "links": []}}\n\n'
        f"Resume text:\n{cleaned_resume}"
    )


def parse_gemini_json(raw_text):
    clean_text = raw_text.replace("```json", "").replace("```", "").strip()
    try:
        data = json.loads(clean_text)
        if isinstance(data, dict):
            return data
    except Exception as exc:
        raise ValueError("Gemini did not return valid JSON. Check the prompt/model response and try again.") from exc
    raise ValueError("Gemini JSON must be an object with portfolio fields.")


def extract_portfolio_data(cleaned_resume, api_key, model=DEFAULT_MODEL, client=None):
    if not api_key:
        raise ValueError("Missing Gemini API key. Add GEMINI_API_KEY to your .env file.")

    client = client or genai.Client(api_key=api_key)
    prompt = build_prompt(cleaned_resume)
    config = {"response_mime_type": "application/json"}

    try:
        if hasattr(client, "chats"):
            response = client.chats.create(model=model, config=config).send_message(prompt)
        else:
            response = client.models.generate_content(model=model, contents=prompt, config=config)
        return parse_gemini_json(response.text)
    except Exception as exc:
        raise RuntimeError(f"Gemini API request failed: {exc}") from exc


# 3. Data Normalization & Verification
def _to_text(val):
    if not val:
        return ""
    if isinstance(val, str):
        return val.strip()
    if isinstance(val, dict):
        title = val.get("name") or val.get("title") or val.get("degree") or ""
        desc = val.get("description", "")
        tech = f"Technologies: {', '.join(val['technologies'])}" if val.get("technologies") else ""
        parts = [p for p in [desc, tech] if p]
        return f"{title}: {' '.join(parts)}" if title and parts else (title or desc or str(val))
    return str(val).strip()


def _to_list(val):
    if isinstance(val, list):
        return [_to_text(x) for x in val if _to_text(x)]
    t = _to_text(val)
    return [t] if t else []


def normalize_portfolio_data(data):
    contact = data.get("contact") if isinstance(data.get("contact"), dict) else {}
    return {
        "name": _to_text(data.get("name")),
        "headline": _to_text(data.get("headline")),
        "summary": _to_text(data.get("summary")),
        "skills": _to_list(data.get("skills")),
        "education": _to_list(data.get("education")),
        "experience": _to_list(data.get("experience")),
        "projects": _to_list(data.get("projects")),
        "achievements": _to_list(data.get("achievements")),
        "contact": {
            "email": _to_text(contact.get("email")),
            "phone": _to_text(contact.get("phone")),
            "linkedin": _to_text(contact.get("linkedin")),
            "github": _to_text(contact.get("github")),
            "links": _to_list(contact.get("links")),
        },
    }


def verify_supported_content(original_resume, data):
    src = original_resume.lower()
    contact = data.get("contact", {})
    report = {k: [x for x in data.get(k, []) if x and x.lower() not in src] for k in ("skills", "projects", "achievements")}
    all_links = [contact.get("linkedin", ""), contact.get("github", ""), *contact.get("links", [])]
    report["links"] = [link for link in all_links if link and link.lower() not in src]
    return report


# 4. HTML Rendering & Output
def _contact_html(contact):
    links = []
    if contact.get("email"):
        links.append(f'<a href="mailto:{html.escape(contact["email"])}">{html.escape(contact["email"])}</a>')
    if contact.get("phone"):
        links.append(f'<span>{html.escape(contact["phone"])}</span>')
    for url in [contact.get("linkedin"), contact.get("github"), *contact.get("links", [])]:
        if url:
            safe_url = html.escape(url, quote=True)
            links.append(f'<a href="{safe_url}" target="_blank" rel="noreferrer">{html.escape(url)}</a>')
    return f'<div class="contact">{"".join(links)}</div>' if links else ""


def generate_portfolio_html(data, template_path="template.html", css_path="style.css"):
    template = Path(template_path).read_text(encoding="utf-8")
    css = Path(css_path).read_text(encoding="utf-8")

    sections = [
        '<main class="page">',
        '<section class="hero">',
        f"<h1>{html.escape(data.get('name') or 'Portfolio')}</h1>",
    ]
    if data.get("headline"):
        sections.append(f'<p class="headline">{html.escape(data["headline"])}</p>')
    sections.append(_contact_html(data.get("contact", {})))
    sections.append("</section>")

    content_blocks = [
        ("Professional Summary", "summary", False),
        ("Skills", "skills", True),
        ("Education", "education", True),
        ("Experience", "experience", True),
        ("Projects", "projects", True),
        ("Achievements", "achievements", True),
    ]
    for title, key, is_list in content_blocks:
        val = data.get(key)
        if val:
            body = f'<ul>{"".join(f"<li>{html.escape(item)}</li>" for item in val)}</ul>' if is_list else f'<p>{html.escape(val)}</p>'
            sections.append(f'<section class="section"><h2>{title}</h2>{body}</section>')

    sections.append("</main>")
    return template.replace("{{ css }}", css).replace("{{ content }}", "\n".join(sections))


def write_output(html_text, path="portfolio.html"):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(html_text, encoding="utf-8")
    return p


def list_templates(templates_dir=DEFAULT_TEMPLATES_DIR):
    d = Path(templates_dir)
    if not d.exists():
        return []
    return sorted(p.name for p in d.iterdir() if p.is_dir() and (p / "template.html").exists() and (p / "style.css").exists())


def get_template_paths(template_name, templates_dir=DEFAULT_TEMPLATES_DIR):
    td = Path(templates_dir) / template_name.strip()
    tpl, css = td / "template.html", td / "style.css"
    if not (tpl.exists() and css.exists()):
        available = ", ".join(list_templates(templates_dir)) or "none"
        raise FileNotFoundError(f"Template '{template_name}' was not found. Available templates: {available}.")
    return TemplatePaths(template=tpl, css=css)


# 5. Pipeline Runner & CLI
def run(*, resume_path="resume.txt", resume_text=None, output_path="portfolio.html", api_key=None, model=None, template_name=DEFAULT_TEMPLATE, templates_dir=DEFAULT_TEMPLATES_DIR):
    load_dotenv(override=True)
    raw = resume_text.strip() if resume_text is not None else read_resume(resume_path)
    validate_resume_text(raw)

    cleaned = clean_resume_text(raw)
    key = api_key or os.getenv("GEMINI_API_KEY", "").strip()
    selected_model = model or os.getenv("GEMINI_MODEL", DEFAULT_MODEL).strip() or DEFAULT_MODEL

    extracted = extract_portfolio_data(cleaned, key, selected_model)
    normalized = normalize_portfolio_data(extracted)
    report = verify_supported_content(raw, normalized)

    tpl = get_template_paths(template_name, templates_dir)
    rendered_html = generate_portfolio_html(normalized, tpl.template, tpl.css)
    out_file = write_output(rendered_html, output_path)

    return RunResult(output_path=out_file, hallucination_report=report)


def main():
    try:
        result = run()
        print(f"Generated {result.output_path}")
        flagged = {k: v for k, v in result.hallucination_report.items() if v}
        if flagged:
            print("Verification warning:\n" + "\n".join(f"- {k}: {', '.join(v)}" for k, v in flagged.items()))
        else:
            print("Verification check: clean.")
    except Exception as exc:
        print(f"Error: {exc}")


if __name__ == "__main__":
    main()


