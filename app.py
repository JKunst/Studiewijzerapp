import streamlit as st
import pandas as pd
from utils import read_first_table

st.set_page_config(page_title="Studiewijzers", layout="wide")

if "studiewijzers" not in st.session_state:
    st.session_state.studiewijzers = {}

pagina = st.sidebar.radio(
    "Navigatie",
    ["Upload", "Bewerken", "Overzicht"]
)

# ─────────────────────────────
# PAGINA 1 – UPLOAD
# ─────────────────────────────
if pagina == "Upload":
    st.title("📤 Studiewijzers uploaden")

    uploads = st.file_uploader(
        "Upload studiewijzers (.docx)",
        type="docx",
        accept_multiple_files=True
    )

    if uploads:
        for file in uploads:
            df = read_first_table(file)

            # Vaknaam simpel afleiden uit bestandsnaam
            vak = file.name.split("-")[1].strip() if "-" in file.name else file.name
            st.session_state.studiewijzers[vak] = df

        st.success("Studiewijzers succesvol ingelezen!")
        st.write("Ga naar **Bewerken** om aanpassingen te doen.")

# ─────────────────────────────
# PAGINA 2 – BEWERKEN
# ─────────────────────────────
elif pagina == "Bewerken":
    st.title("✏️ Studiewijzers bewerken")

    if not st.session_state.studiewijzers:
        st.warning("Nog geen studiewijzers geüpload.")
    else:
        vak = st.selectbox(
            "Kies vak",
            st.session_state.studiewijzers.keys()
        )

        df = st.session_state.studiewijzers[vak]

        edited_df = st.data_editor(
            df,
            use_container_width=True,
            num_rows="dynamic"
        )

        st.session_state.studiewijzers[vak] = edited_df
        st.success("Wijzigingen opgeslagen")

# ─────────────────────────────
# PAGINA 3 – OVERZICHT
# ─────────────────────────────
elif pagina == "Overzicht":
    st.title("📚 Overzicht per vak")

    if not st.session_state.studiewijzers:
        st.info("Nog geen data beschikbaar.")
    else:
        for vak, df in st.session_state.studiewijzers.items():
            st.subheader(vak)
            st.dataframe(df, use_container_width=True)
