# main.py — AASHTO Soil Classification Tool (AASHTO M 145 / ASTM D3282)
# Automation_hub Engineering Group Limited

import io
import os
import tempfile
from datetime import datetime
from typing import List, Optional

import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st
from fpdf import FPDF
from PIL import Image

from branding import (
    CLIENT_NAME, APP_TITLE, PRIMARY_COLOR, LOGO_PATH, FOOTER_NOTE, LOGO_ALT_TEXT,
    COMPANY_ADDRESS, COMPANY_PHONE, COMPANY_EMAIL, COMPANY_WEBSITE
)

st.set_page_config(page_title=APP_TITLE, page_icon="🏗️", layout="wide")

if os.path.exists("style.css"):
    with open("style.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# =============================================================================
# 1. CLASSIFICATION LOGIC (unchanged from original, AASHTO M 145 / ASTM D3282)
# =============================================================================

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

    explanation = f"**Soil Classification Analysis: {group}**\n\n"

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

    explanation += f"- Fines (Passing #200): {passing_200}%  -  "
    if passing_200 > 35:
        explanation += "High fines content. Increased moisture sensitivity.\n"
    elif passing_200 > 15:
        explanation += "Moderate fines. Drainage and compaction may be affected.\n"
    else:
        explanation += "Low fines. Likely to drain well.\n"

    explanation += f"- Passing #40: {passing_40}%, Passing #10: {passing_10}%\n"

    if flags:
        explanation += "\n**Red Flags Detected:**\n"
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


def get_subgrade_rating(classification: str) -> str:
    if classification in granular_materials:
        return "Excellent to Good"
    elif classification in silty_clay_materials:
        return "Fair to Poor"
    return "Not determined"


# =============================================================================
# 2. CHART
# =============================================================================

def create_sieve_chart(pass_10, pass_40, pass_200, label="Sample"):
    sieve_data = pd.DataFrame({
        'Sieve Size (mm)': ['2.0 (No.10)', '0.425 (No.40)', '0.075 (No.200)'],
        '% Passing': [pass_10, pass_40, pass_200]
    })
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.bar(sieve_data['Sieve Size (mm)'], sieve_data['% Passing'], color='#0052cc')
    ax.set_ylim(0, 100)
    ax.set_ylabel('% Passing')
    ax.set_title(f'Sieve Analysis Results - {label}')
    fig.tight_layout()
    return fig


def fig_to_png_bytes(fig, dpi=150):
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=dpi, bbox_inches='tight')
    return buf.getvalue()


# =============================================================================
# 3. PDF REPORT
# =============================================================================

def hex_to_rgb(hex_color):
    try:
        h = hex_color.lstrip('#')
        return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))
    except Exception:
        return (0, 82, 204)


class BrandedPDF(FPDF):
    def footer(self):
        contact_parts = []
        if COMPANY_PHONE:
            contact_parts.append(f"Tel: {COMPANY_PHONE}")
        if COMPANY_EMAIL:
            contact_parts.append(f"Email: {COMPANY_EMAIL}")
        if COMPANY_WEBSITE:
            contact_parts.append(f"Web: {COMPANY_WEBSITE}")
        if COMPANY_ADDRESS:
            contact_parts.append(COMPANY_ADDRESS)
        contact_line = " | ".join(contact_parts)

        self.set_y(-24 if contact_line else -18)
        self.set_draw_color(180, 180, 180)
        self.line(10, self.get_y(), self.w - 10, self.get_y())
        self.set_font("Arial", '', 8)
        self.set_text_color(120, 120, 120)
        footer_left = f"{CLIENT_NAME} | {FOOTER_NOTE}" if FOOTER_NOTE else CLIENT_NAME
        self.cell(0, 6, footer_left.encode('latin-1', errors='replace').decode('latin-1'), 0, 0, 'L')
        self.cell(0, 6, f"Page {self.page_no()}/{{nb}}", 0, 1, 'R')
        if contact_line:
            self.set_x(10)
            self.cell(0, 6, contact_line.encode('latin-1', errors='replace').decode('latin-1'), 0, 1, 'L')
        self.set_text_color(0, 0, 0)


