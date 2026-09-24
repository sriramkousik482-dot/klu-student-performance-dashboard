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
BASE_DIR = Path(__file__).resolve().parent
LOGO_PATH = BASE_DIR / "klu_logo.png.jpg"


# =========================================================
# PAGE CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="KL UNIVERSITY",
    page_icon="🎓",
    layout="wide"
)


# =========================================================
# LOAD DATA
# =========================================================

@st.cache_data
def load_data():

    df = pd.read_csv("student.csv")

    # Clean column names
    df.columns = df.columns.str.strip()

    # Clean text columns
    for col in df.columns:

        if df[col].dtype == "object":

            df[col] = (
                df[col]
                .astype(str)
                .str.strip()
            )

    # Numeric columns
    df["Points"] = pd.to_numeric(
        df["Points"],
        errors="coerce"
    )

    df["Credits"] = pd.to_numeric(
        df["Credits"],
        errors="coerce"
    )

    # Student ID
    df["ID Number"] = (
        df["ID Number"]
        .astype(str)
        .str.strip()
    )

    # Semester
    df["Semester"] = (
        df["Semester"]
        .astype(str)
        .str.strip()
        .str.lower()
    )

    df["Semester"] = df["Semester"].replace({

        "odd": "Odd Sem",
        "odd sem": "Odd Sem",
        "odd semester": "Odd Sem",

        "even": "Even Sem",
        "even sem": "Even Sem",
        "even semester": "Even Sem"

    })

    # -----------------------------------------------------
    # YEAR FROM STUDENT ID
    # -----------------------------------------------------

    df["Year"] = df["ID Number"].str[:2].apply(

        lambda x:
        f"Y{x}"
        if x.isdigit()
        else "Unknown"

    )

    # -----------------------------------------------------
    # CREDIT POINTS
    # -----------------------------------------------------

    df["Credit Points"] = (
        df["Points"] * df["Credits"]
    )

    return df


df = load_data()


# =========================================================
# CGPA CALCULATION
# =========================================================

def calculate_cgpa(data):

    valid_data = data.dropna(
        subset=[
            "Points",
            "Credits"
        ]
    )

    if valid_data.empty:

        return 0.0

    total_credits = (
        valid_data["Credits"].sum()
    )

    if total_credits == 0:

        return 0.0

    total_credit_points = (
        valid_data["Credit Points"].sum()
    )

    return (
        total_credit_points /
        total_credits
    )


# =========================================================
# RESULT
# =========================================================

def get_result(grade):

    grade = (
        str(grade)
        .strip()
        .upper()
    )

    if grade == "DT":

        return "DT"

    if grade in ["F", "FAIL"]:

        return "F"

    return "P"


# =========================================================
# SEMESTER SORTING
# =========================================================

def semester_sort_key(semester):

    semester = str(
        semester
    ).strip()

    digits = "".join(
        char
        for char in semester
        if char.isdigit()
    )

    if digits:

        return int(digits)

    if semester.lower().startswith("odd"):

        return 1

    if semester.lower().startswith("even"):

        return 2

    return 99


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

    grade = (
        str(row["Grade"])
        .strip()
        .upper()
    )

    points = row["Points"]

    result = get_result(grade)

    if result == "P":

        display_grade = (
            f"{grade} (P)"
        )

    elif result == "F":

        display_grade = (
            f"{grade} (F)"
        )

    else:

        display_grade = "DT"

    with st.container(border=True):

        st.markdown(
            f"**{course_code}**"
        )

        st.caption(
            course_name
        )

        st.write(
            display_grade
        )

        if pd.notna(points):

            st.caption(
                f"Points: {points:g}"
            )


# =========================================================
# SEMESTER COURSE CARDS
# =========================================================

