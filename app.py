import streamlit as st
import pandas as pd

from io import BytesIO
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import (
    getSampleStyleSheet,
    ParagraphStyle
)
from reportlab.lib.enums import TA_CENTER
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Image
)
from reportlab.lib.units import inch


# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="KL UNIVERSITY",
    page_icon="🎓",
    layout="wide"
)


# =========================================================
# FILE PATHS
# =========================================================

BASE_DIR = Path(__file__).resolve().parent

CSV_FILE = BASE_DIR / "student.csv"
LOGO_PATH = BASE_DIR / "klu_logo.png.jpg"


# =========================================================
# SEMESTER SORT
# =========================================================

def semester_sort_key(value):

    try:

        parts = str(value).split("-")

        return (
            int(parts[0]),
            int(parts[1])
        )

    except Exception:

        return (999, 999)


# =========================================================
# NORMALIZE SEMESTER
# =========================================================

def normalize_semester(value):

    if pd.isna(value):

        return ""

    value = str(value).strip()

    value_lower = value.lower()

    if value_lower in [
        "odd",
        "odd sem"
    ]:

        return "Odd Sem"

    elif value_lower in [
        "even",
        "even sem"
    ]:

        return "Even Sem"

    elif "summer" in value_lower:

        return "Summer Term"

    return value


# =========================================================
# CALCULATE ACADEMIC SEMESTER
# =========================================================

def calculate_academic_semester(
    joining_year,
    academic_year,
    semester_type
):

    try:

        if pd.isna(joining_year):
            return None

        if pd.isna(academic_year):
            return None

        if pd.isna(semester_type):
            return None

        joining_year = str(
            joining_year
        ).strip().upper()

        academic_year = str(
            academic_year
        ).strip()

        semester_type = str(
            semester_type
        ).strip().lower()

        # Y23 -> 2023
        if joining_year.startswith("Y"):

            join_year = (
                int(joining_year[1:3])
                + 2000
            )

        else:

            join_year = int(
                joining_year
            )

        # 2023-2024 -> 2023
        academic_start_year = int(
            academic_year.split("-")[0]
        )

        year_of_study = (
            academic_start_year
            - join_year
            + 1
        )

        # Summer Term should not
        # receive an academic semester
        if "summer" in semester_type:

            return None

        if "odd" in semester_type:

            semester_number = "1"

        elif "even" in semester_type:

            semester_number = "2"

        else:

            return None

        if year_of_study < 1:

            return None

        return (
            f"{year_of_study}-"
            f"{semester_number}"
        )

    except Exception:

        return None


# =========================================================
# FIND MENTOR COLUMN
# =========================================================

def find_mentor_column(df):

    exact_names = [

        "Mentor",
        "Mentor Name",
        "MENTOR",
        "MENTOR NAME",
        "mentor_name",
        "mentor name",
        "Faculty Mentor",
        "Faculty Mentor Name",
        "MentorName"

    ]

    # Exact match
    for name in exact_names:

        for col in df.columns:

            if (
                str(col)
                .strip()
                .lower()
                == name.lower()
            ):

                return col

    # Flexible match
    for col in df.columns:

        clean = (
            str(col)
            .strip()
            .lower()
            .replace("_", " ")
            .replace("-", " ")
        )

        if "mentor" in clean:

            return col

    return None


# =========================================================
# FIND MARKS COLUMN
# =========================================================

def find_marks_column(df):

    possible_names = [

        "Marks",
        "Mark",
        "Marks Out of 50",
        "Marks out of 50",
        "Marks (Out of 50)",
        "Marks/50",
        "Internal Marks",
        "Internal Mark",
        "Mid Marks",
        "Mid Mark",
        "Mid Marks Out of 50",
        "Mid Marks/50",
        "Exam Marks",
        "Assessment Marks"

    ]

    # Exact match
    for name in possible_names:

        for col in df.columns:

            if (
                str(col)
                .strip()
                .lower()
                == name.lower()
            ):

                return col

    # Flexible match
    for col in df.columns:

        clean = (
            str(col)
            .strip()
            .lower()
            .replace("_", " ")
            .replace("-", " ")
        )

        if (
            "mark" in clean
            and "grade" not in clean
            and "point" not in clean
            and "credit" not in clean
        ):

            return col

    return None


# =========================================================
# LOAD DATA
# =========================================================

