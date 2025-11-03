# student_dashboard.py
# Main Streamlit app: multi-page UI that uses session_state to persist selected student across pages.

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px

from data_preprocessing import load_data, get_student_list, get_student_by_roll, get_student_by_name, get_subject_columns
import utils


st.set_page_config(page_title="Student Performance Dashboard", layout="wide")

# ---------- Load data ----------
try:
    df = load_data(r"D:\DAV(py)\PBL_DAV\student_data_raw_fixed.csv")
except FileNotFoundError as e:
    st.error(str(e))
    st.stop()

# ---------- Session state defaults ----------
if "selected_roll" not in st.session_state:
    st.session_state.selected_roll = None
if "page" not in st.session_state:
    st.session_state.page = "Dashboard"
if "mind_seed" not in st.session_state:
    st.session_state.mind_seed = 0  # used to regenerate activities when Next clicked

# ---------- Top navigation (top-right style) ----------
title_col, nav1, nav2, nav3, nav4, spacer = st.columns([3,1,1,1,1,6])
with title_col:
    st.title("📊 Student Performance Dashboard")

# Buttons behave as navigators; set session_state.page
if nav1.button("Performance"):
    st.session_state.page = "Performance"
if nav2.button("Study Tips"):
    st.session_state.page = "Study Tips"
if nav3.button("Brain Food"):
    st.session_state.page = "Brain Food"
if nav4.button("Mind Freshener"):
    st.session_state.page = "Mind Freshener"

# ---------- Pages ----------
def dashboard_page():
    st.header("🏠 Dashboard")
    st.write("Select a student once here — your choice will persist across all pages.")

    # if student already selected, show profile and a 'Change student' button
    if st.session_state.selected_roll is not None:
        student_row = get_student_by_roll(df, st.session_state.selected_roll)
        if student_row is None:
            st.warning("Previously selected student not found in current dataset. Please select again.")
            st.session_state.selected_roll = None
            st.experimental_rerun()
        st.subheader(f"{student_row['Name']}  —  Roll: {int(student_row['Roll No'])}")
        st.markdown(f"**Class:** {student_row.get('Class','-')}  \n**Exam/Term:** {student_row.get('Exam','-')}  \n**Attendance:** {student_row.get('Attendance (%)','-')}%")
        col1, col2 = st.columns([1,1])
        with col1:
            if st.button("Change Student"):
                st.session_state.selected_roll = None
                st.rerun()
        with col2:
            if st.button("Go to Performance"):
                st.session_state.page = "Performance"
                st.rerun()
    else:
        # no student selected yet -> show selectbox and submit
        student_display = get_student_list(df)
        choice = st.selectbox("Select Student", student_display)
        if choice:
            # display details after selection, before pressing Submit
            student_name = choice.split(" (Roll:")[0]
            # show short details
            sr = get_student_by_name(df, student_name)
            if sr is not None:
                st.write(f"**{sr['Name']}**  •  Class: {sr.get('Class','-')}  •  Exam: {sr.get('Exam','-')}")
                st.write(f"Attendance: {sr.get('Attendance (%)','-')}%  •  Memory Score: {sr.get('Memory Score','-')}")
        if st.button("Submit"):
            # store roll in session_state and navigate to Performance
            if choice:
                roll_text = choice.split("Roll:")[1].strip().replace(")","")
                try:
                    roll_no = int(roll_text)
                except:
                    # fallback by name lookup
                    roll_no = int(sr["Roll No"])
                st.session_state.selected_roll = roll_no
                st.session_state.page = "Performance"
                st.rerun()

    st.markdown("---")
    #st.subheader("Dataset preview (first 8 rows)")
    #st.dataframe(df.head(8))

def performance_page():
    st.header("📈 Performance")
    if st.session_state.selected_roll is None:
        st.warning("No student selected. Go to Dashboard and pick a student first.")
        if st.button("Go to Dashboard"):
            st.session_state.page = "Dashboard"
            st.rerun()
        return

    student = get_student_by_roll(df, st.session_state.selected_roll)
    if student is None:
        st.error("Selected student not found in dataset. Please re-select on Dashboard.")
        st.session_state.selected_roll = None
        return

    st.subheader(f"Student: {student['Name']} (Roll: {int(student['Roll No'])})")
    # Subject-wise bar
    subject_cols = get_subject_columns(df)
    if not subject_cols:
        st.info("No numeric subject columns found in the dataset.")
    else:
        marks = {s: student.get(s, 0) for s in subject_cols}

        # 1) Subject-wise performance bar chart
        fig1 = px.bar(x=list(marks.keys()), y=list(marks.values()), labels={'x':'Subject','y':'Marks'}, title="Subject-wise Performance")
        st.plotly_chart(fig1, use_container_width=True)

        # 2) Score improvement trend (attempt real trend or synthesize)
        trend = utils.compute_improvement_trend(df, student, terms=4)
        trend_df = pd.DataFrame({"Term": [f"Term {i+1}" for i in range(len(trend))], "Score": trend})
        fig2 = px.line(trend_df, x="Term", y="Score", markers=True, title="Score Improvement Trend")
        st.plotly_chart(fig2, use_container_width=True)

        # 3) Strengths & Weaknesses (radar)
        radar_df = pd.DataFrame({
            "Subject": list(marks.keys()),
            "Score": list(marks.values())
        })
        if len(radar_df) >= 3:
            fig3 = px.line_polar(radar_df, r="Score", theta="Subject", line_close=True, title="Strengths & Weaknesses")
            st.plotly_chart(fig3, use_container_width=True)
        else:
            st.info("Need at least 3 subject columns for radar chart.")

        # 4) Study Time vs Performance (class-level scatter, highlight selected student)
        scat = utils.study_time_vs_performance_df(df)
        if not scat.empty:
            fig4 = px.scatter(scat, x="StudyDurationMinutes", y="AvgScore", hover_name="Name",
                              title="Study Time vs Performance (class scatter)")
            # highlight selected student by adding marker layer
            sel = scat[scat["Roll No"] == student["Roll No"]]
            if not sel.empty:
                fig4.add_scatter(x=sel["StudyDurationMinutes"], y=sel["AvgScore"],
                                 mode='markers', marker=dict(size=14, symbol='diamond'),
                                 name=f"Selected: {student['Name']}")
            st.plotly_chart(fig4, use_container_width=True)
        else:
            st.info("No study-duration data found to show scatter plot.")

        # Useful quick metrics
        avg_score = utils.compute_student_average(student, subject_cols)
        cols = st.columns(4)
        cols[0].metric("Avg Score", f"{avg_score:.1f}")
        cols[1].metric("Attendance", f"{student.get('Attendance (%)', 0)}%")
        mem = student.get("Memory Score", "-")
        cols[2].metric("Memory Score", f"{mem}")
        stress = student.get("Stress Level", "-")
        cols[3].metric("Stress Level", f"{stress}")

