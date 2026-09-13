import pandas as pd
import os

DATA_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "data",
    "raw",
    "osha_4470.xlsx"
)

print("=" * 70)
print("INNOMINDS - REAL SAFETY DATASET INSPECTION")
print("=" * 70)

print("\nLoading dataset...")

df = pd.read_excel(DATA_PATH)

print("\nDataset loaded successfully!")

print("\n" + "=" * 70)
print("1. DATASET SIZE")
print("=" * 70)

print("Rows    :", df.shape[0])
print("Columns :", df.shape[1])

print("\n" + "=" * 70)
print("2. COLUMN NAMES")
print("=" * 70)

for i, column in enumerate(df.columns, start=1):
    print(f"{i}. {column}")

print("\n" + "=" * 70)
print("3. DATA TYPES")
print("=" * 70)

print(df.dtypes)

print("\n" + "=" * 70)
print("4. MISSING VALUES")
print("=" * 70)

missing = df.isnull().sum()

for column, count in missing.items():
    if count > 0:
        print(f"{column}: {count}")

print("\n" + "=" * 70)
print("5. FIRST 5 RECORDS")
print("=" * 70)

print(df.head().to_string())

print("\n" + "=" * 70)
print("6. UNIQUE VALUES / CATEGORIES")
print("=" * 70)

for column in df.columns:
    if df[column].nunique() <= 20:
        print(f"\n{column}")
        print(df[column].value_counts(dropna=False).head(20))

print("\n" + "=" * 70)
print("7. TEXT COLUMNS")
print("=" * 70)

for column in df.columns:
    if df[column].dtype == "object":
        print(
            f"{column}: "
            f"average length = "
            f"{df[column].dropna().astype(str).str.len().mean():.1f}"
        )

print("\n" + "=" * 70)
print("INSPECTION COMPLETE")
print("=" * 70)