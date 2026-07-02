from datetime import datetime
import os
import streamlit as st

import database as db
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
            initial_filename = uploaded_file.name
            extension = '.' + initial_filename.split(".")[-1]

            # File naming convention : Source_Type_Timestamp_Code ; code: to avoid collision just in case.
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            new_filename = f"App_Annoté_{timestamp}"

            filepath = os.path.join(DATA_FOLDER, new_filename + "_1" + extension)
            k = 2
            while os.path.exists(filepath):
                filepath = os.path.join(DATA_FOLDER, new_filename + '_' + str(k) + extension)
                k += 1

            img_hash = db.compute_uploaded_file_hash(uploaded_file)
            annotation = None

            if db.image_hash_exists(img_hash):
                st.error("Cette image est déjà présente dans la database.")
                filepath = db.get_filepath_from_hash(img_hash)
            else:
                with open(filepath, "wb") as f:
                    f.write(uploaded_file.getbuffer())

                st.success("Image enregistrée.")

                imag = features_extraction.get_image(filepath)
                imag_l = features_extraction.get_image_l(imag)
                dim = features_extraction.get_image_size(imag)
                color_stats = features_extraction.get_image_color_stats(imag)
                l_stats = features_extraction.get_image_l_stats(imag_l)
                histog = features_extraction.get_image_histogram(imag)
                db.insert_image((
                    initial_filename,
                    new_filename + '_' + str(k - 1) + extension,
                    img_hash,
                    filepath,
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    annotation,
                    None,
                    None,
                    features_extraction.get_file_size(filepath),
                    dim[0], dim[1], #width & height
                    color_stats[0], color_stats[1], color_stats[2], #avg rgb
                    color_stats[3][0], color_stats[4][0], color_stats[5][0], #min rgb
                    color_stats[3][1], color_stats[4][1], color_stats[5][1], #max rgb
                    l_stats[0], l_stats[1][0], l_stats[1][1], #luminance
                    str(histog[0:256]), str(histog[256:512]), str(histog[512:768]), #histograms rgb
                    str(features_extraction.get_image_histogram(imag_l)), #histogram luminance
                    features_extraction.get_image_l_contrast(l_stats[1][1], l_stats[1][0]), #contrast
                    str(features_extraction.get_hue_histogram(imag)) #histogram hue/teinte with basic image
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
                db.update_manual_annotation(annotation, img_hash)
                st.success(f"Annotation '{annotation}' enregistrée.")

            data = db.get_data_from_hash(img_hash)
            (id_, image_hash, filename, initial_filename, filepath, upload_date,
                manual_annotation, ai_annotation, ai_confidence,
                file_size, width, height,
                avg_r, avg_g, avg_b,
                min_r, min_g, min_b,
                max_r, max_g, max_b,
                avg_l, min_l, max_l,
                histogram_r, histogram_g, histogram_b,
                histogram_l,
                contrast,
                hue_histogram,) = data
            st.title("Détails de l'image")
            with st.expander("Général", expanded=True):
                st.write("ID :", id_)
                st.write("Hash :", image_hash)
                st.write("Nom du fichier :", filename)
                st.write("Nom d'origine du fichier :", initial_filename)
                st.write("Chemin d'accès du fichier :", filepath)
                st.write("Date d'upload :", upload_date)
                st.write("Taille du fichier :", f"{file_size} bytes")
                st.write("Dimension de l'image :", f"{width} x {height}")
            with st.expander("Annotations", expanded=True):
                st.write("Annotation manuelle :", manual_annotation)
                st.write("Annotation IA :", ai_annotation)
                st.write("Confiance IA :", ai_confidence)
            with st.expander("RGB", expanded=True):
                col1, col2, col3 = st.columns(3)
                col1.metric("Rouge Moyen :", avg_r)
                col2.metric("Vert Moyen :", avg_g)
                col3.metric("Bleu Moyen :", avg_b)
                col1, col2, col3 = st.columns(3)
                col1.metric("Rouge Min", min_r)
                col2.metric("Vert Min :", min_g)
                col3.metric("Bleu Min :", min_b)
                col1, col2, col3 = st.columns(3)
                col1.metric("Rouge Max :", max_r)
                col2.metric("Vert Max :", max_g)
                col3.metric("Bleu Max :", max_b)
            with st.expander("Luminance"):
                st.metric("Moyenne :", avg_l)
                st.metric("Min :", min_l)
                st.metric("Max :", max_l)
                st.metric("Contraste :", contrast)
            with st.expander("Histogrammes"):
                st.write("Rouge :", histogram_r)
                st.write("Vert :", histogram_g)
                st.write("Bleu :", histogram_b)
                st.write("Luminance :", histogram_l)
                st.write("Teinte :", hue_histogram)
