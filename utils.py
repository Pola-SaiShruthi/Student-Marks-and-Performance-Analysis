# utils.py
# helper utilities: charts data preparation, personalized tips, activity generator

import numpy as np
import pandas as pd
import hashlib
import random

def _seed_from_student(student_row):
    base = str(student_row.get("Roll No", "")) + "|" + str(student_row.get("Name", ""))
    h = hashlib.sha256(base.encode("utf-8")).hexdigest()
    return int(h[:8], 16)

def compute_student_average(student_row, subject_cols):
    vals = [float(student_row[c]) for c in subject_cols if pd.notna(student_row.get(c))]
    if not vals:
        return 0.0
    return sum(vals) / len(vals)

def compute_improvement_trend(df, student_row, terms=4):
    roll = student_row.get("Roll No", None)
    if roll is not None and (df["Roll No"] == roll).sum() > 1:
        rows = df[df["Roll No"] == roll]
        def exam_key(x):
            e = str(x).lower()
            import re
            m = re.search(r'(\d+)', e)
            if m:
                return int(m.group(1))
            return e
        try:
            rows_sorted = rows.sort_values(by="Exam", key=lambda s: s.map(exam_key))
        except Exception:
            rows_sorted = rows
        subject_cols = [c for c in df.columns if c not in ("Roll No","Name","Class","Exam","Attendance (%)","Memory Score","Stress Level","Study Duration (minutes)","Study Duration (hours)","Preferred Study Time","Exam Fear")]
        scores = []
        for _, r in rows_sorted.iterrows():
            vals = [float(r[c]) for c in subject_cols if pd.notna(r.get(c))]
            scores.append(sum(vals)/len(vals) if vals else 0.0)
        if len(scores) >= terms:
            return scores[-terms:]
        else:
            while len(scores) < terms:
                scores.append(scores[-1] if scores else 0.0)
            return scores
    subject_cols = [c for c in df.columns if c not in ("Roll No","Name","Class","Exam","Attendance (%)","Memory Score","Stress Level","Study Duration (minutes)","Study Duration (hours)","Preferred Study Time","Exam Fear")]
    base = compute_student_average(student_row, subject_cols)
    seed = _seed_from_student(student_row)
    rng = random.Random(seed)
    trend = []
    cur = base
    for i in range(terms):
        delta = rng.uniform(-6, 6)
        cur = max(0, min(100, cur + delta))
        trend.append(round(cur,1))
    return trend

def strengths_weaknesses(student_row, subject_cols, top_n=3):
    items = []
    for s in subject_cols:
        val = student_row.get(s, None)
        if pd.isna(val):
            continue
        try:
            items.append((s, float(val)))
        except Exception:
            continue
    if not items:
        return [], []
    items_sorted = sorted(items, key=lambda x: x[1], reverse=True)
    strengths = items_sorted[:top_n]
    weaknesses = items_sorted[-top_n:][::-1]
    return strengths, weaknesses

def study_time_vs_performance_df(df):
    subject_cols = [c for c in df.columns if c not in ("Roll No","Name","Class","Exam","Attendance (%)","Memory Score","Stress Level","Study Duration (minutes)","Study Duration (hours)","Preferred Study Time","Exam Fear")]
    if not subject_cols:
        return pd.DataFrame(columns=["StudyDurationMinutes","AvgScore","Roll No","Name"])
    def avg_row(r):
        vals = [r[c] for c in subject_cols if pd.notna(r.get(c))]
        return float(sum(vals)/len(vals)) if vals else 0.0
    out = pd.DataFrame()
    out["Roll No"] = df["Roll No"]
    out["Name"] = df["Name"]
    if "Study Duration (minutes)" in df.columns:
        out["StudyDurationMinutes"] = pd.to_numeric(df["Study Duration (minutes)"], errors="coerce").fillna(0)
    elif "Study Duration (hours)" in df.columns:
        out["StudyDurationMinutes"] = pd.to_numeric(df["Study Duration (hours)"], errors="coerce").fillna(0) * 60
    else:
        out["StudyDurationMinutes"] = 0
    out["AvgScore"] = df.apply(avg_row, axis=1)
    return out

