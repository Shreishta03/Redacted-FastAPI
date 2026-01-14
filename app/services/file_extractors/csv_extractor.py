import pandas as pd
from io import BytesIO

def get_csv_columns(file_bytes: bytes) -> list[str]:
    df = pd.read_csv(BytesIO(file_bytes), encoding="utf-8-sig")
    df.columns = df.columns.str.strip()
    return df.columns.tolist()


def extract_selected_columns_as_text(
    file_bytes: bytes,
    selected_columns: list[str]
) -> str:
    df = pd.read_csv(BytesIO(file_bytes), encoding="utf-8-sig")
    df.columns = df.columns.str.strip()

    missing = set(selected_columns) - set(df.columns)
    if missing:
        raise ValueError(f"Invalid columns selected: {missing}")

    rows = []
    for _, row in df[selected_columns].iterrows():
        parts = []
        for col, val in row.items():
            parts.append(f"{col} is {val}")
        rows.append(". ".join(parts) + ".")

    return "\n".join(rows)
