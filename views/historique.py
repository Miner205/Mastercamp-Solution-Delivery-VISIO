from datetime import date
from dateutil.relativedelta import relativedelta
import pandas as pd
import streamlit as st

from database import get_db_as_df


def show():
    st.title("Historique")
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

    cols = ("filename", "initial_filename", "filepath", "upload_date", "manual_annotation",
            "ai_annotation", "ai_confidence", "file_size", "width",
            "height", "avg_r", "avg_g", "avg_b", "avg_l", "contrast")
    cols_config = dict()
    cols_config["manual_annotation"] = st.column_config.TextColumn(width=105)
    cols_config["filename"] = st.column_config.TextColumn(width="medium")
    cols_config["initial_filename"] = st.column_config.TextColumn(width="medium")
    cols_config["filepath"] = st.column_config.TextColumn(width="medium")
    cols_config['avg_l'] = st.column_config.NumberColumn(label="avg_luminance")
    st.dataframe(df.style.map(color_fct, subset=['manual_annotation']).map(color_red, subset=['avg_r', 'min_r', 'max_r']).map(color_green, subset=['avg_g', 'min_g', 'max_g']).map(color_blue, subset=['avg_b', 'min_b', 'max_b']), height="content", column_order=cols, column_config=cols_config)


def color_fct(val):
    if val == "Vide":
        color = 'green'
    elif val=="Pleine":
        color = 'red'
    else:
        color = 'black'
    return f'background-color: {color}'
def color_red(r=0, g=0, b=0):
    color = f"rgb({r}, {g}, {b})"
    return f'background-color: {color}'
def color_green(g=0, r=0, b=0):
    color = f"rgb({r}, {g}, {b})"
    return f'background-color: {color}'
def color_blue(b=0, g=0, r=0):
    color = f"rgb({r}, {g}, {b})"
    return f'background-color: {color}'