@st.cache_data
def load_data():

    df = pd.read_csv(
        CSV_FILE,
        low_memory=False
    )

    # -----------------------------------------------------
    # CLEAN COLUMN NAMES
    # -----------------------------------------------------

    df.columns = [
        str(col).strip()
        for col in df.columns
    ]

    # -----------------------------------------------------
    # ID
    # -----------------------------------------------------

    if "ID Number" in df.columns:

        df["ID Number"] = (
            df["ID Number"]
            .astype(str)
            .str.strip()
        )

    # -----------------------------------------------------
    # NAME
    # -----------------------------------------------------

    if "Name" in df.columns:

        df["Name"] = (
            df["Name"]
            .astype(str)
            .str.strip()
        )

    # -----------------------------------------------------
    # COURSE CODE
    # -----------------------------------------------------

    if "Course Code" in df.columns:

        df["Course Code"] = (
            df["Course Code"]
            .astype(str)
            .str.strip()
        )

    # -----------------------------------------------------
    # COURSE NAME
    # -----------------------------------------------------

    if "Course Name" in df.columns:

        df["Course Name"] = (
            df["Course Name"]
            .astype(str)
            .str.strip()
        )

    # -----------------------------------------------------
    # POINTS
    # -----------------------------------------------------

    if "Points" in df.columns:

        df["Points"] = pd.to_numeric(
            df["Points"],
            errors="coerce"
        ).fillna(0)

    else:

        df["Points"] = 0

    # -----------------------------------------------------
    # CREDITS
    # -----------------------------------------------------

    if "Credits" in df.columns:

        df["Credits"] = pd.to_numeric(
            df["Credits"],
            errors="coerce"
        ).fillna(0)

    else:

        df["Credits"] = 0

    # -----------------------------------------------------
    # GRADE
    # -----------------------------------------------------

    if "Grade" not in df.columns:

        df["Grade"] = ""

    # -----------------------------------------------------
    # CATEGORY
    # -----------------------------------------------------

    if "Category" in df.columns:

        df["Category"] = (
            df["Category"]
            .astype("string")
            .str.strip()
            .str.upper()
            .fillna("")
        )

    else:

        df["Category"] = ""

    # -----------------------------------------------------
    # AY
    # -----------------------------------------------------

    if "AY" in df.columns:

        df["AY"] = (
            df["AY"]
            .astype("string")
            .str.strip()
        )

    else:

        df["AY"] = ""

    # -----------------------------------------------------
    # SEMESTER
    # -----------------------------------------------------

    if "Semester" in df.columns:

        df["Semester"] = (
            df["Semester"]
            .apply(normalize_semester)
        )

    else:

        df["Semester"] = ""

    # =====================================================
    # JOINING YEAR FROM ID
    # =====================================================

    def get_joining_year(student_id):

        try:

            student_id = str(
                student_id
            ).strip()

            first_two = int(
                student_id[:2]
            )

            return f"Y{first_two}"

        except Exception:

            return ""

    if "ID Number" in df.columns:

        df["Year"] = (
            df["ID Number"]
            .apply(get_joining_year)
        )

    else:

        df["Year"] = ""

    # =====================================================
    # CREDIT POINTS
    # =====================================================

    df["Credit Points"] = (
        df["Points"]
        * df["Credits"]
    )

    # =====================================================
    # MENTOR
    # =====================================================

    mentor_column = find_mentor_column(
        df
    )

    if mentor_column is not None:

        df["Mentor Name"] = (
            df[mentor_column]
            .astype("string")
            .str.strip()
            .fillna("")
        )

        df["Mentor Name"] = (
            df["Mentor Name"]
            .replace(
                [
                    "",
                    "nan",
                    "NaN",
                    "none",
                    "None",
                    "NONE",
                    "<NA>",
                    "N/A",
                    "NA"
                ],
                ""
            )
        )

    else:

        df["Mentor Name"] = ""

    # =====================================================
    # MARKS
    # =====================================================

    marks_column = find_marks_column(
        df
    )

    if marks_column is not None:

        df["Marks"] = pd.to_numeric(
            df[marks_column],
            errors="coerce"
        )

    else:

        df["Marks"] = pd.NA

    # =====================================================
    # ACADEMIC SEMESTER
    # =====================================================

    df["Academic Semester"] = df.apply(

        lambda row:
        calculate_academic_semester(
            row["Year"],
            row["AY"],
            row["Semester"]
        ),

        axis=1

    )

    return df


# =========================================================
# CGPA
# =========================================================

def calculate_cgpa(data):

    if data.empty:

        return 0.0

    credits = pd.to_numeric(
        data["Credits"],
        errors="coerce"
    ).fillna(0)

    credit_points = pd.to_numeric(
        data["Credit Points"],
        errors="coerce"
    ).fillna(0)

    total_credits = credits.sum()

    total_points = credit_points.sum()

    if total_credits == 0:

        return 0.0

    return (
        total_points
        / total_credits
    )


# =========================================================
# COMPACT COURSE CARD
# =========================================================

