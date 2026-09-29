import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

from io import BytesIO
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
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
# PATHS
# =========================================================

BASE_DIR = Path(__file__).parent

CSV_FILE = BASE_DIR / "student.csv"
LOGO_FILE = BASE_DIR / "klu_logo.png.jpg"


# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="KLU Academic Performance Dashboard",
    page_icon="🎓",
    layout="wide"
)


# =========================================================
# LOAD DATA
# =========================================================

@st.cache_data
def load_data():

    df = pd.read_csv(CSV_FILE)

    # Clean column names
    df.columns = (
        df.columns
        .astype(str)
        .str.strip()
    )

    # Clean string columns
    for col in df.columns:

        if df[col].dtype == "object":

            df[col] = (
                df[col]
                .astype(str)
                .str.strip()
            )

    # Numeric columns
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

    # Credit Points
    if "Points" in df.columns and "Credits" in df.columns:

        df["Credit Points"] = (
            df["Points"] *
            df["Credits"]
        )

    # =====================================================
    # YEAR FROM ID
    # =====================================================

    def get_joining_year(student_id):

        try:

            value = str(student_id).strip()

            first_two = value[:2]

            if first_two.isdigit():

                return "Y" + first_two

            return "Unknown"

        except:

            return "Unknown"

    df["Year"] = df["ID Number"].apply(
        get_joining_year
    )


    # =====================================================
    # NORMALIZE SEMESTER
    # =====================================================

    if "Semester" in df.columns:

        df["Semester"] = (
            df["Semester"]
            .astype(str)
            .str.strip()
            .str.lower()
            .replace({
                "odd": "Odd Sem",
                "odd sem": "Odd Sem",
                "even": "Even Sem",
                "even sem": "Even Sem"
            })
        )


    # =====================================================
    # MENTOR COLUMN
    # =====================================================

    mentor_column = None

    possible_mentor_columns = [
        "Mentor Name",
        "Mentor",
        "MentorName",
        "MENTOR NAME",
        "MENTOR",
        "mentor name"
    ]

    for col in possible_mentor_columns:

        if col in df.columns:

            mentor_column = col
            break

    if mentor_column is None:

        df["Mentor Name"] = "Not Available"

    else:

        df["Mentor Name"] = (
            df[mentor_column]
            .astype(str)
            .str.strip()
        )


    # =====================================================
    # ACADEMIC SEMESTER
    # =====================================================

    def calculate_academic_semester(
        joining_year,
        academic_year,
        semester_type
    ):

        try:

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
            # Y23 -> 2023
            # Y24 -> 2024
            # Y25 -> 2025
            # ---------------------------------------------

            if joining_year.startswith("Y"):

                join_year = int(
                    joining_year[1:3]
                ) + 2000

            else:

                join_year = int(
                    joining_year
                )


            # ---------------------------------------------
            # Get academic year starting year
            #
            # 2023-24 -> 2023
            # 2024-25 -> 2024
            # ---------------------------------------------

            if "-" in academic_year:

                academic_start_year = int(
                    academic_year.split("-")[0]
                )

            else:

                academic_start_year = int(
                    academic_year
                )


            # ---------------------------------------------
            # Calculate year of study
            # ---------------------------------------------

            year_of_study = (
                academic_start_year
                - join_year
                + 1
            )


            # ---------------------------------------------
            # Odd -> 1
            # Even -> 2
            # ---------------------------------------------

            if semester_type.startswith("odd"):

                semester_number = "1"

            elif semester_type.startswith("even"):

                semester_number = "2"

            else:

                return "Unknown"


            if year_of_study < 1:

                return "Unknown"


            return (
                f"{year_of_study}-{semester_number}"
            )


        except:

            return "Unknown"


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


df = load_data()


# =========================================================
# CGPA FUNCTION
# =========================================================

def calculate_cgpa(data):

    if data.empty:

        return 0.0

    valid_data = data.dropna(
        subset=["Points", "Credits"]
    )

    if valid_data.empty:

        return 0.0

    total_credit_points = (
        valid_data["Points"] *
        valid_data["Credits"]
    ).sum()

    total_credits = (
        valid_data["Credits"]
    ).sum()

    if total_credits == 0:

        return 0.0

    return (
        total_credit_points /
        total_credits
    )


# =========================================================
# RESULT FUNCTION
# =========================================================

def get_result(grade):

    grade = str(grade).strip().upper()

    if grade in ["F", "FAIL"]:

        return "FAIL"

    return "PASS"


# =========================================================
# CATEGORY FUNCTION
# =========================================================

def get_category(category):

    if pd.isna(category):

        return "-"

    category = str(category).strip().upper()

    if category == "":

        return "-"

    return category


# =========================================================
# SEMESTER SORT
# =========================================================

