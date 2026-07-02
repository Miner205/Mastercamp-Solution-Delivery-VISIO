from datetime import datetime
import os
import streamlit as st

import database as db
import features_extraction


DATA_FOLDER = "Data/web_app"


def init_state():
    if "images_queue" not in st.session_state:
        st.session_state.images_queue = []
    if "index" not in st.session_state:
        st.session_state.index = 0
    if "left_stack" not in st.session_state:
        st.session_state.left_stack = []   # Vide
    if "right_stack" not in st.session_state:
        st.session_state.right_stack = []  # Pleine
    if 'disabled' not in st.session_state:
        st.session_state.disabled = False
    if "uploader_key" not in st.session_state:
        st.session_state.uploader_key = 0


def reset_state():
    if st.session_state.images_queue:
        st.session_state.images_queue = []
        st.session_state.index = 0
        st.session_state.left_stack = []
        st.session_state.right_stack = []
    st.session_state.other_p = False
    st.session_state.disabled = False
    st.session_state.uploader_key += 1


def save_annotation(annot, hsh, fpath):
    """
    Fonction callback pour enregistrer l'annotation.
    """
    db.update_manual_annotation(annot, hsh)
    if annot == "Vide":
        st.session_state.left_stack.append(fpath)
    else:
        st.session_state.right_stack.append(fpath)

    st.session_state.index += 1


def show():
    init_state()
    if st.session_state.other_p:
        reset_state()

    left_col, center_col, right_col = st.columns([2, 18, 2])

    with left_col:
        st.markdown("### 🟢 Vide")
        for img in st.session_state.left_stack[-8:]:
            st.image(img)

    with right_col:
        st.markdown("### 🔴 Pleine")
        for img in st.session_state.right_stack[-8:]:
            st.image(img)

    with center_col:
        st.title("Multi-Upload")
        st.subheader("Upload plusieurs images en même temps")

        st.markdown("""<div><br><br></div>""", unsafe_allow_html=True)
        uploaded_files = st.file_uploader("Déposer plusieurs images", type=["jpg", "jpeg", "png"], accept_multiple_files=True, disabled=st.session_state.disabled, key=f"uploader_{st.session_state.uploader_key}")

        if uploaded_files and not st.session_state.images_queue:
            for f in uploaded_files:
                st.session_state.images_queue.append(f)

        if st.session_state.index < len(st.session_state.images_queue):
            st.session_state.disabled = True

            current_file = st.session_state.images_queue[st.session_state.index]

            initial_filename = current_file.name
            extension = '.' + initial_filename.split(".")[-1]

            # File naming convention : Source_Type_Timestamp_Code ; code: to avoid collision just in case.
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            new_filename = f"App_Annoté_{timestamp}"

            filepath = os.path.join(DATA_FOLDER, new_filename + "_1" + extension)
            k = 2
            while os.path.exists(filepath):
                filepath = os.path.join(DATA_FOLDER, new_filename + '_' + str(k) + extension)
                k += 1

            img_hash = db.compute_uploaded_file_hash(current_file)

            if db.image_hash_exists(img_hash):
                st.warning(f"Cette image est déjà présente dans la database - vous devez cependant la réannoter.")
                filepath = db.get_filepath_from_hash(img_hash)
                #st.session_state.index += 1
                #st.rerun()
            else:
                with open(filepath, "wb") as f:
                    f.write(current_file.getbuffer())

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
                    None, # Annotation
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
                st.markdown("### Image à annoter")
                st.image(filepath, width="stretch")

                left_col3, center_col3, right_col3 = st.columns(3)
                with center_col3:
                    st.subheader("annotation manuelle")
                    col1, col2 = st.columns(2)
                    with col1:
                        st.button("🟢 Vide", on_click=save_annotation, args=("Vide", img_hash, filepath))

                    with col2:
                        st.button("🔴 Pleine", on_click=save_annotation, args=("Pleine", img_hash, filepath))

        elif st.session_state.images_queue:
            st.success("Toutes les images ont été annotées !")
            _, middle, _ = st.columns(3)
            with middle:
                st.button("Appuyez ici pour réinitialisez la page et pouvoir upload de nouvelles images.", on_click=reset_state)