def show_course_card(row):

    course_code = str(
        row.get(
            "Course Code",
            ""
        )
    )

    course_name = str(
        row.get(
            "Course Name",
            ""
        )
    )

    grade = str(
        row.get(
            "Grade",
            ""
        )
    )

    category = str(
        row.get(
            "Category",
            ""
        )
    )

    points = str(
        row.get(
            "Points",
            ""
        )
    )

    credits = str(
        row.get(
            "Credits",
            ""
        )
    )

    st.markdown(

        f"""
        <div style="
            border:1px solid #d9d9d9;
            border-radius:7px;
            padding:8px 10px;
            margin-bottom:7px;
            min-height:85px;
            background:#ffffff;
        ">

        <div style="
            font-size:14px;
            font-weight:600;
            margin-bottom:4px;
        ">
            {course_code}
        </div>

        <div style="
            font-size:12px;
            margin-bottom:5px;
            line-height:1.25;
        ">
            {course_name}
        </div>

        <div style="
            font-size:11px;
            color:#555;
        ">
            Grade: <b>{grade}</b>
            &nbsp; | &nbsp;
            Category: <b>{category}</b>
            &nbsp; | &nbsp;
            Points: <b>{points}</b>
            &nbsp; | &nbsp;
            Credits: <b>{credits}</b>
        </div>

        </div>
        """,

        unsafe_allow_html=True
    )


# =========================================================
# SEMESTER CARDS
# =========================================================

def show_semester_cards(student_data):

    st.markdown(
        "## Semester-wise Academic Performance"
    )

    semester_list = (
        student_data[
            "Academic Semester"
        ]
        .dropna()
        .unique()
        .tolist()
    )

    semester_list = [
        x
        for x in semester_list
        if str(x).strip() != ""
    ]

    semester_list = sorted(
        semester_list,
        key=semester_sort_key
    )

    for semester in semester_list:

        st.markdown(
            f"### {semester}"
        )

        sem_data = student_data[
            student_data[
                "Academic Semester"
            ] == semester
        ].copy()

        # 4 compact columns
        cols = st.columns(4)

        for index, (_, row) in enumerate(
            sem_data.iterrows()
        ):

            with cols[
                index % 4
            ]:

                show_course_card(row)


# =========================================================
# PDF GENERATION
# =========================================================

