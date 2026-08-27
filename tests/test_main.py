import json
from pathlib import Path

import pytest

import main


def test_clean_resume_text_removes_extra_spaces_and_blank_lines():
    raw = "  Jane   Doe  \n\n\n Skills:   Python,   HTML  \n  "

    assert main.clean_resume_text(raw) == "Jane Doe\nSkills: Python, HTML"


def test_validate_resume_text_rejects_short_resume():
    with pytest.raises(ValueError, match="too short"):
        main.validate_resume_text("Jane Doe")


def test_read_resume_reports_missing_file(tmp_path):
    with pytest.raises(FileNotFoundError, match="resume.txt was not found"):
        main.read_resume(tmp_path / "resume.txt")


def test_parse_gemini_json_rejects_invalid_json():
    with pytest.raises(ValueError, match="valid JSON"):
        main.parse_gemini_json("not json")


def test_extract_portfolio_data_rejects_missing_api_key():
    with pytest.raises(ValueError, match="Missing Gemini API key"):
        main.extract_portfolio_data("Jane Doe\nPython Developer", "", "gemini-2.5-flash")


def test_extract_portfolio_data_wraps_api_failure():
    class BrokenModels:
        def generate_content(self, model, contents, config):
            raise RuntimeError("service unavailable")

    class BrokenClient:
        def __init__(self):
            self.models = BrokenModels()

    with pytest.raises(RuntimeError, match="Gemini API request failed"):
        main.extract_portfolio_data(
            "Jane Doe\nPython Developer",
            "fake-key",
            "gemini-2.5-flash",
            client=BrokenClient(),
        )


def test_normalize_portfolio_data_fills_missing_values():
    data = main.normalize_portfolio_data({"name": "Jane Doe", "skills": ["Python"]})

    assert data["name"] == "Jane Doe"
    assert data["headline"] == ""
    assert data["skills"] == ["Python"]
    assert data["education"] == []
    assert data["contact"]["email"] == ""
    assert data["contact"]["links"] == []


def test_normalize_portfolio_data_converts_object_list_items_to_readable_text():
    data = main.normalize_portfolio_data(
        {
            "projects": [
                {
                    "name": "Resume Portfolio Generator",
                    "description": "Reads resume text and generates HTML.",
                    "technologies": ["Python", "Gemini"],
                }
            ]
        }
    )

    assert data["projects"] == [
        "Resume Portfolio Generator: Reads resume text and generates HTML. Technologies: Python, Gemini"
    ]


def test_generate_portfolio_html_omits_empty_sections(tmp_path):
    template = tmp_path / "template.html"
    css = tmp_path / "style.css"
    template.write_text(
        "<html><head><style>{{ css }}</style></head><body>{{ content }}</body></html>",
        encoding="utf-8",
    )
    css.write_text("body { color: #222; }", encoding="utf-8")
    data = main.normalize_portfolio_data(
        {
            "name": "Jane Doe",
            "headline": "Python Developer",
            "summary": "Builds small automation tools.",
            "skills": ["Python", "HTML"],
            "contact": {"email": "jane@example.com"},
        }
    )

    html = main.generate_portfolio_html(data, template, css)

    assert "Jane Doe" in html
    assert "Python Developer" in html
    assert "Skills" in html
    assert "Education" not in html
    assert "No skills listed" not in html


def test_get_template_paths_returns_named_template_files(tmp_path):
    template_dir = tmp_path / "templates" / "modern"
    template_dir.mkdir(parents=True)
    (template_dir / "template.html").write_text("{{ content }}", encoding="utf-8")
    (template_dir / "style.css").write_text("body {}", encoding="utf-8")

    paths = main.get_template_paths("modern", tmp_path / "templates")

    assert paths.template == template_dir / "template.html"
    assert paths.css == template_dir / "style.css"


def test_get_template_paths_rejects_unknown_template(tmp_path):
    with pytest.raises(FileNotFoundError, match="Template 'missing' was not found"):
        main.get_template_paths("missing", tmp_path / "templates")


def test_list_templates_returns_available_template_names(tmp_path):
    for name in ("classic", "modern"):
        template_dir = tmp_path / "templates" / name
        template_dir.mkdir(parents=True)
        (template_dir / "template.html").write_text("{{ content }}", encoding="utf-8")
        (template_dir / "style.css").write_text("body {}", encoding="utf-8")
    ignored = tmp_path / "templates" / "draft"
    ignored.mkdir()
    (ignored / "template.html").write_text("{{ content }}", encoding="utf-8")

    assert main.list_templates(tmp_path / "templates") == ["classic", "modern"]


