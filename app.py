import os
from pathlib import Path
import streamlit as st
import streamlit.components.v1 as components

from main import (
    DEFAULT_MODEL,
    DEFAULT_TEMPLATE,
    GeminiConfigurationError,
    ResumeInputError,
    ResumePortfolioError,
    list_templates,
    load_api_key,
    load_model,
    run,
)


def get_default_resume_text() -> str:
    resume_file = Path("resume.txt")
    if resume_file.exists():
        try:
            return resume_file.read_text(encoding="utf-8").strip()
        except Exception:
            pass
    return ""


def main() -> None:
    st.set_page_config(
        page_title="AI Resume Portfolio Generator",
        page_icon="💼",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    st.title("💼 AI Resume Portfolio Generator")
    st.markdown(
        "Generate a clean, beautiful personal portfolio web page from your resume using Google Gemini AI."
    )

    # Sidebar setup
    st.sidebar.header("⚙️ Configuration")

    env_api_key = load_api_key()
    api_key_input = st.sidebar.text_input(
        "Gemini API Key",
        value=env_api_key,
        type="password",
        help="Enter your Gemini API key or set GEMINI_API_KEY in your .env file.",
    )

    env_model = load_model()
    model_options = ["gemini-2.5-flash", "gemini-1.5-flash", "gemini-1.5-pro", "gemini-3.1-flash-lite"]
    model_default_idx = model_options.index(env_model) if env_model in model_options else 0
    selected_model = st.sidebar.selectbox("Gemini Model", model_options, index=model_default_idx)

    available_templates = list_templates()
    if not available_templates:
        available_templates = [DEFAULT_TEMPLATE]
    selected_template = st.sidebar.selectbox("Portfolio Template", available_templates, index=0)

    output_filename = st.sidebar.text_input("Output HTML Filename", value="portfolio.html")

    # Main content layout
    st.subheader("1. Resume Input")

    input_mode = st.radio("Choose Resume Source:", ["Type / Paste Text", "Upload Text File (.txt, .md)"], horizontal=True)

    resume_content = ""
    if input_mode == "Type / Paste Text":
        default_resume = get_default_resume_text()
        resume_content = st.text_area(
            "Paste your resume text here:",
            value=default_resume,
            height=300,
            placeholder="Paste your full resume text here...",
        )
    else:
        uploaded_file = st.file_uploader("Upload resume file", type=["txt", "md"])
        if uploaded_file is not None:
            resume_content = uploaded_file.getvalue().decode("utf-8")
            st.text_area("Uploaded Resume Preview:", value=resume_content, height=200, disabled=True)

    st.divider()

    generate_btn = st.button("✨ Generate Portfolio", type="primary", use_container_width=True)

    if generate_btn:
        if not api_key_input.strip():
            st.error("🔑 Gemini API Key is required. Please enter it in the sidebar configuration.")
            return

        if not resume_content.strip():
            st.error("📄 Resume text is empty. Please enter or upload your resume text.")
            return

        with st.spinner("🤖 Gemini is analyzing your resume and building your portfolio HTML..."):
            try:
                result = run(
                    resume_text=resume_content,
                    output_path=output_filename,
                    api_key=api_key_input.strip(),
                    model=selected_model,
                    template_name=selected_template,
                )
            except ResumePortfolioError as exc:
                st.error(f"❌ Generation Failed: {exc}")
                return
            except Exception as exc:
                st.error(f"❌ An unexpected error occurred: {exc}")
                return

        output_path = result.output_path.resolve()
        file_uri = output_path.as_uri()

        st.success(f"🎉 Portfolio generated successfully! Saved to: `{output_path}`")

        # Display Local URL Link & Download Button
        col1, col2 = st.columns([2, 1])
        with col1:
            st.markdown(f"🔗 **Local Portfolio URL:** [`{file_uri}`]({file_uri})")
        with col2:
            if output_path.exists():
                html_bytes = output_path.read_bytes()
                st.download_button(
                    label="📥 Download Portfolio HTML",
                    data=html_bytes,
                    file_name=output_filename,
                    mime="text/html",
                    use_container_width=True,
                )

        # Verification Report Section
        flagged = {k: v for k, v in result.hallucination_report.items() if v}
        if flagged:
            st.warning("⚠️ **Verification Warning**: The following items were flagged for review against your original resume:")
            for key, values in flagged.items():
                st.write(f"- **{key.title()}**: {', '.join(values)}")
        else:
            st.info("✅ **Verification Passed**: No unsupported skills, links, or projects were detected.")

        # Live HTML Preview inside Streamlit
        st.subheader("2. Live Portfolio Preview")
        if output_path.exists():
            html_content = output_path.read_text(encoding="utf-8")
            components.html(html_content, height=800, scrolling=True)


if __name__ == "__main__":
    main()
