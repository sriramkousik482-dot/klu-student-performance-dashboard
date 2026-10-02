import streamlit as st
import pandas as pd
import altair as alt
from pathlib import Path
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image,
    HRFlowable
)
from reportlab.lib.utils import ImageReader
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.barcharts import VerticalBarChart
from datetime import datetime
from reportlab.lib.units import inch


# =========================================================
# PAGE CONFIGURATION
# =========================================================

st.set_page_config(page_title="KL UNIVERSITY", page_icon="🎓", layout="wide")

BASE_DIR = Path(__file__).resolve().parent
CSV_FILE = BASE_DIR / "student.csv"
LOGO_FILE = BASE_DIR / "klu_logo.png.jpg"

CATEGORY_ORDER = ["AB", "D", "DT", "F", "MTO", "-", "BLNA", "GP/MP", "NA"]

if not CSV_FILE.exists():
    st.error(f"student.csv was not found.\n\nExpected location:\n{CSV_FILE}")
    st.stop()


# =========================================================
# THEME / STYLES
# =========================================================

TEXT = "#e6e9f5"
MUTED = "#8e98b8"
CARD = "#141b34"
BORDER = "#263056"

PALETTE = ["#6366f1", "#22d3ee", "#34d399", "#fbbf24", "#fb7185", "#a78bfa", "#fb923c"]

GRADE_ORDER = ["O", "A+", "A", "B+", "B", "C", "P", "F", "DT"]
GRADE_COLORS = {
    "O": "#34d399", "A+": "#4ade80", "A": "#22d3ee", "B+": "#38bdf8",
    "B": "#818cf8", "C": "#a78bfa", "P": "#fbbf24", "F": "#fb7185", "DT": "#ef4444",
}