def generate_pdf(student_data):

    buffer = BytesIO()

    doc = SimpleDocTemplate(

        buffer,

        pagesize=A4,

        rightMargin=30,
        leftMargin=30,
        topMargin=25,
        bottomMargin=25

    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(

        "PDFTitle",

        parent=styles["Title"],

        alignment=TA_CENTER,

        fontSize=16,

        leading=19,

        spaceAfter=4

    )

    dept_style = ParagraphStyle(

        "PDFDept",

        parent=styles["Normal"],

        alignment=TA_CENTER,

        fontSize=10,

        leading=12,

        spaceAfter=8

    )

    heading_style = ParagraphStyle(

        "PDFHeading",

        parent=styles["Heading2"],

        fontSize=12,

        leading=14,

        spaceBefore=8,

        spaceAfter=6

    )

    normal_style = ParagraphStyle(

        "PDFNormal",

        parent=styles["Normal"],

        fontSize=8,

        leading=10

    )

    story = []

    # =====================================================
    # SMALL LOGO
    # =====================================================

    if LOGO_PATH.exists():

        try:

            logo = Image(
                str(LOGO_PATH),
                width=0.65 * inch,
                height=0.65 * inch
            )

            logo.hAlign = "CENTER"

            story.append(logo)

            story.append(
                Spacer(1, 3)
            )

        except Exception:

            pass

    # =====================================================
    # HEADER
    # =====================================================

    story.append(
        Paragraph(
            "KL UNIVERSITY",
            title_style
        )
    )

    story.append(
        Paragraph(
            "Department of CSE-4",
            dept_style
        )
    )

    # =====================================================
    # STUDENT DETAILS
    # =====================================================

    story.append(
        Paragraph(
            "Student Details",
            heading_style
        )
    )

    student_id = str(
        student_data[
            "ID Number"
        ].iloc[0]
    )

    student_name = str(
        student_data[
            "Name"
        ].iloc[0]
    )

    mentor_values = (

        student_data[
            "Mentor Name"
        ]
        .astype(str)
        .str.strip()

    )

    mentor_values = mentor_values[
        ~mentor_values.str.lower().isin(
            [
                "",
                "nan",
                "none",
                "<na>",
                "n/a",
                "not available"
            ]
        )
    ]

    if not mentor_values.empty:

        mentor_name = (
            mentor_values.iloc[0]
        )

    else:

        mentor_name = "Not Available"

    overall_cgpa = calculate_cgpa(
        student_data
    )

    student_details = [

        [
            Paragraph(
                "<b>Student ID</b>",
                normal_style
            ),

            Paragraph(
                student_id,
                normal_style
            )
        ],

        [
            Paragraph(
                "<b>Student Name</b>",
                normal_style
            ),

            Paragraph(
                student_name,
                normal_style
            )
        ],

        [
            Paragraph(
                "<b>Mentor Name</b>",
                normal_style
            ),

            Paragraph(
                mentor_name,
                normal_style
            )
        ],

        [
            Paragraph(
                "<b>Overall CGPA</b>",
                normal_style
            ),

            Paragraph(
                f"{overall_cgpa:.2f}",
                normal_style
            )
        ]

    ]

    student_table = Table(

        student_details,

        colWidths=[
            1.7 * inch,
            4.8 * inch
        ]

    )

    student_table.setStyle(

        TableStyle([

            (
                "GRID",
                (0, 0),
                (-1, -1),
                0.4,
                colors.grey
            ),

            (
                "BACKGROUND",
                (0, 0),
                (0, -1),
                colors.lightgrey
            ),

            (
                "VALIGN",
                (0, 0),
                (-1, -1),
                "MIDDLE"
            ),

            (
                "LEFTPADDING",
                (0, 0),
                (-1, -1),
                5
            ),

            (
                "RIGHTPADDING",
                (0, 0),
                (-1, -1),
                5
            )

        ])

    )

    story.append(
        student_table
    )

    # =====================================================
    # CATEGORY SUMMARY
    # =====================================================

    story.append(
        Paragraph(
            "Category Summary",
            heading_style
        )
    )

    category_order = [

        "AB",
        "DT",
        "F",
        "MTO",
        "-",
        "BLNA",
        "GP/MP",
        "NA"

    ]

    category_data = (

        student_data[
            "Category"
        ]
        .astype(str)
        .str.strip()
        .str.upper()

    )

    category_table_data = [

        [
            Paragraph(
                "<b>Category</b>",
                normal_style
            ),

            Paragraph(
                "<b>Count</b>",
                normal_style
            )
        ]

    ]

    for category in category_order:

        count = category_data.eq(
            category
        ).sum()

        category_table_data.append(

            [
                Paragraph(
                    category,
                    normal_style
                ),

                Paragraph(
                    str(int(count)),
                    normal_style
                )
            ]

        )

    category_table = Table(

        category_table_data,

        colWidths=[
            3.2 * inch,
            3.3 * inch
        ]

    )

    category_table.setStyle(

        TableStyle([

            (
                "GRID",
                (0, 0),
                (-1, -1),
                0.4,
                colors.grey
            ),

            (
                "BACKGROUND",
                (0, 0),
                (-1, 0),
                colors.lightgrey
            ),

            (
                "ALIGN",
                (1, 1),
                (1, -1),
                "CENTER"
            )

        ])

    )

    story.append(
        category_table
    )

    # =====================================================
    # ACADEMIC PERFORMANCE
    # =====================================================

    story.append(
        Paragraph(
            "Academic Performance",
            heading_style
        )
    )

    academic_table_data = [

        [

            Paragraph(
                "<b>Course Code</b>",
                normal_style
            ),

            Paragraph(
                "<b>Course Name</b>",
                normal_style
            ),

            Paragraph(
                "<b>Grade</b>",
                normal_style
            ),

            Paragraph(
                "<b>Points</b>",
                normal_style
            ),

            Paragraph(
                "<b>Credits</b>",
                normal_style
            ),

            Paragraph(
                "<b>Category</b>",
                normal_style
            )

        ]

    ]

    for _, row in student_data.iterrows():

        academic_table_data.append(

            [

                Paragraph(
                    str(
                        row.get(
                            "Course Code",
                            ""
                        )
                    ),
                    normal_style
                ),

                Paragraph(
                    str(
                        row.get(
                            "Course Name",
                            ""
                        )
                    ),
                    normal_style
                ),

                Paragraph(
                    str(
                        row.get(
                            "Grade",
                            ""
                        )
                    ),
                    normal_style
                ),

                Paragraph(
                    str(
                        row.get(
                            "Points",
                            ""
                        )
                    ),
                    normal_style
                ),

                Paragraph(
                    str(
                        row.get(
                            "Credits",
                            ""
                        )
                    ),
                    normal_style
                ),

                Paragraph(
                    str(
                        row.get(
                            "Category",
                            ""
                        )
                    ),
                    normal_style
                )

            ]

        )

    academic_table = Table(

        academic_table_data,

        repeatRows=1,

        colWidths=[
            0.85 * inch,
            2.35 * inch,
            0.55 * inch,
            0.65 * inch,
            0.65 * inch,
            0.75 * inch
        ]

    )

    academic_table.setStyle(

        TableStyle([

            (
                "GRID",
                (0, 0),
                (-1, -1),
                0.35,
                colors.grey
            ),

            (
                "BACKGROUND",
                (0, 0),
                (-1, 0),
                colors.lightgrey
            ),

            (
                "VALIGN",
                (0, 0),
                (-1, -1),
                "MIDDLE"
            ),

            (
                "ALIGN",
                (2, 1),
                (-1, -1),
                "CENTER"
            )

        ])

    )

    story.append(
        academic_table
    )

    # =====================================================
    # SEMESTER SUMMARY
    # =====================================================

    story.append(
        Paragraph(
            "Semester-wise Academic Performance",
            heading_style
        )
    )

    semester_list = (

        student_data[
            "Academic Semester"
        ]
        .dropna()
        .unique()
        .tolist()

    )

    semester_list = [

        x
        for x in semester_list
        if str(x).strip() != ""

    ]

    semester_list = sorted(

        semester_list,

        key=semester_sort_key

    )

    semester_table_data = [

        [

            Paragraph(
                "<b>Semester</b>",
                normal_style
            ),

            Paragraph(
                "<b>Total Courses</b>",
                normal_style
            ),

            Paragraph(
                "<b>Total Credits</b>",
                normal_style
            ),

            Paragraph(
                "<b>CGPA</b>",
                normal_style
            )

        ]

    ]

    for semester in semester_list:

        sem_data = student_data[

            student_data[
                "Academic Semester"
            ] == semester

        ].copy()

        semester_cgpa = calculate_cgpa(
            sem_data
        )

        total_courses = len(
            sem_data
        )

        total_credits = (

            pd.to_numeric(
                sem_data[
                    "Credits"
                ],
                errors="coerce"
            )
            .fillna(0)
            .sum()

        )

        semester_table_data.append(

            [

                Paragraph(
                    str(semester),
                    normal_style
                ),

                Paragraph(
                    str(
                        total_courses
                    ),
                    normal_style
                ),

                Paragraph(
                    str(
                        round(
                            total_credits,
                            2
                        )
                    ),
                    normal_style
                ),

                Paragraph(
                    f"{semester_cgpa:.2f}",
                    normal_style
                )

            ]

        )

    if len(
        semester_table_data
    ) > 1:

        semester_table = Table(

            semester_table_data,

            repeatRows=1,

            colWidths=[
                1.5 * inch,
                1.6 * inch,
                1.6 * inch,
                1.3 * inch
            ]

        )

        semester_table.setStyle(

            TableStyle([

                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.4,
                    colors.grey
                ),

                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.lightgrey
                ),

                (
                    "ALIGN",
                    (0, 0),
                    (-1, -1),
                    "CENTER"
                )

            ])

        )

        story.append(
            semester_table
        )

    # =====================================================
    # BACKLOG SUBJECTS
    # =====================================================

    story.append(
        Paragraph(
            "Backlog Subjects",
            heading_style
        )
    )

    backlog_data = student_data[

        student_data[
            "Category"
        ]
        .astype(str)
        .str.strip()
        .str.upper()
        .isin(
            ["F", "DT"]
        )

    ].copy()

    backlog_table_data = [

        [

            Paragraph(
                "<b>Semester</b>",
                normal_style
            ),

            Paragraph(
                "<b>Course Code</b>",
                normal_style
            ),

            Paragraph(
                "<b>Course Name</b>",
                normal_style
            ),

            Paragraph(
                "<b>Category</b>",
                normal_style
            )

        ]

    ]

    for _, row in backlog_data.iterrows():

        semester_value = row.get(
            "Academic Semester",
            ""
        )

        if pd.isna(
            semester_value
        ):

            semester_value = ""

        backlog_table_data.append(

            [

                Paragraph(
                    str(
                        semester_value
                    ),
                    normal_style
                ),

                Paragraph(
                    str(
                        row.get(
                            "Course Code",
                            ""
                        )
                    ),
                    normal_style
                ),

                Paragraph(
                    str(
                        row.get(
                            "Course Name",
                            ""
                        )
                    ),
                    normal_style
                ),

                Paragraph(
                    str(
                        row.get(
                            "Category",
                            ""
                        )
                    ),
                    normal_style
                )

            ]

        )

    if len(
        backlog_table_data
    ) > 1:

        backlog_table = Table(

            backlog_table_data,

            repeatRows=1,

            colWidths=[
                1.0 * inch,
                1.2 * inch,
                3.0 * inch,
                1.0 * inch
            ]

        )

        backlog_table.setStyle(

            TableStyle([

                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.4,
                    colors.grey
                ),

                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.lightgrey
                ),

                (
                    "ALIGN",
                    (0, 0),
                    (-1, -1),
                    "CENTER"
                )

            ])

        )

        story.append(
            backlog_table
        )

    else:

        story.append(
            Paragraph(
                "No Backlogs",
                normal_style
            )
        )

    # =====================================================
    # MARKS OF ALL MEMBERS
    # =====================================================

    story.append(
        Spacer(1, 8)
    )

    story.append(
        Paragraph(
            "Marks of All Members",
            heading_style
        )
    )

    marks_data = student_data.copy()

    # Remove Summer Term
    marks_data = marks_data[

        marks_data[
            "Semester"
        ]
        .astype(str)
        .str.strip()
        .str.lower()
        != "summer term"

    ].copy()

    # Remove missing academic semesters
    marks_data = marks_data[
        marks_data[
            "Academic Semester"
        ].notna()
    ].copy()

    marks_data = marks_data[

        marks_data[
            "Academic Semester"
        ]
        .astype(str)
        .str.strip()
        != ""

    ].copy()

    if not marks_data.empty:

        marks_data["_sort"] = (
            marks_data[
                "Academic Semester"
            ]
            .map(semester_sort_key)
        )

        marks_data = marks_data.sort_values(
            "_sort"
        )

    marks_table_data = [

        [

            Paragraph(
                "<b>Semester</b>",
                normal_style
            ),

            Paragraph(
                "<b>Course Code</b>",
                normal_style
            ),

            Paragraph(
                "<b>Course Name</b>",
                normal_style
            ),

            Paragraph(
                "<b>Marks (Out of 50)</b>",
                normal_style
            )

        ]

    ]

    for _, row in marks_data.iterrows():

        marks_value = row.get(
            "Marks",
            pd.NA
        )

        if pd.isna(
            marks_value
        ):

            marks_display = "-"

        else:

            try:

                marks_display = (
                    f"{float(marks_value):g}"
                )

            except Exception:

                marks_display = str(
                    marks_value
                )

        marks_table_data.append(

            [

                Paragraph(
                    str(
                        row.get(
                            "Academic Semester",
                            ""
                        )
                    ),
                    normal_style
                ),

                Paragraph(
                    str(
                        row.get(
                            "Course Code",
                            ""
                        )
                    ),
                    normal_style
                ),

                Paragraph(
                    str(
                        row.get(
                            "Course Name",
                            ""
                        )
                    ),
                    normal_style
                ),

                Paragraph(
                    marks_display,
                    normal_style
                )

            ]

        )

    if len(
        marks_table_data
    ) > 1:

        marks_table = Table(

            marks_table_data,

            repeatRows=1,

            colWidths=[
                1.0 * inch,
                1.2 * inch,
                3.0 * inch,
                1.3 * inch
            ]

        )

        marks_table.setStyle(

            TableStyle([

                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.4,
                    colors.grey
                ),

                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.lightgrey
                ),

                (
                    "ALIGN",
                    (0, 0),
                    (-1, -1),
                    "CENTER"
                ),

                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "MIDDLE"
                )

            ])

        )

        story.append(
            marks_table
        )

    else:

        story.append(

            Paragraph(
                "Marks are not available.",
                normal_style
            )

        )

    # =====================================================
    # BUILD PDF
    # =====================================================

    doc.build(story)

    buffer.seek(0)

    return buffer


