import streamlit as st
import pandas as pd
from pathlib import Path
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
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
# PAGE CONFIGURATION
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
LOGO_FILE = BASE_DIR / "klu_logo.png.jpg"


# =========================================================
# CHECK CSV
# =========================================================

if not CSV_FILE.exists():

    st.error(
        f"student.csv was not found.\n\n"
        f"Expected location:\n{CSV_FILE}"
    )

    st.stop()


# =========================================================
# NORMALIZE COLUMN NAME
# =========================================================

def clean_column_name(column):

    return (
        str(column)
        .strip()
        .lower()
        .replace("_", " ")
        .replace("-", " ")
    )


# =========================================================
# FIND COLUMN
# =========================================================

def find_column(df, possible_names):

    # Exact match
    for possible in possible_names:

        for actual in df.columns:

            if (
                clean_column_name(actual)
                == clean_column_name(possible)
            ):

                return actual

    # Partial match
    for possible in possible_names:

        possible_clean = clean_column_name(
            possible
        )

        for actual in df.columns:

            actual_clean = clean_column_name(
                actual
            )

            if possible_clean in actual_clean:

                return actual

    return None


# =========================================================
# FIND MENTOR COLUMN
# =========================================================

def find_mentor_column(df):

    names = [
        "Mentor",
        "Mentor Name",
        "MentorName",
        "Faculty Mentor",
        "Faculty Mentor Name",
        "MENTOR",
        "MENTOR NAME"
    ]

    column = find_column(
        df,
        names
    )

    if column is not None:
        return column

    for col in df.columns:

        name = clean_column_name(col)

        if "mentor" in name:

            return col

    return None


# =========================================================
# FIND MARKS COLUMN
# =========================================================

