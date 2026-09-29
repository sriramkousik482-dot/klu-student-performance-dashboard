import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

from io import BytesIO
from pathlib import Path

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
    Image,
    PageBreak
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
LOGO_PATH = BASE_DIR / "klu_logo.png.jpg"


# =========================================================
# SEMESTER SORTING
# =========================================================

def semester_sort_key(value):

    try:

        parts = str(value).split("-")

        return int(parts[0]), int(parts[1])

    except:

        return 999, 999


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

        joining_year = str(joining_year).strip().upper()

        academic_year = str(academic_year).strip()

        semester_type = str(
            semester_type
        ).strip().lower()


        # Convert Y23 -> 2023
        if joining_year.startswith("Y"):

            join_year = (
                int(joining_year[1:3]) + 2000
            )

        else:

            join_year = int(joining_year)


        # 2023-2024 -> 2023
        academic_start_year = int(
            academic_year.split("-")[0]
        )


        year_of_study = (
            academic_start_year
            - join_year
            + 1
        )


        # Summer Term should not get a semester number
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


        return f"{year_of_study}-{semester_number}"


    except Exception:

        return None


# =========================================================
# NORMALIZE SEMESTER
# =========================================================

def normalize_semester(value):

    if pd.isna(value):

        return ""

    value = str(value).strip()

    value_lower = value.lower()


    if value_lower in ["odd", "odd sem"]:

        return "Odd Sem"


    elif value_lower in ["even", "even sem"]:

        return "Even Sem"


    elif "summer" in value_lower:

        return "Summer Term"


    else:

        return value


# =========================================================
# FIND MARKS COLUMN
# =========================================================

def find_marks_column(df):

    possible_columns = [

        "Marks",
        "Mark",
        "Marks Out of 50",
        "Marks out of 50",
        "Marks/50",
        "Marks (Out of 50)",
        "Internal Marks",
        "Internal Mark",
        "Mid Marks",
        "Mid Mark",
        "Mid Marks Out of 50",
        "Mid Marks/50",
        "Exam Marks",
        "Assessment Marks"

    ]


    # Exact matching first

    for possible in possible_columns:

        for actual in df.columns:

            if str(actual).strip().lower() == possible.lower():

                return actual


    # Flexible matching

    for actual in df.columns:

        clean = (
            str(actual)
            .strip()
            .lower()
            .replace("_", " ")
            .replace("-", " ")
            .replace("(", "")
            .replace(")", "")
        )


        if (
            "mark" in clean
            and "grade" not in clean
            and "point" not in clean
            and "credit" not in clean
        ):

            return actual


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
    # ID NUMBER
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


    # -----------------------------------------------------
    # CREDITS
    # -----------------------------------------------------

    if "Credits" in df.columns:

        df["Credits"] = pd.to_numeric(
            df["Credits"],
            errors="coerce"
        ).fillna(0)


    # -----------------------------------------------------
    # MARKS
    # -----------------------------------------------------

    marks_column = find_marks_column(df)


    if marks_column is not None:

        df["Marks"] = pd.to_numeric(
            df[marks_column],
            errors="coerce"
        )

    else:

        # Keep the application running
        # if the CSV does not contain marks.

        df["Marks"] = pd.NA


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
    # SEMESTER
    # -----------------------------------------------------

    if "Semester" in df.columns:

        df["Semester"] = df["Semester"].apply(
            normalize_semester
        )

    else:

        df["Semester"] = ""


    # -----------------------------------------------------
    # ACADEMIC YEAR
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
    # FIND JOINING YEAR
    # -----------------------------------------------------

    if "ID Number" in df.columns:

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


        df["Year"] = df["ID Number"].apply(
            get_joining_year
        )

    else:

        df["Year"] = ""


    # -----------------------------------------------------
    # CREDIT POINTS
    # -----------------------------------------------------

    df["Credit Points"] = (
        df["Points"]
        * df["Credits"]
    )


    # =====================================================
    # MENTOR NAME
    # =====================================================

    mentor_column = None


    for col in df.columns:

        col_clean = (
            str(col)
            .strip()
            .lower()
            .replace("_", " ")
            .replace("-", " ")
        )


        if "mentor" in col_clean:

            mentor_column = col

            break


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
                    "None",
                    "NONE",
                    "<NA>"
                ],
                ""
            )
        )

    else:

        df["Mentor Name"] = ""


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
# CALCULATE CGPA
# =========================================================

def calculate_cgpa(data):

    if data.empty:

        return 0.0


    total_credits = pd.to_numeric(
        data["Credits"],
        errors="coerce"
    ).fillna(0).sum()


    total_credit_points = pd.to_numeric(
        data["Credit Points"],
        errors="coerce"
    ).fillna(0).sum()


    if total_credits == 0:

        return 0.0


    return (
        total_credit_points
        / total_credits
    )


