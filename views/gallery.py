import math
from datetime import date
from dateutil.relativedelta import relativedelta
import pandas as pd
import streamlit as st
from streamlit_extras.pagination import pagination
from streamlit_scroll_to_top import scroll_to_here

from database import get_db_as_df


def show():
    if "scroll_to_top" not in st.session_state:
        st.session_state.scroll_to_top = False
    if st.session_state.scroll_to_top:
        scroll_to_here(0, key="top")
        st.session_state.scroll_to_top = False

    st.title("Gallery d'images")
    df = get_db_as_df()

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
        start_date = st.date_input("Du", value=date.today()-relativedelta(months=1))
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
        ascending = st.checkbox("Ordre croissant", value=True)

    show_none = st.checkbox("Afficher les images sans annotation (None)", value=True)

    if not show_none:
        df = df[df["manual_annotation"].notna() & df["ai_annotation"].notna()]
    if search:
        df = df[df["filename"].str.contains(search, case=False)]
    if manual_annotation:
        df = df[df["manual_annotation"].isin(manual_annotation)]
    if ai_annotation:
        df = df[df["ai_annotation"].isin(ai_annotation)]
    if not show_none:
        df = df[df["ai_confidence"] >= confidence]
    else:
        df = df[(df["ai_confidence"].isna()) | (df["ai_confidence"] >= confidence)]
    df["upload_date"] = pd.to_datetime(df["upload_date"])
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

    images_per_page = st.selectbox(
        "Nombre d'images par page",
        [9, 21, 51, 99], index=0)

    total_images = len(df)
    total_pages = math.ceil(total_images / images_per_page)

    if total_pages > 0:
        page = pagination(
            num_pages=total_pages,
            max_visible_pages=7,
            key="interactive_pagination_top",
        )
    else:
        page = 0
    st.markdown(f"### Page {page}/{total_pages}")

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

    _, mid, _ = st.columns([3, 2, 2])
    with mid:
        if page and st.button("⬆️ Retour en haut"):
            st.session_state.scroll_to_top = True
            st.rerun()
