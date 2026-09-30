import streamlit as st
import pandas as pd
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
# STYLES (HOME PAGE)
# =========================================================

st.markdown(
    """
<style>
.block-container {padding-top: 2rem;}
.hero {
    background: linear-gradient(135deg, #1e3a8a, #7c3aed);
    padding: 28px 32px; border-radius: 16px; margin-bottom: 24px;
}
.hero h1 {color: white; margin: 0; font-size: 34px;}
.hero p  {color: #e0e7ff; margin: 6px 0 0 0; font-size: 16px;}
.kpi {
    background: #1a1f2e; border: 1px solid #2b3245;
    border-left: 5px solid var(--c);
    border-radius: 12px; padding: 16px 18px;
}
.kpi .label {color: #9ca3af; font-size: 13px; letter-spacing: .5px;}
.kpi .value {color: white; font-size: 26px; font-weight: 700;}
</style>

<div class="hero">
    <h1>🎓 KL UNIVERSITY</h1>
    <p>Department of CSE-4 &nbsp;|&nbsp; Academic Performance Dashboard</p>
</div>
""",
    unsafe_allow_html=True,
)


def kpi_card(label, value, color):
    st.markdown(
        f"""<div class="kpi" style="--c:{color}">
            <div class="label">{label}</div>
            <div class="value">{value}</div>
        </div>""",
        unsafe_allow_html=True,
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
    st.markdown(
        f"""
        <div style="border:1px solid #d8d8d8; border-radius:7px; padding:7px 9px;
                    margin-bottom:6px; background:white; color:#111; min-height:80px;">
            <div style="font-size:13px; font-weight:600; margin-bottom:3px;">
                {row["Course Code"]}
            </div>
            <div style="font-size:11px; margin-bottom:4px; line-height:1.2;">
                {row["Course Name"]}
            </div>
            <div style="font-size:10px; color:#555; line-height:1.2;">
                Grade: <b>{row["Grade"]}</b> &nbsp;|&nbsp;
                Category: <b>{row["Category"]}</b> &nbsp;|&nbsp;
                Points: <b>{row["Points"]}</b> &nbsp;|&nbsp;
                Credits: <b>{row["Credits"]}</b>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# =========================================================
# PDF
# =========================================================

def generate_pdf(student_data):
    buffer = BytesIO()
    document = SimpleDocTemplate(
        buffer, pagesize=A4,
        leftMargin=30, rightMargin=30, topMargin=25, bottomMargin=25,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "TitleStyle", parent=styles["Title"], alignment=TA_CENTER,
        fontName="Helvetica-Bold", fontSize=22, leading=26,
        textColor=colors.HexColor("#1e3a8a"), spaceBefore=4, spaceAfter=2,
    )
    subtitle_style = ParagraphStyle(
        "SubtitleStyle", parent=styles["Normal"], alignment=TA_CENTER,
        fontName="Helvetica-Bold", fontSize=12, leading=15,
        textColor=colors.HexColor("#374151"), spaceAfter=1,
    )
    tagline_style = ParagraphStyle(
        "TaglineStyle", parent=styles["Normal"], alignment=TA_CENTER,
        fontName="Helvetica", fontSize=9, leading=11,
        textColor=colors.HexColor("#6b7280"),
    )
    heading_style = ParagraphStyle(
        "HeadingStyle", parent=styles["Heading2"], fontSize=11, leading=13,
        spaceBefore=8, spaceAfter=5,
    )
    normal_style = ParagraphStyle(
        "NormalStyle", parent=styles["Normal"], fontSize=7.5, leading=9,
    )

    def P(text, bold=False):
        text = str(text)
        return Paragraph(f"<b>{text}</b>" if bold else text, normal_style)

    def grid_table(rows, col_widths, header=True, align_center=False):
        table = Table(rows, colWidths=col_widths, repeatRows=1 if header else 0)
        style = [
            ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]
        if header:
            style.append(("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey))
        if align_center:
            style.append(("ALIGN", (0, 0), (-1, -1), "CENTER"))
        table.setStyle(TableStyle(style))
        return table

    story = []

    # Logo (keeps original aspect ratio, centered)
    if LOGO_FILE.exists():
        try:
            iw, ih = ImageReader(str(LOGO_FILE)).getSize()
            max_w, max_h = 4.2 * inch, 0.95 * inch
            scale = min(max_w / iw, max_h / ih)
            logo = Image(str(LOGO_FILE), width=iw * scale, height=ih * scale)
            logo.hAlign = "CENTER"
            story.append(logo)
            story.append(Spacer(1, 6))
        except Exception:
            pass

    story.append(Paragraph("KL UNIVERSITY", title_style))
    story.append(Paragraph("Department of CSE-4", subtitle_style))
    story.append(Paragraph("Student Academic Performance Report", tagline_style))
    story.append(HRFlowable(
        width="100%", thickness=1.2, color=colors.HexColor("#1e3a8a"),
        spaceBefore=8, spaceAfter=6,
    ))

    # Student details
    story.append(Paragraph("Student Details", heading_style))
    details = [
        [P("Student ID", True), P(student_data["ID Number"].iloc[0])],
        [P("Student Name", True), P(student_data["Name"].iloc[0])],
        [P("Mentor Name", True), P(get_mentor_name(student_data))],
        [P("Overall CGPA", True), P(f"{calculate_cgpa(student_data):.2f}")],
    ]
    t = Table(details, colWidths=[1.7 * inch, 4.8 * inch])
    t.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
        ("BACKGROUND", (0, 0), (0, -1), colors.lightgrey),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(t)

    # Category summary
    story.append(Paragraph("Category Summary", heading_style))
    cat_df = category_summary(student_data)
    rows = [[P("Category", True), P("Count", True)]]
    for _, r in cat_df.iterrows():
        rows.append([P(r["Category"]), P(int(r["Count"]))])
    story.append(grid_table(rows, [3.2 * inch, 3.3 * inch]))

    # Academic performance
    story.append(Paragraph("Academic Performance", heading_style))
    rows = [[P(h, True) for h in
             ["Course Code", "Course Name", "Grade", "Points", "Credits", "Category"]]]
    for _, r in student_data.iterrows():
        rows.append([
            P(r["Course Code"]), P(r["Course Name"]), P(r["Grade"]),
            P(r["Points"]), P(r["Credits"]), P(r["Category"]),
        ])
    story.append(grid_table(
        rows,
        [0.85 * inch, 2.35 * inch, 0.55 * inch, 0.65 * inch, 0.65 * inch, 0.75 * inch],
    ))

    # Semester-wise performance
    story.append(Paragraph("Semester-wise Academic Performance", heading_style))
    rows = [[P(h, True) for h in
             ["Semester", "Total Courses", "Total Credits", "CGPA"]]]
    for _, r in semester_summary(student_data).iterrows():
        rows.append([
            P(r["Semester"]), P(r["Total Courses"]),
            P(r["Total Credits"]), P(f"{r['CGPA']:.2f}"),
        ])
    story.append(grid_table(
        rows, [1.5 * inch, 1.6 * inch, 1.6 * inch, 1.3 * inch], align_center=True
    ))

    # Backlogs
    story.append(Paragraph("Backlog Subjects", heading_style))
    base = base_grade(student_data["Grade"])
    backlog_data = student_data[base.isin(["F", "DT"])]
    if not backlog_data.empty:
        rows = [[P(h, True) for h in
                 ["Semester", "Course Code", "Course Name", "Grade"]]]
        for _, r in backlog_data.iterrows():
            sem = r["Academic Semester"]
            rows.append([
                P("" if pd.isna(sem) else sem),
                P(r["Course Code"]), P(r["Course Name"]), P(r["Grade"]),
            ])
        story.append(grid_table(
            rows, [1.0 * inch, 1.2 * inch, 3.0 * inch, 1.0 * inch],
            align_center=True,
        ))
    else:
        story.append(P("No Backlogs"))

    # Marks
    story.append(Spacer(1, 8))
    story.append(Paragraph("Marks of All Members", heading_style))

    marks_data = student_data[
        student_data["Semester"].astype(str).str.strip().str.lower() != "summer term"
    ].copy()
    marks_data = marks_data[
        marks_data["Academic Semester"].notna()
        & (marks_data["Academic Semester"].astype(str).str.strip() != "")
    ].copy()
    marks_data["_sort"] = marks_data["Academic Semester"].map(semester_sort_key)
    marks_data = marks_data.sort_values("_sort")

    if not marks_data.empty:
        rows = [[P(h, True) for h in
                 ["Semester", "Course Code", "Course Name", "Marks (Out of 50)"]]]
        for _, r in marks_data.iterrows():
            m = r["Marks"]
            if pd.isna(m):
                display = "-"
            else:
                try:
                    display = f"{float(m):g}"
                except Exception:
                    display = str(m)
            rows.append([
                P(r["Academic Semester"]), P(r["Course Code"]),
                P(r["Course Name"]), P(display),
            ])
        story.append(grid_table(
            rows, [1.0 * inch, 1.2 * inch, 3.0 * inch, 1.3 * inch],
            align_center=True,
        ))
    else:
        story.append(P("Marks are not available."))

    document.build(story)
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

st.sidebar.header("Filters")

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


# =========================================================
# DEPARTMENT SUMMARY (HOME)
# =========================================================

st.markdown("## Overall Department Summary")

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
        kpi_card("TOTAL STUDENTS", f"{total_students:,}", "#3b82f6")
    with k2:
        kpi_card("AVERAGE CGPA", f"{department_cgpa:.2f}", "#8b5cf6")
    with k3:
        kpi_card("TOTAL PASSED", f"{pass_courses:,}", "#22c55e")
    with k4:
        kpi_card("TOTAL FAILED", f"{fail_courses:,}", "#f97316")
    with k5:
        kpi_card("BACKLOG STUDENTS", f"{students_with_backlog:,}", "#f59e0b")
    with k6:
        kpi_card("DETAINED", f"{dt_courses:,}", "#ef4444")

    st.write("")

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("#### Grade Distribution")
        grade_order = ["O", "A+", "A", "B+", "B", "C", "P", "F", "DT"]
        gc = base.value_counts().reindex(grade_order).dropna()
        st.bar_chart(gc, height=280)
    with c2:
        st.markdown("#### Students by Joining Year")
        yc = filtered_df.groupby("Year")["ID Number"].nunique().sort_index()
        st.bar_chart(yc, height=280)

    st.markdown("---")


# =========================================================
# STUDENT SEARCH  (single searchable box - no second "select" step)
# =========================================================

st.markdown("## Student Search")

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
    placeholder="Type a Student ID or Name and press Enter",
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

    st.markdown("## Student Details")
    d1, d2, d3, d4 = st.columns(4)
    with d1:
        kpi_card("STUDENT ID", student_id, "#3b82f6")
    with d2:
        kpi_card("STUDENT NAME", student_name.title(), "#8b5cf6")
    with d3:
        kpi_card("MENTOR", mentor_name, "#14b8a6")
    with d4:
        kpi_card("OVERALL CGPA", f"{student_cgpa:.2f}", "#f59e0b")

    # Academic summary
    st.markdown("## Academic Summary")
    pass_count, fail_count, detained_count = grade_counts(selected_student_data)

    a1, a2, a3, a4 = st.columns(4)
    with a1:
        kpi_card("OVERALL CGPA", f"{student_cgpa:.2f}", "#8b5cf6")
    with a2:
        kpi_card("PASS", pass_count, "#22c55e")
    with a3:
        kpi_card("FAIL", fail_count, "#f59e0b")
    with a4:
        kpi_card("DETAINED", detained_count, "#ef4444")

    # Semester-wise CGPA graph
    st.markdown("## Semester-wise CGPA")
    sem_df = semester_summary(selected_student_data)
    if not sem_df.empty:
        st.line_chart(sem_df.set_index("Semester")[["CGPA"]], height=300)
    else:
        st.info("Semester-wise CGPA data is not available.")

    # Course-wise data
    st.markdown("## Course-wise Academic Data")
    course_data = selected_student_data[
        ["Course Code", "Course Name", "Academic Semester",
         "Grade", "Points", "Credits", "Category"]
    ].copy()
    course_data["_sort"] = course_data["Academic Semester"].map(semester_sort_key)
    course_data = course_data.sort_values("_sort").drop(columns=["_sort"])
    st.dataframe(course_data, use_container_width=True, hide_index=True)

    # Semester summary table
    st.markdown("## Semester-wise Summary")
    st.dataframe(sem_df, use_container_width=True, hide_index=True)

    # Category summary
    st.markdown("## Category-wise Summary")
    category_summary_df = category_summary(selected_student_data)
    st.dataframe(category_summary_df, use_container_width=True, hide_index=True)

    # Cards
    st.markdown("## Semester-wise Academic Performance")
    for semester in get_semesters(selected_student_data):
        st.markdown(f"### {semester}")
        semester_data = selected_student_data[
            selected_student_data["Academic Semester"] == semester
        ]
        card_columns = st.columns(4)
        for index, (_, row) in enumerate(semester_data.iterrows()):
            with card_columns[index % 4]:
                show_course_card(row)

    # Complete record
    st.markdown("## Complete Academic Record")
    complete_data = selected_student_data[[
        "ID Number", "Name", "Course Code", "Course Name", "AY", "Semester",
        "Academic Semester", "Grade", "Points", "Credits", "Category",
        "Mentor Name",
    ]].copy()
    st.dataframe(complete_data, use_container_width=True, hide_index=True)

    # Export
    st.markdown("## Export")
    export_col1, export_col2 = st.columns(2)

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
        )

    pdf_buffer = generate_pdf(selected_student_data)
    with export_col2:
        st.download_button(
            "📄 Download PDF",
            data=pdf_buffer,
            file_name=f"{student_id}_Academic_Performance.pdf",
            mime="application/pdf",
        )

else:
    st.markdown("---")
    st.info(
        "Search and select a student above to view individual academic performance."
    )