def show_semester_cards(student_data):

    if student_data.empty:

        st.info(
            "No academic records found."
        )

        return

    semesters = (
        student_data["Semester"]
        .dropna()
        .unique()
        .tolist()
    )

    semesters = sorted(
        semesters,
        key=semester_sort_key
    )

    for semester in semesters:

        semester_data = student_data[
            student_data["Semester"] == semester
        ].copy()

        semester_data = (
            semester_data
            .reset_index(drop=True)
        )

        st.markdown(
            f"### ● {semester}"
        )

        st.caption(
            f"{len(semester_data)} Courses"
        )

        for start in range(
            0,
            len(semester_data),
            4
        ):

            current_courses = (
                semester_data.iloc[
                    start:start + 4
                ]
            )

            columns = st.columns(4)

            for i, (_, row) in enumerate(
                current_courses.iterrows()
            ):

                with columns[i]:

                    show_course_card(row)

        st.write("")


# =========================================================
# STUDENT PERFORMANCE
# =========================================================

def show_student_performance(student_id):

    student_data = df[
        df["ID Number"] == student_id
    ].copy()

    if student_data.empty:

        return

    student_name = (
        student_data["Name"].iloc[0]
    )

    cgpa = calculate_cgpa(
        student_data
    )

    results = (
        student_data["Grade"]
        .apply(get_result)
    )

    backlog_data = student_data[
        results == "F"
    ]

    backlog_count = len(
        backlog_data
    )

    st.markdown(
        "## 🎓 Academic Performance Overview"
    )

    st.write(
        f"**{student_name}**  |  "
        f"Student ID: **{student_id}**"
    )

    c1, c2, c3 = st.columns(3)

    with c1:

        st.metric(
            "Overall CGPA",
            f"{cgpa:.2f} / 10"
        )

    with c2:

        st.metric(
            "Backlogs",
            backlog_count
        )

    with c3:

        st.metric(
            "Courses",
            len(student_data)
        )

    st.divider()

    show_semester_cards(
        student_data
    )

    st.markdown(
        "## 📕 Backlog Subjects"
    )

    if backlog_data.empty:

        st.success(
            "No Backlogs 🎉"
        )

    else:

        backlog_display = backlog_data[
            [
                "Course Code",
                "Course Name",
                "Grade",
                "Points",
                "Credits",
                "Semester"
            ]
        ].copy()

        st.dataframe(
            backlog_display,
            use_container_width=True,
            hide_index=True
        )


# =========================================================
# DASHBOARD HEADER
# =========================================================

st.title(
    "🎓 KL UNIVERSITY"
)

st.caption(
    "Department of CSE-4 | Academic Performance Dashboard"
)


# =========================================================
# SIDEBAR FILTERS
# =========================================================

st.sidebar.header(
    "🔎 Filters"
)


# =========================================================
# YEAR FILTER
# =========================================================

year_options = sorted(
    df["Year"]
    .dropna()
    .unique()
    .tolist()
)

selected_year = st.sidebar.multiselect(
    "Year",
    options=year_options,
    default=[]
)


# =========================================================
# CASCADING COURSE CODE
# =========================================================

course_code_filter_df = df.copy()

if selected_year:

    course_code_filter_df = (
        course_code_filter_df[
            course_code_filter_df[
                "Year"
            ].isin(selected_year)
        ]
    )


course_code_options = sorted(
    course_code_filter_df[
        "Course Code"
    ]
    .dropna()
    .unique()
    .tolist()
)

selected_course_code = (
    st.sidebar.multiselect(
        "Course Code",
        options=course_code_options,
        default=[]
    )
)


# =========================================================
# CASCADING COURSE NAME
# =========================================================

course_name_filter_df = (
    course_code_filter_df.copy()
)

if selected_course_code:

    course_name_filter_df = (
        course_name_filter_df[
            course_name_filter_df[
                "Course Code"
            ].isin(
                selected_course_code
            )
        ]
    )


course_name_options = sorted(
    course_name_filter_df[
        "Course Name"
    ]
    .dropna()
    .unique()
    .tolist()
)

