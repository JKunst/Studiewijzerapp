from docx import Document
import pandas as pd

from docx import Document
import pandas as pd
import re

def extract_week_number(value):
    if pd.isna(value):
        return None
    match = re.search(r"\d+", str(value))
    return int(match.group()) if match else None

def make_unique(columns):
    seen = {}
    new_cols = []
    for col in columns:
        if col in seen:
            seen[col] += 1
            new_cols.append(f"{col}_{seen[col]}")
        else:
            seen[col] = 0
            new_cols.append(col)
    return new_cols

def is_week_column(colname: str) -> bool:
    col = colname.lower()
    return "week" in col
def normalize_week_columns(df: pd.DataFrame) -> pd.DataFrame:
    # detecteer alle week-gerelateerde kolommen
    week_cols = [c for c in df.columns if "week" in c.lower()]

    # niks te doen
    if len(week_cols) <= 1:
        return df

    # combineer inhoud van alle weekkolommen
    combined = []

    for _, row in df.iterrows():
        parts = []
        for col in week_cols:
            val = str(row[col]).strip()
            if val and val.lower() != "nan":
                parts.append(val)
        combined.append(" ".join(parts))

    # verwijder oude weekkolommen
    df = df.drop(columns=week_cols)

    # voeg nieuwe Week-kolom toe
    df.insert(0, "Week", combined)

    return df
def read_first_table(docx_file):
    doc = Document(docx_file)
    table = doc.tables[0]

    # 1️⃣ lees alle rijen en combineer cellen met meerdere paragrafen in één string
    rows = []
    for row in table.rows:
        new_row = []
        for cell in row.cells:
            # combineer meerdere paragrafen in één cel met \n
            cell_text = "\n".join(p.text.strip() for p in cell.paragraphs)
            new_row.append(cell_text)
        rows.append(new_row)

    # 2️⃣ vind de header
    header_idx = None
    for i, row in enumerate(rows):
        if any("week" in str(cell).lower() for cell in row):
            header_idx = i
            break

    if header_idx is None:
        raise ValueError("Geen geldige header gevonden in studiewijzer")

    headers = rows[header_idx]
    data = rows[header_idx + 1 :]

    # 3️⃣ enforce unique headers (zorgt dat dubbele kolomnamen geen probleem zijn)
    headers = make_unique(headers)

    # 4️⃣ vul ontbrekende cellen aan zodat elke rij evenveel kolommen heeft als headers
    for i, row in enumerate(data):
        if len(row) < len(headers):
            row.extend([""] * (len(headers) - len(row)))
        elif len(row) > len(headers):
            row = row[: len(headers)]
            data[i] = row

    # 5️⃣ maak DataFrame
    df = pd.DataFrame(data, columns=headers)

    # 6️⃣ drop volledig lege rijen
    df = df.dropna(how="all")

    # 7️⃣ forceer alle kolomnamen naar strings
    df.columns = df.columns.astype(str)

    return df

# def read_first_table(docx_file):
#     doc = Document(docx_file)
#     table = doc.tables[0]
#
#     rows = [[cell.text.strip() for cell in row.cells] for row in table.rows]
#
#     # 1️⃣ find the real header row
#     header_idx = None
#     for i, row in enumerate(rows):
#         if any("week" in cell.lower() for cell in row):
#             header_idx = i
#             break
#
#     if header_idx is None:
#         raise ValueError("Geen geldige header gevonden in studiewijzer")
#
#     headers = rows[header_idx]
#     data = rows[header_idx + 1 :]
#
#     # 2️⃣ enforce unique column names
#     headers = make_unique(headers)
#
#     df = pd.DataFrame(data, columns=headers)
#
#     # 3️⃣ drop fully empty rows
#     df = df.dropna(how="all")
#     #df = normalize_week_columns(df)
#     df.columns = df.columns.astype(str)
#     return df

def merge_studiewijzers_by_week(studiewijzers: dict):
    """
    studiewijzers = {
        "Wiskunde": DataFrame,
        "Nederlands": DataFrame,
        ...
    }
    """

    merged = None

    for vak, df in studiewijzers.items():
        df = df.copy()

        # normalize column names
        df.columns = [c.lower().strip() for c in df.columns]

        # detect columns
        week_col = next(c for c in df.columns if "week" in c)
        les_col = next((c for c in df.columns if "les" in c), None)
        taak_col = next((c for c in df.columns if "taak" in c), None)

        # combine content
        def combine(row):
            parts = []
            if les_col and row.get(les_col):
                parts.append(f"📘 {row[les_col]}")
            if taak_col and row.get(taak_col):
                parts.append(f"📝 {row[taak_col]}")
            return "\n".join(parts)

        df[vak] = df.apply(combine, axis=1)

        df = df[[week_col, vak]]
        df = df.rename(columns={week_col: "Week"})

        if merged is None:
            merged = df
        else:
            if merged['Week'].dtype != df['Week'].dtype:
                # Convert both to string (safe for mixed types)
                merged['Week'] = merged['Week'].astype(str)
                df['Week'] = df['Week'].astype(str)
            merged = pd.merge(
                merged,
                df,
                on="Week",
                how="outer"
            )

    #merged = merged.sort_values("Week").reset_index(drop=True)

    merged["Week_num"] = merged["Week"].apply(extract_week_number)

    merged = (
        merged
        .sort_values("Week_num")
        .drop(columns="Week_num")
        .reset_index(drop=True)
    )
    return merged


def get_week_details(studiewijzers: dict, selected_week):
    """
    Returns:
    {
        "Wiskunde": {
            "les": "...",
            "taak": "..."
        },
        ...
    }
    """

    details = {}

    target_week = extract_week_number(selected_week)

    for vak, df in studiewijzers.items():
        df = df.copy()
        df.columns = [c.lower().strip() for c in df.columns]

        week_col = next(c for c in df.columns if "week" in c)
        les_col = next((c for c in df.columns if "les" in c), None)
        taak_col = next((c for c in df.columns if "taak" in c), None)

        df["week_num"] = df[week_col].apply(extract_week_number)

        row = df[df["week_num"] == target_week]

        if row.empty:
            continue

        row = row.iloc[0]

        details[vak] = {
            "les": row[les_col] if les_col else "",
            "taak": row[taak_col] if taak_col else ""
        }

    return details