def personalized_study_advice(student_row):
    adv = {}
    mem = student_row.get("Memory Score", None)
    stress = student_row.get("Stress Level", None)
    att = student_row.get("Attendance (%)", None)
    study_min = student_row.get("Study Duration (minutes)", None)
    if study_min is None and "Study Duration (hours)" in student_row:
        study_min = student_row.get("Study Duration (hours)", 0) * 60

    if mem is not None:
        try:
            m = float(mem)
            if m <= 2:
                adv["Memory"] = "Low memory score — use spaced repetition and short high-focus sessions (20–30 min)."
            elif m <= 3.5:
                adv["Memory"] = "Average memory — active recall + brief nightly revision will help."
            else:
                adv["Memory"] = "Good memory — maintain consistency and use practice tests."
        except:
            adv["Memory"] = "Memory tips: use flashcards, review before sleep."
    else:
        adv["Memory"] = "Memory tips: use spaced repetition and summarise."

    if stress is not None:
        try:
            s = float(stress)
            if s >= 8:
                adv["Stress"] = "High stress — practice short breathing exercises, reduce study marathon sessions, and maintain good sleep."
            elif s >= 5:
                adv["Stress"] = "Moderate stress — schedule short breaks and light exercise."
            else:
                adv["Stress"] = "Stress level OK — maintain routine and light relaxation."
        except:
            adv["Stress"] = "Try relaxation if feeling overwhelmed."
    else:
        adv["Stress"] = "Maintain a calm routine."

    if att is not None:
        try:
            a = float(att)
            if a < 75:
                adv["Attendance"] = "Attendance is low. Prioritize class attendance or catch up with short revision notes daily."
            else:
                adv["Attendance"] = "Good attendance — keep going."
        except:
            adv["Attendance"] = "Keep regular attendance."

    if study_min is not None:
        try:
            sm = float(study_min)
            if sm < 60:
                adv["StudyTime"] = "Study duration seems low — aim for multiple focused sessions (25–45 min)."
            elif sm > 300:
                adv["StudyTime"] = "Long study sessions detected — ensure breaks and active recall."
            else:
                adv["StudyTime"] = "Study time looks reasonable — keep balanced sessions and review regularly."
        except:
            adv["StudyTime"] = "Maintain consistent study schedule."
    return adv

def generate_mind_activities(student_row, n=6):
    seed = _seed_from_student(student_row)
    rng = random.Random(seed)
    pool = [
        "5-minute doodle or sketch",
        "Quick walk around the house/yard",
        "10 deep breaths (box breathing)",
        "Stretch neck & shoulders (3 minutes)",
        "Stand & look outside for 2 minutes",
        "Drink a glass of water + small snack",
        "Play a 2-minute memory card game",
        "Listen to one calming song",
        "Do a 2-min guided grounding exercise",
        "Close eyes and visualise success for 1 min",
        "Organize your study desk for 3 minutes",
        "Practice a tongue-twister (fun!)"
    ]
    rng.shuffle(pool)
    return pool[:n]

def brain_food_recommendations(student_row):
    rec = {}
    rec["Daily Focus Foods"] = ["Oats/oatmeal", "Walnuts", "Blueberries", "Eggs", "Spinach"]
    rec["Revision Snacks"] = ["Almonds", "Dark chocolate (small piece)", "Greek yogurt", "Fruits"]
    rec["Night Before Exam"] = ["Light carbohydrate (rice/oats)", "Banana", "Warm milk (if you tolerate)"]
    rec["Hydration Tips"] = ["Keep a water bottle; sip every 20–30 minutes", "Avoid heavy caffeinated drinks before sleep"]
    rec["Meal Time Schedule"] = [
        "Breakfast: within 1 hour of waking (oats/eggs/fruit)",
        "Mid-morning: small fruit or nuts",
        "Lunch: balanced meal with protein + veggies",
        "Evening (revision time): light snack + water",
        "Dinner: light, avoid heavy fried foods late"
    ]
    stress = student_row.get("Stress Level", None)
    if stress is not None and stress >= 8:
        rec["Note"] = "High stress — include magnesium-rich foods (almonds, spinach) and avoid excessive caffeine."
    return rec