def create_pdf_report(samples: list, project_name: str, client_name: str = "",
                       engineer_name: str = "", stamp_image_path: str = None) -> Optional[bytes]:
    """samples: list of dicts, each with keys:
    sample_id, classification, mat_type, constituents, LL, PL, PI, is_np,
    pass_10, pass_40, pass_200, red_flags, ai_summary, chart_png
    """
    try:
        pdf = BrandedPDF()
        pdf.alias_nb_pages()
        pdf.set_auto_page_break(auto=True, margin=22)

        def safe_text(text):
            if not isinstance(text, str):
                text = str(text)
            return text.encode('latin-1', errors='replace').decode('latin-1')

        def draw_table_row(col_widths, values, aligns=None, line_height=5, min_row_height=8, bold=False):
            if aligns is None:
                aligns = ['L'] * len(values)
            pdf.set_font("Arial", 'B' if bold else '', 10)
            x_start = (pdf.w - sum(col_widths)) / 2

            def wrap(text, width):
                text = safe_text(text)
                usable = width - 2
                words = text.split(' ')
                lines, current = [], ""
                for word in words:
                    trial = (current + " " + word).strip()
                    if not current or pdf.get_string_width(trial) <= usable:
                        current = trial
                    else:
                        lines.append(current)
                        current = word
                if current:
                    lines.append(current)
                return lines or [""]

            wrapped = [wrap(v, w) for v, w in zip(values, col_widths)]
            n_lines = max(len(w) for w in wrapped)
            row_height = max(min_row_height, n_lines * line_height)

            if pdf.get_y() + row_height > pdf.h - pdf.b_margin:
                pdf.add_page()

            y_start = pdf.get_y()
            x = x_start
            for width, lines, align in zip(col_widths, wrapped, aligns):
                pdf.rect(x, y_start, width, row_height)
                pdf.set_xy(x, y_start + (row_height - len(lines) * line_height) / 2)
                for line in lines:
                    pdf.set_x(x)
                    pdf.cell(width, line_height, line, 0, 2, align)
                x += width
            pdf.set_y(y_start + row_height)
            pdf.set_x(pdf.l_margin)

        def render_markdown_lite(text):
            """Render the '**bold**' / '- bullet' style AI summary text as PDF paragraphs."""
            for raw_line in text.split("\n"):
                line = raw_line.strip()
                if not line:
                    pdf.ln(2)
                    continue
                bold = line.startswith("**") and line.count("**") >= 2
                clean = line.replace("**", "")
                if clean.startswith("- "):
                    clean = "    " + chr(8226) + " " + clean[2:]  # bullet char, safe in latin-1
                clean = clean.strip()
                if not clean:
                    continue
                pdf.set_font("Arial", 'B' if bold else '', 10)
                pdf.set_x(pdf.l_margin)
                pdf.multi_cell(0, 5.5, safe_text(clean))

        # --- Cover Page ---
        pdf.add_page()
        accent_rgb = hex_to_rgb(PRIMARY_COLOR)
        pdf.set_fill_color(*accent_rgb)
        pdf.rect(0, 0, pdf.w, 10, 'F')

        logo_bottom = 28
        if LOGO_PATH and os.path.exists(LOGO_PATH):
            try:
                with Image.open(LOGO_PATH) as img:
                    if img.mode != 'RGB':
                        img = img.convert('RGB')
                    temp_logo_path = os.path.join(tempfile.gettempdir(),
                                                f"temp_logo_{datetime.now().strftime('%Y%m%d%H%M%S')}.jpg")
                    img.save(temp_logo_path, format='JPEG', quality=95)
                    pdf.image(temp_logo_path, x=(pdf.w - 40) / 2, y=22, w=40)
                    os.unlink(temp_logo_path)
                logo_bottom = 22 + 40 + 8
            except Exception as e:
                st.error(f"Logo processing error: {str(e)}")

        pdf.set_y(logo_bottom)
        pdf.set_font("Arial", 'B', 24)
        pdf.set_text_color(*accent_rgb)
        pdf.cell(0, 14, safe_text("AASHTO Soil Classification Report"), 0, 1, 'C')
        pdf.set_text_color(90, 90, 90)
        pdf.set_font("Arial", '', 12)
        pdf.cell(0, 8, safe_text(APP_TITLE), 0, 1, 'C')
        pdf.set_text_color(0, 0, 0)

        pdf.ln(4)
        pdf.set_draw_color(*accent_rgb)
        pdf.set_line_width(0.6)
        pdf.line(50, pdf.get_y(), pdf.w - 50, pdf.get_y())
        pdf.set_line_width(0.2)
        pdf.set_draw_color(0, 0, 0)
        pdf.ln(12)

        info_rows = [("Project", project_name)]
        if client_name:
            info_rows.append(("Prepared For", client_name))
        info_rows.append(("Prepared By", CLIENT_NAME))
        info_rows.append(("Date Generated", datetime.now().strftime('%Y-%m-%d %H:%M')))
        info_rows.append(("Total Samples", str(len(samples))))

        panel_w, label_w, row_h = 150, 55, 9
        x0 = (pdf.w - panel_w) / 2
        y0 = pdf.get_y()
        panel_h = row_h * len(info_rows)
        pdf.set_draw_color(200, 200, 200)
        pdf.rect(x0, y0, panel_w, panel_h)
        for idx, (label, value) in enumerate(info_rows):
            y = y0 + idx * row_h
            if idx > 0:
                pdf.line(x0, y, x0 + panel_w, y)
            pdf.set_xy(x0 + 4, y)
            pdf.set_font("Arial", 'B', 11)
            pdf.cell(label_w - 4, row_h, safe_text(label), 0, 0, 'L')
            pdf.set_font("Arial", '', 11)
            pdf.cell(panel_w - label_w - 4, row_h, safe_text(value), 0, 0, 'L')
        pdf.set_draw_color(0, 0, 0)
        pdf.set_y(y0 + panel_h + 14)

        if FOOTER_NOTE:
            pdf.set_font("Arial", 'I', 10)
            pdf.set_text_color(120, 120, 120)
            pdf.cell(0, 8, safe_text(FOOTER_NOTE), 0, 1, 'C')
            pdf.set_text_color(0, 0, 0)

        # --- Per-Sample Pages ---
        for i, s in enumerate(samples, 1):
            pdf.add_page()
            pdf.set_font("Arial", 'B', 16)
            pdf.cell(0, 10, safe_text(f"Sample: {s.get('sample_id', f'Sample {i}')}"), 0, 1, 'C')
            pdf.set_font("Arial", 'B', 20)
            pdf.set_text_color(*accent_rgb)
            pdf.cell(0, 12, safe_text(f"AASHTO Classification: {s['classification']}"), 0, 1, 'C')
            pdf.set_text_color(0, 0, 0)
            pdf.set_font("Arial", '', 11)
            pdf.cell(0, 7, safe_text(s['mat_type']), 0, 1, 'C')
            pdf.ln(4)

            col_widths = [70, 60, 30]
            draw_table_row(col_widths, ["Parameter", "Value", "Unit"], aligns=['L', 'C', 'C'], bold=True)
            rows = [
                ("Significant Constituents", s['constituents'], ""),
                ("Liquid Limit (LL)", s['LL'] if not s.get('is_np') else "N/A (NP)", "%"),
                ("Plastic Limit (PL)", s['PL'] if not s.get('is_np') else "N/A (NP)", "%"),
                ("Plasticity Index (PI)", s['PI'], "%"),
                ("Passing No. 10 (2.0mm)", s['pass_10'], "%"),
                ("Passing No. 40 (0.425mm)", s['pass_40'], "%"),
                ("Passing No. 200 (0.075mm)", s['pass_200'], "%"),
                ("General Subgrade Rating", get_subgrade_rating(s['classification']), ""),
                ("Red Flags", ", ".join(s['red_flags']).replace("_", " ").title() if s.get('red_flags') else "None", ""),
            ]
            for p, v, u in rows:
                draw_table_row(col_widths, [p, v, u], aligns=['L', 'C', 'C'])

            pdf.ln(4)
            pdf.set_font("Arial", 'B', 12)
            pdf.set_x(pdf.l_margin)
            pdf.cell(0, 8, safe_text("Engineering Interpretation"), 0, 1, 'L')
            render_markdown_lite(s.get('ai_summary', ''))

            if s.get("chart_png"):
                pdf.ln(4)
                try:
                    chart_path = os.path.join(tempfile.gettempdir(),
                                            f"temp_sieve_{i}_{datetime.now().strftime('%Y%m%d%H%M%S%f')}.png")
                    with open(chart_path, 'wb') as f:
                        f.write(s["chart_png"])
                    if pdf.get_y() + 80 > pdf.h - pdf.b_margin:
                        pdf.add_page()
                    pdf.image(chart_path, x=(pdf.w - 150) / 2, w=150)
                    os.unlink(chart_path)
                except Exception:
                    pass

        # --- Certification Page ---
        pdf.add_page()
        pdf.set_font("Arial", 'B', 18)
        pdf.cell(0, 15, safe_text("Certification"), 0, 1, 'C')
        pdf.ln(4)
        pdf.set_font("Arial", '', 11)
        pdf.set_x(pdf.l_margin)
        pdf.multi_cell(0, 7, safe_text(
            "This soil classification report has been reviewed and is certified as suitable "
            "for the stated project and engineering requirements."
        ))
        pdf.ln(10)

        pdf.set_font("Arial", 'B', 11)
        pdf.cell(60, 8, safe_text("Engineer Name:"), 0, 0)
        pdf.set_font("Arial", '', 11)
        pdf.cell(0, 8, safe_text(engineer_name), 'B', 1)
        pdf.ln(6)

        pdf.set_font("Arial", 'B', 11)
        pdf.cell(60, 8, safe_text("Date:"), 0, 0)
        pdf.set_font("Arial", '', 11)
        pdf.cell(0, 8, safe_text(datetime.now().strftime('%Y-%m-%d')), 'B', 1)
        pdf.ln(15)

        pdf.set_font("Arial", 'B', 11)
        pdf.cell(0, 8, safe_text("Signature / Stamp"), 0, 1)
        box_y = pdf.get_y()
        box_w, box_h = 70, 35
        if stamp_image_path and os.path.exists(stamp_image_path):
            try:
                pdf.image(stamp_image_path, x=15, y=box_y, w=box_w, h=box_h)
            except Exception:
                pdf.rect(15, box_y, box_w, box_h)
        else:
            pdf.rect(15, box_y, box_w, box_h)
        pdf.set_y(box_y + box_h + 8)

        pdf.set_font("Arial", '', 9)
        pdf.set_text_color(120, 120, 120)
        prepared_by = f"Report prepared using {APP_TITLE} by {CLIENT_NAME}."
        if FOOTER_NOTE:
            prepared_by += f" {FOOTER_NOTE}"
        pdf.set_x(pdf.l_margin)
        pdf.multi_cell(0, 5, safe_text(prepared_by))
        pdf.set_text_color(0, 0, 0)

        pdf_output = pdf.output()
        if isinstance(pdf_output, (bytes, bytearray)):
            return bytes(pdf_output)
        return pdf_output.encode('latin-1', errors='replace')

    except Exception as e:
        st.error(f"PDF generation failed: {str(e)}")
        return None


