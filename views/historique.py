import os
import pandas as pd
import sqlite3
import streamlit as st

from database import get_db_as_df

DB_NAME = "visio_database.db"
DATA_FOLDER = "Data/web_app"


def show():
    st.title("Historique")
    df = get_db_as_df()
    cols = ("filename", "filepath", "upload_date", "manual_annotation",
            "ai_annotation", "ai_confidence", "file_size", "width",
            "height", "avg_r", "avg_g", "avg_b")
    cols_config = dict()
    cols_config["manual_annotation"] = st.column_config.TextColumn(width=105)
    cols_config["filename"] = st.column_config.TextColumn(width="medium")
    cols_config["filepath"] = st.column_config.TextColumn(width="medium")
    st.dataframe(df.style.map(color_fct, subset=['manual_annotation']).map(color_fct2, subset=['avg_r']).map(color_fct3, subset=['avg_g']).map(color_fct4, subset=['avg_b']), height="content", column_order=cols, column_config=cols_config)


def color_fct(val):
    if val == "Vide":
        color = 'green'
    elif val=="Pleine":
        color = 'red'
    else:
        color = 'black'
    return f'background-color: {color}'
def color_fct2(r=0, g=0, b=0):
    color = f"rgb({r}, {g}, {b})"
    return f'background-color: {color}'
def color_fct3(g=0, r=0, b=0):
    color = f"rgb({r}, {g}, {b})"
    return f'background-color: {color}'
def color_fct4(b=0, g=0, r=0):
    color = f"rgb({r}, {g}, {b})"
    return f'background-color: {color}'
