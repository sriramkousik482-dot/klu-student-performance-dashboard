import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns


# =========================================================
# PAGE CONFIG
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

    # =====================================================
    # SEMESTER
    # =====================================================

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

    # =====================================================
    # YEAR FROM ID
    # =====================================================

    df["Year"] = df["ID Number"].str[:2].apply(
        lambda x:
        f"Y{x}" if x.isdigit()
        else "Unknown"
    )

    # =====================================================
    # CREDIT POINTS
    # =====================================================

    df["Credit Points"] = (
        df["Points"] * df["Credits"]
    )

    return df


df = load_data()


# =========================================================
# FUNCTIONS
# =========================================================


def calculate_cgpa(data):

    valid_data = data.dropna(
        subset=["Points", "Credits"]
    )

    if valid_data.empty:
        return 0.0

    total_credits = valid_data["Credits"].sum()

    if total_credits == 0:
        return 0.0

    total_credit_points = (
        valid_data["Credit Points"].sum()
    )

    return (
        total_credit_points /
        total_credits
    )


def get_result(grade):

    grade = str(grade).strip().upper()

    if grade == "DT":
        return "DT"

    if grade in ["F", "FAIL"]:
        return "F"

    return "P"


def semester_sort_key(semester):

    semester = str(semester).strip()

    # Semester 1, Semester 2, etc.
    digits = "".join(
        char
        for char in semester
        if char.isdigit()
    )

    if digits:
        return int(digits)

    # Odd / Even
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

    grade = str(
        row["Grade"]
    ).strip().upper()

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

        # Semester heading
        st.markdown(
            f"### ● {semester}"
        )

        st.caption(
            f"{len(semester_data)} Courses"
        )

        # Four course cards per row
        for start in range(
            0,
            len(semester_data),
            4
        ):

            current_courses = (
                semester_data
                .iloc[start:start + 4]
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

    # Complete records of selected student
    student_data = df[
        df["ID Number"] == student_id
    ].copy()

    if student_data.empty:
        return

    student_name = student_data[
        "Name"
    ].iloc[0]

    # Overall CGPA
    cgpa = calculate_cgpa(
        student_data
    )

    # Backlogs
    results = student_data[
        "Grade"
    ].apply(get_result)

    backlog_data = student_data[
        results == "F"
    ]

    backlog_count = len(
        backlog_data
    )

    # =====================================================
    # HEADER
    # =====================================================

    st.markdown(
        "## 🎓 Academic Performance Overview"
    )

    st.write(
        f"**{student_name}**  |  "
        f"Student ID: **{student_id}**"
    )

    # =====================================================
    # STUDENT KPI
    # =====================================================

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

    # =====================================================
    # SEMESTER CARDS
    # =====================================================

    show_semester_cards(
        student_data
    )

    # =====================================================
    # BACKLOG SUBJECTS
    # =====================================================

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
# TITLE
# =========================================================

st.title(
    "🎓 KL UNIVERSITY"
)

st.caption(
    "Academic Performance Dashboard"
)


# =========================================================
# SIDEBAR - CASCADING FILTERS
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
# COURSE CODE FILTER
#
# IMPORTANT:
# Course Code options depend on selected Year.
# =========================================================

course_code_filter_df = df.copy()

if selected_year:

    course_code_filter_df = (
        course_code_filter_df[
            course_code_filter_df["Year"].isin(
                selected_year
            )
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
# COURSE NAME FILTER
#
# IMPORTANT:
# Course Name depends on:
# Year + Course Code
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
# MAIN STUDENT SEARCH
# =========================================================

st.subheader(
    "🔍 Student Search"
)


search_col1, search_col2 = (
    st.columns(2)
)


# =========================================================
# STUDENT ID / NAME
# =========================================================

with search_col1:

    student_search = st.text_input(
        "Search Student ID or Full Name",
        placeholder="Enter ID or full name..."
    )


# =========================================================
# SEMESTER
# =========================================================

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
# APPLY ALL FILTERS
# =========================================================

filtered_df = df.copy()


# =========================================================
# YEAR
# =========================================================

if selected_year:

    filtered_df = filtered_df[
        filtered_df["Year"].isin(
            selected_year
        )
    ]


# =========================================================
# COURSE CODE
# =========================================================

if selected_course_code:

    filtered_df = filtered_df[
        filtered_df["Course Code"].isin(
            selected_course_code
        )
    ]


# =========================================================
# COURSE NAME
# =========================================================

if selected_course_name:

    filtered_df = filtered_df[
        filtered_df["Course Name"].isin(
            selected_course_name
        )
    ]


# =========================================================
# SEMESTER
# =========================================================

if selected_semester != "All":

    filtered_df = filtered_df[
        filtered_df["Semester"]
        == selected_semester
    ]


# =========================================================
# STUDENT SEARCH
# =========================================================

if student_search:

    search_text = (
        student_search
        .strip()
        .lower()
    )

    filtered_df = filtered_df[
        filtered_df["ID Number"]
        .str.lower()
        .str.contains(
            search_text,
            na=False
        )
        |
        filtered_df["Name"]
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
    filtered_df["ID Number"]
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
# OVERALL AVERAGE CGPA
#
# Filters identify students.
# Complete student records are used for CGPA.
# =========================================================

student_cgpas = []

for student_id in matching_student_ids:

    complete_student_data = df[
        df["ID Number"] == student_id
    ]

    cgpa = calculate_cgpa(
        complete_student_data
    )

    student_cgpas.append(cgpa)


if student_cgpas:

    average_cgpa = (
        sum(student_cgpas)
        / len(student_cgpas)
    )

else:

    average_cgpa = 0.0


# =========================================================
# KPI CALCULATIONS
# =========================================================

total_students = (
    filtered_df["ID Number"]
    .nunique()
)

course_registrations = len(
    filtered_df
)

results = filtered_df[
    "Grade"
].apply(get_result)

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
    ]["ID Number"]
    .nunique()
)


# =========================================================
# KPI ROW 1
# =========================================================

k1, k2, k3, k4 = st.columns(4)


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


# =========================================================
# KPI ROW 2
# =========================================================

k5, k6, k7 = st.columns(3)


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
    "📌 **Legend:** "
    "CGPA is out of 10.0  |  "
    "**P = Passed**  |  "
    "**F = Failed / Backlog**  |  "
    "**DT = Detained**"
)


# =========================================================
# STUDENT PERFORMANCE
# =========================================================

st.divider()


if len(matching_student_ids) == 1:

    # =====================================================
    # ONE STUDENT
    # =====================================================

    selected_student_id = (
        matching_student_ids[0]
    )

    show_student_performance(
        selected_student_id
    )


elif len(matching_student_ids) > 1:

    # =====================================================
    # MULTIPLE STUDENTS
    # =====================================================

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
                len(
                    complete_student_data
                ),

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
        "No students found for the "
        "selected filters."
    )


