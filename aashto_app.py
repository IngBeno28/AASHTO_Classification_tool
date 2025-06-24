import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import re
from fpdf import FPDF
from io import BytesIO
from typing import List

# --- Classification Logic ---
granular_materials = ["A-1-a", "A-1-b", "A-3", "A-2-4", "A-2-5", "A-2-6", "A-2-7"]
silty_clay_materials = ["A-4", "A-5", "A-6", "A-7"]

def classify_soil(LL, PL, PI, pass_10, pass_40, pass_200, is_np):
    if is_np:
        PI = 0
    if pass_10 <= 50 and pass_40 <= 30 and pass_200 <= 15 and PI <= 6:
        return "A-1-a"
    elif pass_40 <= 50 and pass_200 <= 25 and PI <= 6:
        return "A-1-b"
    elif pass_40 >= 51 and pass_200 <= 10 and PI == 0:
        return "A-3"
    elif pass_200 <= 35 and LL <= 40 and PI <= 10:
        return "A-2-4"
    elif pass_200 <= 35 and LL >= 41 and PI <= 10:
        return "A-2-5"
    elif pass_200 <= 35 and LL <= 40 and PI >= 11:
        return "A-2-6"
    elif pass_200 <= 35 and LL >= 41 and PI >= 11:
        return "A-2-7"
    elif pass_200 >= 36 and LL <= 40 and PI <= 10:
        return "A-4"
    elif pass_200 >= 36 and LL >= 41 and PI <= 10:
        return "A-5"
    elif pass_200 >= 36 and LL <= 40 and PI >= 11:
        return "A-6"
    elif pass_200 >= 36 and LL >= 41 and PI >= 11:
        return "A-7"
    else:
        return "Invalid input or not classifiable"

def classify_material_type(pass_200):
    return "Granular Material" if pass_200 <= 35 else "Silt-Clay Material"

def identify_constituents_from_classification(classification):
    if classification in ("A-1-a", "A-1-b"):
        return "Stone fragments, Gravel and Sand"
    elif classification == "A-3":
        return "Fine sand"
    elif classification in ("A-2-4", "A-2-5", "A-2-6", "A-2-7"):
        return "Silty or Clayey Gravel and Sand"
    elif classification in ("A-4", "A-5"):
        return "Silty soils"
    elif classification in ("A-6", "A-7"):
        return "Clayey soils"
    else:
        return "Unknown"

def generate_soil_analysis(group: str, PI: float, LL: float, passing_200: float,
                           passing_40: float, passing_10: float, flags: List[str]) -> str:
    description_map = {
        "A-1-a": "Well-graded gravel and sand with minimal fines. Excellent for subbase and base courses.",
        "A-1-b": "Coarser than A-1-a, mostly gravel. High strength, great for heavy-duty subbases.",
        "A-2-4": "Silty or clayey sand with low plasticity. Suitable for lightly loaded subgrades.",
        "A-2-5": "Clayey sand with higher PI. Moderate strength, sensitive to moisture.",
        "A-2-6": "Silty/clayey sand with high PI and LL. Moderate, but moisture-sensitive.",
        "A-2-7": "Very silty/clayey sand with high PI and LL. Marginal quality, prone to expansion.",
        "A-3": "Clean sand, non-plastic. Good for subbase with excellent drainage.",
        "A-4": "Low plasticity silts. Fair performance, sensitive to moisture.",
        "A-5": "Silty soils with higher LL. Low strength and frost susceptible.",
        "A-6": "Clayey soils with moderate plasticity. Prone to shrink-swell behavior.",
        "A-7-5": "Silty clays with high LL. Weak, moisture sensitive, poor drainage.",
        "A-7-6": "Highly plastic clays. Very low strength, severe expansion risk."
    }

    explanation = f"🧾 **Soil Classification Analysis: {group}**\n\n"

    if group in description_map:
        explanation += f"{description_map[group]}\n\n"
    else:
        explanation += "Unrecognized AASHTO group. Limited analysis available.\n\n"

    if PI > 20:
        explanation += f"- High Plasticity (PI = {PI}): Soil may swell or shrink with moisture.\n"
    elif PI > 10:
        explanation += f"- Moderate Plasticity (PI = {PI}): May be moisture-sensitive.\n"
    else:
        explanation += f"- Low Plasticity (PI = {PI}): Stable and less moisture-sensitive.\n"

    if LL > 50:
        explanation += f"- Very High Liquid Limit (LL = {LL}): Indicates poor drainage and high compressibility.\n"
    elif LL > 40:
        explanation += f"- High Liquid Limit (LL = {LL}): May be sensitive to water content changes.\n"
    else:
        explanation += f"- Low Liquid Limit (LL = {LL}): Generally stable.\n"

    explanation += f"- Fines (Passing #200): {passing_200}% — "
    if passing_200 > 35:
        explanation += "High fines content. Increased moisture sensitivity.\n"
    elif passing_200 > 15:
        explanation += "Moderate fines. Drainage and compaction may be affected.\n"
    else:
        explanation += "Low fines. Likely to drain well.\n"

    explanation += f"- Passing #40: {passing_40}%, Passing #10: {passing_10}%\n"

    if flags:
        explanation += "\n🚩 **Red Flags Detected:**\n"
        for flag in flags:
            if flag == "stone":
                explanation += "- Presence of stone: May cause inconsistent compaction.\n"
            elif flag == "organic_matter":
                explanation += "- Organic matter: May decay and reduce long-term strength.\n"
            elif flag == "mottled_color":
                explanation += "- Mottled color: May indicate fluctuating water tables.\n"
            else:
                explanation += f"- {flag.replace('_', ' ').capitalize()}: Review required.\n"

    return explanation.strip()