# =========================================================
# LOAD DATA
# =========================================================

try:

    df = load_data()

except Exception as e:

    st.error(
        f"Unable to load student.csv: {e}"
    )

    st.stop()


# =========================================================
# HEADER
# =========================================================

st.title(
    "🎓 KL UNIVERSITY"
)

st.subheader(
    "Department of CSE-4 | Academic Performance Dashboard"
)


# =========================================================
# SIDEBAR
# =========================================================

st.sidebar.header(
    "Filters"
)


# =========================================================
# JOINING YEAR FILTER
# =========================================================

joining_years = sorted(

    df["Year"]
    .dropna()
    .astype(str)
    .unique()
    .tolist()

)

selected_year = st.sidebar.selectbox(

    "Joining Year",

    ["All"] + joining_years

)


# =========================================================
# COURSE CODE FILTER
# =========================================================

course_codes = sorted(

    df["Course Code"]
    .dropna()
    .astype(str)
    .unique()
    .tolist()

)

selected_course_code = (
    st.sidebar.selectbox(
        "Course Code",
        ["All"] + course_codes
    )
)


# =========================================================
# COURSE NAME FILTER
# =========================================================

course_names = sorted(

    df["Course Name"]
    .dropna()
    .astype(str)
    .unique()
    .tolist()

)

