"""Extrait les noms et IDs de toutes les entités Snétor depuis BUT000."""

from pathlib import Path

import pandas as pd

BUT000 = Path(r"\\interfacessap.file.core.windows.net\interfacess4p\data_mdm_export\BP_BUT000.csv")

SNETOR_KEYWORDS = [
    "SNETOR",
    "SNETOR OVERSEAS",
    "SNETOR OVERSEAS SAS,"
    "SNETOR MAROC",
    "EIXO SNETOR BRASIL",
    "SNETOR ECUADOR",
    "SNETOR FRANCE",
    "OZYANCE",
    "SNETOR KOREA",
    "SNETOR EGYPT",
    "SNETOR SOUTH AFRICA",
    "SNETOR COLOMBIA",
    "SNETOR CHILE",
    "SNETOR UK LTD",
    "TECNOPOL SNETOR ITALIA",
    "SNETOR SHANGHAI",
    "SNETOR WEST AFRICA LTD",
    "SNETOR EAST AFRICA",
    "SNETOR PERU",
    "SNETOR USA",
    "SNETOR BENELUX",
    "OZYANCE ITALIA",
    "SNETOR DISTRIBUTION UGANDA",
    "SNETOR MIDDLE EAST",
    "COANSA SNETOR COSTA RICA",
    "COANSA SNETOR EL SALVADOR",
    "SNETOR NORDEN",
    "LEONARDI",
    "SNETOR MUSQAT",
    "COANSA SNETOR GUATEMALA",
    "SNETOR MEXICO",
    "SNETOR GERMANY GMBH",
    "TECNOPOL SNETOR IBERIA",
    "SNETOR EASTERN EUROPE",
    "SNETOR BALKAN",
    "MEG SNETOR TURKIYE",
    "SNETOR LOGISTICS"
    ]


def load_but000(path: Path = BUT000) -> pd.DataFrame:
    df = pd.read_csv(path, dtype=str, sep=";", on_bad_lines="skip", engine="python")
    df = df.iloc[:, [0, 7]].copy()
    df.columns = ["BP", "Name"]

    df["BP"] = df["BP"].fillna("").astype(str).str.strip().str.lstrip("0")
    df["Name"] = df["Name"].fillna("").astype(str).str.strip()
    return df


def get_snetor_entities(df: pd.DataFrame) -> pd.DataFrame:
    mask = df["Name"].str.upper().str.contains(
        "|".join(SNETOR_KEYWORDS), na=False
    )
    return df[mask].sort_values("Name").reset_index(drop=True)


def main() -> None:
    df = load_but000()
    snetor = get_snetor_entities(df)

    print(f"{len(snetor)} entités Snétor trouvées:\n")
    print(snetor.to_string(index=False))

    out = Path(__file__).parent / "snetor_ids.xlsx"
    snetor.to_excel(out, index=False)
    print(f"\nExporté dans : {out}")


if __name__ == "__main__":
    main()