# =========================================================
# RESULT
# =========================================================

def get_result(grade):

    grade = str(
        grade
    ).strip().upper()


    if grade in ["F", "FAIL"]:

        return "FAIL"


    return "PASS"


# =========================================================
# COURSE CARD
# =========================================================

def show_course_card(row):

    st.markdown(
        f"""
        <div style="
            border:1px solid #ddd;
            border-radius:10px;
            padding:15px;
            margin-bottom:10px;
        ">

        <h4>
        {row.get("Course Code", "")}
        -
        {row.get("Course Name", "")}
        </h4>

        <b>Grade:</b>
        {row.get("Grade", "")}

        &nbsp;&nbsp;

        <b>Category:</b>
        {row.get("Category", "")}

        &nbsp;&nbsp;

        <b>Points:</b>
        {row.get("Points", "")}

        &nbsp;&nbsp;

        <b>Credits:</b>
        {row.get("Credits", "")}

        </div>
        """,
        unsafe_allow_html=True
    )


# =========================================================
# SEMESTER CARDS
# =========================================================

def show_semester_cards(student_data):

    st.subheader(
        "Semester-wise Academic Performance"
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
        x for x in semester_list
        if str(x).strip() != ""
    ]


    semester_list = sorted(
        semester_list,
        key=semester_sort_key
    )


    for semester in semester_list:

        st.markdown(
            f"### Semester {semester}"
        )


        sem_data = student_data[
            student_data[
                "Academic Semester"
            ] == semester
        ].copy()


        cols = st.columns(3)


        for index, (_, row) in enumerate(
            sem_data.iterrows()
        ):

            with cols[index % 3]:

                show_course_card(row)


# =========================================================
# PDF GENERATION
# =========================================================