selected_course_name = (
    st.sidebar.multiselect(
        "Course Name",
        options=course_name_options,
        default=[]
    )
)


# =========================================================
# STUDENT SEARCH
# =========================================================

st.subheader(
    "🔍 Student Search"
)

search_col1, search_col2 = (
    st.columns(2)
)

with search_col1:

    student_search = st.text_input(
        "Search Student ID or Full Name",
        placeholder="Enter ID or full name..."
    )

with search_col2:

    selected_semester = st.selectbox(
        "Semester",
        [
            "All",
            "Odd Sem",
            "Even Sem"
        ]
    )


# =========================================================
# APPLY FILTERS
# =========================================================

filtered_df = df.copy()


if selected_year:

    filtered_df = filtered_df[
        filtered_df["Year"].isin(
            selected_year
        )
    ]


if selected_course_code:

    filtered_df = filtered_df[
        filtered_df[
            "Course Code"
        ].isin(
            selected_course_code
        )
    ]


if selected_course_name:

    filtered_df = filtered_df[
        filtered_df[
            "Course Name"
        ].isin(
            selected_course_name
        )
    ]


if selected_semester != "All":

    filtered_df = filtered_df[
        filtered_df[
            "Semester"
        ] == selected_semester
    ]


if student_search:

    search_text = (
        student_search
        .strip()
        .lower()
    )

    filtered_df = filtered_df[
        filtered_df[
            "ID Number"
        ]
        .str.lower()
        .str.contains(
            search_text,
            na=False
        )
        |
        filtered_df[
            "Name"
        ]
        .str.lower()
        .str.contains(
            search_text,
            na=False
        )
    ]


# =========================================================
# MATCHING STUDENTS
# =========================================================

matching_student_ids = (
    filtered_df[
        "ID Number"
    ]
    .dropna()
    .unique()
    .tolist()
)


# =========================================================
# DASHBOARD OVERVIEW
# =========================================================

st.divider()

st.subheader(
    "📊 Dashboard Overview"
)


# =========================================================
# AVERAGE CGPA
# =========================================================

student_cgpas = []

for student_id in matching_student_ids:

    complete_student_data = df[
        df["ID Number"] == student_id
    ]

    cgpa = calculate_cgpa(
        complete_student_data
    )

    student_cgpas.append(
        cgpa
    )


if student_cgpas:

    average_cgpa = (
        sum(student_cgpas) /
        len(student_cgpas)
    )

else:

    average_cgpa = 0.0


# =========================================================
# KPI VALUES
# =========================================================

total_students = (
    filtered_df[
        "ID Number"
    ].nunique()
)

course_registrations = len(
    filtered_df
)

results = (
    filtered_df[
        "Grade"
    ].apply(get_result)
)

passed = (
    results == "P"
).sum()

failed = (
    results == "F"
).sum()

detained = (
    results == "DT"
).sum()

backlogs = failed

students_with_backlogs = (
    filtered_df[
        results == "F"
    ][
        "ID Number"
    ].nunique()
)


# =========================================================
# KPI CARDS
# =========================================================

k1, k2, k3, k4 = (
    st.columns(4)
)

with k1:

    st.metric(
        "👨‍🎓 Total Students",
        total_students
    )

with k2:

    st.metric(
        "📈 Average CGPA",
        f"{average_cgpa:.2f} / 10"
    )

with k3:

    st.metric(
        "📚 Course Registrations",
        course_registrations
    )

with k4:

    st.metric(
        "📕 Backlogs",
        backlogs
    )


k5, k6, k7 = (
    st.columns(3)
)

with k5:

    st.metric(
        "⚠️ Students With Backlogs",
        students_with_backlogs
    )

with k6:

    st.metric(
        "✅ Passed",
        passed
    )

with k7:

    st.metric(
        "⛔ Detained",
        detained
    )


# =========================================================
# LEGEND
# =========================================================

