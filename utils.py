from docx import Document
import pandas as pd

from docx import Document
import pandas as pd

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


def read_first_table(docx_file):
    doc = Document(docx_file)
    table = doc.tables[0]

    rows = [[cell.text.strip() for cell in row.cells] for row in table.rows]

    # 1️⃣ find the real header row
    header_idx = None
    for i, row in enumerate(rows):
        if any("week" in cell.lower() for cell in row):
            header_idx = i
            break

    if header_idx is None:
        raise ValueError("Geen geldige header gevonden in studiewijzer")

    headers = rows[header_idx]
    data = rows[header_idx + 1 :]

    # 2️⃣ enforce unique column names
    headers = make_unique(headers)

    df = pd.DataFrame(data, columns=headers)

    # 3️⃣ drop fully empty rows
    df = df.dropna(how="all")

    return df