selected_course_name = (
    st.sidebar.selectbox(
        "Course Name",
        ["All"] + course_names
    )
)


# =========================================================
# APPLY FILTERS
# =========================================================

filtered_df = df.copy()


if selected_year != "All":

    filtered_df = filtered_df[
        filtered_df["Year"]
        == selected_year
    ]


if selected_course_code != "All":

    filtered_df = filtered_df[
        filtered_df["Course Code"]
        == selected_course_code
    ]


if selected_course_name != "All":

    filtered_df = filtered_df[
        filtered_df["Course Name"]
        == selected_course_name
    ]


# =========================================================
# GENERAL DASHBOARD KPIs
# =========================================================

st.markdown(
    "## Overall Department Summary"
)

overall_cgpa = calculate_cgpa(
    filtered_df
)

all_grades = (
    filtered_df[
        "Grade"
    ]
    .astype(str)
    .str.strip()
    .str.upper()
)

overall_pass = (
    ~all_grades.isin(
        ["F", "FAIL"]
    )
).sum()

overall_fail = (
    all_grades.isin(
        ["F", "FAIL"]
    )
).sum()

overall_categories = (
    filtered_df[
        "Category"
    ]
    .astype(str)
    .str.strip()
    .str.upper()
)

overall_dt = (
    overall_categories
    .eq("DT")
    .sum()
)

k1, k2, k3, k4 = st.columns(4)

with k1:

    st.metric(
        "Average CGPA",
        f"{overall_cgpa:.2f}"
    )

with k2:

    st.metric(
        "Pass",
        int(overall_pass)
    )

