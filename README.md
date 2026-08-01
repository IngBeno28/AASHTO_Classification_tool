# AASHTO Soil Classification Tool

A Streamlit application for classifying soils per **AASHTO M 145 / ASTM D3282**,
built by **Automation_hub Engineering Group Limited**.

## Features

- Atterberg Limits (LL, PL, PI) with Non-Plastic handling
- Sieve analysis (% passing No. 10, No. 40, No. 200)
- Full AASHTO group classification (A-1-a through A-7)
- Material type and significant constituent identification
- General subgrade rating (granular vs silt-clay behavior)
- Red-flag detection (stone, organic matter, mottled color) with engineering notes
- Automatic engineering interpretation per classification
- Sieve analysis bar chart
- Branded PDF report (cover page, results, chart, certification/sign-off)
- CSV and text export
- Batch processing (upload a CSV of multiple samples, classify all at once)

## Project Structure

```
.
├── main.py              # App entry point — UI, classification engine, PDF generation
├── branding.py           # Company name, colors, logo path, contact details
├── style.css             # Visual styling — auto-loaded if present
├── requirements.txt      # Python dependencies
├── assets/
│   └── 2.png              # Your logo (add this yourself — see below)
└── README.md
```

## Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
2. **Add your logo** (optional): place a PNG at `assets/2.png`. If missing, the
   app and PDF report still work — the logo slot is just left blank, and the
   app will show a diagnostic caption telling you the exact path it checked.
3. **Customize branding**: edit `branding.py` — company name, app title, brand
   color, contact details (leave any as `""` to omit from the report).
4. **Run locally:**
   ```bash
   streamlit run main.py
   ```

## Deploying to Streamlit Community Cloud

Push to GitHub, connect the repo at [share.streamlit.io](https://share.streamlit.io),
set the main file path to `main.py`. No secrets or external services required.

## Using the App

### Single Sample
Enter a sample ID, fill in Atterberg limits and sieve results, flag any red
flags observed, then classify. Results include the AASHTO group, material
type, subgrade rating, engineering interpretation, and sieve chart —
downloadable as CSV, text, or a full PDF report.

### Batch Processing
Download the CSV template, fill in one row per sample, upload it, and
classify every row at once. Results include a combined summary table and one
PDF report covering the whole batch.

## License / Ownership

© Automation_hub Engineering Group Limited. Internal engineering tool.