def academic_semester_sort_key(value):

    try:

        year_part, semester_part = (
            str(value).split("-")
        )

        return (
            int(year_part),
            int(semester_part)
        )

    except:

        return (
            999,
            999
        )


# =========================================================
# COURSE CARD
# =========================================================

def show_course_card(row):

    grade = str(
        row["Grade"]
    ).strip()

    category = get_category(
        row["Category"]
    )

    academic_semester = str(
        row["Academic Semester"]
    )

    st.markdown(
        f"""
        <div style="
            border:1px solid #ddd;
            border-radius:10px;
            padding:15px;
            margin-bottom:10px;
            background-color:#fafafa;
        ">

        <b>{row["Course Code"]}</b>
        <br>

        {row["Course Name"]}

        <br><br>

        <b>Semester:</b> {academic_semester}

        &nbsp;&nbsp;

        <b>Grade:</b> {grade}

        &nbsp;&nbsp;

        <b>Category:</b> {category}

        <br>

        <b>Credits:</b> {row["Credits"]}

        &nbsp;&nbsp;

        <b>Points:</b> {row["Points"]}

        </div>
        """,
        unsafe_allow_html=True
    )


# =========================================================
# SEMESTER CARDS
# =========================================================

def show_semester_cards(student_data):

    if student_data.empty:

        st.info("No course records found.")

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
        key=academic_semester_sort_key
    )


    # =====================================================
    # DISPLAY EACH SEMESTER
    # =====================================================

    for semester in semesters:

        semester_data = student_data[
            student_data["Academic Semester"]
            == semester
        ].copy()


        st.markdown(
            f"### 📘 Semester {semester}"
        )


        for _, row in semester_data.iterrows():

            show_course_card(row)


        st.markdown("---")


# =========================================================
# STUDENT PERFORMANCE
# =========================================================

def show_student_performance(
    student_data,
    student_id
):

    if student_data.empty:

        return


    student_name = str(
        student_data["Name"].iloc[0]
    )

    mentor_name = str(
        student_data["Mentor Name"].iloc[0]
    )


    overall_cgpa = calculate_cgpa(
        student_data
    )


    # =====================================================
    # STUDENT INFORMATION
    # =====================================================

    st.markdown(
        "## 👨‍🎓 Student Details"
    )


    col1, col2, col3 = st.columns(3)


    with col1:

        st.metric(
            "Student ID",
            student_id
        )


    with col2:

        st.metric(
            "Student Name",
            student_name
        )


    with col3:

        st.metric(
            "Mentor",
            mentor_name
        )


    st.markdown("### 📚 Overall Academic Performance")


    col1, col2, col3, col4 = st.columns(4)


    # =====================================================
    # PASS
    # =====================================================

    pass_count = (
        student_data["Grade"]
        .apply(get_result)
        .eq("PASS")
        .sum()
    )


    # =====================================================
    # FAIL
    # =====================================================

    fail_count = (
        student_data["Grade"]
        .apply(get_result)
        .eq("FAIL")
        .sum()
    )


    # =====================================================
    # DETAINED
    # =====================================================

    dt_count = (
        student_data["Category"]
        .astype(str)
        .str.upper()
        .eq("DT")
        .sum()
    )


    # =====================================================
    # BACKLOGS
    # =====================================================

    backlog_count = (
        student_data["Category"]
        .astype(str)
        .str.upper()
        .isin(["F", "DT"])
        .sum()
    )


    with col1:

        st.metric(
            "Overall CGPA",
            f"{overall_cgpa:.2f}"
        )


    with col2:

        st.metric(
            "Pass",
            int(pass_count)
        )


    with col3:

        st.metric(
            "Fail",
            int(fail_count)
        )


    with col4:

        st.metric(
            "Backlogs",
            int(backlog_count)
        )


    st.markdown("---")


    # =====================================================
    # COURSE SUMMARY
    # =====================================================

    st.markdown(
        "## 📖 Course Performance"
    )


    show_semester_cards(
        student_data
    )


# =========================================================
# HEADER
# =========================================================

if LOGO_FILE.exists():

    col1, col2, col3 = st.columns(
        [1, 5, 1]
    )

    with col1:

        st.image(
            str(LOGO_FILE),
            width=100
        )

    with col2:

        st.markdown(
            """
            <h1 style="text-align:center;">
            KL UNIVERSITY
            </h1>

            <h3 style="text-align:center;">
            Department of CSE-4
            </h3>

            <p style="text-align:center;">
            Academic Performance Dashboard
            </p>
            """,
            unsafe_allow_html=True
        )

else:

    st.title(
        "KL UNIVERSITY | Department of CSE-4"
    )

    st.subheader(
        "Academic Performance Dashboard"
    )


st.markdown("---")


# =========================================================
# SIDEBAR FILTERS
# =========================================================

