import pandas as pd
import numpy as np

# Show all columns properly
pd.set_option('display.max_columns', None)
pd.set_option('display.width', None)


def preprocess_data(file_path):
    # Step 1: Load raw dataset
    df = pd.read_csv(file_path)

    # Step 2: Remove extra unnamed columns (caused by commas or misalignment)
    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]

    # Step 3: Clean column names
    df.columns = [col.strip() for col in df.columns]

    # Step 4: Standardize column names
    rename_map = {
        "Roll No": "Roll No",
        "Name": "Name",
        "Class": "Class",
        "Exam": "Exam",
        "Attendance (%)": "Attendance (%)",
        "Math": "Mathematics",
        "Science": "Science",
        "English": "English",
        "History": "History",
        "Memory Score": "Memory Score (1-5)",
        "Stress Level": "Stress Level (1-5)",
        "Study Duration (minutes)": "Study Duration (minutes)",
        "Preferred Study Time": "Preferred Study Time",
        "Exam Fear": "Exam Fear",
        "Exam Fear)": "Exam Fear",
        "Exam Fear (Yes/No)": "Exam Fear"
    }

    # Apply rename
    df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns}, inplace=True)

    # Step 5: Handle missing values and cleanup
    df.replace(["N/A", "NaN", "None", "--", "", " "], np.nan, inplace=True)

    # Fill text columns with placeholders and numbers with 0
    for col in df.columns:
        if df[col].dtype == 'O':  # Text
            df[col] = df[col].fillna("Unknown")
        else:  # Numeric
            df[col] = df[col].fillna(0)

    # Step 6: Convert numeric columns properly
    numeric_cols = [
        "Mathematics", "Science", "English", "History",
        "Attendance (%)", "Memory Score (1-5)", "Stress Level (1-5)",
        "Study Duration (minutes)"
    ]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    # Step 7: Clean text columns formatting
    if "Preferred Study Time" in df.columns:
        df["Preferred Study Time"] = df["Preferred Study Time"].astype(str).str.strip().str.capitalize()

    if "Exam Fear (Yes/No)" in df.columns:
        df["Exam Fear (Yes/No)"] = df["Exam Fear (Yes/No)"].astype(str).str.strip().str.upper()

    return df


if __name__ == "__main__":
    file_path = "student_data_raw_fixed.csv"

    # Before preprocessing
    df_raw = pd.read_csv(file_path)
    print("📊 BEFORE PREPROCESSING (RAW DATA):")
    print(df_raw.head(10).to_string(index=False))
    print("\n---\n")

    # After preprocessing
    df_cleaned = preprocess_data(file_path)
    print("✅ AFTER PREPROCESSING (CLEANED DATA):")
    print(df_cleaned.head(10).to_string(index=False))

    # Save cleaned dataset
    df_cleaned.to_csv("student_data_cleaned.csv", index=False)
    print("\n💾 Cleaned data saved as 'student_data_cleaned.csv'")
