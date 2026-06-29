import math
import os
import pandas as pd
import sqlite3
import streamlit as st


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

    filter_class = st.multiselect("Filtrer - annotation manuelle", ["Vide", "Pleine"])
    if filter_class:
        df = df[df["manual_annotation"].isin(filter_class)]

    total_images = len(df)
    total_pages = math.ceil(total_images / images_per_page)

    page = st.number_input("Page", min_value=1, max_value=max(total_pages, 1), value=1)

    start = (page - 1) * images_per_page
    end = start + images_per_page

    page_df = df.iloc[start:end]

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

    col1, col2, col3 = st.columns([1, 2, 1])
    with col1:
        if page > 1:
            if st.button("<- Précédent"):
                page -= 1
    with col3:
        if page < total_pages:
            if st.button("Suivant ->"):
                page += 1