from fpdf import FPDF
from pathlib import Path

def create_pdf(content):
    pdf = FPDF()
    pdf.add_page()
    
    # Define the font path 
    font_path = "fonts/DejaVuSans.ttf"
    if not font_path.exists():
    raise FileNotFoundError(f"Font file not found at: {font_path}")
    
    # Add the font to FPDF
    pdf.add_font("DejaVu", "", str(font_path), uni=True)
    pdf.set_font("DejaVu", size=12)
    
    # Add content
    for line in content.split('\n'):
        pdf.cell(200, 10, txt=line, ln=True, align='L')
    
    # Generate PDF bytes
    buffer = BytesIO()
    pdf.output(buffer)
    return buffer.getvalue()


# --- Streamlit UI ---
st.set_page_config(page_title="AASHTO Soil Classifier", layout="centered")
st.title("🧪 AASHTO Soil Classification Tool \n Powered by: Automation_hub")

with st.form("soil_form"):
    st.subheader("Atterberg Limits")
    LL = st.number_input("Liquid Limit (LL)", min_value=0)
    PL = st.number_input("Plastic Limit (PL)", min_value=0)
    is_np = st.checkbox("Check if Non-Plastic (N.P)")
    PI = 0 if is_np else LL - PL
    if not is_np:
        st.write(f"Plasticity Index (PI) = **{PI}**")

    st.subheader("Sieve Analysis (%) Passing")
    pass_10 = st.number_input("Sieve No. 10 (2.0 mm)", min_value=0, max_value=100)
    pass_40 = st.number_input("Sieve No. 40 (0.425 mm)", min_value=0, max_value=100)
    pass_200 = st.number_input("Sieve No. 200 (0.075 mm)", min_value=0, max_value=100)

    red_flags = st.multiselect("🚩 Select any red flags identified in the soil:",
                               ["stone", "organic_matter", "mottled_color"])

    submitted = st.form_submit_button("Classify Soil")

if submitted:
    classification = classify_soil(LL, PL, PI, pass_10, pass_40, pass_200, is_np)
    mat_type = classify_material_type(pass_200)
    constituents = identify_constituents_from_classification(classification)

    st.success(f"🧾 AASHTO Classification: **{classification}**")
    st.info(f"🧱 Material Type: **{mat_type}**")
    st.write(f"🔬 Significant Constituent Materials: **{constituents}**")

    if classification in granular_materials:
        st.success("🟢 General Subgrade Rating: **Excellent to Good**")
    elif classification in silty_clay_materials:
        st.warning("🟠 General Subgrade Rating: **Fair to Poor**")

    # 📋 Add rule-based AI soil analysis
    st.subheader("🤖 AI-Based Soil Analysis")
    ai_summary = generate_soil_analysis(classification, PI, LL, pass_200, pass_40, pass_10, red_flags)
    st.markdown(ai_summary)

    # Bar chart of sieve results
    st.subheader("📊 Sieve Analysis Chart")
    sieve_data = pd.DataFrame({
        'Sieve Size (mm)': ['2.0 (No.10)', '0.425 (No.40)', '0.075 (No.200)'],
        '% Passing': [pass_10, pass_40, pass_200]
    })
    fig, ax = plt.subplots()
    ax.bar(sieve_data['Sieve Size (mm)'], sieve_data['% Passing'], color='skyblue')
    ax.set_ylim(0, 100)
    ax.set_ylabel('% Passing')
    ax.set_title('Sieve Analysis Results')
    st.pyplot(fig)

    # Export results
    st.subheader("📥 Download Results")
    export_df = pd.DataFrame({
        'Classification': [classification],
        'Material Type': [mat_type],
        'Significant Constituents': [constituents],
        'LL': [LL],
        'PL': [PL],
        'PI': [PI],
        'Pass 2.0mm': [pass_10],
        'Pass 0.425mm': [pass_40],
        'Pass 0.075mm': [pass_200],
        'AI Analysis': [ai_summary]
    })
    st.download_button("Download as CSV", export_df.to_csv(index=False), "classification_results.csv", "text/csv")

    pdf_bytes = create_pdf(ai_summary)
    st.download_button("Download AI Analysis as PDF", pdf_bytes, file_name="soil_analysis.pdf", mime="application/pdf")

# --- Footer ---
st.markdown("---")
st.caption("© 2025 AASHTO Classifying_tool | Built by Automation_hub")
