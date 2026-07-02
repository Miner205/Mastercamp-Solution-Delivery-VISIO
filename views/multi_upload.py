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


def reset_state():
    if st.session_state.images_queue:
        st.session_state.images_queue = []
        st.session_state.index = 0
        st.session_state.left_stack = []
        st.session_state.right_stack = []
    st.session_state.other_p = False


def show():
    init_state()
    if st.session_state.other_p:
        reset_state()
    left_col, center_col, right_col = st.columns([2, 18, 2])

    with left_col:
        st.markdown("### 🟢 Vide")
        for img in st.session_state.left_stack[-5:]:
            st.image(img)

    with right_col:
        st.markdown("### 🔴 Pleine")
        for img in st.session_state.right_stack[-5:]:
            st.image(img)

    with center_col:
        st.title("Multi-Upload")
        st.subheader("Upload plusieurs images en même temps")

        st.markdown("""<div><br><br></div>""", unsafe_allow_html=True)
        uploaded_files = st.file_uploader("Déposer plusieurs images", type=["jpg", "jpeg", "png"], accept_multiple_files=True)

        if uploaded_files and not st.session_state.images_queue:
            for f in uploaded_files:
                st.session_state.images_queue.append(f)

        if st.session_state.index < len(st.session_state.images_queue):
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
            annotation = None

            if db.image_hash_exists(img_hash):
                st.warning(f"{current_file.name} est déjà présente dans la database.")
                filepath = db.get_filepath_from_hash(img_hash)  # not necessary but just in case.
                st.session_state.index += 1
                st.rerun()
            else:
                with open(filepath, "wb") as f:
                    f.write(current_file.getbuffer())

                imag = features_extraction.get_image(filepath)
                imag_l = features_extraction.get_image_l(imag)
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
                    features_extraction.get_image_size(imag)[0],
                    features_extraction.get_image_size(imag)[1],
                    features_extraction.get_image_color_stats(imag)[0],
                    features_extraction.get_image_color_stats(imag)[1],
                    features_extraction.get_image_color_stats(imag)[2],
                    features_extraction.get_image_color_stats(imag)[3][0],
                    features_extraction.get_image_color_stats(imag)[4][0],
                    features_extraction.get_image_color_stats(imag)[5][0],
                    features_extraction.get_image_color_stats(imag)[3][1],
                    features_extraction.get_image_color_stats(imag)[4][1],
                    features_extraction.get_image_color_stats(imag)[5][1],
                    features_extraction.get_image_l_stats(imag_l)[0],
                    features_extraction.get_image_l_stats(imag_l)[1][0],
                    features_extraction.get_image_l_stats(imag_l)[1][1],
                    str(features_extraction.get_image_histogram(imag)[0:256]),
                    str(features_extraction.get_image_histogram(imag)[256:512]),
                    str(features_extraction.get_image_histogram(imag)[512:768]),
                    str(features_extraction.get_image_histogram(imag_l)),
                    features_extraction.get_image_l_contrast(features_extraction.get_image_l_stats(imag_l)[1][1], features_extraction.get_image_l_stats(imag_l)[1][0]),
                    str(features_extraction.get_hue_histogram(imag))
                ))

            left_col2, center_col2, right_col2 = st.columns([1, 10, 1])
            with center_col2:
                st.markdown("### Image à annoter")
                st.image(filepath, width="stretch")

                left_col3, center_col3, right_col3 = st.columns(3)
                with center_col3:
                    st.subheader("annotation manuelle")
                    col1, col2 = st.columns(2)
                    annotation = None
                    with col1:
                        if st.button("🟢 Vide"):
                            annotation = "Vide"
                            print("vvv", annotation)
                    with col2:
                        if st.button("🔴 Pleine"):
                            annotation = "Pleine"
                            print("vvvccc", annotation)
                    print("kkk", annotation)
            print("gggg", annotation)
            if annotation:
                db.update_manual_annotation(annotation, img_hash)
                if annotation == "Vide":
                    st.session_state.left_stack.append(filepath)
                else:
                    st.session_state.right_stack.append(filepath)

                st.success(f"Annotation '{annotation}' enregistrée.")

                st.session_state.index += 1
                st.rerun()

        elif st.session_state.images_queue:
            st.success("Toutes les images ont été annotées !")
