import os
from pathlib import Path
import streamlit as st
import streamlit.components.v1 as components

from dotenv import load_dotenv

from main import (
    DEFAULT_MODEL,
    DEFAULT_TEMPLATE,
    list_templates,
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
    load_dotenv(override=True)
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

    env_api_key = os.getenv("GEMINI_API_KEY", "").strip()
    api_key_input = st.sidebar.text_input(
        "Gemini API Key",
        value=env_api_key,
        type="password",
        help="Enter your Gemini API key or set GEMINI_API_KEY in your .env file.",
    )

    env_model = os.getenv("GEMINI_MODEL", DEFAULT_MODEL).strip() or DEFAULT_MODEL
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
                output_path = result.output_path.resolve()
                st.session_state["portfolio_html"] = output_path.read_text(encoding="utf-8")
                st.session_state["portfolio_path"] = str(output_path)
                st.session_state["file_uri"] = output_path.as_uri()
                st.session_state["output_filename"] = output_filename
                st.session_state["hallucination_report"] = result.hallucination_report
            except Exception as exc:
                st.error(f"❌ Generation Failed: {exc}")
                return

    if "portfolio_html" in st.session_state:
        st.success(f"🎉 Portfolio generated successfully! Saved to: `{st.session_state['portfolio_path']}`")

        col1, col2 = st.columns([2, 1])
        with col1:
            st.markdown(f"🔗 **Local Portfolio URL:** [`{st.session_state['file_uri']}`]({st.session_state['file_uri']})")
        with col2:
            st.download_button(
                label="📥 Download Portfolio HTML",
                data=st.session_state["portfolio_html"].encode("utf-8"),
                file_name=st.session_state["output_filename"],
                mime="text/html",
                use_container_width=True,
            )

        flagged = {k: v for k, v in st.session_state["hallucination_report"].items() if v}
        if flagged:
            st.warning("⚠️ **Verification Warning**: The following items were flagged for review against your original resume:")
            for key, values in flagged.items():
                st.write(f"- **{key.title()}**: {', '.join(values)}")
        else:
            st.info("✅ **Verification Passed**: No unsupported skills, links, or projects were detected.")

        st.subheader("2. Live Portfolio Preview")
        components.html(st.session_state["portfolio_html"], height=800, scrolling=True)


if __name__ == "__main__":
    main()
