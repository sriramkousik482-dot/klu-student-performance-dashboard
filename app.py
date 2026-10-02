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
            "CGPA": round(calculate_cgpa(sem_data), 2),
        })
    return pd.DataFrame(rows)


def category_summary(data):
    cats = data["Category"].astype(str).str.strip().str.upper()
    return pd.DataFrame([
        {"Category": c, "Count": int(cats.eq(c).sum())} for c in CATEGORY_ORDER
    ])


# =========================================================
# LOAD DATA
# =========================================================

@st.cache_data
def load_data():
    df = pd.read_csv(CSV_FILE, low_memory=False, encoding="utf-8-sig")
    df.columns = [str(col).strip() for col in df.columns]

    required_columns = [
        "ID Number", "Name", "Course Code", "Course Name", "Grade",
        "Points", "Credits", "Category", "AY", "Semester",
    ]
    missing = [c for c in required_columns if c not in df.columns]
    if missing:
        st.error("The following required columns are missing from student.csv:")
        st.write(missing)
        st.write("Columns found in your CSV:")
        st.write(list(df.columns))
        st.stop()

    # The CSV has a second table appended at the bottom (mentor list):
    #   ID Number = "Y-25", Name = student ID, Course Code = student name,
    #   Grade = mentor name.  Separate it from the academic records.
    id_text = df["ID Number"].astype(str).str.strip()
    is_student_row = id_text.str.fullmatch(r"\d{10}")
    mentor_rows = df[~is_student_row]
    df = df[is_student_row].copy()

    # Keep only genuine course records: valid academic year (2025-2026) and a
    # real course code (no spaces, has digits).  This drops stray rows such as
    # marks tables where the course NAME sits in the Course Code column.
    ay_ok = df["AY"].astype(str).str.strip().str.fullmatch(r"\d{4}-\d{2,4}")
    code_ok = df["Course Code"].astype(str).str.strip().str.fullmatch(r"\S*\d\S*")
    df = df[ay_ok & code_ok].copy()

    mentor_map = {}
    for sid, mname in zip(
        mentor_rows["Name"].astype(str).str.strip(),
        mentor_rows["Grade"].astype(str).str.strip(),
    ):
        if len(sid) == 10 and sid.isdigit() and mname.lower() not in ("", "nan", "none"):
            mentor_map[sid] = mname

    for col in ["ID Number", "Name", "Course Code", "Course Name", "Grade", "AY"]:
        df[col] = df[col].astype(str).str.strip()

    df["Points"] = pd.to_numeric(df["Points"], errors="coerce").fillna(0)
    df["Credits"] = pd.to_numeric(df["Credits"], errors="coerce").fillna(0)

    df["Category"] = df["Category"].astype(str).str.strip().str.upper()
    df["Category"] = df["Category"].replace("NAN", "")

    df["Semester"] = df["Semester"].apply(normalize_semester)
    df["Year"] = df["ID Number"].apply(get_joining_year)
    df["Credit Points"] = df["Points"] * df["Credits"]

    mentor_column = find_mentor_column(df)
    if mentor_column is not None:
        df["Mentor Name"] = df[mentor_column].astype(str).str.strip()
        df["Mentor Name"] = df["Mentor Name"].replace(
            ["nan", "NaN", "None", "none", "NONE", "<NA>", "N/A", "NA"], ""
        )
    else:
        df["Mentor Name"] = df["ID Number"].map(mentor_map).fillna("")

    marks_column = find_marks_column(df)
    if marks_column is not None:
        df["Marks"] = pd.to_numeric(df[marks_column], errors="coerce")
    else:
        df["Marks"] = pd.NA

    df["Academic Semester"] = df.apply(
        lambda r: calculate_academic_semester(r["Year"], r["AY"], r["Semester"]),
        axis=1,
    )
    return df


# =========================================================
# COURSE CARD
# =========================================================

