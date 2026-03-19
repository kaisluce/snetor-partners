import pandas as pd

PATH = r"\\snetor-docs\Users\MDM\000_SOP & INSTRUCTIONS\000_MATRIX\001_BP\Sales Group.xlsx"
SHEET_NAME = "Base do not update"

def import_sales_group():
    try:
        df = pd.read_excel(PATH, sheet_name=SHEET_NAME, dtype=str).iloc[:, [2, 5]].copy()
        df.columns = ["Sales Group", "Affected User"]
        return df
    except Exception as e:
        print(f"Error loading Excel file: {e}")
        return pd.DataFrame()  # Return an empty DataFrame on error

if __name__ == "__main__":
    df = import_sales_group()
    print(f"Loaded {len(df)} rows and {len(df.columns)} columns from {PATH}")
    print(df.head())