st.markdown(
    """
<style>
.stApp {
    background:
        radial-gradient(1200px 500px at 10% -10%, #1b2352 0%, transparent 60%),
        radial-gradient(900px 500px at 100% 0%, #2a1650 0%, transparent 55%),
        #0b1020;
}
.block-container {padding-top: 1.6rem; max-width: 1400px;}
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #121a3a 0%, #0d1330 100%);
    border-right: 1px solid #263056;
}
h2 {color: #e6e9f5 !important; font-weight: 700 !important;}

.hero {
    background: linear-gradient(120deg, #4f46e5 0%, #7c3aed 45%, #db2777 100%);
    padding: 30px 36px; border-radius: 20px; margin-bottom: 26px;
    box-shadow: 0 10px 40px rgba(99,102,241,.35);
    position: relative; overflow: hidden;
}
.hero:after {
    content: "🎓"; position: absolute; right: 34px; top: 8px;
    font-size: 110px; opacity: .18;
}
.hero h1 {color: #fff; margin: 0; font-size: 36px; letter-spacing: .5px;}
.hero p  {color: #e9e7ff; margin: 8px 0 0 0; font-size: 16px;}
.hero .tag {
    display:inline-block; margin-top: 14px; padding: 4px 12px; font-size: 12px;
    background: rgba(255,255,255,.18); color:#fff; border-radius: 999px;
}

.section-title {
    color: #e6e9f5; font-size: 22px; font-weight: 700; margin: 26px 0 12px 0;
    display:flex; align-items:center; gap:10px;
}
.section-title:before {
    content:""; width: 6px; height: 22px; border-radius: 4px;
    background: linear-gradient(180deg, #6366f1, #22d3ee);
}

.kpi {
    background: linear-gradient(145deg, #171f3d 0%, #121931 100%);
    border: 1px solid #263056; border-radius: 16px;
    padding: 16px 18px; position: relative; overflow: hidden;
    box-shadow: 0 6px 20px rgba(0,0,0,.25);
}
.kpi:before {
    content:""; position:absolute; left:0; top:0; right:0; height:4px;
    background: var(--c);
}
.kpi:after {
    content:""; position:absolute; right:-30px; top:-30px; width:100px; height:100px;
    border-radius:50%; background: var(--c); opacity:.12;
}
.kpi .icon  {font-size: 20px; margin-bottom: 4px;}
.kpi .label {color:#8e98b8; font-size: 11.5px; letter-spacing: .8px; font-weight:600;}
.kpi .value {color:#fff; font-size: 28px; font-weight: 800; line-height: 1.15;
             white-space: nowrap; overflow: hidden; text-overflow: ellipsis;}
.kpi .sub   {color: var(--c); font-size: 12px; margin-top: 2px;}

.panel {
    background: #141b34; border: 1px solid #263056; border-radius: 16px;
    padding: 14px 18px 4px 18px; margin-bottom: 8px;
}
.panel h4 {margin: 0 0 4px 0; color:#e6e9f5; font-size: 16px;}
.panel small {color:#8e98b8;}

.profile {
    display:flex; align-items:center; gap:22px;
    background: linear-gradient(120deg, #1a2150, #2a1b55);
    border: 1px solid #343f78; border-radius: 20px; padding: 22px 26px;
    box-shadow: 0 10px 30px rgba(0,0,0,.3);
}
.avatar {
    width: 74px; height: 74px; border-radius: 50%; flex: none;
    background: linear-gradient(135deg, #22d3ee, #6366f1, #db2777);
    display:flex; align-items:center; justify-content:center;
    color:#fff; font-size: 28px; font-weight: 800;
}
.profile .name {color:#fff; font-size: 24px; font-weight: 800;}
.profile .meta {color:#b8c0e0; font-size: 14px; margin-top: 4px;}
.chip {
    display:inline-block; padding: 3px 12px; border-radius: 999px;
    font-size: 12px; font-weight: 700; margin-top: 8px; margin-right: 6px;
}
.chip.good {background: rgba(52,211,153,.18); color:#34d399;}
.chip.warn {background: rgba(251,191,36,.18); color:#fbbf24;}
.chip.info {background: rgba(129,140,248,.2); color:#a5b4fc;}
.profile .cgpa {margin-left:auto; text-align:center;}
.profile .cgpa .n {font-size: 44px; font-weight: 800; color:#22d3ee; line-height:1;}
.profile .cgpa .l {font-size: 11px; color:#b8c0e0; letter-spacing: 1px;}

.ccard {
    background: #141b34; border: 1px solid #263056; border-left: 5px solid var(--g);
    border-radius: 12px; padding: 10px 12px; margin-bottom: 10px; min-height: 96px;
}
.ccard .code {font-size: 13px; font-weight: 700; color:#e6e9f5;}
.ccard .nm {font-size: 11px; color:#aab3d1; margin: 3px 0 7px 0; line-height: 1.25;}
.ccard .row {display:flex; gap:6px; flex-wrap:wrap; align-items:center;}
.ccard .g {
    background: var(--g); color:#0b1020; font-weight: 800; font-size: 12px;
    padding: 1px 9px; border-radius: 6px;
}
.ccard .m {font-size: 10.5px; color:#8e98b8;}

[data-baseweb="tab-list"] {gap: 6px;}
[data-baseweb="tab"] {border-radius: 10px 10px 0 0;}
</style>

<div class="hero">
    <h1>KL UNIVERSITY</h1>
    <p>Department of CSE-4 &nbsp;|&nbsp; Academic Performance Dashboard</p>
    <span class="tag">Student analytics &amp; reports</span>
</div>
""",
    unsafe_allow_html=True,
)


def section(title):
    st.markdown(f'<div class="section-title">{title}</div>', unsafe_allow_html=True)


def kpi_card(label, value, color, icon="", sub=""):
    st.markdown(
        f"""<div class="kpi" style="--c:{color}">
            <div class="icon">{icon}</div>
            <div class="label">{label}</div>
            <div class="value">{value}</div>
            <div class="sub">{sub}&nbsp;</div>
        </div>""",
        unsafe_allow_html=True,
    )


def style_chart(chart, height=300):
    return (
        chart.properties(height=height, background="transparent")
        .configure_view(strokeWidth=0)
        .configure_axis(
            labelColor="#aab3d1", titleColor="#aab3d1", gridColor="#222b4c",
            domainColor="#222b4c", tickColor="#222b4c",
        )
        .configure_legend(labelColor="#aab3d1", titleColor="#aab3d1")
    )


# =========================================================
# HELPERS
# =========================================================

def clean_column_name(column):
    return str(column).strip().lower().replace("_", " ").replace("-", " ")


def find_column(df, possible_names):
    for possible in possible_names:
        for actual in df.columns:
            if clean_column_name(actual) == clean_column_name(possible):
                return actual
    for possible in possible_names:
        possible_clean = clean_column_name(possible)
        for actual in df.columns:
            if possible_clean in clean_column_name(actual):
                return actual
    return None


