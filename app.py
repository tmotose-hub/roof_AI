import os
import tempfile

import numpy as np
import streamlit as st
from PIL import Image
from ultralytics import YOLO


# -------------------------------
# ページ設定
# -------------------------------

st.set_page_config(
    page_title="屋根コケ診断AI",
    layout="wide"
)


# -------------------------------
# YOLOモデル読み込み
# -------------------------------

@st.cache_resource
def load_model():
    return YOLO("models/best.pt")


model = load_model()


# -------------------------------
# タイトル
# -------------------------------

st.title("🏠 屋根コケ診断AI")

uploaded_file = st.file_uploader(

    "屋根画像をアップロードしてください",

    type=["jpg", "jpeg", "png"]

)


# -------------------------------
# 推論
# -------------------------------

if uploaded_file is not None:

    image = Image.open(uploaded_file).convert("RGB")

    # Renderメモリ対策
    image.thumbnail((320, 320))

    col1, col2 = st.columns(2)

    with col1:

        st.subheader("アップロード画像")

        st.image(image, use_container_width=True)

    try:

        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=".jpg"
        ) as tmp:

            image.save(tmp.name)

            results = model.predict(

                source=tmp.name,

                imgsz=320,

                conf=0.25,

                verbose=False

            )

    finally:

        if os.path.exists(tmp.name):

            os.remove(tmp.name)

    # -----------------------
    # 推論画像表示
    # -----------------------

    result_img = results[0].plot()

    with col2:

        st.subheader("AI解析結果")

        st.image(result_img, use_container_width=True)

    # -----------------------
    # コケ率計算
    # -----------------------

    if results[0].masks is None:

        st.success("コケは検出されませんでした。")

    else:

        masks = results[0].masks.data.cpu().numpy()

        merged = np.any(masks, axis=0)

        moss_pixels = np.sum(merged)

        total_pixels = merged.shape[0] * merged.shape[1]

        moss_ratio = moss_pixels / total_pixels * 100

        st.divider()

        st.metric(

            "コケ率",

            f"{moss_ratio:.1f}%"

        )