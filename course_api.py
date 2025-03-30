from fastapi import FastAPI, Query
import pandas as pd

app = FastAPI()

# Load CSV file
csv_path = r"C:\Users\7890v\Course Recommned\Cleaned_Online_Courses1.csv"

try:
    df = pd.read_csv(csv_path)
    df.fillna("", inplace=True)  # Replace NaN with empty strings to avoid errors
    print("CSV Loaded Successfully!")
    print("Columns in CSV:", df.columns.tolist())
except Exception as e:
    print("Error loading CSV:", e)
    df = pd.DataFrame()  # Empty DataFrame if loading fails

@app.get("/courses/")
def get_courses(
    title: str = Query(None, description="Search by course title"),
    category: str = Query(None, description="Search by category"),
    site: str = Query(None, description="Search by platform")
):
    """API to filter courses based on title, category, or site"""
    if df.empty:
        return {"error": "Data not loaded"}

    results = df.copy()

    # Apply filters safely
    if title and "Title" in df.columns:
        results = results[results["Title"].str.contains(title, case=False, na=False)]
    if category and "Category" in df.columns:
        results = results[results["Category"].str.contains(category, case=False, na=False)]
    if site and "Site" in df.columns:
        results = results[results["Site"].str.contains(site, case=False, na=False)]

    return results.to_dict(orient="records")