with k3:

    st.metric(
        "Fail",
        int(overall_fail)
    )

with k4:

    st.metric(
        "Detained",
        int(overall_dt)
    )


# =========================================================
# STUDENT SEARCH
# =========================================================

st.markdown(
    "## Student Search"
)

search_student = st.text_input(

    "Search by Student ID or Name",

    placeholder="Enter Student ID or Name"

)


# =========================================================
# FIND STUDENTS
# =========================================================

student_matches = filtered_df.copy()


if search_student.strip():

    search_value = (
        search_student
        .strip()
        .lower()
    )

    student_matches = filtered_df[

        filtered_df[
            "ID Number"
        ]
        .astype(str)
        .str.lower()
        .str.contains(
            search_value,
            na=False
        )

        |

        filtered_df[
            "Name"
        ]
        .astype(str)
        .str.lower()
        .str.contains(
            search_value,
            na=False
        )

    ]


# =========================================================
# STUDENT SELECTION
# =========================================================

selected_student_data = None


if search_student.strip():

    if student_matches.empty:

        st.warning(
            "No student found."
        )

    else:

        student_options = (

            student_matches[
                [
                    "ID Number",
                    "Name"
                ]
            ]
            .drop_duplicates()

        )

        student_options["Display"] = (

            student_options[
                "ID Number"
            ].astype(str)

            + " - "

            + student_options[
                "Name"
            ].astype(str)

        )

        selected_student = st.selectbox(

            "Select Student",

            student_options[
                "Display"
            ].tolist()

        )

        selected_id = (
            selected_student
            .split(" - ")[0]
        )

        selected_student_data = (
            student_matches[
                student_matches[
                    "ID Number"
                ].astype(str)
                == selected_id
            ].copy()
        )


# =========================================================
# SHOW STUDENT DATA ONLY AFTER SELECTION
# =========================================================

