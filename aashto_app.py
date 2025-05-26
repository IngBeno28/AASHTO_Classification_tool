import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt


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

    # Export results to CSV
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
        'Pass 0.075mm': [pass_200]
    })
    st.download_button("Download as CSV", export_df.to_csv(index=False), "classification_results.csv", "text/csv")



