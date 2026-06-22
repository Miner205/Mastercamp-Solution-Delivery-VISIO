import streamlit as st
import os
from datetime import datetime
import sqlite3
import pandas as pd

from database import create_database, insert_image
#from metadata import extract_metadata

DB_NAME = "visio_database.db"


create_database()

DATA_FOLDER = "Data/myTests"
os.makedirs(DATA_FOLDER, exist_ok=True)


st.title("Web App VISIO - Wild Dump Prevention")
st.subheader("Détection de l'état des poubelles")

uploaded_file = st.file_uploader("Choisir une image", type=["jpg", "jpeg", "png"])

if uploaded_file:
    filepath = os.path.join(DATA_FOLDER, uploaded_file.name)

    with open(filepath, "wb") as f:
        f.write(uploaded_file.getbuffer())

    st.success("Image enregistrée.")
    st.image(filepath)  #, width=500)

    col1, col2 = st.columns(2)
    annotation = None
    with col1:
        if st.button("🟢 Vide"):
            annotation = "Vide"
    with col2:
        if st.button("🔴 Pleine"):
            annotation = "Pleine"

    '''if annotation:
        metadata = extract_metadata(filepath)
        insert_image((
            uploaded_file.name,
            filepath,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            annotation,
            metadata["file_size"],
            metadata["width"],
            metadata["height"],
            metadata["avg_r"],
            metadata["avg_g"],
            metadata["avg_b"]
        ))
        st.success(
            f"Annotation '{annotation}' enregistrée."
        )'''



st.divider()
st.subheader("Historique des annotations")
conn = sqlite3.connect(DB_NAME)
df = pd.read_sql_query("SELECT * FROM images", conn)
st.dataframe(df)
conn.close()

