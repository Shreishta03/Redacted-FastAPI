import pandas as pd
from io import BytesIO

def get_csv_columns(file_bytes: bytes) -> list[str]:
    df = pd.read_csv(BytesIO(file_bytes), encoding="utf-8-sig")
    df.columns = df.columns.str.strip()
    return df.columns.tolist()

def extract_redacted_csv_data(
    file_bytes: bytes,
    selected_columns: list[str]
) -> tuple[list[str], list, int]:
    df = pd.read_csv(BytesIO(file_bytes), encoding="utf-8-sig")
    df.columns = df.columns.str.strip()

    missing = set(selected_columns) - set(df.columns)
    if missing:
        raise ValueError(f"Invalid columns selected: {missing}")

    entity_count = len(df) * len(selected_columns)

    for col in selected_columns:
        df[col] = "[REDACTED]"

    headers = df.columns.tolist()
    rows = df.values.tolist()

    return headers, rows, entity_count

def get_redacted_csv_preview(
    file_bytes: bytes,
    selected_columns: list[str],
    limit: int = 5
) -> dict:
    df = pd.read_csv(BytesIO(file_bytes), encoding="utf-8-sig", nrows=limit)
    df.columns = df.columns.str.strip()

    missing = set(selected_columns) - set(df.columns)
    if missing:
        raise ValueError(f"Invalid columns selected: {missing}")

    for col in selected_columns:
        if col in df.columns:
            df[col] = "[REDACTED]"

    return {
        "headers": df.columns.tolist(),
        "rows": df.values.tolist()
    }