st.info(
    "📌 **Legend:** CGPA is out of 10.0  |  "
    "**P = Passed**  |  "
    "**F = Failed / Backlog**  |  "
    "**DT = Detained**"
)


# =========================================================
# STUDENT SUMMARY
# =========================================================

st.divider()


if len(matching_student_ids) == 1:

    selected_student_id = (
        matching_student_ids[0]
    )

    show_student_performance(
        selected_student_id
    )


elif len(matching_student_ids) > 1:

    st.subheader(
        "👨‍🎓 Students"
    )

    student_summary = []

    for student_id in matching_student_ids:

        complete_student_data = df[
            df["ID Number"] == student_id
        ]

        student_name = (
            complete_student_data[
                "Name"
            ].iloc[0]
        )

        cgpa = calculate_cgpa(
            complete_student_data
        )

        complete_results = (
            complete_student_data[
                "Grade"
            ].apply(get_result)
        )

        student_backlogs = (
            complete_results == "F"
        ).sum()

        student_summary.append({

            "Student ID":
                student_id,

            "Name":
                student_name,

            "CGPA":
                round(cgpa, 2),

            "Courses":
                len(complete_student_data),

            "Backlogs":
                student_backlogs

        })


    summary_df = pd.DataFrame(
        student_summary
    )

    st.dataframe(
        summary_df,
        use_container_width=True,
        hide_index=True
    )

    st.caption(
        "🔎 Search for a Student ID or "
        "full name above to view "
        "semester-wise course cards."
    )


else:

    st.warning(
        "No students found for "
        "the selected filters."
    )


# =========================================================
# AVERAGE CGPA BY SEMESTER
# =========================================================

st.divider()

st.subheader(
    "📈 Average CGPA by Semester"
)


# Initialize
average_semester_cgpa = (
    pd.DataFrame()
)


if matching_student_ids:

    selected_students_df = df[
        df["ID Number"].isin(
            matching_student_ids
        )
    ].copy()

    semester_cgpa_records = []


    for student_id in matching_student_ids:

        student_data = (
            selected_students_df[
                selected_students_df[
                    "ID Number"
                ] == student_id
            ]
        )

        semesters = (
            student_data[
                "Semester"
            ]
            .dropna()
            .unique()
            .tolist()
        )


        for semester in semesters:

            semester_data = (
                student_data[
                    student_data[
                        "Semester"
                    ] == semester
                ]
            )

            semester_cgpa = (
                calculate_cgpa(
                    semester_data
                )
            )

            semester_cgpa_records.append({

                "Student ID":
                    student_id,

                "Semester":
                    semester,

                "CGPA":
                    semester_cgpa

            })


    semester_cgpa_df = pd.DataFrame(
        semester_cgpa_records
    )


    if not semester_cgpa_df.empty:

        average_semester_cgpa = (
            semester_cgpa_df
            .groupby(
                "Semester",
                as_index=False
            )["CGPA"]
            .mean()
        )


        average_semester_cgpa[
            "Sort"
        ] = (
            average_semester_cgpa[
                "Semester"
            ]
            .apply(
                semester_sort_key
            )
        )


        average_semester_cgpa = (
            average_semester_cgpa
            .sort_values("Sort")
            .drop(
                columns=["Sort"]
            )
            .reset_index(
                drop=True
            )
        )


        # =================================================
        # LINE GRAPH
        # =================================================

        fig, ax = plt.subplots(
            figsize=(10, 5)
        )


        sns.lineplot(

            data=average_semester_cgpa,

            x="Semester",

            y="CGPA",

            marker="o",

            linewidth=3,

            markersize=10,

            color="#1565C0",

            ax=ax

        )


        # Values above points

        for _, row in (
            average_semester_cgpa.iterrows()
        ):

            ax.text(

                row["Semester"],

                row["CGPA"] + 0.15,

                f"{row['CGPA']:.2f}",

                ha="center",

                va="bottom",

                fontsize=11,

                fontweight="bold",

                color="#1565C0"

            )


        ax.set_title(

            "Average CGPA by Semester",

            fontsize=16,

            fontweight="bold"

        )


        ax.set_xlabel(
            "Semester",
            fontsize=11
        )

        ax.set_ylabel(
            "Average CGPA",
            fontsize=11
        )


        ax.set_ylim(
            0,
            10
        )


        ax.grid(
            axis="y",
            alpha=0.25
        )


        sns.despine(
            ax=ax
        )


        plt.tight_layout()


        st.pyplot(
            fig,
            use_container_width=True
        )


        plt.close(fig)


        st.caption(
            f"Average CGPA calculated "
            f"from {len(matching_student_ids)} "
            f"selected student(s)."
        )


    else:

        st.info(
            "Not enough academic data "
            "to calculate the graph."
        )


