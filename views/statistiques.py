import os
import pandas as pd
import sqlite3
import streamlit as st

from database import get_db_as_df

DB_NAME = "visio_database.db"
DATA_FOLDER = "Data/web_app"


def show():
    st.title("Statistiques")
    df = get_db_as_df()
    st.metric("Nombre d'images analysées :", len(df))
    st.markdown("""<div><br><br></div>""", unsafe_allow_html=True)
    if len(df) > 0:
        st.bar_chart(df["manual_annotation"].value_counts(), x_label="Annotation manuelle")
