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
    st.dataframe(df)