else:

    st.info(
        "Select filters to display "
        "the average CGPA graph."
    )


# =========================================================
# AVERAGE CGPA VALUES
# =========================================================

if (
    matching_student_ids
    and not average_semester_cgpa.empty
):

    with st.expander(
        "📊 View Average CGPA Values"
    ):

        st.dataframe(
            average_semester_cgpa,
            use_container_width=True,
            hide_index=True
        )


# =========================================================
# FILTERED RECORDS
# =========================================================

st.divider()

st.subheader(
    "📋 Filtered Records"
)


if not filtered_df.empty:

    display_columns = [

        "ID Number",
        "Name",
        "Course Code",
        "Course Name",
        "Grade",
        "Points",
        "Credits",
        "Category",
        "Year",
        "Semester"

    ]


    available_columns = [

        col
        for col in display_columns
        if col in filtered_df.columns

    ]


    st.dataframe(

        filtered_df[
            available_columns
        ],

        use_container_width=True,

        hide_index=True

    )

else:

    st.info(
        "No records available."
    )


# =========================================================
# EXCEL CREATION
# =========================================================

def create_excel_file(data):

    output = BytesIO()

    with pd.ExcelWriter(
        output,
        engine="openpyxl"
    ) as writer:

        data.to_excel(
            writer,
            index=False,
            sheet_name="Filtered Records"
        )

        if (
            matching_student_ids
            and not average_semester_cgpa.empty
        ):

            average_semester_cgpa.to_excel(

                writer,

                index=False,

                sheet_name="Average CGPA"

            )

    output.seek(0)

    return output


# =========================================================
# PDF GRAPH IMAGE
# =========================================================

def create_graph_image(
    average_semester_cgpa
):

    if (
        average_semester_cgpa is None
        or average_semester_cgpa.empty
    ):

        return None


    graph_buffer = BytesIO()


    fig, ax = plt.subplots(
        figsize=(9, 4.5)
    )


    sns.lineplot(

        data=average_semester_cgpa,

        x="Semester",

        y="CGPA",

        marker="o",

        linewidth=3,

        markersize=9,

        color="#1565C0",

        ax=ax

    )


    for _, row in (
        average_semester_cgpa.iterrows()
    ):

        ax.text(

            row["Semester"],

            row["CGPA"] + 0.15,

            f"{row['CGPA']:.2f}",

            ha="center",

            va="bottom",

            fontsize=10,

            fontweight="bold",

            color="#1565C0"

        )


    ax.set_title(
        "Average CGPA by Semester",
        fontsize=15,
        fontweight="bold"
    )

    ax.set_xlabel(
        "Semester"
    )

    ax.set_ylabel(
        "Average CGPA"
    )

    ax.set_ylim(
        0,
        10
    )

    ax.grid(
        axis="y",
        alpha=0.25
    )

    sns.despine(
        ax=ax
    )

    plt.tight_layout()


    fig.savefig(

        graph_buffer,

        format="png",

        dpi=180,

        bbox_inches="tight"

    )


    plt.close(fig)

    graph_buffer.seek(0)

    return graph_buffer