st.sidebar.header(
    "🔎 Filters"
)


# =========================================================
# JOINING YEAR
# =========================================================

joining_years = sorted(
    df["Year"]
    .dropna()
    .unique()
    .tolist()
)


selected_year = st.sidebar.selectbox(
    "Joining Year",
    ["All"] + joining_years
)


# =========================================================
# COURSE CODE
# =========================================================

course_codes = sorted(
    df["Course Code"]
    .dropna()
    .unique()
    .tolist()
)


selected_course_code = st.sidebar.selectbox(
    "Course Code",
    ["All"] + course_codes
)


# =========================================================
# COURSE NAME
# =========================================================

course_names = sorted(
    df["Course Name"]
    .dropna()
    .unique()
    .tolist()
)


selected_course_name = st.sidebar.selectbox(
    "Course Name",
    ["All"] + course_names
)


# =========================================================
# APPLY SIDEBAR FILTERS
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
# MAIN SEARCH
# =========================================================

st.markdown(
    "## 🔍 Search Student"
)


search_col1, search_col2 = st.columns(2)


with search_col1:

    student_search = st.text_input(
        "Search Student ID / Name",
        placeholder="Enter student ID or student name"
    )


with search_col2:

    semester_search = st.text_input(
        "Search Semester",
        placeholder="Example: 1-1, 1-2, 2-1"
    )


# =========================================================
# STUDENT SEARCH
# =========================================================

student_filtered_df = filtered_df.copy()


if student_search:

    search_value = (
        student_search
        .strip()
        .lower()
    )

    student_filtered_df = (
        student_filtered_df[
            student_filtered_df[
                "ID Number"
            ]
            .astype(str)
            .str.lower()
            .str.contains(
                search_value,
                na=False
            )
            |
            student_filtered_df[
                "Name"
            ]
            .astype(str)
            .str.lower()
            .str.contains(
                search_value,
                na=False
            )
        ]
    )


# =========================================================
# SEMESTER SEARCH
# =========================================================

if semester_search:

    semester_search = (
        semester_search
        .strip()
    )

    student_filtered_df = (
        student_filtered_df[
            student_filtered_df[
                "Academic Semester"
            ]
            .astype(str)
            .str.lower()
            .str.contains(
                semester_search.lower(),
                na=False
            )
        ]
    )


# =========================================================
# KPIs
# =========================================================

st.markdown("---")

st.markdown(
    "## 📊 Dashboard Summary"
)


kpi1, kpi2, kpi3, kpi4 = st.columns(4)


overall_dashboard_cgpa = calculate_cgpa(
    student_filtered_df
)


dashboard_pass = (
    student_filtered_df["Grade"]
    .apply(get_result)
    .eq("PASS")
    .sum()
)


dashboard_fail = (
    student_filtered_df["Grade"]
    .apply(get_result)
    .eq("FAIL")
    .sum()
)


dashboard_dt = (
    student_filtered_df["Category"]
    .astype(str)
    .str.upper()
    .eq("DT")
    .sum()
)


with kpi1:

    st.metric(
        "Average CGPA",
        f"{overall_dashboard_cgpa:.2f}"
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
        ["ID Number", "Name"]
    ]
    .drop_duplicates()
)


if len(unique_students) == 0:

    st.warning(
        "No students found."
    )