def find_marks_column(df):

    names = [
        "Marks",
        "Mark",
        "Marks Out of 50",
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

    column = find_column(
        df,
        names
    )

    if column is not None:
        return column

    for col in df.columns:

        name = clean_column_name(col)

        if (
            "mark" in name
            and "remark" not in name
            and "grade" not in name
            and "point" not in name
            and "credit" not in name
        ):

            return col

    return None


# =========================================================
# NORMALIZE SEMESTER
# =========================================================

def normalize_semester(value):

    if pd.isna(value):

        return ""

    value = str(value).strip()

    lower_value = value.lower()

    if lower_value in [
        "odd",
        "odd sem",
        "odd semester"
    ]:

        return "Odd Sem"

    if lower_value in [
        "even",
        "even sem",
        "even semester"
    ]:

        return "Even Sem"

    if "summer" in lower_value:

        return "Summer Term"

    return value


# =========================================================
# GET JOINING YEAR
# =========================================================

def get_joining_year(student_id):

    try:

        student_id = str(
            student_id
        ).strip()

        first_two = int(
            student_id[:2]
        )

        return f"Y{first_two}"

    except:

        return ""


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

        # Joining Year
        if joining_year.startswith("Y"):

            join_year = (
                int(joining_year[1:3])
                + 2000
            )

        else:

            join_year = int(
                joining_year
            )

        # Academic Year
        academic_start_year = int(
            academic_year.split("-")[0]
        )

        year_of_study = (
            academic_start_year
            - join_year
            + 1
        )

        if year_of_study < 1:

            return None

        # Summer Term should not get
        # an academic semester number
        if "summer" in semester_type:

            return None

        # Odd / Even
        if "odd" in semester_type:

            semester_number = "1"

        elif "even" in semester_type:

            semester_number = "2"

        else:

            return None

        return (
            f"{year_of_study}-"
            f"{semester_number}"
        )

    except:

        return None


# =========================================================
# SEMESTER SORT
# =========================================================

def semester_sort_key(value):

    try:

        first, second = str(
            value
        ).split("-")

        return (
            int(first),
            int(second)
        )

    except:

        return (
            999,
            999
        )


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
    # REQUIRED COLUMNS
    # -----------------------------------------------------

    required_columns = [
        "ID Number",
        "Name",
        "Course Code",
        "Course Name",
        "Grade",
        "Points",
        "Credits",
        "Category",
        "AY",
        "Semester"
    ]

    missing_columns = [
        col
        for col in required_columns
        if col not in df.columns
    ]

    if missing_columns:

        st.error(
            "The following required columns "
            "are missing from student.csv:"
        )

        st.write(
            missing_columns
        )

        st.write(
            "Columns found in your CSV:"
        )

        st.write(
            list(df.columns)
        )

        st.stop()

    # -----------------------------------------------------
    # ID
    # -----------------------------------------------------

    df["ID Number"] = (
        df["ID Number"]
        .astype(str)
        .str.strip()
    )

    # -----------------------------------------------------
    # NAME
    # -----------------------------------------------------

    df["Name"] = (
        df["Name"]
        .astype(str)
        .str.strip()
    )

    # -----------------------------------------------------
    # COURSE CODE
    # -----------------------------------------------------

    df["Course Code"] = (
        df["Course Code"]
        .astype(str)
        .str.strip()
    )

    # -----------------------------------------------------
    # COURSE NAME
    # -----------------------------------------------------

    df["Course Name"] = (
        df["Course Name"]
        .astype(str)
        .str.strip()
    )

    # -----------------------------------------------------
    # POINTS
    # -----------------------------------------------------

    df["Points"] = pd.to_numeric(
        df["Points"],
        errors="coerce"
    ).fillna(0)

    # -----------------------------------------------------
    # CREDITS
    # -----------------------------------------------------

    df["Credits"] = pd.to_numeric(
        df["Credits"],
        errors="coerce"
    ).fillna(0)

    # -----------------------------------------------------
    # GRADE
    # -----------------------------------------------------

    df["Grade"] = (
        df["Grade"]
        .astype(str)
        .str.strip()
    )

    # -----------------------------------------------------
    # CATEGORY
    # -----------------------------------------------------

    df["Category"] = (
        df["Category"]
        .astype(str)
        .str.strip()
        .str.upper()
    )

    df["Category"] = df["Category"].replace(
        "NAN",
        ""
    )

    # -----------------------------------------------------
    # AY
    # -----------------------------------------------------

    df["AY"] = (
        df["AY"]
        .astype(str)
        .str.strip()
    )

    # -----------------------------------------------------
    # SEMESTER
    # -----------------------------------------------------

    df["Semester"] = (
        df["Semester"]
        .apply(normalize_semester)
    )

    # -----------------------------------------------------
    # JOINING YEAR
    # -----------------------------------------------------

    df["Year"] = (
        df["ID Number"]
        .apply(get_joining_year)
    )

    # -----------------------------------------------------
    # CREDIT POINTS
    # -----------------------------------------------------

    df["Credit Points"] = (
        df["Points"]
        * df["Credits"]
    )

    # -----------------------------------------------------
    # MENTOR
    # -----------------------------------------------------

    mentor_column = find_mentor_column(
        df
    )

    if mentor_column is not None:

        df["Mentor Name"] = (
            df[mentor_column]
            .astype(str)
            .str.strip()
        )

        df["Mentor Name"] = (
            df["Mentor Name"]
            .replace(
                [
                    "nan",
                    "NaN",
                    "None",
                    "none",
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

    # -----------------------------------------------------
    # MARKS
    # -----------------------------------------------------

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

    # -----------------------------------------------------
    # ACADEMIC SEMESTER
    # -----------------------------------------------------

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
# CALCULATE CGPA
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

    total_credit_points = (
        credit_points.sum()
    )

    if total_credits == 0:

        return 0.0

    return (
        total_credit_points
        / total_credits
    )


# =========================================================
# COMPACT COURSE CARD
# =========================================================

def show_course_card(row):

    course_code = str(
        row["Course Code"]
    )

    course_name = str(
        row["Course Name"]
    )

    grade = str(
        row["Grade"]
    )

    category = str(
        row["Category"]
    )

    points = str(
        row["Points"]
    )

    credits = str(
        row["Credits"]
    )

    st.markdown(

        f"""
        <div style="
            border:1px solid #d8d8d8;
            border-radius:7px;
            padding:7px 9px;
            margin-bottom:6px;
            background:white;
            min-height:80px;
        ">

        <div style="
            font-size:13px;
            font-weight:600;
            margin-bottom:3px;
        ">
            {course_code}
        </div>

        <div style="
            font-size:11px;
            margin-bottom:4px;
            line-height:1.2;
        ">
            {course_name}
        </div>

        <div style="
            font-size:10px;
            color:#555;
            line-height:1.2;
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
# GENERATE PDF
# =========================================================

def generate_pdf(student_data):

    buffer = BytesIO()

    document = SimpleDocTemplate(

        buffer,

        pagesize=A4,

        leftMargin=30,
        rightMargin=30,
        topMargin=25,
        bottomMargin=25

    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "TitleStyle",
        parent=styles["Title"],
        alignment=TA_CENTER,
        fontSize=16,
        leading=18
    )

    subtitle_style = ParagraphStyle(
        "SubtitleStyle",
        parent=styles["Normal"],
        alignment=TA_CENTER,
        fontSize=9,
        leading=11
    )

    heading_style = ParagraphStyle(
        "HeadingStyle",
        parent=styles["Heading2"],
        fontSize=11,
        leading=13,
        spaceBefore=8,
        spaceAfter=5
    )

    normal_style = ParagraphStyle(
        "NormalStyle",
        parent=styles["Normal"],
        fontSize=7.5,
        leading=9
    )

    story = []

    # =====================================================
    # LOGO
    # =====================================================

    if LOGO_FILE.exists():

        try:

            logo = Image(
                str(LOGO_FILE),
                width=0.60 * inch,
                height=0.60 * inch
            )

            logo.hAlign = "CENTER"

            story.append(
                logo
            )

            story.append(
                Spacer(1, 3)
            )

        except:

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
            subtitle_style
        )
    )

    story.append(
        Spacer(1, 8)
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
        student_data["ID Number"].iloc[0]
    )

    student_name = str(
        student_data["Name"].iloc[0]
    )

    mentor_values = (
        student_data["Mentor Name"]
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

    categories = (
        student_data["Category"]
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

        count = (
            categories
            .eq(category)
            .sum()
        )

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
                    str(row["Course Code"]),
                    normal_style
                ),

                Paragraph(
                    str(row["Course Name"]),
                    normal_style
                ),

                Paragraph(
                    str(row["Grade"]),
                    normal_style
                ),

                Paragraph(
                    str(row["Points"]),
                    normal_style
                ),

                Paragraph(
                    str(row["Credits"]),
                    normal_style
                ),

                Paragraph(
                    str(row["Category"]),
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
    # SEMESTER-WISE ACADEMIC PERFORMANCE
    # =====================================================

    story.append(
        Paragraph(
            "Semester-wise Academic Performance",
            heading_style
        )
    )

    semesters = (
        student_data[
            "Academic Semester"
        ]
        .dropna()
        .unique()
        .tolist()
    )

    semesters = [
        semester
        for semester in semesters
        if str(semester).strip() != ""
    ]

    semesters = sorted(
        semesters,
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

    for semester in semesters:

        sem_data = student_data[
            student_data[
                "Academic Semester"
            ] == semester
        ].copy()

        sem_cgpa = calculate_cgpa(
            sem_data
        )

        total_credits = (
            pd.to_numeric(
                sem_data["Credits"],
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
                    str(len(sem_data)),
                    normal_style
                ),

                Paragraph(
                    str(round(
                        total_credits,
                        2
                    )),
                    normal_style
                ),

                Paragraph(
                    f"{sem_cgpa:.2f}",
                    normal_style
                )
            ]

        )

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
        .isin([
            "F",
            "DT"
        ])

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

        semester_value = (
            row["Academic Semester"]
        )

        if pd.isna(
            semester_value
        ):

            semester_value = ""

        backlog_table_data.append(

            [
                Paragraph(
                    str(semester_value),
                    normal_style
                ),

                Paragraph(
                    str(row["Course Code"]),
                    normal_style
                ),

                Paragraph(
                    str(row["Course Name"]),
                    normal_style
                ),

                Paragraph(
                    str(row["Category"]),
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

    # Remove empty academic semesters
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

    # Sort semester
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

        marks_value = row["Marks"]

        if pd.isna(
            marks_value
        ):

            marks_display = "-"

        else:

            try:

                marks_display = (
                    f"{float(marks_value):g}"
                )

            except:

                marks_display = str(
                    marks_value
                )

        marks_table_data.append(

            [
                Paragraph(
                    str(
                        row[
                            "Academic Semester"
                        ]
                    ),
                    normal_style
                ),

                Paragraph(
                    str(
                        row["Course Code"]
                    ),
                    normal_style
                ),

                Paragraph(
                    str(
                        row["Course Name"]
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

    document.build(
        story
    )

    buffer.seek(0)

    return buffer


# =========================================================
# LOAD DATA
# =========================================================

try:

    df = load_data()

except Exception as error:

    st.error(
        "There was an error while loading the CSV."
    )

    st.exception(
        error
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
# JOINING YEAR
# =========================================================

joining_year_options = sorted(

    df["Year"]
    .dropna()
    .astype(str)
    .unique()
    .tolist()

)

selected_year = st.sidebar.selectbox(

    "Joining Year",

    ["All"] + joining_year_options

)


# =========================================================
# COURSE CODE
# =========================================================

course_code_options = sorted(

    df["Course Code"]
    .dropna()
    .astype(str)
    .unique()
    .tolist()

)

selected_course_code = (
    st.sidebar.selectbox(
        "Course Code",
        ["All"] + course_code_options
    )
)


# =========================================================
# COURSE NAME
# =========================================================

course_name_options = sorted(

    df["Course Name"]
    .dropna()
    .astype(str)
    .unique()
    .tolist()

)

selected_course_name = (
    st.sidebar.selectbox(
        "Course Name",
        ["All"] + course_name_options
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
# DEPARTMENT SUMMARY
# =========================================================

st.markdown(
    "## Overall Department Summary"
)

if filtered_df.empty:

    st.warning(
        "No records match the selected filters."
    )

else:

    # =====================================================
    # TOTAL UNIQUE STUDENTS
    # =====================================================

    total_students = (
        filtered_df[
            "ID Number"
        ]
        .astype(str)
        .str.strip()
        .replace(
            ["", "nan", "None"],
            pd.NA
        )
        .dropna()
        .nunique()
    )

    # =====================================================
    # DEPARTMENT CGPA
    # =====================================================

    department_cgpa = calculate_cgpa(
        filtered_df
    )

    # =====================================================
    # GRADES
    # =====================================================

    department_grades = (
        filtered_df["Grade"]
        .astype(str)
        .str.strip()
        .str.upper()
    )

    # =====================================================
    # CATEGORIES
    # =====================================================

    department_categories = (
        filtered_df["Category"]
        .astype(str)
        .str.strip()
        .str.upper()
    )

    # =====================================================
    # PASS
    # =====================================================

    department_pass = (
        ~department_grades.isin(
            ["F", "FAIL"]
        )
    ).sum()

    # =====================================================
    # FAIL
    # =====================================================

    department_fail = (
        department_grades.isin(
            ["F", "FAIL"]
        )
    ).sum()

    # =====================================================
    # DETAINED
    # =====================================================

    department_dt = (
        department_categories
        .eq("DT")
        .sum()
    )

    # =====================================================
    # FIVE KPI COLUMNS
    # =====================================================

    k1, k2, k3, k4, k5 = st.columns(5)

    with k1:

        st.metric(
            "Total Students",
            int(total_students)
        )

    with k2:

        st.metric(
            "Average CGPA",
            f"{department_cgpa:.2f}"
        )

    with k3:

        st.metric(
            "Pass",
            int(department_pass)
        )

    with k4:

        st.metric(
            "Fail",
            int(department_fail)
        )

    with k5:

        st.metric(
            "Detained",
            int(department_dt)
        )


# =========================================================
# STUDENT SEARCH
# =========================================================

st.markdown(
    "## Student Search"
)

student_search = st.text_input(

    "Search by Student ID or Name",

    placeholder="Enter Student ID or Name"

)


# =========================================================
# STUDENT MATCHES
# =========================================================

if student_search.strip():

    search_text = (
        student_search
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
            search_text,
            na=False
        )

        |

        filtered_df[
            "Name"
        ]
        .astype(str)
        .str.lower()
        .str.contains(
            search_text,
            na=False
        )

    ].copy()

else:

    student_matches = pd.DataFrame()


# =========================================================
# SELECT STUDENT
# =========================================================

selected_student_data = None


if student_search.strip():

    if student_matches.empty:

        st.warning(
            "No student found for this search."
        )

    else:

        student_options_df = (
            student_matches[
                [
                    "ID Number",
                    "Name"
                ]
            ]
            .drop_duplicates()
            .sort_values(
                "ID Number"
            )
        )

        student_options = [

            f"{row['ID Number']} - {row['Name']}"

            for _, row
            in student_options_df.iterrows()

        ]

        selected_student_option = st.selectbox(

            "Select Student",

            student_options,

            index=None,

            placeholder="Select a student"

        )

        if selected_student_option:

            selected_id = (
                selected_student_option
                .split(" - ", 1)[0]
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
# STUDENT-SPECIFIC SECTION
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

    student_id = str(
        selected_student_data[
            "ID Number"
        ].iloc[0]
    )

    student_name = str(
        selected_student_data[
            "Name"
        ].iloc[0]
    )

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

    if not mentor_values.empty:

        mentor_name = (
            mentor_values.iloc[0]
        )

    else:

        mentor_name = "Not Available"

    student_cgpa = calculate_cgpa(
        selected_student_data
    )

    d1, d2, d3, d4 = st.columns(4)

    with d1:

        st.metric(
            "Student ID",
            student_id
        )

    with d2:

        st.metric(
            "Student Name",
            student_name
        )

    with d3:

        st.metric(
            "Mentor",
            mentor_name
        )

    with d4:

        st.metric(
            "Overall CGPA",
            f"{student_cgpa:.2f}"
        )


    # =====================================================
    # STUDENT SUMMARY
    # =====================================================

    st.markdown(
        "## Academic Summary"
    )

    grades = (
        selected_student_data["Grade"]
        .astype(str)
        .str.strip()
        .str.upper()
    )

    categories = (
        selected_student_data["Category"]
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

    detained_count = (
        categories.eq("DT")
        .sum()
    )

    a1, a2, a3, a4 = st.columns(4)

    with a1:

        st.metric(
            "Overall CGPA",
            f"{student_cgpa:.2f}"
        )

    with a2:

        st.metric(
            "Pass",
            int(pass_count)
        )

    with a3:

        st.metric(
            "Fail",
            int(fail_count)
        )

    with a4:

        st.metric(
            "Detained",
            int(detained_count)
        )


    # =====================================================
    # ONLY GRAPH
    # =====================================================

    st.markdown(
        "## Semester-wise CGPA"
    )

    graph_rows = []

    graph_semesters = (
        selected_student_data[
            "Academic Semester"
        ]
        .dropna()
        .unique()
        .tolist()
    )

    graph_semesters = [

        semester
        for semester in graph_semesters
        if str(semester).strip() != ""

    ]

    graph_semesters = sorted(
        graph_semesters,
        key=semester_sort_key
    )

    for semester in graph_semesters:

        semester_data = (
            selected_student_data[
                selected_student_data[
                    "Academic Semester"
                ] == semester
            ].copy()
        )

        graph_rows.append(

            {
                "Semester": semester,
                "CGPA": round(
                    calculate_cgpa(
                        semester_data
                    ),
                    2
                )
            }

        )

    if graph_rows:

        graph_df = pd.DataFrame(
            graph_rows
        )

        st.line_chart(
            graph_df.set_index(
                "Semester"
            ),
            height=300
        )

    else:

        st.info(
            "Semester-wise CGPA data is not available."
        )


    # =====================================================
    # COURSE-WISE ACADEMIC DATA
    # =====================================================

    st.markdown(
        "## Course-wise Academic Data"
    )

    course_data = (
        selected_student_data[
            [
                "Course Code",
                "Course Name",
                "Academic Semester",
                "Grade",
                "Points",
                "Credits",
                "Category"
            ]
        ].copy()
    )

    course_data["_sort"] = (
        course_data[
            "Academic Semester"
        ]
        .map(semester_sort_key)
    )

    course_data = (
        course_data
        .sort_values("_sort")
        .drop(
            columns=["_sort"]
        )
    )

    st.dataframe(
        course_data,
        use_container_width=True,
        hide_index=True
    )


    # =====================================================
    # SEMESTER SUMMARY
    # =====================================================

    st.markdown(
        "## Semester-wise Summary"
    )

    summary_rows = []

    for semester in graph_semesters:

        semester_data = (
            selected_student_data[
                selected_student_data[
                    "Academic Semester"
                ] == semester
            ].copy()
        )

        total_credits = (
            pd.to_numeric(
                semester_data["Credits"],
                errors="coerce"
            )
            .fillna(0)
            .sum()
        )

        summary_rows.append(

            {
                "Semester": semester,

                "Total Courses":
                    len(semester_data),

                "Total Credits":
                    round(
                        total_credits,
                        2
                    ),

                "CGPA":
                    round(
                        calculate_cgpa(
                            semester_data
                        ),
                        2
                    )
            }

        )

    semester_summary_df = pd.DataFrame(
        summary_rows
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

    category_rows = []

    for category in category_order:

        category_rows.append(

            {
                "Category": category,

                "Count": int(
                    categories.eq(
                        category
                    ).sum()
                )
            }

        )

    category_summary_df = pd.DataFrame(
        category_rows
    )

    st.dataframe(
        category_summary_df,
        use_container_width=True,
        hide_index=True
    )


    # =====================================================
    # SEMESTER-WISE COMPACT CARDS
    # =====================================================

    st.markdown(
        "## Semester-wise Academic Performance"
    )

    for semester in graph_semesters:

        st.markdown(
            f"### {semester}"
        )

        semester_data = (
            selected_student_data[
                selected_student_data[
                    "Academic Semester"
                ] == semester
            ].copy()
        )

        card_columns = st.columns(4)

        for index, (_, row) in enumerate(
            semester_data.iterrows()
        ):

            with card_columns[
                index % 4
            ]:

                show_course_card(
                    row
                )


    # =====================================================
    # COMPLETE ACADEMIC RECORD
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

    complete_data = (
        selected_student_data[
            complete_columns
        ].copy()
    )

    st.dataframe(
        complete_data,
        use_container_width=True,
        hide_index=True
    )


    # =====================================================
    # EXPORT
    # =====================================================

    st.markdown(
        "## Export"
    )

    export_col1, export_col2 = st.columns(2)


    # =====================================================
    # EXCEL EXPORT
    # =====================================================

    excel_buffer = BytesIO()

    with pd.ExcelWriter(
        excel_buffer,
        engine="openpyxl"
    ) as writer:

        complete_data.to_excel(
            writer,
            index=False,
            sheet_name="Academic Record"
        )

        semester_summary_df.to_excel(
            writer,
            index=False,
            sheet_name="Semester Summary"
        )

        category_summary_df.to_excel(
            writer,
            index=False,
            sheet_name="Category Summary"
        )

    excel_buffer.seek(0)

    with export_col1:

        st.download_button(

            "📊 Download Excel",

            data=excel_buffer,

            file_name=(
                f"{student_id}_"
                "Academic_Performance.xlsx"
            ),

            mime=(
                "application/vnd.openxmlformats-"
                "officedocument.spreadsheetml.sheet"
            )

        )


    # =====================================================
    # PDF EXPORT
    # =====================================================

    pdf_buffer = generate_pdf(
        selected_student_data
    )

    with export_col2:

        st.download_button(

            "📄 Download PDF",

            data=pdf_buffer,

            file_name=(
                f"{student_id}_"
                "Academic_Performance.pdf"
            ),

            mime="application/pdf"

        )


# =========================================================
# WHEN NO STUDENT IS SELECTED
# =========================================================

else:

    st.markdown(
        "---"
    )

    st.info(
        "Search and select a student above "
        "to view individual academic performance."
    )
