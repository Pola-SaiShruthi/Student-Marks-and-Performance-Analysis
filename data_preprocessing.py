# data_preprocessing.py
# Load and normalize the CSV, provide helper data-access functions.

import pandas as pd
import os
import numpy as np

def _clean_col_name(c: str) -> str:
    s = str(c).strip()
    s = s.replace('%',' percent ').replace('/',' ').replace('-',' ').replace('(',' ').replace(')',' ')
    s = s.replace('.', ' ').replace('_', ' ').lower()
    s = " ".join(s.split())
    return s

def _canonical_map(col: str):
    """Map many variants to canonical column names used by the app."""
    c = _clean_col_name(col)
    if c in ("roll", "roll no", "rollno", "roll number", "roll_number"):
        return "Roll No"
    if c in ("name", "student name", "student"):
        return "Name"
    if "class" == c or c.startswith("class "):
        return "Class"
    if "term" in c or "exam" in c:
        return "Exam"
    if "attendance" in c:
        return "Attendance (%)"
    if "math" in c or "mathematics" in c:
        return "Math"
    if "science" in c:
        return "Science"
    if "english" in c:
        return "English"
    if "history" in c:
        return "History"
    if "memory" in c and "score" in c:
        return "Memory Score"
    if "stress" in c and "level" in c:
        return "Stress Level"
    if "study" in c and ("min" in c or "minute" in c):
        return "Study Duration (minutes)"
    if "study" in c and ("hr" in c or "hour" in c):
        return "Study Duration (hours)"
    if "preferred" in c and "time" in c:
        return "Preferred Study Time"
    if "exam fear" in c or (c in ("fear",) and "exam" in col.lower()):
        return "Exam Fear"
    return col

def load_data(filepath="student_data_raw_fixed.csv"):
    """
    Load CSV and canonicalize column names.
    Coalesce columns that map to the same canonical name to avoid duplicates.
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"CSV file not found at: {filepath}\nPlace student_data_raw_fixed.csv in the same folder or run the dataset generator.")
    df_raw = pd.read_csv(filepath)

    # Map originals -> canonical
    col_map = {c: _canonical_map(c) for c in df_raw.columns}
    canon_to_orig = {}
    for orig, canon in col_map.items():
        canon_to_orig.setdefault(canon, []).append(orig)

    # Build new DataFrame by coalescing columns that map to same canonical name
    new_cols = {}
    for canon, origs in canon_to_orig.items():
        if len(origs) == 1:
            new_cols[canon] = df_raw[origs[0]]
        else:
            # coalesce: take first non-null value across the originals
            s = df_raw[origs[0]].copy()
            for o in origs[1:]:
                s = s.combine_first(df_raw[o])
            new_cols[canon] = s

    df = pd.DataFrame(new_cols)

    # Ensure Roll No exists
    if "Roll No" not in df.columns:
        df.insert(0, "Roll No", range(1, len(df) + 1))

    # Ensure Name exists
    if "Name" not in df.columns:
        for alt in ["Student Name", "Student"]:
            if alt in df.columns:
                df["Name"] = df[alt]
                break
        else:
            df["Name"] = df["Roll No"].astype(str)

    # Attendance numeric
    if "Attendance (%)" in df.columns:
        df["Attendance (%)"] = pd.to_numeric(df["Attendance (%)"], errors="coerce").fillna(0)

    # If Study Duration (hours) present but minutes missing, convert
    if "Study Duration (hours)" in df.columns and "Study Duration (minutes)" not in df.columns:
        df["Study Duration (minutes)"] = pd.to_numeric(df["Study Duration (hours)"], errors="coerce").fillna(0) * 60

    # Try to coerce non-meta columns to numeric where possible
    meta = {"Roll No", "Name", "Class", "Exam", "Attendance (%)",
            "Memory Score", "Stress Level", "Study Duration (minutes)", "Study Duration (hours)",
            "Preferred Study Time", "Exam Fear"}
    for c in df.columns:
        if c not in meta:
            try:
                df[c] = pd.to_numeric(df[c], errors="coerce")
            except Exception:
                pass

    # final tidy: fill simple NaNs for numeric columns with sensible defaults (optional)
    # Note: don't force-fill textual meta columns
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    df[numeric_cols] = df[numeric_cols].fillna(0)

    return df

def get_student_list(df):
    """Return list of display strings 'Name (Roll: X)' in df order."""
    out = []
    for _, row in df.iterrows():
        rn = row.get("Roll No", "")
        name = row.get("Name", "")
        try:
            rn_display = int(rn)
        except:
            rn_display = rn
        out.append(f"{name} (Roll: {rn_display})")
    return out

def get_student_by_roll(df, roll):
    try:
        roll = int(roll)
    except Exception:
        return None
    mask = df["Roll No"] == roll
    if mask.any():
        return df.loc[mask].iloc[0]
    return None

def get_student_by_name(df, name):
    mask = df["Name"].astype(str) == str(name)
    if mask.any():
        return df.loc[mask].iloc[0]
    return None

def get_subject_columns(df):
    """Return numeric subject columns (excluding known meta columns)."""
    meta = {"Roll No", "Name", "Class", "Exam", "Attendance (%)",
            "Memory Score", "Stress Level", "Study Duration (minutes)", "Study Duration (hours)",
            "Preferred Study Time", "Exam Fear"}
    subject_cols = []
    for c in df.columns:
        if c in meta:
            continue
        if pd.api.types.is_numeric_dtype(df[c]):
            subject_cols.append(c)
    return subject_cols

def class_average(df):
    subs = get_subject_columns(df)
    if not subs:
        return {}
    return df[subs].mean().to_dict()