def find_mentor_column(df):
    names = [
        "Mentor", "Mentor Name", "MentorName", "Faculty Mentor",
        "Faculty Mentor Name", "MENTOR", "MENTOR NAME",
    ]
    column = find_column(df, names)
    if column is not None:
        return column
    for col in df.columns:
        if "mentor" in clean_column_name(col):
            return col
    return None


def find_marks_column(df):
    names = [
        "Marks", "Mark", "Marks Out of 50", "Marks (Out of 50)", "Marks/50",
        "Internal Marks", "Internal Mark", "Mid Marks", "Mid Mark",
        "Mid Marks Out of 50", "Mid Marks/50", "Exam Marks", "Assessment Marks",
    ]
    column = find_column(df, names)
    if column is not None:
        return column
    for col in df.columns:
        name = clean_column_name(col)
        if (
            "mark" in name and "remark" not in name and "grade" not in name
            and "point" not in name and "credit" not in name
        ):
            return col
    return None


def normalize_semester(value):
    if pd.isna(value):
        return ""
    value = str(value).strip()
    lower_value = value.lower()
    if lower_value in ["odd", "odd sem", "odd semester"]:
        return "Odd Sem"
    if lower_value in ["even", "even sem", "even semester"]:
        return "Even Sem"
    if "summer" in lower_value:
        return "Summer Term"
    return value


def get_joining_year(student_id):
    try:
        return f"Y{int(str(student_id).strip()[:2])}"
    except Exception:
        return ""


def calculate_academic_semester(joining_year, academic_year, semester_type):
    try:
        if pd.isna(joining_year) or pd.isna(academic_year) or pd.isna(semester_type):
            return None

        joining_year = str(joining_year).strip().upper()
        academic_year = str(academic_year).strip()
        semester_type = str(semester_type).strip().lower()

        if joining_year.startswith("Y"):
            join_year = int(joining_year[1:3]) + 2000
        else:
            join_year = int(joining_year)

        academic_start_year = int(academic_year.split("-")[0])
        year_of_study = academic_start_year - join_year + 1

        if year_of_study < 1:
            return None
        if "summer" in semester_type:
            return None
        if "odd" in semester_type:
            semester_number = "1"
        elif "even" in semester_type:
            semester_number = "2"
        else:
            return None

        return f"{year_of_study}-{semester_number}"
    except Exception:
        return None


def semester_sort_key(value):
    try:
        first, second = str(value).split("-")
        return (int(first), int(second))
    except Exception:
        return (999, 999)


def base_grade(series):
    """'B+(F,B+)' -> 'B+', 'F(F,F)' -> 'F'"""
    return (
        series.astype(str).str.strip().str.upper()
        .str.split("(", n=1).str[0].str.strip()
    )


def grade_counts(data):
    """Returns (pass, fail, detained) course counts."""
    base = base_grade(data["Grade"])
    fail = int((base == "F").sum())
    dt = int((base == "DT").sum())
    passed = int((~base.isin(["F", "DT"])).sum())
    return passed, fail, dt


def calculate_cgpa(data):
    if data.empty:
        return 0.0
    credits = pd.to_numeric(data["Credits"], errors="coerce").fillna(0)
    credit_points = pd.to_numeric(data["Credit Points"], errors="coerce").fillna(0)
    total_credits = credits.sum()
    if total_credits == 0:
        return 0.0
    return credit_points.sum() / total_credits


def get_mentor_name(data):
    values = data["Mentor Name"].astype(str).str.strip()
    values = values[
        ~values.str.lower().isin(["", "nan", "none", "<na>", "n/a", "not available"])
    ]
    return values.iloc[0] if not values.empty else "Not Available"


def get_semesters(data):
    semesters = data["Academic Semester"].dropna().unique().tolist()
    semesters = [s for s in semesters if str(s).strip() != ""]
    return sorted(semesters, key=semester_sort_key)


def semester_summary(data):
    rows = []
    for semester in get_semesters(data):
        sem_data = data[data["Academic Semester"] == semester]
        total_credits = (
            pd.to_numeric(sem_data["Credits"], errors="coerce").fillna(0).sum()
        )
        rows.append({
            "Semester": semester,
            "Total Courses": len(sem_data),
            "Total Credits": round(total_credits, 2),
