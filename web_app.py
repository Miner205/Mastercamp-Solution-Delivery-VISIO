import pandas as pd
import os
import sqlite3
import streamlit as st
from streamlit_option_menu import option_menu

from views import accueil, historique, statistiques, gallery
from database import create_database

#from metadata import extract_metadata


DB_NAME = "visio_database.db"

if not os.path.isfile(DB_NAME):
    create_database()

DATA_FOLDER = "Data/web_app"
os.makedirs(DATA_FOLDER, exist_ok=True)


st.set_page_config(layout="wide")

st.markdown("""
<style>
.main {
    background-color: #F7FAF7;
}
.block-container {
    padding-top: 2rem;
}
.card {
    background:white;
    padding:20px;
    border-radius:20px;
    box-shadow:0 2px 8px rgba(0,0,0,0.08);
}
.green-title {
    color:#1B5E20;
    font-size:32px;
    font-weight:700;
}
.result-ok {
    color:#1B5E20;
    font-size:30px;
    font-weight:700;
}
.result-full {
    color:#E53935;
    font-size:30px;
    font-weight:700;
}
</style>
""", unsafe_allow_html=True)


with st.sidebar:
    selected = option_menu(
        "VISIO",
        ["Accueil - Upload",
                "Gallery",
                "Historique",
                "Statistiques",
                "À propos"],
        icons=["house",
                "image",
                "clock-history",
                "bar-chart",
                "info-circle"],
        default_index=0
    )


if selected == "Accueil - Upload":
    accueil.show()
elif selected == "Historique":
    historique.show()
elif selected == "Statistiques":
    statistiques.show()
elif selected == "Gallery":
    gallery.show()


#st.divider()


