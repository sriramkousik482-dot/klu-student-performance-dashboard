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
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Image
)


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
# LOAD DATA
# =========================================================

@st.cache_data
def load_data():

    df = pd.read_csv(CSV_FILE)

    # =====================================================
    # CLEAN COLUMN NAMES
    # =====================================================

    df.columns = (
        df.columns
        .astype(str)
        .str.strip()
    )

    # =====================================================
    # CLEAN STRING COLUMNS
    # =====================================================

    for col in df.columns:

        if df[col].dtype == "object":

            df[col] = (
                df[col]
                .astype("string")
                .str.strip()
            )

    # =====================================================
    # NUMERIC COLUMNS
    # =====================================================

    if "Points" in df.columns:

        df["Points"] = pd.to_numeric(
            df["Points"],
            errors="coerce"
        )

    if "Credits" in df.columns:

        df["Credits"] = pd.to_numeric(
            df["Credits"],
            errors="coerce"
        )

    # =====================================================
    # ID NUMBER
    # =====================================================

    if "ID Number" in df.columns:

        df["ID Number"] = (
            df["ID Number"]
            .astype("string")
            .str.strip()
        )

    # =====================================================
    # CREDIT POINTS
    # =====================================================

    if (
        "Points" in df.columns
        and
        "Credits" in df.columns
    ):

        df["Credit Points"] = (
            df["Points"] *
            df["Credits"]
        )

    # =====================================================
    # JOINING YEAR
    #
    # 23XXXXXXXX -> Y23
    # 24XXXXXXXX -> Y24
    # 25XXXXXXXX -> Y25
    # =====================================================

    def get_joining_year(student_id):

        if pd.isna(student_id):

            return "Unknown"

        try:

            student_id = str(
                student_id
            ).strip()

            first_two = student_id[:2]

            if first_two.isdigit():

                return "Y" + first_two

            return "Unknown"

        except Exception:

            return "Unknown"


    df["Year"] = (
        df["ID Number"]
        .apply(get_joining_year)
    )

    # =====================================================
    # NORMALIZE SEMESTER
    # =====================================================

    if "Semester" in df.columns:

        def normalize_semester(value):

            # Missing values
            if pd.isna(value):

                return ""

            value = str(
                value
            ).strip()

            value_lower = (
                value.lower()
            )

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

            else:

                return value


        df["Semester"] = (
            df["Semester"]
            .apply(normalize_semester)
        )

    else:

        df["Semester"] = ""

    # =====================================================
    # CATEGORY
    # =====================================================

    if "Category" in df.columns:

        df["Category"] = (
            df["Category"]
            .fillna("-")
            .astype(str)
            .str.strip()
            .str.upper()
        )

    else:

        df["Category"] = "-"

    # =====================================================
    # MENTOR COLUMN
    #
    # Automatically detects:
    # Mentor
    # Mentor Name
    # MentorName
    # Mentor_Name
    # Faculty Mentor
    # etc.
    # =====================================================

    mentor_column = None

    for col in df.columns:

        column_name = (
            str(col)
            .strip()
            .lower()
            .replace("_", " ")
            .replace("-", " ")
        )

        if "mentor" in column_name:

            mentor_column = col

            break

    # =====================================================
    # CREATE STANDARD MENTOR NAME
    # =====================================================

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
    # ACADEMIC SEMESTER CALCULATION
    # =====================================================

    def calculate_academic_semester(
        joining_year,
        academic_year,
        semester_type
    ):

        try:

            # ---------------------------------------------
            # MISSING VALUES
            # ---------------------------------------------

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

            # ---------------------------------------------
            # JOINING YEAR
            #
            # Y23 -> 2023
            # Y24 -> 2024
            # Y25 -> 2025
            # ---------------------------------------------

            if joining_year.startswith("Y"):

                join_year = (
                    int(joining_year[1:3])
                    + 2000
                )

            else:

                join_year = int(
                    joining_year
                )

            # ---------------------------------------------
            # ACADEMIC YEAR
            #
            # 2023-2024 -> 2023
            # 2024-2025 -> 2024
            # ---------------------------------------------

            academic_start_year = int(
                academic_year
                .split("-")[0]
            )

            # ---------------------------------------------
            # YEAR OF STUDY
            # ---------------------------------------------

            year_of_study = (
                academic_start_year
                - join_year
                + 1
            )

            # ---------------------------------------------
            # SUMMER TERM
            # ---------------------------------------------

            if "summer" in semester_type:

                return None

            # ---------------------------------------------
            # ODD SEMESTER
            # ---------------------------------------------

            if "odd" in semester_type:

                semester_number = "1"

            # ---------------------------------------------
            # EVEN SEMESTER
            # ---------------------------------------------

            elif "even" in semester_type:

                semester_number = "2"

            else:

                return None

            if year_of_study < 1:

                return None

            # ---------------------------------------------
            # RESULT
            # ---------------------------------------------

            return (
                f"{year_of_study}-"
                f"{semester_number}"
            )

        except Exception:

            return None

    # =====================================================
    # CREATE ACADEMIC SEMESTER COLUMN
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
# LOAD CSV
# =========================================================