else:

    student_options = []

    for _, row in unique_students.iterrows():

        student_options.append(
            f'{row["ID Number"]} - {row["Name"]}'
        )


    selected_student = st.selectbox(
        "Select Student",
        student_options
    )


    selected_student_id = (
        selected_student.split(" - ")[0]
    )


    selected_student_data = (
        student_filtered_df[
            student_filtered_df[
                "ID Number"
            ]
            .astype(str)
            == str(selected_student_id)
        ]
        .copy()
    )


    # =====================================================
    # STUDENT PERFORMANCE
    # =====================================================

    show_student_performance(
        selected_student_data,
        selected_student_id
    )


    # =====================================================
    # FILTERED DATA
    # =====================================================

    st.markdown("---")

    st.markdown(
        "## 📋 Course Records"
    )


    display_columns = [
        "ID Number",
        "Name",
        "Course Code",
        "Course Name",
        "Academic Semester",
        "Grade",
        "Points",
        "Credits",
        "Category"
    ]


    available_columns = [
        col
        for col in display_columns
        if col in selected_student_data.columns
    ]


    st.dataframe(
        selected_student_data[
            available_columns
        ],
        use_container_width=True,
        hide_index=True
    )


    # =====================================================
    # EXCEL EXPORT
    # =====================================================

    st.markdown("---")

    st.markdown(
        "## 📥 Download Student Data"
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


    st.download_button(
        label="📊 Download Excel",
        data=excel_buffer.getvalue(),
        file_name=f"{selected_student_id}_performance.xlsx",
        mime=(
            "application/vnd.openxmlformats-officedocument."
            "spreadsheetml.sheet"
        )
    )


    # =====================================================
    # PDF GENERATION
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
            alignment=TA_CENTER,
            fontSize=18,
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
            fontSize=9
        )


        story = []


        # =================================================
        # LOGO
        # =================================================

        if LOGO_FILE.exists():

            try:

                logo = Image(
                    str(LOGO_FILE),
                    width=0.8 * inch,
                    height=0.8 * inch
                )

                logo.hAlign = "CENTER"

                story.append(logo)

                story.append(
                    Spacer(1, 5)
                )

            except:

                pass


        # =================================================
        # TITLE
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
                normal_style
            )
        )


        story.append(
            Paragraph(
                "Student Academic Performance Report",
                normal_style
            )
        )


        story.append(
            Spacer(1, 15)
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


        student_name = str(
            student_data["Name"].iloc[0]
        )


        mentor_name = str(
            student_data["Mentor Name"].iloc[0]
        )


        overall_cgpa = calculate_cgpa(
            student_data
        )


        # -----------------------------------------------
        # STUDENT DETAILS TABLE
        # -----------------------------------------------

        student_info = [

            [
                "Student ID",
                str(student_id)
            ],

            [
                "Student Name",
                student_name
            ],

            [
                "Mentor Name",
                mentor_name
            ],

            [
                "Overall CGPA",
                f"{overall_cgpa:.2f} / 10"
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
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.grey
                ),

                (
                    "FONTNAME",
                    (0, 0),
                    (-1, -1),
                    "Helvetica"
                ),

                (
                    "FONTNAME",
                    (0, 0),
                    (0, -1),
                    "Helvetica-Bold"
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
            Spacer(1, 15)
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


        categories = [
            "AB",
            "DT",
            "F",
            "MTO",
            "-",
            "BLNA",
            "GP/MP",
            "NA"
        ]


        category_rows = [
            ["Category", "Count"]
        ]


        for category in categories:

            count = (
                student_data["Category"]
                .astype(str)
                .str.strip()
                .str.upper()
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
            category_table
        )


        story.append(
            Spacer(1, 15)
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


        academic_rows = [

            [
                "Semester",
                "Course Code",
                "Course Name",
                "Grade",
                "Points",
                "Credits",
                "Category"
            ]

        ]


        academic_data = student_data.copy()


        academic_data = academic_data.sort_values(
            by="Academic Semester",
            key=lambda series: series.map(
                academic_semester_sort_key
            )
        )


        for _, row in academic_data.iterrows():

            academic_rows.append(

                [

                    str(
                        row["Academic Semester"]
                    ),

                    str(
                        row["Course Code"]
                    ),

                    str(
                        row["Course Name"]
                    ),

                    str(
                        row["Grade"]
                    ),

                    str(
                        row["Points"]
                    ),

                    str(
                        row["Credits"]
                    ),

                    get_category(
                        row["Category"]
                    )

                ]

            )


        academic_table = Table(
            academic_rows,
            repeatRows=1,
            colWidths=[
                0.65 * inch,
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
            Spacer(1, 15)
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


        semester_groups = []


        for semester, sem_df in student_data.groupby(
            "Academic Semester"
        ):

            semester_groups.append(
                (
                    semester,
                    sem_df
                )
            )


        semester_groups.sort(
            key=lambda x:
            academic_semester_sort_key(x[0])
        )


        for semester, sem_df in semester_groups:

            semester_cgpa = calculate_cgpa(
                sem_df
            )


            story.append(
                Paragraph(
                    f"Semester {semester} - CGPA: "
                    f"{semester_cgpa:.2f}",
                    normal_style
                )
            )


            story.append(
                Spacer(1, 5)
            )


        story.append(
            Spacer(1, 10)
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
            student_data["Category"]
            .astype(str)
            .str.strip()
            .str.upper()
            .isin(
                ["F", "DT"]
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

            backlog_rows = [

                [
                    "Semester",
                    "Course Code",
                    "Course Name",
                    "Grade",
                    "Category"
                ]

            ]


            backlog_data = backlog_data.sort_values(
                by="Academic Semester",
                key=lambda series: series.map(
                    academic_semester_sort_key
                )
            )


            for _, row in backlog_data.iterrows():

                backlog_rows.append(

                    [

                        str(
                            row["Academic Semester"]
                        ),

                        str(
                            row["Course Code"]
                        ),

                        str(
                            row["Course Name"]
                        ),

                        str(
                            row["Grade"]
                        ),

                        get_category(
                            row["Category"]
                        )

                    ]

                )


            backlog_table = Table(
                backlog_rows,
                repeatRows=1,
                colWidths=[
                    0.8 * inch,
                    1 * inch,
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