def generate_pdf(student_data):

    buffer = BytesIO()


    doc = SimpleDocTemplate(

        buffer,

        pagesize=A4,

        rightMargin=35,
        leftMargin=35,
        topMargin=35,
        bottomMargin=35

    )


    styles = getSampleStyleSheet()


    title_style = ParagraphStyle(

        "TitleStyle",

        parent=styles["Title"],

        alignment=TA_CENTER,

        fontSize=18,

        leading=22,

        spaceAfter=10

    )


    heading_style = ParagraphStyle(

        "HeadingStyle",

        parent=styles["Heading2"],

        fontSize=13,

        leading=16,

        spaceBefore=10,

        spaceAfter=8

    )


    normal_style = ParagraphStyle(

        "NormalStyle",

        parent=styles["Normal"],

        fontSize=9,

        leading=12

    )


    story = []


    # =====================================================
    # LOGO
    # =====================================================

    if LOGO_PATH.exists():

        try:

            logo = Image(
                str(LOGO_PATH),
                width=1.0 * inch,
                height=1.0 * inch
            )

            logo.hAlign = "CENTER"

            story.append(logo)

            story.append(
                Spacer(1, 5)
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
            ParagraphStyle(
                "Dept",
                parent=normal_style,
                alignment=TA_CENTER,
                fontSize=11
            )
        )

    )


    story.append(
        Spacer(1, 12)
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


    student_id = (
        str(
            student_data["ID Number"].iloc[0]
        )
    )


    student_name = (
        str(
            student_data["Name"].iloc[0]
        )
    )


    # Mentor

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
            Paragraph("<b>Student ID</b>", normal_style),
            Paragraph(student_id, normal_style)
        ],

        [
            Paragraph("<b>Student Name</b>", normal_style),
            Paragraph(student_name, normal_style)
        ],

        [
            Paragraph("<b>Mentor Name</b>", normal_style),
            Paragraph(mentor_name, normal_style)
        ],

        [
            Paragraph("<b>Overall CGPA</b>", normal_style),
            Paragraph(
                f"{overall_cgpa:.2f}",
                normal_style
            )
        ]

    ]


    student_table = Table(

        student_details,

        colWidths=[
            1.8 * inch,
            4.7 * inch
        ]

    )


    student_table.setStyle(

        TableStyle([

            (
                "GRID",
                (0, 0),
                (-1, -1),
                0.5,
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
                6
            ),

            (
                "RIGHTPADDING",
                (0, 0),
                (-1, -1),
                6
            )

        ])

    )


    story.append(student_table)

    story.append(
        Spacer(1, 15)
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
            Paragraph("<b>Category</b>", normal_style),
            Paragraph("<b>Count</b>", normal_style)
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
                0.5,
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


    story.append(category_table)

    story.append(
        Spacer(1, 15)
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


    academic_columns = [

        "Course Code",
        "Course Name",
        "Grade",
        "Points",
        "Credits",
        "Category"

    ]


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
                    str(row.get(
                        "Course Code",
                        ""
                    )),
                    normal_style
                ),

                Paragraph(
                    str(row.get(
                        "Course Name",
                        ""
                    )),
                    normal_style
                ),

                Paragraph(
                    str(row.get(
                        "Grade",
                        ""
                    )),
                    normal_style
                ),

                Paragraph(
                    str(row.get(
                        "Points",
                        ""
                    )),
                    normal_style
                ),

                Paragraph(
                    str(row.get(
                        "Credits",
                        ""
                    )),
                    normal_style
                ),

                Paragraph(
                    str(row.get(
                        "Category",
                        ""
                    )),
                    normal_style
                )

            ]

        )


    academic_table = Table(

        academic_table_data,

        repeatRows=1,

        colWidths=[
            0.9 * inch,
            2.3 * inch,
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


    story.append(academic_table)

    story.append(
        Spacer(1, 15)
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


    semester_list = (

        student_data[
            "Academic Semester"
        ]
        .dropna()
        .unique()
        .tolist()

    )


    semester_list = [

        x for x in semester_list

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


        total_courses = len(
            sem_data
        )


        semester_table_data.append(

            [

                Paragraph(
                    str(semester),
                    normal_style
                ),

                Paragraph(
                    str(
                        int(total_courses)
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
                    f"{sem_cgpa:.2f}",
                    normal_style
                )

            ]

        )


    if len(semester_table_data) > 1:

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
                    0.5,
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


    story.append(
        Spacer(1, 15)
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

        backlog_table_data.append(

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


    if len(backlog_table_data) > 1:

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
                    0.5,
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
            backlog_table
        )

    else:

        story.append(

            Paragraph(
                "No Backlogs",
                normal_style
            )

        )


    story.append(
        Spacer(1, 18)
    )


    # =====================================================
    # NEW SECTION
    # MARKS OF ALL MEMBERS / ALL COURSES
    # =====================================================

    story.append(

        Paragraph(
            "Marks of All Members",
            heading_style
        )

    )


    # -----------------------------------------------------
    # Remove Summer Term
    # -----------------------------------------------------

    marks_data = student_data.copy()


    marks_data = marks_data[

        marks_data[
            "Semester"
        ]
        .astype(str)
        .str.strip()
        .str.lower()
        .ne("summer term")

    ].copy()


    # Remove rows without academic semester

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
        .ne("")

    ].copy()


    # Sort semester

    if not marks_data.empty:

        marks_data["_sort"] = (
            marks_data[
                "Academic Semester"
            ]
            .map(semester_sort_key)
        )


        marks_data = marks_data.sort_values(
            by="_sort"
        )


    # -----------------------------------------------------
    # Marks table
    # -----------------------------------------------------

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


        if pd.isna(marks_value):

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


    if len(marks_table_data) > 1:

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
                    0.5,
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
# TITLE
# =========================================================

st.title(
    "🎓 KL UNIVERSITY"
)

st.subheader(
    "Department of CSE-4 | Academic Performance Dashboard"
)


# =========================================================
# SIDEBAR FILTERS
# =========================================================

st.sidebar.header(
    "Filters"
)


# ---------------------------------------------------------
# Joining Year
# ---------------------------------------------------------

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


# ---------------------------------------------------------
# Course Code
# ---------------------------------------------------------

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


# ---------------------------------------------------------
# Course Name
# ---------------------------------------------------------

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
# SEARCH STUDENT
# =========================================================

st.markdown(
    "### Student Search"
)


search_student = st.text_input(

    "Search by Student ID or Name",

    placeholder="Enter Student ID or Name"

)


if search_student.strip():

    search_value = (
        search_student
        .strip()
        .lower()
    )


    filtered_df = filtered_df[

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
# SEMESTER SEARCH
# =========================================================

search_semester = st.text_input(

    "Search Semester",

    placeholder="Example: 1-1, 1-2, 2-1"

)


if search_semester.strip():

    search_sem = (
        search_semester
        .strip()
        .lower()
    )


    filtered_df = filtered_df[

        filtered_df[
            "Academic Semester"
        ]
        .astype(str)
        .str.lower()
        .str.contains(
            search_sem,
            na=False
        )

    ]


# =========================================================
# NO DATA
# =========================================================

if filtered_df.empty:

    st.warning(
        "No records found."
    )

    st.stop()


# =========================================================
# SELECT STUDENT
# =========================================================

student_options = (

    filtered_df[
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


# =========================================================
# SELECTED STUDENT DATA
# =========================================================

selected_student_data = filtered_df[

    filtered_df[
        "ID Number"
    ].astype(str)
    == selected_id

].copy()


if selected_student_data.empty:

    st.warning(
        "Student data not found."
    )

    st.stop()


# =========================================================
# STUDENT INFORMATION
# =========================================================

st.markdown(
    "## Student Details"
)


student_col1, student_col2, student_col3, student_col4 = (
    st.columns(4)
)


with student_col1:

    st.metric(
        "Student ID",
        str(
            selected_student_data[
                "ID Number"
            ].iloc[0]
        )
    )


with student_col2:

    st.metric(
        "Student Name",
        str(
            selected_student_data[
                "Name"
            ].iloc[0]
        )
    )


with student_col3:

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
                "<na>"
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


with student_col4:

    st.metric(

        "Overall CGPA",

        f"{calculate_cgpa(selected_student_data):.2f}"

    )


# =========================================================
# KPI SECTION
# =========================================================

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


category_values = (

    selected_student_data[
        "Category"
    ]
    .astype(str)
    .str.strip()
    .str.upper()

)


detained_count = category_values.eq(
    "DT"
).sum()


k1, k2, k3, k4 = st.columns(4)


with k1:

    st.metric(
        "Overall CGPA",
        f"{calculate_cgpa(selected_student_data):.2f}"
    )


with k2:

    st.metric(
        "Pass",
        int(pass_count)
    )


with k3:

    st.metric(
        "Fail",
        int(fail_count)
    )


with k4:

    st.metric(
        "Detained",
        int(detained_count)
    )


# =========================================================
# VISUAL ANALYTICS
# =========================================================

st.markdown(
    "## Visual Analytics"
)


graph_col1, graph_col2 = st.columns(2)


# ---------------------------------------------------------
# Grade Distribution
# ---------------------------------------------------------

with graph_col1:

    st.markdown(
        "### Grade Distribution"
    )


    grade_data = (

        selected_student_data[
            "Grade"
        ]
        .astype(str)
        .str.strip()
        .str.upper()

    )


    grade_counts = (
        grade_data
        .value_counts()
        .reset_index()
    )


    grade_counts.columns = [
        "Grade",
        "Count"
    ]


    if not grade_counts.empty:

        st.bar_chart(

            grade_counts.set_index(
                "Grade"
            )

        )


# ---------------------------------------------------------
# Category Distribution
# ---------------------------------------------------------

with graph_col2:

    st.markdown(
        "### Category Distribution"
    )


    category_data = (

        selected_student_data[
            "Category"
        ]
        .astype(str)
        .str.strip()
        .str.upper()

    )


    category_counts = (
        category_data
        .value_counts()
        .reset_index()
    )


    category_counts.columns = [
        "Category",
        "Count"
    ]


    if not category_counts.empty:

        st.bar_chart(

            category_counts.set_index(
                "Category"
            )

        )


# =========================================================
# SEMESTER CGPA GRAPH
# =========================================================

st.markdown(
    "### Semester-wise CGPA"
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

    x for x in semester_list

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


    sem_cgpa = calculate_cgpa(
        sem_data
    )


    semester_graph_data.append(

        {
            "Semester": semester,
            "CGPA": round(
                sem_cgpa,
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
        )

    )


# =========================================================
# COURSE-WISE TABLE
# =========================================================

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


# =========================================================
# SEMESTER SUMMARY TABLE
# =========================================================

st.markdown(
    "## Semester-wise Summary"
)


semester_table_data = []


for semester in semester_list:

    sem_data = selected_student_data[

        selected_student_data[
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


    total_courses = len(
        sem_data
    )


    semester_table_data.append(

        {

            "Semester": semester,

            "Total Courses":
                int(total_courses),

            "Total Credits":
                round(
                    total_credits,
                    2
                ),

            "CGPA":
                round(
                    sem_cgpa,
                    2
                )

        }

    )


semester_summary_df = pd.DataFrame(

    semester_table_data

)


st.dataframe(

    semester_summary_df,

    use_container_width=True,

    hide_index=True

)


# =========================================================
# CATEGORY SUMMARY TABLE
# =========================================================

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


category_table_data = []


for category in category_order:

    count = category_data.eq(
        category
    ).sum()


    category_table_data.append(

        {

            "Category":
                category,

            "Count":
                int(count)

        }

    )


category_summary_df = pd.DataFrame(

    category_table_data

)


st.dataframe(

    category_summary_df,

    use_container_width=True,

    hide_index=True

)


# =========================================================
# SEMESTER CARDS
# =========================================================

show_semester_cards(
    selected_student_data
)


# =========================================================
# COMPLETE ACADEMIC RECORD
# =========================================================

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


available_complete_columns = [

    col for col in complete_columns

    if col in selected_student_data.columns

]


complete_table = selected_student_data[
    available_complete_columns
].copy()


st.dataframe(

    complete_table,

    use_container_width=True,

    hide_index=True

)


# =========================================================
# EXCEL EXPORT
# =========================================================

st.markdown(
    "## Export"
)


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


# =========================================================
# PDF EXPORT
# =========================================================

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
