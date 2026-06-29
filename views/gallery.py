import math
import os
import pandas as pd
import sqlite3
import streamlit as st
#import streamlit_extras


DB_NAME = "visio_database.db"
DATA_FOLDER = "Data/web_app"


def show():
    st.title("Gallery d'images")

    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT * FROM images ORDER BY id DESC", conn)
    conn.close()

    images_per_page = st.selectbox(
        "Nombre d'images par page",
        [3, 10, 20, 50, 100], index=0)

    ##Partie Filtres
    st.subheader("Filtres")
    col1, col2, col3 = st.columns(3)
    with col1:
        search = st.text_input("Nom de l'image", placeholder="Ex : img_001")
    with col2:
        manual_annotation = st.multiselect("Annotation manuelle", ["Vide", "Pleine"])
    with col3:
        ai_annotation = st.multiselect("Annotation IA", ["Vide", "Pleine"])

    col4, col5, col6 = st.columns(3)
    with col4:
        confidence = st.slider("Confiance IA minimale (%)", 0, 100, 0)
    with col5:
        start_date = st.date_input("Du")
    with col6:
        end_date = st.date_input("Au")

    col7, col8 = st.columns(2)
    with col7:
        sort_by = st.selectbox(
            "Trier par",
            [
                "Date",
                "Confiance IA",
                "Nom",
                "Annotation IA",
                "Annotation manuelle"])
    with col8:
        ascending = st.checkbox("Ordre croissant", value=False)

    show_none = st.checkbox("Afficher les images sans annotation (None)", value=True)

    if not show_none:
        df = df[df["manual_annotation"].notna() & df["ai_annotation"].notna()]
    if search:
        df = df[df["filename"].str.contains(search, case=False)]
    if manual_annotation:
        df = df[df["manual_annotation"].isin(manual_annotation)]
    if ai_annotation:
        df = df[df["ai_annotation"].isin(ai_annotation)]
    print(0, df)
    if not show_none:
        df = df[df["ai_confidence"] >= confidence]
    else:
        df = df[(df["ai_confidence"].isna()) | (df["ai_confidence"] >= confidence)]
    print(1, df)
    df["upload_date"] = pd.to_datetime(df["upload_date"])
    print(2, df)
    df = df[
        (df["upload_date"].dt.date >= start_date) &
        (df["upload_date"].dt.date <= end_date)]

    columns = {
        "Date": "upload_date",
        "Confiance IA": "ai_confidence",
        "Nom": "filename",
        "Annotation IA": "ai_annotation",
        "Annotation manuelle": "manual_annotation"}
    df = df.sort_values(by=columns[sort_by], ascending=ascending)
    ##Fin Partie Filtres

    total_images = len(df)
    total_pages = math.ceil(total_images / images_per_page)

    if "page" not in st.session_state:
        st.session_state.page = 0

    def pagination(position):
        c1, c2, c3 = st.columns([1, 2, 1])
        with c1:
            if st.button("<-", disabled=st.session_state.page == 0, key=f"prev_{position}"):
                st.session_state.page -= 1
                st.rerun()
        with c2:
            #page = st.selectbox("Page", options=list(range(total_pages)), format_func=lambda x: f"{x + 1}/{total_pages}", key="page", label_visibility="collapsed")
            st.markdown(f"### Page {st.session_state.page + 1}/{total_pages}")
            '''if page != st.session_state.page:
                st.session_state.page = page
                st.rerun()'''
        with c3:
            if st.button("->", disabled=st.session_state.page == total_pages-1, key=f"next_{position}"):
                st.session_state.page += 1
                st.rerun()

    start = st.session_state.page * images_per_page
    end = start + images_per_page

    page_df = df.iloc[start:end]

    pagination("top")

    cols = st.columns(3)
    for idx, row in enumerate(page_df.itertuples()):
        col = cols[idx % 3]
        conf = row.ai_confidence if row.ai_confidence is not None else 0
        with col:
            st.image(row.filepath, width="stretch")
            st.markdown(f"**{row.filename}**")
            st.write(f"📅 {row.upload_date}")
            st.write(f"Annotation manuelle : {row.manual_annotation}")
            st.write(f"Annotation IA : {row.ai_annotation}")
            st.progress(conf / 100)
            st.caption(f"Score de confiance : {conf:.1f}%")

    pagination("bottom")

    '''col1, col2, col3 = st.columns([1, 2, 1])
    with col1:
        if page > 1:
            if st.button("<- Précédent"):
                page -= 1
    with col3:
        if page < total_pages:
            if st.button("Suivant ->"):
                page += 1'''
