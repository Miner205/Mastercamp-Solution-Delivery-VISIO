from datetime import datetime
import os
import streamlit as st

from database import insert_image, update_manual_annotation, image_hash_exists, compute_uploaded_file_hash
import features_extraction


DATA_FOLDER = "Data/web_app"


def show():
    left_col, center_col, right_col = st.columns([1, 10, 1])
    with center_col:
        st.title("Web App VISIO - Wild Dump Prevention")
        st.subheader("Détection de l'état des poubelles")

        st.markdown("""
            <div class='green-title'>
            Une ville plus propre,
            des déchets mieux gérés.
            </div>
            """,
                    unsafe_allow_html=True)

        # st.image("assets/hero.png")

        st.markdown("""<div><br><br></div>""", unsafe_allow_html=True)
        uploaded_file = st.file_uploader("Déposer une image de poubelle", type=["jpg", "jpeg", "png"])

        if uploaded_file:
            filepath = os.path.join(DATA_FOLDER, uploaded_file.name)

            img_hash = compute_uploaded_file_hash(uploaded_file)
            annotation = None

            if image_hash_exists(img_hash):
                st.error("Cette image est déjà présente dans la database.")
            else:
                with open(filepath, "wb") as f:
                    f.write(uploaded_file.getbuffer())

                st.success("Image enregistrée.")

                insert_image((
                    uploaded_file.name,
                    img_hash,
                    filepath,
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    annotation,
                    None,
                    None,
                    features_extraction.get_file_size(filepath),
                    features_extraction.get_image_size(features_extraction.get_image(filepath))[0],
                    features_extraction.get_image_size(features_extraction.get_image(filepath))[1],
                    features_extraction.get_image_color_stats(features_extraction.get_image(filepath))[0],
                    features_extraction.get_image_color_stats(features_extraction.get_image(filepath))[1],
                    features_extraction.get_image_color_stats(features_extraction.get_image(filepath))[2]
                ))

            left_col2, center_col2, right_col2 = st.columns([1, 10, 1])
            with center_col2:
                st.image(filepath, width="stretch")

                left_col3, center_col3, right_col3 = st.columns(3)
                with center_col3:
                    st.subheader("annotation manuelle")
                    col1, col2 = st.columns(2)
                    annotation = None
                    with col1:
                        if st.button("🟢 Vide"):
                            annotation = "Vide"
                    with col2:
                        if st.button("🔴 Pleine"):
                            annotation = "Pleine"

            if annotation:
                update_manual_annotation(annotation, img_hash)
                st.success(f"Annotation '{annotation}' enregistrée.")