if (
    selected_student_data is not None
    and not selected_student_data.empty
):

    # =====================================================
    # STUDENT DETAILS
    # =====================================================

    st.markdown(
        "## Student Details"
    )

    c1, c2, c3, c4 = st.columns(4)

    with c1:

        st.metric(
            "Student ID",
            str(
                selected_student_data[
                    "ID Number"
                ].iloc[0]
            )
        )

    with c2:

        st.metric(
            "Student Name",
            str(
                selected_student_data[
                    "Name"
                ].iloc[0]
            )
        )

    with c3:

        mentor_values = (

            selected_student_data[
                "Mentor Name"
            ]
            .astype(str)
            .str.strip()

        )

        mentor_values = mentor_values[
            ~mentor_values.str.lower().isin(
                [
                    "",
                    "nan",
                    "none",
                    "<na>",
                    "n/a"
                ]
            )
        ]

        mentor_display = (

            mentor_values.iloc[0]
            if not mentor_values.empty
            else "Not Available"

        )

        st.metric(
            "Mentor",
            mentor_display
        )

    with c4:

        st.metric(
            "Overall CGPA",
            f"{calculate_cgpa(selected_student_data):.2f}"
        )


    # =====================================================
    # STUDENT SUMMARY
    # =====================================================

    st.markdown(
        "## Academic Summary"
    )

    grades = (

        selected_student_data[
            "Grade"
        ]
        .astype(str)
        .str.strip()
        .str.upper()

    )

    pass_count = (
        ~grades.isin(
            ["F", "FAIL"]
        )
    ).sum()

    fail_count = (
        grades.isin(
            ["F", "FAIL"]
        )
    ).sum()

    categories = (

        selected_student_data[
            "Category"
        ]
        .astype(str)
        .str.strip()
        .str.upper()

    )

    detained_count = (
        categories.eq(
            "DT"
        ).sum()
    )

    s1, s2, s3, s4 = st.columns(4)

    with s1:

        st.metric(
            "Overall CGPA",
            f"{calculate_cgpa(selected_student_data):.2f}"
        )

    with s2:

        st.metric(
            "Pass",
            int(pass_count)
        )

    with s3:

        st.metric(
            "Fail",
            int(fail_count)
        )

    with s4:

        st.metric(
            "Detained",
            int(detained_count)
        )


    # =====================================================
    # ONLY LINE GRAPH
    # =====================================================

    st.markdown(
        "## Semester-wise CGPA"
    )

    semester_graph_data = []

    semester_list = (

        selected_student_data[
            "Academic Semester"
        ]
        .dropna()
        .unique()
        .tolist()

    )

    semester_list = [

        x
        for x in semester_list
        if str(x).strip() != ""

    ]

    semester_list = sorted(

        semester_list,

        key=semester_sort_key

    )

    for semester in semester_list:

        sem_data = selected_student_data[

            selected_student_data[
                "Academic Semester"
            ] == semester

        ].copy()

        semester_cgpa = calculate_cgpa(
            sem_data
        )

        semester_graph_data.append(

            {
                "Semester": semester,
                "CGPA": round(
                    semester_cgpa,
                    2
                )
            }

        )

    if semester_graph_data:

        semester_graph_df = pd.DataFrame(
            semester_graph_data
        )

        st.line_chart(

            semester_graph_df.set_index(
                "Semester"
            ),

            height=300

        )

    else:

        st.info(
            "Semester-wise CGPA data is not available."
        )


    # =====================================================
    # COURSE-WISE TABLE
    # =====================================================

    st.markdown(
        "## Course-wise Academic Data"
    )

    course_table_columns = [

        "Course Code",
        "Course Name",
        "Academic Semester",
        "Grade",
        "Points",
        "Credits",
        "Category"

    ]

    course_table = (
        selected_student_data[
            course_table_columns
        ].copy()
    )

    course_table = course_table.sort_values(

        by="Academic Semester",

        key=lambda x:
        x.map(semester_sort_key)

    )

    st.dataframe(

        course_table,

        use_container_width=True,

        hide_index=True

    )


    # =====================================================
    # SEMESTER SUMMARY TABLE
    # =====================================================

    st.markdown(
        "## Semester-wise Summary"
    )

    semester_summary_data = []

    for semester in semester_list:

        sem_data = selected_student_data[

            selected_student_data[
                "Academic Semester"
            ] == semester

        ].copy()

        semester_summary_data.append(

            {

                "Semester":
                    semester,

                "Total Courses":
                    len(sem_data),

                "Total Credits":
                    round(
                        pd.to_numeric(
                            sem_data[
                                "Credits"
                            ],
                            errors="coerce"
                        )
                        .fillna(0)
                        .sum(),
                        2
                    ),

                "CGPA":
                    round(
                        calculate_cgpa(
                            sem_data
                        ),
                        2
                    )

            }

        )

    semester_summary_df = pd.DataFrame(
        semester_summary_data
    )

    st.dataframe(

        semester_summary_df,

        use_container_width=True,

        hide_index=True

    )


    # =====================================================
    # CATEGORY SUMMARY
    # =====================================================

    st.markdown(
        "## Category-wise Summary"
    )

    category_order = [

        "AB",
        "DT",
        "F",
        "MTO",
        "-",
        "BLNA",
        "GP/MP",
        "NA"

    ]

    category_summary_data = []

    for category in category_order:

        count = categories.eq(
            category
        ).sum()

        category_summary_data.append(

            {

                "Category":
                    category,

                "Count":
                    int(count)

            }

        )

    category_summary_df = pd.DataFrame(
        category_summary_data
    )

    st.dataframe(

        category_summary_df,

        use_container_width=True,

        hide_index=True

    )


    # =====================================================
    # SEMESTER CARDS
    # =====================================================

    show_semester_cards(
        selected_student_data
    )


    # =====================================================
    # COMPLETE RECORD
    # =====================================================

    st.markdown(
        "## Complete Academic Record"
    )

    complete_columns = [

        "ID Number",
        "Name",
        "Course Code",
        "Course Name",
        "AY",
        "Semester",
        "Academic Semester",
        "Grade",
        "Points",
        "Credits",
        "Category",
        "Mentor Name"

    ]

    available_columns = [

        col
        for col in complete_columns
        if col in selected_student_data.columns

    ]

    complete_table = (
        selected_student_data[
            available_columns
        ].copy()
    )

    st.dataframe(

        complete_table,

        use_container_width=True,

        hide_index=True

    )


    # =====================================================
    # EXPORT
    # =====================================================

    st.markdown(
        "## Export"
    )


    # -----------------------------------------------------
    # EXCEL
    # -----------------------------------------------------

    excel_buffer = BytesIO()

    with pd.ExcelWriter(

        excel_buffer,

        engine="openpyxl"

    ) as writer:

        selected_student_data.to_excel(

            writer,

            index=False,

            sheet_name="Student Performance"

        )

        course_table.to_excel(

            writer,

            index=False,

            sheet_name="Course Wise"

        )

        semester_summary_df.to_excel(

            writer,

            index=False,

            sheet_name="Semester Wise"

        )

        category_summary_df.to_excel(

            writer,

            index=False,

            sheet_name="Category Wise"

        )

    excel_buffer.seek(0)

    st.download_button(

        label="📊 Download Excel",

        data=excel_buffer,

        file_name=(

            f"{selected_id}_"
            "Academic_Performance.xlsx"

        ),

        mime=(

            "application/vnd.openxmlformats-"
            "officedocument.spreadsheetml.sheet"

        )

    )


    # -----------------------------------------------------
    # PDF
    # -----------------------------------------------------

    pdf_buffer = generate_pdf(

        selected_student_data

    )

    st.download_button(

        label="📄 Download Student PDF",

        data=pdf_buffer,

        file_name=(

            f"{selected_id}_"
            "Academic_Performance.pdf"

        ),

        mime="application/pdf"

    )

else:

    st.info(
        "Search for a student above to view individual academic performance."
    )
