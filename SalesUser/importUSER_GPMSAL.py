import pandas as pd

PATH = r"\\interfacessap.file.core.windows.net\interfacess4p\data_mdm_export\BP_USER_GPMSAL.csv"

def load_user_gpmsal(path: str = PATH) -> pd.DataFrame:
    df = pd.read_csv(path, dtype=str, sep=";")
    df = df.iloc[:, [0,1]]
    df.columns = ["BP", "Affected User"]
    df["BP"] = df["BP"].str.strip().str.lstrip("0")
    return df

if __name__ == "__main__":
    df = load_user_gpmsal()
    df = df.sort_values(by=["BP"]).reset_index(drop=True)
    print(f"Loaded {len(df)} rows and {len(df.columns)} columns from {PATH}")
    print(df.head())
    print(df.tail())