def study_tips_page():
    st.header("📘 Study Tips & Personalised Analysis")
    if st.session_state.selected_roll is None:
        st.warning("No student selected. Choose a student from Dashboard first.")
        if st.button("Go to Dashboard"):
            st.session_state.page = "Dashboard"
            st.rerun()
        return
    student = get_student_by_roll(df, st.session_state.selected_roll)
    if student is None:
        st.error("Selected student missing. Go to Dashboard and select again.")
        return

    st.subheader("Personalized Analysis")
    adv = utils.personalized_study_advice(student)
    # show results in a box
    st.write("**Summary**")
    for k,v in adv.items():
        st.markdown(f"- **{k}:** {v}")

    st.markdown("---")
    st.subheader("Memory Enhancement Tips")
    st.write("- Use spaced repetition (short, frequent reviews).")
    st.write("- Create and review flashcards before sleep.")
    st.write("- Break material into small chunks and practice active recall.")

    st.subheader("Exam Fear Solutions")
    st.write("- Follow a pre-exam routine: short warm-up, small review, breathing.")
    st.write("- Practice mock tests under timed conditions.")
    st.write("- Visualize success and positive outcomes.")

def brain_food_page():
    st.header("🥗 Brain Food")
    if st.session_state.selected_roll is None:
        st.warning("Select a student from Dashboard to see personalised recommendations.")
        return
    student = get_student_by_roll(df, st.session_state.selected_roll)
    rec = utils.brain_food_recommendations(student)
    st.subheader("Daily Focus Foods")
    for item in rec["Daily Focus Foods"]:
        st.write(f"- {item}")
    st.subheader("Revision Snacks")
    for item in rec["Revision Snacks"]:
        st.write(f"- {item}")
    st.subheader("Night Before Exams")
    for item in rec["Night Before Exam"]:
        st.write(f"- {item}")
    st.subheader("Hydration Tips")
    for item in rec["Hydration Tips"]:
        st.write(f"- {item}")
    st.subheader("Meal Time Schedule")
    for item in rec["Meal Time Schedule"]:
        st.write(f"- {item}")
    if "Note" in rec:
        st.info(rec["Note"])

def mind_freshener_page():
    st.header("🌸 Mind Freshener")
    if st.session_state.selected_roll is None:
        st.warning("Select a student from Dashboard first.")
        return
    student = get_student_by_roll(df, st.session_state.selected_roll)
    # generate or re-generate activities based on session seed
    if "mind_seed" not in st.session_state:
        st.session_state.mind_seed = 0
    #if st.button("Next (regenerate activities)"):
        #st.session_state.mind_seed += 1

    # We incorporate mind_seed so Next regenerates. We feed a combined deterministic seed but change with mind_seed
    # utils.generate_mind_activities uses student's roll; to make Next change, we alter the name slightly by appending mind_seed
    activities = utils.generate_mind_activities(student, n=6)
    # if mind_seed is odd, rotate activities to simulate regeneration (simple, deterministic behaviour)
    idx = st.session_state.mind_seed % len(activities)
    activities = activities[idx:] + activities[:idx]
    # present activities in 2x3 grid
    cols = st.columns(3)
    for i, act in enumerate(activities):
        with cols[i % 3]:
            st.info(act)

# ---------- Page router ----------
if st.session_state.page == "Dashboard":
    dashboard_page()
elif st.session_state.page == "Performance":
    performance_page()
elif st.session_state.page == "Study Tips":
    study_tips_page()
elif st.session_state.page == "Brain Food":
    brain_food_page()
elif st.session_state.page == "Mind Freshener":
    mind_freshener_page()
else:
    st.write("Unknown page-Returning to Dashboard.")
    st.session_state.page = "Dashboard"
    st.rerun()