# =========================================================
# AVERAGE CGPA GRAPH
# =========================================================

st.divider()

st.subheader(
    "📈 Average CGPA by Semester"
)


if matching_student_ids:

    # -----------------------------------------------------
    # Get complete records of selected students
    # -----------------------------------------------------

    selected_students_df = df[
        df["ID Number"].isin(
            matching_student_ids
        )
    ].copy()


    # =====================================================
    # CALCULATE EACH STUDENT'S CGPA
    # FOR EACH SEMESTER
    # =====================================================

    semester_cgpa_records = []

    for student_id in matching_student_ids:

        student_data = selected_students_df[
            selected_students_df[
                "ID Number"
            ] == student_id
        ]

        semesters = (
            student_data["Semester"]
            .dropna()
            .unique()
            .tolist()
        )

        for semester in semesters:

            semester_data = student_data[
                student_data["Semester"]
                == semester
            ]

            semester_cgpa = calculate_cgpa(
                semester_data
            )

            semester_cgpa_records.append({

                "Student ID":
                    student_id,

                "Semester":
                    semester,

                "CGPA":
                    semester_cgpa
            })


    # =====================================================
    # DATAFRAME
    # =====================================================

    semester_cgpa_df = pd.DataFrame(
        semester_cgpa_records
    )


    if not semester_cgpa_df.empty:

        # =================================================
        # AVERAGE CGPA FOR ALL STUDENTS
        # FOR EACH SEMESTER
        # =================================================

        average_semester_cgpa = (
            semester_cgpa_df
            .groupby(
                "Semester",
                as_index=False
            )["CGPA"]
            .mean()
        )


        # =================================================
        # SORT SEMESTERS
        # =================================================

        average_semester_cgpa["Sort"] = (
            average_semester_cgpa[
                "Semester"
            ].apply(
                semester_sort_key
            )
        )

        average_semester_cgpa = (
            average_semester_cgpa
            .sort_values("Sort")
            .drop(
                columns=["Sort"]
            )
            .reset_index(drop=True)
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
            markersize=9,
            ax=ax
        )


        # =================================================
        # CGPA LABELS
        # =================================================

        for i in range(
            len(average_semester_cgpa)
        ):

            semester = (
                average_semester_cgpa
                .iloc[i]["Semester"]
            )

            cgpa = (
                average_semester_cgpa
                .iloc[i]["CGPA"]
            )

            ax.text(
                semester,
                cgpa + 0.15,
                f"{cgpa:.2f}",
                ha="center",
                fontsize=11,
                fontweight="bold"
            )


        # =================================================
        # GRAPH FORMATTING
        # =================================================

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

        # CGPA is out of 10
        ax.set_ylim(
            0,
            10
        )

        ax.grid(
            axis="y",
            alpha=0.3
        )

        plt.tight_layout()

        st.pyplot(fig)

        plt.close(fig)


        st.caption(
            f"Average calculated from "
            f"{len(matching_student_ids)} "
            f"student(s)."
        )


    else:

        st.info(
            "Not enough academic data to "
            "calculate the graph."
        )


else:

    st.info(
        "Select filters to display "
        "the average CGPA graph."
    )


# =========================================================
# AVERAGE CGPA TABLE
# =========================================================

if (
    matching_student_ids
    and not semester_cgpa_df.empty
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
# DOWNLOAD CSV
# =========================================================

st.divider()

st.subheader(
    "⬇️ Download Data"
)


csv_data = filtered_df.to_csv(
    index=False
).encode("utf-8")


st.download_button(
    label="📥 Download Filtered CSV",
    data=csv_data,
    file_name="filtered_student_data.csv",
    mime="text/csv"
)