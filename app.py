import streamlit as st
import re
import json
import time
from google import genai
from google.genai import types

def mask_pii(text):
    """
    Mask sensitive PII like SSNs and Credit Card numbers.
    This demonstrates basic regex usage for privacy pre-processing.
    """
    # Mask 9-digit SSN-like patterns (e.g., XXX-XX-XXXX)
    text = re.sub(r'\b\d{3}[-.\s]?\d{2}[-.\s]?\d{4}\b', '[REDACTED SSN]', text)
    
    # Mask 16-digit Credit Card numbers
    text = re.sub(r'\b(?:\d{4}[-.\s]?){3}\d{4}\b', '[REDACTED CC]', text)
    
    return text

def extract_portfolio_data(text, api_key):
    """
    Call the Gemini API to extract structured data from the resume text.
    Enforces JSON output via the system prompt and configuration.
    """
    client = genai.Client(api_key=api_key)
    
    prompt = f"""
    You are an expert resume parser. Extract the following information from the provided resume text and format it STRICTLY as a JSON object.
    Do not add markdown formatting (like ```json) to the output. Just return the raw JSON.
    
    Expected JSON Structure:
    {{
        "Name": "Full Name",
        "Contact": {{"Email": "email@example.com", "Phone": "...", "Links": ["url1", "url2"]}},
        "Summary": "A brief professional summary.",
        "Education": ["Degree in X from Y (Year)"],
        "Experience": ["Job Title at Company (Dates): Responsibilities"],
        "Projects": ["Project Name: Description"],
        "Skills": ["Skill 1", "Skill 2"],
        "Achievements": ["Achievement 1"]
    }}
    
    Resume Text:
    {text}
    """
    
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model='gemini-3.6-flash',
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                )
            )
            # Strip markdown formatting if the model incorrectly added it
            raw_text = response.text.replace("```json", "").replace("```", "").strip()
            return json.loads(raw_text)
        except Exception as e:
            error_str = str(e)
            # If it's a 503 error, wait and retry. Otherwise, or if out of retries, fail.
            if ("503" in error_str or "UNAVAILABLE" in error_str) and attempt < max_retries - 1:
                time.sleep(2 ** attempt)  # 1s, then 2s
                continue
            
            st.error(f"Error calling Gemini API: {e}")
            return None

def check_hallucinations(original_text, extracted_json):
    """
    Compare extracted skills and links against the original raw text 
    to flag potential hallucinations (items the AI invented).
    """
    original_lower = original_text.lower()
    hallucinations = {"skills": [], "links": []}
    
    if "Skills" in extracted_json:
        for skill in extracted_json["Skills"]:
            if skill.lower() not in original_lower:
                hallucinations["skills"].append(skill)
                
    if "Contact" in extracted_json and "Links" in extracted_json["Contact"]:
        for link in extracted_json["Contact"]["Links"]:
            if link.lower() not in original_lower:
                hallucinations["links"].append(link)
                
    return hallucinations

