import streamlit as st
from utils import (
    read_first_table,
    merge_studiewijzers_by_week,
    get_week_details
)
from db import (
    init_db,
    save_studiewijzer,
    load_all_studiewijzers,
    delete_studiewijzer
)

st.set_page_config(page_title="Studiewijzers", layout="wide")

# ─────────────────────────────
# INIT
# ─────────────────────────────
init_db()
studiewijzers = load_all_studiewijzers()

pagina = st.sidebar.radio(
    "Navigatie",
    ["Upload", "Bewerken", "Overzicht", "Weekoverzicht", "Weekdetail", "Beheer"]
)

# ─────────────────────────────
# SIDEBAR – VAK SELECTIE
# ─────────────────────────────
st.sidebar.markdown("### 📚 Vakken")

selected_vakken = []

for vak in studiewijzers.keys():
    checked = st.sidebar.checkbox(vak, value=True, key=f"vak_{vak}")
    if checked:
        selected_vakken.append(vak)

if st.sidebar.button("Alles selecteren"):
    for vak in studiewijzers:
        st.session_state[f"vak_{vak}"] = True

if st.sidebar.button("Alles uit"):
    for vak in studiewijzers:
        st.session_state[f"vak_{vak}"] = False

# Helper
def get_filtered():
    return {
        vak: df
        for vak, df in studiewijzers.items()
        if vak in selected_vakken
    }

# ─────────────────────────────
# PAGINA – UPLOAD
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
            vak = file.name.split("-")[1].strip() if "-" in file.name else file.name
            save_studiewijzer(vak, df)

        st.success("Studiewijzers opgeslagen in database ✔")
        st.rerun()

# ─────────────────────────────
# PAGINA – BEWERKEN
# ─────────────────────────────
elif pagina == "Bewerken":
    st.title("✏️ Studiewijzers bewerken")

    if not studiewijzers:
        st.info("Geen studiewijzers gevonden.")
    else:
        vak = st.selectbox("Kies vak", studiewijzers.keys())
        df = studiewijzers[vak]

        edited_df = st.data_editor(
            df,
            use_container_width=True,
            num_rows="dynamic"
        )

        st.markdown("### 🧹 Kolommen beheren")

        cols_to_remove = st.multiselect(
            "Verwijder kolommen",
            edited_df.columns
        )

        if cols_to_remove:
            edited_df = edited_df.drop(columns=cols_to_remove)

        st.markdown("### 🗑️ Rijen beheren")
        # 1️⃣ kies op basis van een kolom (bijv. Week)
        if "Week" in edited_df.columns:
            rows_to_remove = st.multiselect(
                "Verwijder rijen op Week",
                edited_df["Week"].tolist()
            )
            if rows_to_remove:
                edited_df = edited_df[~edited_df["Week"].isin(rows_to_remove)]
        else:
            # alternatief: selecteer op index als Week niet bestaat
            rows_to_remove = st.multiselect(
                "Verwijder rijen op index",
                edited_df.index.tolist()
            )
            if rows_to_remove:
                edited_df = edited_df.drop(index=rows_to_remove)
                
        if st.button("💾 Opslaan"):
            save_studiewijzer(vak, edited_df)
            st.success("Wijzigingen opgeslagen")
            st.rerun()

# ─────────────────────────────
# PAGINA – OVERZICHT
# ─────────────────────────────
elif pagina == "Overzicht":
    st.title("📚 Overzicht per vak")

    for vak, df in studiewijzers.items():
        st.subheader(vak)
        st.dataframe(df, use_container_width=True)

# ─────────────────────────────
# PAGINA – WEEKOVERZICHT
# ─────────────────────────────
elif pagina == "Weekoverzicht":
    st.title("🗓️ Weekoverzicht")

    if len(selected_vakken) < 1:
        st.warning("Selecteer minimaal één vak.")
        st.stop()

    merged_df = merge_studiewijzers_by_week(get_filtered())

    st.data_editor(
        merged_df,
        use_container_width=True,
        disabled=True
    )

# ─────────────────────────────
# PAGINA – WEEKDETAIL
# ─────────────────────────────
elif pagina == "Weekdetail":
    st.title("📖 Weekdetail")

    if len(selected_vakken) < 1:
        st.warning("Selecteer minimaal één vak.")
        st.stop()

    filtered = get_filtered()
    merged_df = merge_studiewijzers_by_week(filtered)

    week = st.selectbox("Selecteer week", merged_df["Week"])

    details = get_week_details(filtered, week)

    for vak, content in details.items():
        with st.container(border=True):
            st.markdown(f"### 📚 {vak}")
            if content["les"]:
                st.markdown(f"**📘 In de les**  \n{content['les']}")
            if content["taak"]:
                st.markdown(f"**📝 Weektaak**  \n{content['taak']}")

# ─────────────────────────────
# PAGINA – BEHEER (VERWIJDEREN)
# ─────────────────────────────
elif pagina == "Beheer":
    st.title("🗑️ Studiewijzers beheren")

    if not studiewijzers:
        st.info("Geen studiewijzers om te verwijderen.")
    else:
        vak = st.selectbox("Selecteer vak", studiewijzers.keys())

        st.warning(f"Dit verwijdert **{vak}** permanent.")

        if st.button("❌ Verwijderen"):
            delete_studiewijzer(vak)
            st.success(f"{vak} verwijderd")
            st.rerun()