def create_dashboard_pdf(
    filtered_df,
    matching_student_ids,
    average_cgpa,
    total_students,
    course_registrations,
    backlogs,
    students_with_backlogs,
    passed,
    failed,
    detained,
    average_semester_cgpa
):

    pdf_buffer = BytesIO()

    doc = SimpleDocTemplate(
        pdf_buffer,
        pagesize=A4,
        rightMargin=30,
        leftMargin=30,
        topMargin=30,
        bottomMargin=30
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "PDFTitle",
        parent=styles["Title"],
        fontSize=20,
        leading=24,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#1565C0"),
        spaceAfter=5
    )

    department_style = ParagraphStyle(
        "Department",
        parent=styles["Heading2"],
        fontSize=15,
        leading=19,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#1565C0"),
        spaceAfter=5
    )

    subtitle_style = ParagraphStyle(
        "Subtitle",
        parent=styles["Normal"],
        fontSize=10,
        leading=14,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#555555"),
        spaceAfter=12
    )

    heading_style = ParagraphStyle(
        "PDFHeading",
        parent=styles["Heading2"],
        fontSize=14,
        leading=18,
        textColor=colors.HexColor("#1565C0"),
        spaceBefore=12,
        spaceAfter=8
    )

    normal_style = ParagraphStyle(
        "NormalPDF",
        parent=styles["Normal"],
        fontSize=9,
        leading=12
    )

    story = []

    # =====================================================
    # KLU LOGO
    # =====================================================

    if LOGO_PATH.exists():

        logo = Image(
            str(LOGO_PATH),
            width=5.5 * inch,
            height=(5.5 * 183 / 940) * inch
        )

        logo.hAlign = "CENTER"

        story.append(logo)
        story.append(Spacer(1, 8))

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
            department_style
        )
    )

    story.append(
        Paragraph(
            "Student Academic Performance Report",
            subtitle_style
        )
    )

    header_line = Table(
        [[""]],
        colWidths=[7.0 * inch],
        rowHeights=[4]
    )

    header_line.setStyle(
        TableStyle([
            (
                "BACKGROUND",
                (0, 0),
                (-1, -1),
                colors.HexColor("#1565C0")
            )
        ])
    )

    story.append(header_line)
    story.append(Spacer(1, 15))

    # =====================================================
    # NO STUDENT SELECTED
    # =====================================================

    if not matching_student_ids:

        story.append(
            Paragraph(
                "No student selected.",
                heading_style
            )
        )

        story.append(
            Paragraph(
                "Please search for a student before generating the PDF.",
                normal_style
            )
        )

        doc.build(story)

        pdf_buffer.seek(0)

        return pdf_buffer

    # =====================================================
    # STUDENT DETAILS
    # =====================================================

    for student_id in matching_student_ids:

        student_data = df[
            df["ID Number"] == student_id
        ].copy()

        if student_data.empty:
            continue

        student_name = str(
            student_data["Name"].iloc[0]
        )

        overall_cgpa = calculate_cgpa(
            student_data
        )

        # =================================================
        # STUDENT INFORMATION
        # =================================================

        story.append(
            Paragraph(
                "Student Details",
                heading_style
            )
        )

        student_info = [
            ["Student ID", str(student_id)],
            ["Student Name", student_name],
            ["Overall CGPA", f"{overall_cgpa:.2f} / 10"],
        ]

        student_info_table = Table(
            student_info,
            colWidths=[
                1.7 * inch,
                5.3 * inch
            ]
        )

        student_info_table.setStyle(
            TableStyle([
                (
                    "BACKGROUND",
                    (0, 0),
                    (0, -1),
                    colors.HexColor("#E3F2FD")
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
                    "PADDING",
                    (0, 0),
                    (-1, -1),
                    7
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
            student_info_table
        )

        story.append(Spacer(1, 10))

        # =================================================
        # ACADEMIC PERFORMANCE
        # =================================================

        story.append(
            Paragraph(
                "Academic Performance",
                heading_style
            )
        )

        detail_data = [
            [
                "Semester",
                "Course Code",
                "Course Name",
                "Grade",
                "Points",
                "Credits",
                "Result"
            ]
        ]

        # Sort by semester
        student_data = student_data.copy()

        student_data["_sort"] = (
            student_data["Semester"]
            .apply(semester_sort_key)
        )

        student_data = student_data.sort_values(
            "_sort"
        )

        for _, row in student_data.iterrows():

            result = get_result(
                row["Grade"]
            )

            detail_data.append([
                str(row["Semester"]),
                str(row["Course Code"]),
                str(row["Course Name"]),
                str(row["Grade"]),
                (
                    f"{row['Points']:.2f}"
                    if pd.notna(row["Points"])
                    else ""
                ),
                (
                    f"{row['Credits']:.1f}"
                    if pd.notna(row["Credits"])
                    else ""
                ),
                result
            ])

        detail_table = Table(
            detail_data,
            repeatRows=1,
            colWidths=[
                0.75 * inch,
                0.85 * inch,
                2.55 * inch,
                0.55 * inch,
                0.65 * inch,
                0.60 * inch,
                0.70 * inch
            ]
        )

        detail_table.setStyle(
            TableStyle([

                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.HexColor("#1565C0")
                ),

                (
                    "TEXTCOLOR",
                    (0, 0),
                    (-1, 0),
                    colors.white
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
                    "ROWBACKGROUNDS",
                    (0, 1),
                    (-1, -1),
                    [
                        colors.white,
                        colors.HexColor("#F5F9FF")
                    ]
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
                ),

                (
                    "PADDING",
                    (0, 0),
                    (-1, -1),
                    4
                )
            ])
        )

        story.append(
            detail_table
        )

        # =================================================
        # SEMESTER-WISE CGPA
        # =================================================

        story.append(
            Paragraph(
                "Semester-wise Academic Performance",
                heading_style
            )
        )

        semester_data = []

        for semester, sem_df in (
            student_data.groupby("Semester")
        ):

            semester_cgpa = calculate_cgpa(
                sem_df
            )

            semester_data.append([
                str(semester),
                f"{semester_cgpa:.2f} / 10",
                str(len(sem_df))
            ])

        semester_data.sort(
            key=lambda x: semester_sort_key(x[0])
        )

        semester_table_data = [
            [
                "Semester",
                "Semester CGPA",
                "Courses"
            ]
        ] + semester_data

        semester_table = Table(
            semester_table_data,
            repeatRows=1,
            colWidths=[
                2.2 * inch,
                2.4 * inch,
                2.4 * inch
            ]
        )

        semester_table.setStyle(
            TableStyle([

                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.HexColor("#1976D2")
                ),

                (
                    "TEXTCOLOR",
                    (0, 0),
                    (-1, 0),
                    colors.white
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
                    0.4,
                    colors.grey
                ),

                (
                    "ROWBACKGROUNDS",
                    (0, 1),
                    (-1, -1),
                    [
                        colors.white,
                        colors.HexColor("#F5F9FF")
                    ]
                ),

                (
                    "ALIGN",
                    (0, 0),
                    (-1, -1),
                    "CENTER"
                ),

                (
                    "PADDING",
                    (0, 0),
                    (-1, -1),
                    6
                )
            ])
        )

        story.append(
            semester_table
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
            student_data["Grade"]
            .apply(get_result) == "F"
        ]

        if backlog_data.empty:

            story.append(
                Paragraph(
                    "No Backlogs",
                    normal_style
                )
            )

        else:

            backlog_table_data = [
                [
                    "Course Code",
                    "Course Name",
                    "Grade",
                    "Points",
                    "Semester"
                ]
            ]

            for _, row in backlog_data.iterrows():

                backlog_table_data.append([
                    str(row["Course Code"]),
                    str(row["Course Name"]),
                    str(row["Grade"]),
                    (
                        f"{row['Points']:.2f}"
                        if pd.notna(row["Points"])
                        else ""
                    ),
                    str(row["Semester"])
                ])

            backlog_table = Table(
                backlog_table_data,
                repeatRows=1,
                colWidths=[
                    1.0 * inch,
                    3.0 * inch,
                    0.7 * inch,
                    0.8 * inch,
                    1.5 * inch
                ]
            )

            backlog_table.setStyle(
                TableStyle([

                    (
                        "BACKGROUND",
                        (0, 0),
                        (-1, 0),
                        colors.HexColor("#C62828")
                    ),

                    (
                        "TEXTCOLOR",
                        (0, 0),
                        (-1, 0),
                        colors.white
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
                        0.4,
                        colors.grey
                    ),

                    (
                        "ROWBACKGROUNDS",
                        (0, 1),
                        (-1, -1),
                        [
                            colors.white,
                            colors.HexColor("#FFF5F5")
                        ]
                    ),

                    (
                        "FONTSIZE",
                        (0, 0),
                        (-1, -1),
                        8
                    ),

                    (
                        "PADDING",
                        (0, 0),
                        (-1, -1),
                        5
                    )
                ])
            )

            story.append(
                backlog_table
            )

        # Page break between students
        if student_id != matching_student_ids[-1]:

            story.append(
                PageBreak()
            )

    # =====================================================
    # FOOTER
    # =====================================================

    story.append(
        Spacer(1, 15)
    )

    story.append(
        Paragraph(
            "KL UNIVERSITY | Department of CSE-4",
            ParagraphStyle(
                "Footer",
                parent=styles["Normal"],
                fontSize=8,
                alignment=TA_CENTER,
                textColor=colors.HexColor("#777777")
            )
        )
    )

    # =====================================================
    # BUILD PDF
    # =====================================================

    doc.build(story)

    pdf_buffer.seek(0)

    return pdf_buffer


# =========================================================
# DOWNLOAD SECTION
# =========================================================

st.divider()

st.subheader(
    "⬇️ Download Dashboard"
)


# =========================================================
# EXCEL DOWNLOAD
# =========================================================

excel_file = create_excel_file(
    filtered_df
)


st.download_button(

    label="📊 Download Excel",

    data=excel_file,

    file_name=(
        "KL_University_CSE4_Dashboard.xlsx"
    ),

    mime=(
        "application/vnd.openxmlformats-officedocument."
        "spreadsheetml.sheet"
    )

)


# =========================================================
# PDF DOWNLOAD
# =========================================================

if st.button(
    "📄 Generate Student Academic PDF",
    use_container_width=True
):

    if not matching_student_ids:

        st.warning(
            "Please search/select a student first."
        )

    elif not LOGO_PATH.exists():

        st.error(
            "KLU logo not found. "
            "Please make sure 'klu_logo.png.jpg' "
            "is in the same GitHub folder as app.py."
        )

    else:

        with st.spinner(
            "Generating student academic PDF..."
        ):

            pdf_file = create_dashboard_pdf(

                filtered_df=filtered_df,

                matching_student_ids=matching_student_ids,

                average_cgpa=average_cgpa,

                total_students=total_students,

                course_registrations=course_registrations,

                backlogs=backlogs,

                students_with_backlogs=(
                    students_with_backlogs
                ),

                passed=passed,

                failed=failed,

                detained=detained,

                average_semester_cgpa=(
                    average_semester_cgpa
                )

            )

        st.success(
            "Student academic PDF generated successfully! ✅"
        )

        st.download_button(

            label="⬇️ Download Student Academic PDF",

            data=pdf_file,

            file_name=(
                "KL_University_Student_Academic_Report.pdf"
            ),

            mime="application/pdf",

            use_container_width=True

        )