df = load_data()


# =========================================================
# CALCULATE CGPA
# =========================================================

def calculate_cgpa(data):

    if data.empty:

        return 0.0

    valid_data = data.dropna(
        subset=[
            "Points",
            "Credits"
        ]
    )

    if valid_data.empty:

        return 0.0

    total_credit_points = (
        valid_data["Points"]
        *
        valid_data["Credits"]
    ).sum()

    total_credits = (
        valid_data["Credits"]
    ).sum()

    if total_credits == 0:

        return 0.0

    return (
        total_credit_points
        /
        total_credits
    )


# =========================================================
# GRADE RESULT
# =========================================================

def get_result(grade):

    if pd.isna(grade):

        return "PASS"

    grade = str(
        grade
    ).strip().upper()

    if grade in [
        "F",
        "FAIL"
    ]:

        return "FAIL"

    return "PASS"


# =========================================================
# CLEAN CATEGORY
# =========================================================

def clean_category(category):

    if pd.isna(category):

        return "-"

    category = str(
        category
    ).strip().upper()

    if category == "":

        return "-"

    return category


# =========================================================
# SEMESTER SORTING
# =========================================================

def semester_sort_key(value):

    try:

        parts = str(
            value
        ).split("-")

        return (
            int(parts[0]),
            int(parts[1])
        )

    except Exception:

        return (
            999,
            999
        )


# =========================================================
# COURSE CARD
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

    category = clean_category(
        row["Category"]
    )

    points = row["Points"]

    credits = row["Credits"]

    st.markdown(
        f"""
        <div style="
            border:1px solid #ddd;
            border-radius:10px;
            padding:15px;
            margin-bottom:10px;
            background-color:#fafafa;
        ">

        <b>{course_code}</b>

        <br>

        {course_name}

        <br><br>

        <b>Grade:</b> {grade}

        &nbsp;&nbsp;

        <b>Category:</b> {category}

        &nbsp;&nbsp;

        <b>Points:</b> {points}

        &nbsp;&nbsp;

        <b>Credits:</b> {credits}

        </div>
        """,
        unsafe_allow_html=True
    )


# =========================================================
# SEMESTER CARDS
# =========================================================

def show_semester_cards(student_data):

    if student_data.empty:

        st.info(
            "No course records found."
        )

        return

    semesters = (
        student_data[
            "Academic Semester"
        ]
        .dropna()
        .unique()
        .tolist()
    )

    semesters = sorted(
        semesters,
        key=semester_sort_key
    )

    for semester in semesters:

        semester_data = (
            student_data[
                student_data[
                    "Academic Semester"
                ] == semester
            ]
            .copy()
        )

        st.markdown(
            f"### 📘 {semester}"
        )

        for _, row in (
            semester_data.iterrows()
        ):

            show_course_card(row)

        st.markdown("---")