def test_run_uses_named_template_folder(tmp_path, monkeypatch):
    resume = tmp_path / "resume.txt"
    output = tmp_path / "portfolio.html"
    templates = tmp_path / "templates"
    modern = templates / "modern"
    modern.mkdir(parents=True)
    resume.write_text(
        "Jane Doe\nEmail: jane@example.com\nPython Developer\nSkills: Python\nProject: Portfolio Generator",
        encoding="utf-8",
    )
    (modern / "template.html").write_text(
        "<html><head><style>{{ css }}</style></head><body><div class=\"modern\">{{ content }}</div></body></html>",
        encoding="utf-8",
    )
    (modern / "style.css").write_text(".modern { color: #123456; }", encoding="utf-8")

    def fake_extract(cleaned_resume, api_key, model):
        return {"name": "Jane Doe", "headline": "Python Developer", "skills": ["Python"]}

    monkeypatch.setattr(main, "extract_portfolio_data", fake_extract)

    main.run(
        resume_path=resume,
        output_path=output,
        api_key="fake-key",
        template_name="modern",
        templates_dir=templates,
    )

    html = output.read_text(encoding="utf-8")
    assert "modern" in html
    assert "#123456" in html


def test_extract_portfolio_data_uses_injected_client_and_model():
    class FakeResponse:
        text = json.dumps({"name": "Jane Doe", "skills": ["Python"]})

    class FakeModels:
        def __init__(self):
            self.calls = []

        def generate_content(self, model, contents, config):
            self.calls.append((model, contents, config))
            return FakeResponse()

    class FakeClient:
        def __init__(self):
            self.models = FakeModels()

    client = FakeClient()

    data = main.extract_portfolio_data("Jane Doe\nPython developer", "key", "gemini-test", client=client)

    assert data["name"] == "Jane Doe"
    assert data["skills"] == ["Python"]
    assert client.models.calls[0][0] == "gemini-test"
    assert "Return JSON only" in client.models.calls[0][1]


def test_extract_portfolio_data_prefers_chat_send_message_when_available():
    class FakeResponse:
        text = json.dumps({"name": "Jane Doe", "skills": ["Python"]})

    class FakeChat:
        def __init__(self):
            self.messages = []

        def send_message(self, message):
            self.messages.append(message)
            return FakeResponse()

    class FakeChats:
        def __init__(self):
            self.created = []
            self.chat = FakeChat()

        def create(self, model, config):
            self.created.append((model, config))
            return self.chat

    class FakeClient:
        def __init__(self):
            self.chats = FakeChats()

    client = FakeClient()

    data = main.extract_portfolio_data("Jane Doe\nPython developer", "key", "gemini-test", client=client)

    assert data["name"] == "Jane Doe"
    assert client.chats.created[0][0] == "gemini-test"
    assert "Return JSON only" in client.chats.chat.messages[0]


def test_run_generates_portfolio_with_fake_extractor(tmp_path, monkeypatch):
    resume = tmp_path / "resume.txt"
    templates = tmp_path / "templates"
    classic = templates / "classic"
    classic.mkdir(parents=True)
    template = classic / "template.html"
    css = classic / "style.css"
    output = tmp_path / "portfolio.html"
    resume.write_text(
        "Jane Doe\nEmail: jane@example.com\nPython Developer\nSkills: Python\nProject: Portfolio Generator",
        encoding="utf-8",
    )
    template.write_text("<html><head><style>{{ css }}</style></head><body>{{ content }}</body></html>", encoding="utf-8")
    css.write_text("body { font-family: Arial; }", encoding="utf-8")

    def fake_extract(cleaned_resume, api_key, model):
        assert api_key == "fake-key"
        assert model == "gemini-2.5-flash"
        assert "Jane Doe" in cleaned_resume
        return {
            "name": "Jane Doe",
            "headline": "Python Developer",
            "summary": "Python Developer",
            "skills": ["Python"],
            "projects": ["Portfolio Generator"],
            "contact": {"email": "jane@example.com"},
        }

    monkeypatch.setattr(main, "extract_portfolio_data", fake_extract)

    result = main.run(
        resume_path=resume,
        templates_dir=templates,
        template_name="classic",
        output_path=output,
        api_key="fake-key",
        model="gemini-2.5-flash",
    )

    assert result.output_path == output
    assert output.exists()
    assert "Jane Doe" in output.read_text(encoding="utf-8")