def show_course_card(row):
    g = str(row["Grade"]).strip().upper().split("(")[0].strip()
    color = GRADE_COLORS.get(g, "#94a3b8")
    st.markdown(
        f"""
        <div class="ccard" style="--g:{color}">
            <div class="code">{row["Course Code"]}</div>
            <div class="nm">{row["Course Name"]}</div>
            <div class="row">
                <span class="g">{row["Grade"]}</span>
                <span class="m">Pts {row["Points"]:g}</span>
                <span class="m">• Cr {row["Credits"]:g}</span>
                <span class="m">• {row["Category"]}</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# =========================================================
# PDF
# =========================================================

PDF_PRIMARY = colors.HexColor("#4f46e5")
PDF_DARK = colors.HexColor("#312e81")
PDF_SOFT = colors.HexColor("#eef2ff")
PDF_LINE = colors.HexColor("#d6daf5")
PDF_ZEBRA = colors.HexColor("#f7f8ff")
PDF_TEXT = colors.HexColor("#1f2340")
PDF_MUTED = colors.HexColor("#6b7280")

PDF_GRADE_BG = {
    "O": "#bbf7d0", "A+": "#d1fae5", "A": "#cffafe", "B+": "#e0f2fe",
    "B": "#e0e7ff", "C": "#ede9fe", "P": "#fef3c7", "F": "#fecaca", "DT": "#fca5a5",
}


def _rounded_table(data, col_widths, radius=8):
    try:
        return Table(data, colWidths=col_widths, cornerRadii=[radius] * 4)
    except TypeError:
        return Table(data, colWidths=col_widths)


def generate_pdf(student_data):
    buffer = BytesIO()
    page_w, page_h = A4
    margin = 30
    content_w = page_w - 2 * margin
    generated_on = datetime.now().strftime("%d %b %Y")

    def draw_page(canvas, doc):
        canvas.saveState()
        canvas.setFillColor(PDF_PRIMARY)
        canvas.rect(0, page_h - 8, page_w, 8, fill=1, stroke=0)
        canvas.setStrokeColor(PDF_LINE)
        canvas.line(margin, 26, page_w - margin, 26)
        canvas.setFont("Helvetica", 7.5)
        canvas.setFillColor(PDF_MUTED)
        canvas.drawString(
            margin, 15,
            "KL University  |  Department of CSE-4  |  Student Academic Performance Report",
        )
        canvas.drawRightString(
            page_w - margin, 15, f"Generated {generated_on}  |  Page {doc.page}"
        )
        canvas.restoreState()

    document = SimpleDocTemplate(
        buffer, pagesize=A4,
        leftMargin=margin, rightMargin=margin, topMargin=26, bottomMargin=36,
    )

    styles = getSampleStyleSheet()

    def style(name, **kw):
        base = dict(parent=styles["Normal"], fontName="Helvetica",
                    fontSize=8, leading=10, textColor=PDF_TEXT)
        base.update(kw)
        return ParagraphStyle(name, **base)

    st_cell = style("cell")
    st_cell_c = style("cellc", alignment=TA_CENTER)
    st_head = style("head", fontName="Helvetica-Bold", textColor=colors.white)
    st_head_c = style("headc", fontName="Helvetica-Bold", textColor=colors.white,
                      alignment=TA_CENTER)
    st_section = style("section", fontName="Helvetica-Bold", fontSize=12.5,
                       leading=15, textColor=PDF_DARK, spaceBefore=14,
                       spaceAfter=3, keepWithNext=1)

    def cell(text, center=False, bold=False, color=None):
        text = "" if text is None or (not isinstance(text, str) and pd.isna(text)) else str(text)
        text = text.replace("&", "&amp;").replace("<", "&lt;")
        if bold:
            text = f"<b>{text}</b>"
        if color:
            text = f'<font color="{color}">{text}</font>'
        return Paragraph(text, st_cell_c if center else st_cell)

    def head(text, center=True):
        return Paragraph(text, st_head_c if center else st_head)

    def section_heading(title):
        return [
            Paragraph(title, st_section),
            HRFlowable(width="100%", thickness=1, color=PDF_LINE,
                       spaceBefore=0, spaceAfter=6),
        ]

    def data_table(rows, widths, header_color=PDF_DARK, extra=None):
        t = Table(rows, colWidths=widths, repeatRows=1)
        cmds = [
            ("BACKGROUND", (0, 0), (-1, 0), header_color),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, PDF_ZEBRA]),
            ("GRID", (0, 0), (-1, -1), 0.4, PDF_LINE),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 3.5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3.5),
            ("LEFTPADDING", (0, 0), (-1, -1), 5),
            ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ]
        if extra:
            cmds += extra
        t.setStyle(TableStyle(cmds))
        return t

    story = []

    # ---------------- Header ----------------
    if LOGO_FILE.exists():
        try:
            iw, ih = ImageReader(str(LOGO_FILE)).getSize()
            scale = min(4.2 * inch / iw, 0.95 * inch / ih)
            logo = Image(str(LOGO_FILE), width=iw * scale, height=ih * scale)
            logo.hAlign = "CENTER"
            story.append(logo)
            story.append(Spacer(1, 8))
        except Exception:
            pass

    banner_rows = [
        [Paragraph("KL UNIVERSITY", style(
            "bt", fontName="Helvetica-Bold", fontSize=22, leading=26,
            textColor=colors.white, alignment=TA_CENTER))],
        [Paragraph("Department of CSE-4", style(
            "bd", fontName="Helvetica-Bold", fontSize=12, leading=15,
            textColor=colors.HexColor("#e0e7ff"), alignment=TA_CENTER))],
        [Paragraph("STUDENT ACADEMIC PERFORMANCE REPORT", style(
            "bg", fontSize=8, leading=10, textColor=colors.HexColor("#c7d2fe"),
            alignment=TA_CENTER))],
    ]
    banner = _rounded_table(banner_rows, [content_w], radius=10)
    banner.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), PDF_PRIMARY),
        ("TOPPADDING", (0, 0), (-1, 0), 12),
        ("BOTTOMPADDING", (0, -1), (-1, -1), 12),
        ("TOPPADDING", (0, 1), (-1, -1), 1),
        ("BOTTOMPADDING", (0, 0), (-1, -2), 1),
    ]))
    story.append(banner)
    story.append(Spacer(1, 12))

    # ---------------- Profile card ----------------
    student_id = str(student_data["ID Number"].iloc[0])
    student_name = str(student_data["Name"].iloc[0]).title()
    mentor_name = get_mentor_name(student_data)
    overall_cgpa = calculate_cgpa(student_data)
    joined = str(student_data["Year"].iloc[0])
    pass_count, fail_count, dt_count = grade_counts(student_data)
    total_credits = pd.to_numeric(student_data["Credits"], errors="coerce").fillna(0).sum()

    if fail_count + dt_count > 0:
        status = '<font color="#b45309"><b>Has backlogs</b></font>'
    else:
        status = '<font color="#047857"><b>All clear</b></font>'

    left = [
        Paragraph(student_name, style("pn", fontName="Helvetica-Bold",
                                      fontSize=15, leading=18, textColor=PDF_DARK)),
        Spacer(1, 3),
        Paragraph(f"<b>ID:</b> {student_id} &nbsp;&nbsp;|&nbsp;&nbsp; <b>Batch:</b> {joined}",
                  style("pm", fontSize=9, leading=12)),
        Paragraph(f"<b>Mentor:</b> {mentor_name}", style("pm2", fontSize=9, leading=12)),
        Paragraph(f"<b>Status:</b> {status}", style("pm3", fontSize=9, leading=12)),
    ]
    right = [
        Paragraph("OVERALL CGPA", style("cl", fontSize=7.5, textColor=PDF_MUTED,
                                        alignment=TA_CENTER)),
        Paragraph(f"{overall_cgpa:.2f}", style(
            "cn", fontName="Helvetica-Bold", fontSize=32, leading=36,
            textColor=PDF_PRIMARY, alignment=TA_CENTER)),
        Paragraph("out of 10", style("co", fontSize=7.5, textColor=PDF_MUTED,
                                      alignment=TA_CENTER)),
    ]
    profile = _rounded_table([[left, right]], [content_w - 1.7 * inch, 1.7 * inch])
    profile.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), PDF_SOFT),
        ("BOX", (0, 0), (-1, -1), 0.8, colors.HexColor("#c7d2fe")),
        ("LINEBEFORE", (1, 0), (1, 0), 0.8, colors.HexColor("#c7d2fe")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 14),
        ("RIGHTPADDING", (0, 0), (-1, -1), 14),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
    ]))
    story.append(profile)
    story.append(Spacer(1, 10))

    # ---------------- KPI strip ----------------
    kpis = [
        ("COURSES", len(student_data), "#4f46e5", "#eef2ff"),
        ("CREDITS", f"{total_credits:g}", "#0891b2", "#ecfeff"),
        ("PASS", pass_count, "#059669", "#ecfdf5"),
        ("FAIL", fail_count, "#ea580c", "#fff7ed"),
        ("DETAINED", dt_count, "#dc2626", "#fef2f2"),
    ]
    kpi_cells = [[
        [Paragraph(label, style("kl", fontSize=7, textColor=PDF_MUTED,
                                alignment=TA_CENTER)),
         Paragraph(str(val), style("kv", fontName="Helvetica-Bold", fontSize=17,
                                   leading=21, alignment=TA_CENTER,
                                   textColor=colors.HexColor(col)))]
        for label, val, col, _ in kpis
    ]]
    kw = content_w / 5
    kpi_table = Table(kpi_cells, colWidths=[kw] * 5)
    cmds = [
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ]
    for i, (_, _, col, bg) in enumerate(kpis):
        cmds += [
            ("BACKGROUND", (i, 0), (i, 0), colors.HexColor(bg)),
            ("LINEABOVE", (i, 0), (i, 0), 3, colors.HexColor(col)),
        ]
        if i < 4:
            cmds.append(("LINEAFTER", (i, 0), (i, 0), 6, colors.white))
    kpi_table.setStyle(TableStyle(cmds))
    story.append(kpi_table)

    # ---------------- Semester CGPA chart ----------------
    sem_df = semester_summary(student_data)
    if not sem_df.empty:
        story += section_heading("Semester-wise CGPA")
        drawing = Drawing(content_w, 165)
        chart = VerticalBarChart()
        chart.x, chart.y = 35, 28
        chart.width, chart.height = content_w - 55, 115
        chart.data = [sem_df["CGPA"].tolist()]
        chart.categoryAxis.categoryNames = [str(x) for x in sem_df["Semester"]]
        chart.categoryAxis.labels.fontSize = 8
        chart.categoryAxis.strokeColor = PDF_LINE
        chart.valueAxis.valueMin = 0
        chart.valueAxis.valueMax = 10
        chart.valueAxis.valueStep = 2
        chart.valueAxis.labels.fontSize = 8
        chart.valueAxis.strokeColor = PDF_LINE
        chart.valueAxis.gridStrokeColor = PDF_LINE
        chart.valueAxis.visibleGrid = True
        chart.bars[0].fillColor = PDF_PRIMARY
        chart.bars[0].strokeColor = None
        chart.barWidth = 18
        chart.groupSpacing = 12
        chart.barLabelFormat = "%0.2f"
        chart.barLabels.nudge = 8
        chart.barLabels.fontSize = 8
        chart.barLabels.fillColor = PDF_DARK
        drawing.add(chart)
        story.append(drawing)

    # ---------------- Semester summary ----------------
    if not sem_df.empty:
        story += section_heading("Semester-wise Summary")
        rows = [[head("Semester"), head("Total Courses"), head("Total Credits"), head("CGPA")]]
        for _, r in sem_df.iterrows():
            rows.append([
                cell(r["Semester"], True, True), cell(r["Total Courses"], True),
                cell(r["Total Credits"], True),
                cell(f"{r['CGPA']:.2f}", True, True, "#4f46e5"),
            ])
        story.append(data_table(rows, [content_w / 4] * 4))

    # ---------------- Category summary ----------------
    story += section_heading("Category Summary")
    cat_df = category_summary(student_data)
    n = len(cat_df)
    rows = [
        [head(c) for c in cat_df["Category"]],
        [cell(int(v), True, bool(v), "#4f46e5" if v else "#9ca3af") for v in cat_df["Count"]],
    ]
    story.append(data_table(rows, [content_w / n] * n))

    # ---------------- Academic performance ----------------
    story += section_heading("Academic Performance")

    acad = student_data.copy()
    acad["_label"] = acad["Academic Semester"].where(
        acad["Academic Semester"].notna(), acad["Semester"])
    acad["_sort"] = acad["Academic Semester"].map(semester_sort_key)
    acad = acad.sort_values(["_sort", "Course Code"])

    rows = [[head("Sem"), head("Course Code"), head("Course Name", False),
             head("Grade"), head("Points"), head("Credits"), head("Category")]]
    extra = []
    for i, (_, r) in enumerate(acad.iterrows(), start=1):
        g = str(r["Grade"]).strip().upper().split("(")[0].strip()
        rows.append([
            cell(r["_label"], True), cell(r["Course Code"], True),
            cell(r["Course Name"]), cell(r["Grade"], True, True),
            cell(f"{r['Points']:g}", True), cell(f"{r['Credits']:g}", True),
            cell(r["Category"], True),
        ])
        if g in PDF_GRADE_BG:
            extra.append(("BACKGROUND", (3, i), (3, i), colors.HexColor(PDF_GRADE_BG[g])))
    story.append(data_table(
        rows,
        [0.65 * inch, 0.9 * inch, 2.75 * inch, 0.65 * inch, 0.8 * inch, 0.75 * inch, 0.9 * inch],
        extra=extra,
    ))

    # ---------------- Backlogs ----------------
    story += section_heading("Backlog Subjects")
    base = base_grade(student_data["Grade"])
    backlog_data = student_data[base.isin(["F", "DT"])]
    if not backlog_data.empty:
        rows = [[head("Semester"), head("Course Code"), head("Course Name", False), head("Grade")]]
        for _, r in backlog_data.iterrows():
            sem = r["Academic Semester"] if pd.notna(r["Academic Semester"]) else r["Semester"]
            rows.append([cell(sem, True), cell(r["Course Code"], True),
                         cell(r["Course Name"]), cell(r["Grade"], True, True, "#b91c1c")])
        story.append(data_table(
            rows, [1.0 * inch, 1.2 * inch, 3.9 * inch, 1.0 * inch],
            header_color=colors.HexColor("#b91c1c")))
    else:
        ok = _rounded_table(
            [[Paragraph('<font color="#047857"><b>No backlogs - all courses cleared.</b></font>',
                        style("nb", fontSize=9, leading=12))]],
            [content_w], radius=6)
        ok.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#ecfdf5")),
            ("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor("#a7f3d0")),
            ("TOPPADDING", (0, 0), (-1, -1), 7), ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ]))
        story.append(ok)

    # ---------------- Marks ----------------
    marks_data = student_data[
        student_data["Semester"].astype(str).str.strip().str.lower() != "summer term"
    ].copy()
    marks_data = marks_data[
        marks_data["Academic Semester"].notna()
        & (marks_data["Academic Semester"].astype(str).str.strip() != "")
    ].copy()
    marks_data["_sort"] = marks_data["Academic Semester"].map(semester_sort_key)
    marks_data = marks_data.sort_values("_sort")

    story += section_heading("Marks of All Members")
    if not marks_data.empty and marks_data["Marks"].notna().any():
        rows = [[head("Semester"), head("Course Code"), head("Course Name", False),
                 head("Marks (Out of 50)")]]
        for _, r in marks_data.iterrows():
            m = r["Marks"]
            display = "-" if pd.isna(m) else f"{float(m):g}"
            rows.append([cell(r["Academic Semester"], True), cell(r["Course Code"], True),
                         cell(r["Course Name"]), cell(display, True, True)])
        story.append(data_table(
            rows, [1.0 * inch, 1.2 * inch, 3.3 * inch, 1.6 * inch]))
    else:
        story.append(cell("Marks are not available.", color="#6b7280"))

    document.build(story, onFirstPage=draw_page, onLaterPages=draw_page)
    buffer.seek(0)
    return buffer


# =========================================================
# LOAD DATA
# =========================================================

try:
    df = load_data()
except Exception as error:
    st.error("There was an error while loading the CSV.")
    st.exception(error)
    st.stop()


# =========================================================
# SIDEBAR FILTERS
# =========================================================

st.sidebar.markdown("### 🎛️ Filters")

selected_year = st.sidebar.selectbox(
    "Joining Year",
    ["All"] + sorted(df["Year"].dropna().astype(str).unique().tolist()),
)
selected_course_code = st.sidebar.selectbox(
    "Course Code",
    ["All"] + sorted(df["Course Code"].dropna().astype(str).unique().tolist()),
)
selected_course_name = st.sidebar.selectbox(
    "Course Name",
    ["All"] + sorted(df["Course Name"].dropna().astype(str).unique().tolist()),
)

filtered_df = df.copy()
if selected_year != "All":
    filtered_df = filtered_df[filtered_df["Year"] == selected_year]
if selected_course_code != "All":
    filtered_df = filtered_df[filtered_df["Course Code"] == selected_course_code]
if selected_course_name != "All":
    filtered_df = filtered_df[filtered_df["Course Name"] == selected_course_name]

st.sidebar.caption(f"{len(filtered_df):,} course records • "
                   f"{filtered_df['ID Number'].nunique():,} students")


# =========================================================
# DEPARTMENT SUMMARY (HOME)
# =========================================================

section("Overall Department Summary")

if filtered_df.empty:
    st.warning("No records match the selected filters.")
else:
    base = base_grade(filtered_df["Grade"])

    total_students = filtered_df["ID Number"].nunique()
    department_cgpa = calculate_cgpa(filtered_df)
    pass_courses, fail_courses, dt_courses = grade_counts(filtered_df)
    students_with_backlog = filtered_df.loc[
        base.isin(["F", "DT"]), "ID Number"
    ].nunique()

    k1, k2, k3, k4, k5, k6 = st.columns(6)
    with k1:
        kpi_card("TOTAL STUDENTS", f"{total_students:,}", "#6366f1", "👥", "enrolled")
    with k2:
        kpi_card("AVERAGE CGPA", f"{department_cgpa:.2f}", "#a78bfa", "⭐", "out of 10")
    with k3:
        kpi_card("TOTAL PASSED", f"{pass_courses:,}", "#34d399", "✅", "courses")
    with k4:
        kpi_card("TOTAL FAILED", f"{fail_courses:,}", "#fb923c", "❌", "courses")
    with k5:
        kpi_card("BACKLOG STUDENTS", f"{students_with_backlog:,}", "#fbbf24", "⚠️",
                 f"{students_with_backlog / max(total_students, 1):.0%} of students")
    with k6:
        kpi_card("DETAINED", f"{dt_courses:,}", "#fb7185", "🚫", "courses")

    # per-student table
    per_student = (
        filtered_df.groupby("ID Number")
        .agg(Name=("Name", "first"), Year=("Year", "first"),
             CP=("Credit Points", "sum"), CR=("Credits", "sum"))
        .reset_index()
    )
    per_student["CGPA"] = (per_student["CP"] / per_student["CR"].where(per_student["CR"] > 0)).round(2)
    per_student = per_student.dropna(subset=["CGPA"])

    st.write("")
    c1, c2 = st.columns([3, 2])

    with c1:
        st.markdown('<div class="panel"><h4>Grade Distribution</h4>'
                    '<small>Final grade of every course record</small></div>',
                    unsafe_allow_html=True)
        gc = base.value_counts().reset_index()
        gc.columns = ["Grade", "Count"]
        gc = gc[gc["Grade"].isin(GRADE_ORDER)]
        chart = (
            alt.Chart(gc)
            .mark_bar(cornerRadiusTopLeft=6, cornerRadiusTopRight=6)
            .encode(
                x=alt.X("Grade:N", sort=GRADE_ORDER, title=None,
                        axis=alt.Axis(labelAngle=0)),
                y=alt.Y("Count:Q", title="Courses"),
                color=alt.Color(
                    "Grade:N", legend=None,
                    scale=alt.Scale(domain=list(GRADE_COLORS),
                                    range=list(GRADE_COLORS.values())),
                ),
                tooltip=["Grade", "Count"],
            )
        )
        st.altair_chart(style_chart(chart, 300), use_container_width=True)

    with c2:
        st.markdown('<div class="panel"><h4>Students by Joining Year</h4>'
                    '<small>Share of each batch</small></div>',
                    unsafe_allow_html=True)
        yc = per_student.groupby("Year").size().reset_index(name="Students")
        yc = yc[yc["Year"] != ""]
        donut = (
            alt.Chart(yc)
            .mark_arc(innerRadius=70, outerRadius=115, cornerRadius=6)
            .encode(
                theta="Students:Q",
                color=alt.Color("Year:N", scale=alt.Scale(range=PALETTE),
                                legend=alt.Legend(title=None, orient="bottom")),
                tooltip=["Year", "Students"],
            )
        )
        st.altair_chart(style_chart(donut, 300), use_container_width=True)

    c3, c4 = st.columns([3, 2])

    with c3:
        st.markdown('<div class="panel"><h4>CGPA Distribution</h4>'
                    '<small>Number of students in each CGPA band</small></div>',
                    unsafe_allow_html=True)
        hist = (
            alt.Chart(per_student)
            .mark_bar(cornerRadiusTopLeft=5, cornerRadiusTopRight=5, color="#8b5cf6")
            .encode(
                x=alt.X("CGPA:Q", bin=alt.Bin(step=0.5), title="CGPA"),
                y=alt.Y("count()", title="Students"),
                tooltip=[alt.Tooltip("count()", title="Students")],
            )
        )
        st.altair_chart(style_chart(hist, 300), use_container_width=True)

    with c4:
        st.markdown('<div class="panel"><h4>🏆 Top 10 Students</h4>'
                    '<small>Highest overall CGPA</small></div>',
                    unsafe_allow_html=True)
        top10 = (
            per_student[per_student["CR"] >= 20]
            .sort_values("CGPA", ascending=False)
            .head(10)[["ID Number", "Name", "CGPA"]]
        )
        st.dataframe(
            top10, hide_index=True, use_container_width=True, height=318,
            column_config={
                "CGPA": st.column_config.ProgressColumn(
                    "CGPA", min_value=0, max_value=10, format="%.2f"),
            },
        )


# =========================================================
# STUDENT SEARCH  (single searchable box)
# =========================================================

section("Student Search")

student_list = (
    filtered_df[["ID Number", "Name"]]
    .drop_duplicates(subset="ID Number")
    .sort_values("ID Number")
)
student_options = [
    f"{sid} - {name}"
    for sid, name in zip(student_list["ID Number"], student_list["Name"])
]

selected_option = st.selectbox(
    "Search by Student ID or Name",
    student_options,
    index=None,
    placeholder="🔍  Type a Student ID or Name and press Enter",
)

selected_student_data = None
if selected_option:
    selected_id = selected_option.split(" - ", 1)[0]
    selected_student_data = filtered_df[
        filtered_df["ID Number"].astype(str) == selected_id
    ].copy()


# =========================================================
# STUDENT-SPECIFIC SECTION
# =========================================================

if selected_student_data is not None and not selected_student_data.empty:

    student_id = str(selected_student_data["ID Number"].iloc[0])
    student_name = str(selected_student_data["Name"].iloc[0])
    mentor_name = get_mentor_name(selected_student_data)
    student_cgpa = calculate_cgpa(selected_student_data)
    pass_count, fail_count, detained_count = grade_counts(selected_student_data)
    total_credits = pd.to_numeric(
        selected_student_data["Credits"], errors="coerce").fillna(0).sum()
    sem_df = semester_summary(selected_student_data)

    initials = "".join(w[0] for w in student_name.split()[:2]).upper()
    joined = selected_student_data["Year"].iloc[0]
    if fail_count + detained_count > 0:
        status = '<span class="chip warn">⚠ Has backlogs</span>'
    else:
        status = '<span class="chip good">✓ All clear</span>'

    st.markdown(
        f"""
        <div class="profile">
            <div class="avatar">{initials}</div>
            <div>
                <div class="name">{student_name.title()}</div>
                <div class="meta">ID: {student_id} &nbsp;•&nbsp; Mentor: {mentor_name}</div>
                {status}<span class="chip info">Batch {joined}</span>
            </div>
            <div class="cgpa"><div class="n">{student_cgpa:.2f}</div>
                 <div class="l">OVERALL CGPA</div></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.write("")
    a1, a2, a3, a4, a5 = st.columns(5)
    with a1:
        kpi_card("COURSES", len(selected_student_data), "#6366f1", "📚")
    with a2:
        kpi_card("CREDITS", f"{total_credits:g}", "#22d3ee", "🎯")
    with a3:
        kpi_card("PASS", pass_count, "#34d399", "✅")
    with a4:
        kpi_card("FAIL", fail_count, "#fb923c", "❌")
    with a5:
        kpi_card("DETAINED", detained_count, "#fb7185", "🚫")

    # Semester-wise CGPA graph
    section("Semester-wise CGPA")
    if not sem_df.empty:
        enc = alt.Chart(sem_df).encode(
            x=alt.X("Semester:N", sort=None, title="Semester",
                    axis=alt.Axis(labelAngle=0)),
            y=alt.Y("CGPA:Q", scale=alt.Scale(domain=[0, 10])),
            tooltip=["Semester", "CGPA", "Total Courses", "Total Credits"],
        )
        layered = (
            enc.mark_area(opacity=0.22, color="#6366f1")
            + enc.mark_line(color="#818cf8", strokeWidth=3)
            + enc.mark_point(filled=True, size=130, color="#22d3ee")
            + enc.mark_text(dy=-16, color="#e6e9f5", fontWeight="bold").encode(
                text=alt.Text("CGPA:Q", format=".2f"))
        )
        st.altair_chart(style_chart(layered, 320), use_container_width=True)
    else:
        st.info("Semester-wise CGPA data is not available.")

    category_summary_df = category_summary(selected_student_data)

    course_data = selected_student_data[
        ["Course Code", "Course Name", "Academic Semester",
         "Grade", "Points", "Credits", "Category"]
    ].copy()
    course_data["_sort"] = course_data["Academic Semester"].map(semester_sort_key)
    course_data = course_data.sort_values("_sort").drop(columns=["_sort"])

    complete_data = selected_student_data[[
        "ID Number", "Name", "Course Code", "Course Name", "AY", "Semester",
        "Academic Semester", "Grade", "Points", "Credits", "Category",
        "Mentor Name",
    ]].copy()

    section("Academic Details")
    tab_cards, tab_courses, tab_summary, tab_full = st.tabs(
        ["🗂️ Semester Cards", "📋 Course Table", "📊 Summaries", "🧾 Full Record"]
    )

    with tab_cards:
        for semester in get_semesters(selected_student_data):
            sem_row = sem_df[sem_df["Semester"] == semester].iloc[0]
            st.markdown(
                f"#### Semester {semester} "
                f"<span class='chip info'>CGPA {sem_row['CGPA']:.2f}</span>",
                unsafe_allow_html=True,
            )
            semester_data = selected_student_data[
                selected_student_data["Academic Semester"] == semester
            ]
            card_columns = st.columns(4)
            for index, (_, row) in enumerate(semester_data.iterrows()):
                with card_columns[index % 4]:
                    show_course_card(row)

    with tab_courses:
        st.dataframe(course_data, use_container_width=True, hide_index=True)

    with tab_summary:
        s1, s2 = st.columns(2)
        with s1:
            st.markdown("##### Semester-wise Summary")
            st.dataframe(
                sem_df, use_container_width=True, hide_index=True,
                column_config={"CGPA": st.column_config.ProgressColumn(
                    "CGPA", min_value=0, max_value=10, format="%.2f")},
            )
        with s2:
            st.markdown("##### Category-wise Summary")
            st.dataframe(category_summary_df, use_container_width=True, hide_index=True)

    with tab_full:
        st.dataframe(complete_data, use_container_width=True, hide_index=True)

    # Export
    section("Export")
    export_col1, export_col2, _ = st.columns([1, 1, 3])

    excel_buffer = BytesIO()
    with pd.ExcelWriter(excel_buffer, engine="openpyxl") as writer:
        complete_data.to_excel(writer, index=False, sheet_name="Academic Record")
        sem_df.to_excel(writer, index=False, sheet_name="Semester Summary")
        category_summary_df.to_excel(writer, index=False, sheet_name="Category Summary")
    excel_buffer.seek(0)

    with export_col1:
        st.download_button(
            "📊 Download Excel",
            data=excel_buffer,
            file_name=f"{student_id}_Academic_Performance.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )

    pdf_buffer = generate_pdf(selected_student_data)
    with export_col2:
        st.download_button(
            "📄 Download PDF",
            data=pdf_buffer,
            file_name=f"{student_id}_Academic_Performance.pdf",
            mime="application/pdf",
            use_container_width=True,
        )

else:
    st.info("Search and select a student above to view individual academic performance.")