def generate_html(data):
    """Generate a simple, clean HTML template based on the extracted JSON data."""
    name = data.get("Name", "Portfolio")
    summary = data.get("Summary", "No summary provided.")
    
    contact_html = ""
    if "Contact" in data:
        email = data["Contact"].get("Email", "")
        phone = data["Contact"].get("Phone", "")
        links = data["Contact"].get("Links", [])
        
        if email: contact_html += f"<p><strong>Email:</strong> {email}</p>"
        if phone: contact_html += f"<p><strong>Phone:</strong> {phone}</p>"
        for link in links:
            contact_html += f'<p><a href="{link}" target="_blank">{link}</a></p>'
            
    skills_html = "".join([f"<li>{skill}</li>" for skill in data.get("Skills", [])])
    exp_html = "".join([f"<li>{exp}</li>" for exp in data.get("Experience", [])])
    edu_html = "".join([f"<li>{edu}</li>" for edu in data.get("Education", [])])
    proj_html = "".join([f"<li>{proj}</li>" for proj in data.get("Projects", [])])

    html_template = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{name} - Portfolio</title>
        <style>
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; margin: 0; padding: 0; background-color: #f8f9fa; color: #333; }}
            .container {{ max-width: 900px; margin: 40px auto; background: white; padding: 40px; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }}
            h1 {{ color: #2c3e50; font-size: 2.5em; margin-bottom: 5px; }}
            h2 {{ color: #34495e; border-bottom: 2px solid #ecf0f1; padding-bottom: 10px; margin-top: 30px; }}
            .contact-info {{ color: #7f8c8d; margin-bottom: 30px; }}
            .contact-info a {{ color: #3498db; text-decoration: none; }}
            .contact-info a:hover {{ text-decoration: underline; }}
            .section {{ margin-bottom: 25px; }}
            ul {{ padding-left: 20px; }}
            li {{ margin-bottom: 8px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <header class="section">
                <h1>{name}</h1>
                <div class="contact-info">{contact_html}</div>
            </header>
            
            <section class="section">
                <h2>Professional Summary</h2>
                <p>{summary}</p>
            </section>
            
            <section class="section">
                <h2>Skills</h2>
                <ul>{skills_html if skills_html else "<li>No skills listed.</li>"}</ul>
            </section>
            
            <section class="section">
                <h2>Experience</h2>
                <ul>{exp_html if exp_html else "<li>No experience listed.</li>"}</ul>
            </section>
            
            <section class="section">
                <h2>Projects</h2>
                <ul>{proj_html if proj_html else "<li>No projects listed.</li>"}</ul>
            </section>
            
            <section class="section">
                <h2>Education</h2>
                <ul>{edu_html if edu_html else "<li>No education listed.</li>"}</ul>
            </section>
        </div>
    </body>
    </html>
    """
    return html_template

def main():
    st.set_page_config(page_title="AI Portfolio Generator", layout="wide", page_icon="📄")
    
    st.title("AI-Assisted Portfolio Generator")
    st.markdown("Transform your raw resume text into a structured, responsive portfolio website using **Google Gemini 3.6 Flash**.")
    
    # Sidebar for Configuration
    with st.sidebar:
        st.header("⚙️ Configuration")
        api_key = st.text_input("Google Gemini API Key", type="password")
        st.markdown("[Get your API key here](https://aistudio.google.com/app/apikey)")
        st.divider()
        st.markdown("### About")
        st.markdown("This app demonstrates:")
        st.markdown("- **Regex**: Masking PII (SSN/CC)")
        st.markdown("- **LLM Integration**: Gemini API parsing")
        st.markdown("- **Prompt Eng**: Deterministic JSON output")
        st.markdown("- **Verification**: Basic hallucination detection")
        
    # Main Content Area
    st.subheader("1. Input Resume Content")
    raw_resume = st.text_area("Paste your resume text here:", height=250, placeholder="John Doe\njohndoe@email.com\n\nExperience: Software Engineer at Tech Corp...")
    
    if st.button("🚀 Generate Portfolio", type="primary"):
        if not api_key:
            st.warning("⚠️ Please enter your Gemini API Key in the sidebar.")
            return
        if not raw_resume.strip():
            st.warning("⚠️ Please paste your resume text.")
            return
            
        with st.spinner("Analyzing resume and generating portfolio..."):
            # Step 1: Pre-processing (Mask PII)
            masked_resume = mask_pii(raw_resume)
            
            # Step 2: LLM Extraction
            extracted_data = extract_portfolio_data(masked_resume, api_key)
            
            if extracted_data:
                # Step 3: Post-processing (Hallucination Check)
                hallucinations = check_hallucinations(raw_resume, extracted_data)
                
                st.success("✅ Portfolio generated successfully!")
                st.divider()
                
                # Step 4: Display & Export
                st.subheader("2. Results & Export")
                tab1, tab2, tab3 = st.tabs(["👁️ Live Preview", "🧩 Raw JSON", "🛡️ Hallucination Report"])
                
                with tab1:
                    html_content = generate_html(extracted_data)
                    st.components.v1.html(html_content, height=600, scrolling=True)
                    
                    st.download_button(
                        label="⬇️ Download portfolio.html",
                        data=html_content,
                        file_name="portfolio.html",
                        mime="text/html"
                    )
                    
                with tab2:
                    st.json(extracted_data)
                    
                with tab3:
                    st.markdown("### Hallucination Check")
                    st.info("This simple algorithm checks if the extracted skills and links actually appear in the original text. It helps flag information the AI might have fabricated.")
                    
                    if not hallucinations["skills"] and not hallucinations["links"]:
                        st.success("✅ No hallucinations detected in Skills or Links!")
                    else:
                        if hallucinations["skills"]:
                            st.warning(f"⚠️ **Potentially Hallucinated Skills:** {', '.join(hallucinations['skills'])}")
                        if hallucinations["links"]:
                            st.warning(f"⚠️ **Potentially Hallucinated Links:** {', '.join(hallucinations['links'])}")

if __name__ == "__main__":
    main()
