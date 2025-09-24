import pandas as pd

def preprocess_data(file_path):
    # Read dataset
    df = pd.read_csv(file_path)

    # Convert Roll to integer
    if "Roll" in df.columns:
        df["Roll"] = df["Roll"].astype(int)

    # Fill any missing values with 0
    df = df.fillna(0)

    # Convert percentage columns to numeric
    if "Attendance" in df.columns:
        df["Attendance"] = pd.to_numeric(df["Attendance"], errors="coerce").fillna(0)

    if "Memory_Score" in df.columns:
        df["Memory_Score"] = pd.to_numeric(df["Memory_Score"], errors="coerce").fillna(0)

    return df


# Run directly when executed
if __name__ == "__main__":
    file_path = r"D:\DAV(py)\PBL_DAV\student_data_v3.csv"

    # Before preprocessing
    df_before = pd.read_csv(file_path)
    print("📌 BEFORE Preprocessing:")
    print(df_before.head())   # show first 5 rows
    print("\n---\n")

    # After preprocessing
    df_after = preprocess_data(file_path)
    print("✅ AFTER Preprocessing:")
    print(df_after.head())    # show first 5 rows

# Compare
diff = df_before.compare(df_after)
print("✅ COMPARING:")
print(diff)