# =========================================================
# HEADER
# =========================================================

if LOGO_PATH.exists():

    col1, col2, col3 = st.columns(
        [1, 5, 1]
    )

    with col1:

        st.image(
            str(LOGO_PATH),
            width=100
        )

    with col2:

        st.markdown(
            """
            <h1 style="
                text-align:center;
                margin-bottom:0px;
            ">
                KL UNIVERSITY
            </h1>

            <h3 style="
                text-align:center;
                margin-top:5px;
            ">
                Department of CSE-4
            </h3>

            <p style="
                text-align:center;
                font-size:18px;
            ">
                Academic Performance Dashboard
            </p>
            """,
            unsafe_allow_html=True
        )

else:

    st.title(
        "KL UNIVERSITY"
    )

    st.subheader(
        "Department of CSE-4"
    )

    st.write(
        "Academic Performance Dashboard"
    )


st.markdown("---")


# =========================================================
# SIDEBAR
# =========================================================

st.sidebar.header(
    "🔎 Filters"
)


# =========================================================
# JOINING YEAR FILTER
# =========================================================

joining_years = sorted(
    df["Year"]
    .dropna()
    .unique()
    .tolist()
)

selected_year = (
    st.sidebar.selectbox(
        "Joining Year",
        ["All"] + joining_years
    )
)


# =========================================================
# COURSE CODE FILTER
# =========================================================

course_codes = sorted(
    df["Course Code"]
    .dropna()
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
        ==
        selected_year
    ]


if selected_course_code != "All":

    filtered_df = filtered_df[
        filtered_df["Course Code"]
        ==
        selected_course_code
    ]


if selected_course_name != "All":

    filtered_df = filtered_df[
        filtered_df["Course Name"]
        ==
        selected_course_name
    ]


# =========================================================
# STUDENT SEARCH
# =========================================================

st.markdown(
    "## 🔍 Search Student"
)

search_col1, search_col2 = (
    st.columns(2)
)

with search_col1:

    student_search = st.text_input(
        "Search Student ID / Name",
        placeholder=(
            "Enter student ID or student name"
        )
    )

with search_col2:

    semester_search = st.text_input(
        "Search Semester",
        placeholder=(
            "Example: 1-1, 1-2, 2-1"
        )
    )


# =========================================================
# APPLY STUDENT SEARCH
# =========================================================

student_filtered_df = (
    filtered_df.copy()
)


if student_search:

    search_value = (
        student_search
        .strip()
        .lower()
    )

    id_match = (
        student_filtered_df[
            "ID Number"
        ]
        .astype(str)
        .str.lower()
        .str.contains(
            search_value,
            na=False
        )
    )

    name_match = (
        student_filtered_df[
            "Name"
        ]
        .astype(str)
        .str.lower()
        .str.contains(
            search_value,
            na=False
        )
    )

    student_filtered_df = (
        student_filtered_df[
            id_match | name_match
        ]
    )


# =========================================================
# SEMESTER SEARCH
# =========================================================

if semester_search:

    search_semester = (
        semester_search
        .strip()
        .lower()
    )

    student_filtered_df = (
        student_filtered_df[
            student_filtered_df[
                "Academic Semester"
            ]
            .astype(str)
            .str.lower()
            .str.contains(
                search_semester,
                na=False
            )
        ]
    )


# =========================================================
# DASHBOARD SUMMARY
# =========================================================

st.markdown("---")

st.markdown(
    "## 📊 Dashboard Summary"
)

kpi1, kpi2, kpi3, kpi4 = (
    st.columns(4)
)


average_cgpa = calculate_cgpa(
    student_filtered_df
)