# =============================================================================
# 4. UI
# =============================================================================

if LOGO_PATH and os.path.exists(LOGO_PATH):
    st.image(LOGO_PATH, width=180)

st.title("🏗️ AASHTO Soil Classification Tool")
st.caption(f"⚡ Powered by {CLIENT_NAME}  -  AASHTO M 145 / ASTM D3282")

st.markdown("**Project Name**")
project_name = st.text_input("", "Unnamed Project", key="project_name_input", label_visibility="collapsed")

st.markdown("**Client / Project Owner**")
client_name = st.text_input("", "", key="client_name_input", label_visibility="collapsed")

with st.expander("🖋️ Certification Details (for PDF Report)"):
    st.markdown("**Engineer Name**")
    engineer_name = st.text_input("", st.session_state.get('engineer_name', ''), key="engineer_name_input")
    st.session_state['engineer_name'] = engineer_name

    st.markdown("**Signature / Stamp Image (optional)**")
    stamp_file = st.file_uploader("", type=['png', 'jpg', 'jpeg'], key="stamp_upload")
    if stamp_file is not None:
        st.session_state['stamp_bytes'] = stamp_file.getvalue()
    if st.session_state.get('stamp_bytes'):
        st.image(st.session_state['stamp_bytes'], width=150, caption="Stamp preview")
    st.caption("Leave blank to print an empty signature box in the report for a physical wet stamp instead.")

