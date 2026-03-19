import pandas as pd
from pathlib import Path

PATH = Path(r"C:\Users\K.luce\OneDrive - SNETOR\Documents\partners\reformateName\BUT000_Fournisseurs CN à modifier_PROD.xlsx")


def load_base_dataset(path: Path = PATH) -> pd.DataFrame:
    df = pd.read_excel(path, dtype=str)
    return df

if __name__ == "__main__":
    df = load_base_dataset()
    print(f"Loaded {len(df)} rows and {len(df.columns)} columns from {PATH}")