dashboard_pass = (
    student_filtered_df[
        "Grade"
    ]
    .apply(get_result)
    .eq("PASS")
    .sum()
)


dashboard_fail = (
    student_filtered_df[
        "Grade"
    ]
    .apply(get_result)
    .eq("FAIL")
    .sum()
)


dashboard_dt = (
    student_filtered_df[
        "Category"
    ]
    .astype(str)
    .str.strip()
    .str.upper()
    .eq("DT")
    .sum()
)


with kpi1:

    st.metric(
        "Average CGPA",
        f"{average_cgpa:.2f}"
    )


with kpi2:

    st.metric(
        "Pass",
        int(dashboard_pass)
    )


with kpi3:

    st.metric(
        "Fail",
        int(dashboard_fail)
    )


with kpi4:

    st.metric(
        "Detained",
        int(dashboard_dt)
    )


# =========================================================
# STUDENT SELECTION
# =========================================================

st.markdown("---")


unique_students = (
    student_filtered_df[
        [
            "ID Number",
            "Name"
        ]
    ]
    .drop_duplicates()
)


if unique_students.empty:

    st.warning(
        "No students found."
    )

else:

    student_options = []

    for _, row in (
        unique_students.iterrows()
    ):

        student_options.append(
            f'{row["ID Number"]} - '
            f'{row["Name"]}'
        )

    selected_student = (
        st.selectbox(
            "Select Student",
            student_options
        )
    )

    selected_student_id = (
        selected_student
        .split(" - ")[0]
    )

    selected_student_data = (
        student_filtered_df[
            student_filtered_df[
                "ID Number"
            ]
            .astype(str)
            ==
            str(selected_student_id)
        ]
        .copy()
    )


    # =====================================================
    # STUDENT NAME
    # =====================================================

    student_name = str(
        selected_student_data[
            "Name"
        ].iloc[0]
    ).strip()


    # =====================================================
    # MENTOR
    # =====================================================

    mentor_values = (
        selected_student_data[
            "Mentor Name"
        ]
        .astype(str)
        .str.strip()
    )

    mentor_values = (
        mentor_values[
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
    )

    if not mentor_values.empty:

        mentor_name = (
            mentor_values.iloc[0]
        )

    else:

        mentor_name = (
            "Not Available"
        )


    # =====================================================
    # STUDENT DETAILS
    # =====================================================

    st.markdown(
        "## 👨‍🎓 Student Details"
    )

    detail_col1, detail_col2, detail_col3 = (
        st.columns(3)
    )

    with detail_col1:

        st.info(
            f"**Student ID**\n\n"
            f"{selected_student_id}"
        )

    with detail_col2:

        st.info(
            f"**Student Name**\n\n"
            f"{student_name}"
        )

    with detail_col3:

        st.info(
            f"**Mentor**\n\n"
            f"{mentor_name}"
        )


    # =====================================================
    # STUDENT SUMMARY
    # =====================================================

    student_cgpa = calculate_cgpa(
        selected_student_data
    )


    student_pass = (
        selected_student_data[
            "Grade"
        ]
        .apply(get_result)
        .eq("PASS")
        .sum()
    )


    student_fail = (
        selected_student_data[
            "Grade"
        ]
        .apply(get_result)
        .eq("FAIL")
        .sum()
    )


    student_dt = (
        selected_student_data[
            "Category"
        ]
        .astype(str)
        .str.strip()
        .str.upper()
        .eq("DT")
        .sum()
    )


    student_backlogs = (
        selected_student_data[
            "Category"
        ]
        .astype(str)
        .str.strip()
        .str.upper()
        .isin(
            [
                "F",
                "DT"
            ]
        )
        .sum()
    )


    st.markdown(
        "## 📈 Academic Summary"
    )


    s1, s2, s3, s4 = (
        st.columns(4)
    )


    with s1:

        st.metric(
            "Overall CGPA",
            f"{student_cgpa:.2f}"
        )


    with s2:

        st.metric(
            "Pass",
            int(student_pass)
        )


    with s3:

        st.metric(
            "Fail",
            int(student_fail)
        )


    with s4:

        st.metric(
            "Backlogs",
            int(student_backlogs)
        )


    # =====================================================
    # VISUAL ANALYTICS
    # =====================================================

    st.markdown("---")

    st.markdown(
        "## 📊 Visual Analytics"
    )


    graph_col1, graph_col2 = (
        st.columns(2)
    )


    # =====================================================
    # GRADE DISTRIBUTION
    # =====================================================

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


    with graph_col1:

        st.markdown(
            "### Grade Distribution"
        )

        st.bar_chart(
            grade_counts.set_index(
                "Grade"
            )
        )


    # =====================================================
    # CATEGORY DISTRIBUTION
    # =====================================================

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


    with graph_col2:

        st.markdown(
            "### Category Distribution"
        )

        st.bar_chart(
            category_counts.set_index(
                "Category"
            )
        )


    # =====================================================
    # SEMESTER-WISE CGPA DATA
    # =====================================================

    semester_graph_data = []


    semester_list = (
        selected_student_data[
            "Academic Semester"
        ]
        .dropna()
        .unique()
        .tolist()
    )


    semester_list = sorted(
        semester_list,
        key=semester_sort_key
    )


    for semester in semester_list:

        sem_data = (
            selected_student_data[
                selected_student_data[
                    "Academic Semester"
                ] == semester
            ]
            .copy()
        )


        sem_cgpa = calculate_cgpa(
            sem_data
        )


        semester_graph_data.append({

            "Semester": semester,

            "CGPA": round(
                sem_cgpa,
                2
            )

        })


    if semester_graph_data:

        semester_graph_df = pd.DataFrame(
            semester_graph_data
        )


        st.markdown(
            "### Semester-wise CGPA"
        )


        st.line_chart(
            semester_graph_df.set_index(
                "Semester"
            )
        )


    # =====================================================
    # COURSE-WISE TABLE
    # =====================================================

    st.markdown("---")

    st.markdown(
        "## 📚 Course-wise Academic Data"
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
        ]
        .copy()
    )


    course_table = (
        course_table
        .sort_values(
            by="Academic Semester",
            key=lambda x:
            x.map(
                semester_sort_key
            )
        )
    )


    st.dataframe(
        course_table,
        use_container_width=True,
        hide_index=True
    )


    # =====================================================
    # SEMESTER-WISE TABLE
    # =====================================================

    st.markdown(
        "## 📅 Semester-wise Summary"
    )


    semester_table_data = []


    for semester in semester_list:

        sem_data = (
            selected_student_data[
                selected_student_data[
                    "Academic Semester"
                ] == semester
            ]
            .copy()
        )


        sem_cgpa = calculate_cgpa(
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


        total_courses = len(
            sem_data
        )


        semester_table_data.append({

            "Semester": semester,

            "Total Courses": int(
                total_courses
            ),

            "Total Credits": round(
                total_credits,
                2
            ),

            "CGPA": round(
                sem_cgpa,
                2
            )

        })


    semester_summary_df = pd.DataFrame(
        semester_table_data
    )


    st.dataframe(
        semester_summary_df,
        use_container_width=True,
        hide_index=True
    )


    # =====================================================
    # CATEGORY-WISE TABLE
    # =====================================================

    st.markdown(
        "## 📋 Category-wise Summary"
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

        count = (
            category_data
            .eq(category)
            .sum()
        )


        category_table_data.append({

            "Category": category,

            "Count": int(count)

        })


    category_summary_df = pd.DataFrame(
        category_table_data
    )


    st.dataframe(
        category_summary_df,
        use_container_width=True,
        hide_index=True
    )


    # =====================================================
    # ACADEMIC PERFORMANCE - SEMESTER CARDS
    # =====================================================

    st.markdown("---")

    st.markdown(
        "## 📖 Academic Performance"
    )


    show_semester_cards(
        selected_student_data
    )


    # =====================================================
    # COMPLETE COURSE RECORD
    # =====================================================

    st.markdown(
        "## 📋 Complete Academic Record"
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


    complete_data = (
        selected_student_data[
            available_columns
        ]
        .copy()
    )


    st.dataframe(
        complete_data,
        use_container_width=True,
        hide_index=True
    )


    # =====================================================
    # DOWNLOAD SECTION
    # =====================================================

    st.markdown("---")

    st.markdown(
        "## 📥 Download Reports"
    )


    # =====================================================
    # EXCEL DOWNLOAD
    # =====================================================

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


    st.download_button(
        label="📊 Download Excel",
        data=excel_buffer.getvalue(),
        file_name=(
            f"{selected_student_id}"
            "_performance.xlsx"
        ),
        mime=(
            "application/vnd.openxmlformats-officedocument."
            "spreadsheetml.sheet"
        )
    )


    # =====================================================
    # CREATE PDF
    # =====================================================

    def create_student_pdf(
        student_data,
        student_id
    ):

        buffer = BytesIO()


        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=30,
            leftMargin=30,
            topMargin=30,
            bottomMargin=30
        )


        styles = getSampleStyleSheet()


        title_style = ParagraphStyle(
            "TitleStyle",
            parent=styles["Title"],
            fontSize=18,
            alignment=TA_CENTER,
            spaceAfter=8
        )


        subtitle_style = ParagraphStyle(
            "SubtitleStyle",
            parent=styles["Normal"],
            fontSize=10,
            alignment=TA_CENTER,
            spaceAfter=10
        )


        heading_style = ParagraphStyle(
            "HeadingStyle",
            parent=styles["Heading2"],
            fontSize=13,
            spaceBefore=10,
            spaceAfter=8
        )


        normal_style = ParagraphStyle(
            "NormalStyle",
            parent=styles["Normal"],
            fontSize=8
        )


        story = []


        # =================================================
        # LOGO
        # =================================================

        if LOGO_PATH.exists():

            try:

                logo = Image(
                    str(LOGO_PATH),
                    width=0.8 * inch,
                    height=0.8 * inch
                )

                logo.hAlign = "CENTER"

                story.append(
                    logo
                )

                story.append(
                    Spacer(1, 5)
                )

            except Exception:

                pass


        # =================================================
        # PDF HEADER
        # =================================================

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
            Paragraph(
                "Student Academic Performance Report",
                subtitle_style
            )
        )


        story.append(
            Spacer(1, 8)
        )


        # =================================================
        # STUDENT DETAILS
        # =================================================

        story.append(
            Paragraph(
                "Student Details",
                heading_style
            )
        )


        pdf_student_name = str(
            student_data[
                "Name"
            ].iloc[0]
        ).strip()


        # =================================================
        # PDF MENTOR
        # =================================================

        pdf_mentor_values = (
            student_data[
                "Mentor Name"
            ]
            .astype(str)
            .str.strip()
        )


        pdf_mentor_values = (
            pdf_mentor_values[
                ~pdf_mentor_values.str.lower().isin(
                    [
                        "",
                        "nan",
                        "none",
                        "<na>",
                        "not available"
                    ]
                )
            ]
        )


        if not pdf_mentor_values.empty:

            pdf_mentor_name = (
                pdf_mentor_values.iloc[0]
            )

        else:

            pdf_mentor_name = (
                "Not Available"
            )


        pdf_cgpa = calculate_cgpa(
            student_data
        )


        # =================================================
        # STUDENT INFORMATION TABLE
        # =================================================

        student_info = [

            [
                "Student ID",
                str(student_id)
            ],

            [
                "Student Name",
                pdf_student_name
            ],

            [
                "Mentor Name",
                pdf_mentor_name
            ],

            [
                "Overall CGPA",
                f"{pdf_cgpa:.2f} / 10"
            ]

        ]


        student_table = Table(
            student_info,
            colWidths=[
                1.6 * inch,
                4.8 * inch
            ]
        )


        student_table.setStyle(
            TableStyle([

                (
                    "BACKGROUND",
                    (0, 0),
                    (0, -1),
                    colors.lightgrey
                ),

                (
                    "FONTNAME",
                    (0, 0),
                    (0, -1),
                    "Helvetica-Bold"
                ),

                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.grey
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
                ),

                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    6
                ),

                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    6
                )

            ])
        )


        story.append(
            student_table
        )


        story.append(
            Spacer(1, 12)
        )


        # =================================================
        # CATEGORY SUMMARY
        # =================================================

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


        category_rows = [

            [
                "Category",
                "Count"
            ]

        ]


        for category in category_order:

            count = (
                category_data
                .eq(category)
                .sum()
            )


            category_rows.append(

                [
                    category,
                    str(int(count))
                ]

            )


        category_table = Table(
            category_rows,
            colWidths=[
                2.5 * inch,
                2 * inch
            ]
        )


        category_table.setStyle(
            TableStyle([

                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.lightgrey
                ),

                (
                    "FONTNAME",
                    (0, 0),
                    (-1, 0),
                    "Helvetica-Bold"
                ),

                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.grey
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


        story.append(
            Spacer(1, 12)
        )


        # =================================================
        # ACADEMIC PERFORMANCE
        # =================================================

        story.append(
            Paragraph(
                "Academic Performance",
                heading_style
            )
        )


        academic_data = (
            student_data[
                student_data[
                    "Academic Semester"
                ].notna()
            ]
            .copy()
        )


        academic_data = (
            academic_data
            .sort_values(
                by="Academic Semester",
                key=lambda x:
                x.map(
                    semester_sort_key
                )
            )
        )


        academic_rows = [

            [
                "Sem",
                "Course Code",
                "Course Name",
                "Grade",
                "Points",
                "Credits",
                "Category"
            ]

        ]


        for _, row in (
            academic_data.iterrows()
        ):

            academic_rows.append(

                [

                    str(
                        row[
                            "Academic Semester"
                        ]
                    ),

                    str(
                        row[
                            "Course Code"
                        ]
                    ),

                    str(
                        row[
                            "Course Name"
                        ]
                    ),

                    str(
                        row[
                            "Grade"
                        ]
                    ),

                    str(
                        row[
                            "Points"
                        ]
                    ),

                    str(
                        row[
                            "Credits"
                        ]
                    ),

                    clean_category(
                        row[
                            "Category"
                        ]
                    )

                ]

            )


        academic_table = Table(
            academic_rows,
            repeatRows=1,
            colWidths=[
                0.55 * inch,
                0.85 * inch,
                2.15 * inch,
                0.55 * inch,
                0.55 * inch,
                0.55 * inch,
                0.75 * inch
            ]
        )


        academic_table.setStyle(
            TableStyle([

                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.lightgrey
                ),

                (
                    "FONTNAME",
                    (0, 0),
                    (-1, 0),
                    "Helvetica-Bold"
                ),

                (
                    "FONTSIZE",
                    (0, 0),
                    (-1, -1),
                    7
                ),

                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.4,
                    colors.grey
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
            academic_table
        )


        story.append(
            Spacer(1, 12)
        )


        # =================================================
        # SEMESTER-WISE PERFORMANCE
        # =================================================

        story.append(
            Paragraph(
                "Semester-wise Academic Performance",
                heading_style
            )
        )


        semester_list_pdf = (
            student_data[
                "Academic Semester"
            ]
            .dropna()
            .unique()
            .tolist()
        )


        semester_list_pdf = sorted(
            semester_list_pdf,
            key=semester_sort_key
        )


        semester_rows = [

            [
                "Semester",
                "Courses",
                "Credits",
                "CGPA"
            ]

        ]


        for semester in semester_list_pdf:

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
                    sem_data[
                        "Credits"
                    ],
                    errors="coerce"
                )
                .fillna(0)
                .sum()
            )


            course_count = len(
                sem_data
            )


            semester_rows.append(

                [

                    str(semester),

                    str(course_count),

                    str(
                        round(
                            total_credits,
                            2
                        )
                    ),

                    f"{sem_cgpa:.2f}"

                ]

            )


        semester_table = Table(
            semester_rows,
            repeatRows=1,
            colWidths=[
                1.2 * inch,
                1.3 * inch,
                1.3 * inch,
                1.3 * inch
            ]
        )


        semester_table.setStyle(
            TableStyle([

                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.lightgrey
                ),

                (
                    "FONTNAME",
                    (0, 0),
                    (-1, 0),
                    "Helvetica-Bold"
                ),

                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.grey
                ),

                (
                    "ALIGN",
                    (1, 1),
                    (-1, -1),
                    "CENTER"
                )

            ])
        )


        story.append(
            semester_table
        )


        story.append(
            Spacer(1, 12)
        )


        # =================================================
        # BACKLOG SUBJECTS
        # =================================================

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
                [
                    "F",
                    "DT"
                ]
            )
        ].copy()


        if backlog_data.empty:

            story.append(
                Paragraph(
                    "No backlog subjects.",
                    normal_style
                )
            )


        else:

            backlog_data = (
                backlog_data[
                    backlog_data[
                        "Academic Semester"
                    ].notna()
                ]
                .copy()
            )


            backlog_data = (
                backlog_data
                .sort_values(
                    by="Academic Semester",
                    key=lambda x:
                    x.map(
                        semester_sort_key
                    )
                )
            )


            backlog_rows = [

                [
                    "Sem",
                    "Course Code",
                    "Course Name",
                    "Grade",
                    "Category"
                ]

            ]


            for _, row in (
                backlog_data.iterrows()
            ):

                backlog_rows.append(

                    [

                        str(
                            row[
                                "Academic Semester"
                            ]
                        ),

                        str(
                            row[
                                "Course Code"
                            ]
                        ),

                        str(
                            row[
                                "Course Name"
                            ]
                        ),

                        str(
                            row[
                                "Grade"
                            ]
                        ),

                        clean_category(
                            row[
                                "Category"
                            ]
                        )

                    ]

                )


            backlog_table = Table(
                backlog_rows,
                repeatRows=1,
                colWidths=[
                    0.65 * inch,
                    1.0 * inch,
                    2.5 * inch,
                    0.7 * inch,
                    0.8 * inch
                ]
            )


            backlog_table.setStyle(
                TableStyle([

                    (
                        "BACKGROUND",
                        (0, 0),
                        (-1, 0),
                        colors.lightgrey
                    ),

                    (
                        "FONTNAME",
                        (0, 0),
                        (-1, 0),
                        "Helvetica-Bold"
                    ),

                    (
                        "FONTSIZE",
                        (0, 0),
                        (-1, -1),
                        8
                    ),

                    (
                        "GRID",
                        (0, 0),
                        (-1, -1),
                        0.5,
                        colors.grey
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


        # =================================================
        # BUILD PDF
        # =================================================

        doc.build(
            story
        )


        buffer.seek(0)

        return buffer


    # =====================================================
    # PDF DOWNLOAD
    # =====================================================

    pdf_buffer = create_student_pdf(
        selected_student_data,
        selected_student_id
    )


    st.download_button(
        label="📄 Download Student PDF",
        data=pdf_buffer.getvalue(),
        file_name=(
            f"{selected_student_id}"
            "_academic_performance.pdf"
        ),
        mime="application/pdf"
    )