tab_single, tab_batch = st.tabs(["🔬 Single Sample", "📦 Batch Processing"])

# -----------------------------------------------------------------------
# TAB 1: SINGLE SAMPLE
# -----------------------------------------------------------------------
with tab_single:
    sample_id = st.text_input("Sample / Borehole ID", "Sample 1", key="single_sample_id")

    with st.form("soil_form"):
        st.subheader("📊 Atterberg Limits")
        LL = st.number_input("Liquid Limit (LL)", min_value=0)
        PL = st.number_input("Plastic Limit (PL)", min_value=0)
        is_np = st.checkbox("Check if Non-Plastic (N.P)")
        PI = 0 if is_np else LL - PL
        if not is_np:
            st.write(f"Plasticity Index (PI) = **{PI}**")

        st.subheader("🔍 Sieve Analysis (%) Passing")
        pass_10 = st.number_input("Sieve No. 10 (2.0 mm)", min_value=0, max_value=100)
        pass_40 = st.number_input("Sieve No. 40 (0.425 mm)", min_value=0, max_value=100)
        pass_200 = st.number_input("Sieve No. 200 (0.075 mm)", min_value=0, max_value=100)

        red_flags = st.multiselect("⚠️ Select any red flags identified in the soil:",
                                 ["stone", "organic_matter", "mottled_color"])

        submitted = st.form_submit_button("🚀 Classify Soil")

    if submitted:
        classification = classify_soil(LL, PL, PI, pass_10, pass_40, pass_200, is_np)
        mat_type = classify_material_type(pass_200)
        constituents = identify_constituents_from_classification(classification)
        ai_summary = generate_soil_analysis(classification, PI, LL, pass_200, pass_40, pass_10, red_flags)
        chart_fig = create_sieve_chart(pass_10, pass_40, pass_200, label=sample_id)
        chart_png = fig_to_png_bytes(chart_fig)
        plt.close(chart_fig)

        st.session_state['soil_result'] = {
            "sample_id": sample_id, "classification": classification, "mat_type": mat_type,
            "constituents": constituents, "LL": LL, "PL": PL, "PI": PI, "is_np": is_np,
            "pass_10": pass_10, "pass_40": pass_40, "pass_200": pass_200,
            "red_flags": red_flags, "ai_summary": ai_summary, "chart_png": chart_png
        }

    if st.session_state.get('soil_result'):
        r = st.session_state['soil_result']

        st.markdown("---")
        st.success(f"🎯 AASHTO Classification: **{r['classification']}**")
        st.info(f"🧱 Material Type: **{r['mat_type']}**")
        st.write(f"⚗️ Significant Constituent Materials: **{r['constituents']}**")

        rating = get_subgrade_rating(r['classification'])
        if rating == "Excellent to Good":
            st.success(f"✅ General Subgrade Rating: **{rating}**")
        elif rating == "Fair to Poor":
            st.warning(f"⚠️ General Subgrade Rating: **{rating}**")

        st.subheader("🤖 AI Analysis")
        st.markdown(r['ai_summary'])

        st.subheader("📈 Sieve Analysis Chart")
        st.image(r['chart_png'])

        st.subheader("📥 Download Results")
        export_df = pd.DataFrame({
            'Sample ID': [r['sample_id']], 'Classification': [r['classification']],
            'Material Type': [r['mat_type']], 'Significant Constituents': [r['constituents']],
            'LL': [r['LL']], 'PL': [r['PL']], 'PI': [r['PI']],
            'Pass 2.0mm': [r['pass_10']], 'Pass 0.425mm': [r['pass_40']], 'Pass 0.075mm': [r['pass_200']],
            'Red Flags': [", ".join(r['red_flags'])], 'AI Analysis': [r['ai_summary']]
        })

        col_dl1, col_dl2 = st.columns(2)
        with col_dl1:
            st.download_button("📊 Download as CSV", export_df.to_csv(index=False),
                              "classification_results.csv", "text/csv", key="single_csv_dl")
        with col_dl2:
            st.download_button("📄 Download Analysis as Text", r['ai_summary'],
                              file_name="soil_analysis.txt", mime="text/plain", key="single_txt_dl")

        if st.button("📄 Generate PDF Report", key="single_pdf_btn"):
            stamp_path = None
            if st.session_state.get('stamp_bytes'):
                stamp_path = os.path.join(tempfile.gettempdir(),
                                        f"temp_stamp_{datetime.now().strftime('%Y%m%d%H%M%S%f')}.png")
                with open(stamp_path, 'wb') as f:
                    f.write(st.session_state['stamp_bytes'])
            pdf_data = create_pdf_report([r], project_name, client_name,
                                        st.session_state.get('engineer_name', ''), stamp_path)
            if stamp_path and os.path.exists(stamp_path):
                os.unlink(stamp_path)
            if pdf_data:
                st.download_button("⬇️ Download PDF Report", data=pdf_data,
                                  file_name=f"aashto_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                                  mime="application/pdf", key="single_pdf_dl")

# -----------------------------------------------------------------------
# TAB 2: BATCH PROCESSING
# -----------------------------------------------------------------------
with tab_batch:
    st.subheader("Batch Sample Upload")
    st.caption("Upload a CSV with one row per sample. Download the template below to get the exact column format.")

    template_df = pd.DataFrame([{
        "Sample_ID": "BH-1 @ 1.5m", "LL": 32, "PL": 19, "Non_Plastic": "N",
        "Pass_10": 68, "Pass_40": 45, "Pass_200": 28,
        "Stone": "N", "Organic_Matter": "N", "Mottled_Color": "N"
    }])
    st.download_button("📥 Download CSV Template", template_df.to_csv(index=False),
                      "aashto_batch_template.csv", "text/csv", key="batch_template_dl")

    batch_file = st.file_uploader("Upload Batch CSV", type=["csv"], key="batch_uploader")

    if batch_file is not None:
        try:
            batch_input_df = pd.read_csv(batch_file)
            st.dataframe(batch_input_df, use_container_width=True, hide_index=True)

            if st.button("🚀 Classify All Samples", key="batch_classify_btn"):
                flag_cols = {"Stone": "stone", "Organic_Matter": "organic_matter", "Mottled_Color": "mottled_color"}
                batch_results = []
                for _, row in batch_input_df.iterrows():
                    is_np_b = str(row.get("Non_Plastic", "N")).strip().upper().startswith("Y")
                    LL_b = float(row.get("LL", 0) or 0)
                    PL_b = float(row.get("PL", 0) or 0)
                    PI_b = 0 if is_np_b else LL_b - PL_b
                    pass_10_b = float(row.get("Pass_10", 0) or 0)
                    pass_40_b = float(row.get("Pass_40", 0) or 0)
                    pass_200_b = float(row.get("Pass_200", 0) or 0)
                    red_flags_b = [flag_cols[c] for c in flag_cols if str(row.get(c, "N")).strip().upper().startswith("Y")]
                    sample_id_b = str(row.get("Sample_ID", "Sample"))

                    classification_b = classify_soil(LL_b, PL_b, PI_b, pass_10_b, pass_40_b, pass_200_b, is_np_b)
                    mat_type_b = classify_material_type(pass_200_b)
                    constituents_b = identify_constituents_from_classification(classification_b)
                    ai_summary_b = generate_soil_analysis(classification_b, PI_b, LL_b, pass_200_b, pass_40_b, pass_10_b, red_flags_b)
                    chart_fig_b = create_sieve_chart(pass_10_b, pass_40_b, pass_200_b, label=sample_id_b)
                    chart_png_b = fig_to_png_bytes(chart_fig_b)
                    plt.close(chart_fig_b)

                    batch_results.append({
                        "sample_id": sample_id_b, "classification": classification_b, "mat_type": mat_type_b,
                        "constituents": constituents_b, "LL": LL_b, "PL": PL_b, "PI": PI_b, "is_np": is_np_b,
                        "pass_10": pass_10_b, "pass_40": pass_40_b, "pass_200": pass_200_b,
                        "red_flags": red_flags_b, "ai_summary": ai_summary_b, "chart_png": chart_png_b
                    })
                st.session_state['batch_results'] = batch_results

        except Exception as e:
            st.error(f"Could not read that CSV: {str(e)}")

    if st.session_state.get('batch_results'):
        results = st.session_state['batch_results']
        st.markdown("---")
        st.subheader(f"📊 Batch Results ({len(results)} samples)")

        summary_rows = [{
            "Sample ID": r['sample_id'], "Classification": r['classification'],
            "Material Type": r['mat_type'], "LL": r['LL'], "PI": r['PI'],
            "Pass No.200 (%)": r['pass_200'], "Subgrade Rating": get_subgrade_rating(r['classification'])
        } for r in results]
        summary_df = pd.DataFrame(summary_rows)
        st.dataframe(summary_df, use_container_width=True, hide_index=True)

        st.subheader("📥 Downloads")
        st.download_button("📊 Download Batch Results as CSV", summary_df.to_csv(index=False),
                          "aashto_batch_results.csv", "text/csv", key="batch_csv_dl")

        if st.button("📄 Generate Batch PDF Report", key="batch_pdf_btn"):
            stamp_path = None
            if st.session_state.get('stamp_bytes'):
                stamp_path = os.path.join(tempfile.gettempdir(),
                                        f"temp_stamp_{datetime.now().strftime('%Y%m%d%H%M%S%f')}.png")
                with open(stamp_path, 'wb') as f:
                    f.write(st.session_state['stamp_bytes'])
            pdf_data = create_pdf_report(results, project_name, client_name,
                                        st.session_state.get('engineer_name', ''), stamp_path)
            if stamp_path and os.path.exists(stamp_path):
                os.unlink(stamp_path)
            if pdf_data:
                st.download_button("⬇️ Download Batch PDF Report", data=pdf_data,
                                  file_name=f"aashto_batch_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                                  mime="application/pdf", key="batch_pdf_dl")

st.markdown("---")
st.caption(f"© 2025 AASHTO Classifying Tool | Built by {CLIENT_NAME}")
