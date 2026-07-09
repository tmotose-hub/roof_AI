from ultralytics import YOLO
import streamlit as st
from PIL import Image
import tempfile
import numpy as np

# ==========================
# モデル読み込み
# ==========================
model = YOLO("runs/segment/train-2/weights/best.pt")

st.set_page_config(page_title="屋根コケ診断AI", layout="wide")

st.title("🏠 屋根コケ診断AI")

uploaded_file = st.file_uploader(
    "屋根画像をアップロードしてください",
    type=["jpg", "jpeg", "png"]
)

if uploaded_file is not None:

    # ------------------------
    # 元画像表示
    # ------------------------
    image = Image.open(uploaded_file)

    st.subheader("アップロード画像")

    st.image(image, use_container_width=True)

    # ------------------------
    # 一時保存
    # ------------------------
    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:

        image.save(tmp.name)

        results = model.predict(
            source=tmp.name,
            conf=0.25
        )

    # ------------------------
    # AI結果画像
    # ------------------------
    result_img = results[0].plot()

    st.subheader("AI診断結果")

    st.image(result_img, use_container_width=True)

    # ------------------------
    # コケ率計算
    # ------------------------
    if results[0].masks is not None:

        masks = results[0].masks.data.cpu().numpy()

        # 重複マスク除去
        merged_mask = np.any(masks, axis=0)

        moss_pixels = np.sum(merged_mask)

        image_pixels = merged_mask.shape[0] * merged_mask.shape[1]

        moss_ratio = moss_pixels / image_pixels * 100

        # ------------------------
        # 劣化スコア
        # ------------------------
        score = max(0, 100 - moss_ratio)

        st.divider()

        st.subheader(f"🟢 コケ率：{moss_ratio:.1f}%")

        st.metric(
            "劣化スコア",
            f"{score:.0f}点"
        )

        st.progress(score / 100)

        # ------------------------
        # ランク判定
        # ------------------------

        if score >= 95:

            rank = "A"

            st.success("★★★★★ 非常に良好")

        elif score >= 85:

            rank = "B"

            st.info("★★★★☆ 良好")

        elif score >= 70:

            rank = "C"

            st.warning("★★★☆☆ 軽度劣化")

        elif score >= 50:

            rank = "D"

            st.warning("★★☆☆☆ 中度劣化")

        else:

            rank = "E"

            st.error("★☆☆☆☆ 重度劣化")

        st.subheader(f"診断ランク：{rank}")

        # ------------------------
        # AIコメント
        # ------------------------

        st.divider()

        st.subheader("🤖 AI診断コメント")

        if moss_ratio < 5:

            st.success("""
屋根の状態は非常に良好です。

現時点で洗浄の必要性は低く、
半年〜1年後の再点検を推奨します。
""")

        elif moss_ratio < 15:

            st.info("""
軽度のコケが確認されました。

今後徐々に増殖する可能性があります。

1年以内の点検を推奨します。
""")

        elif moss_ratio < 30:

            st.warning("""
コケが確認されました。

屋根材の保水が始まっている可能性があります。

高圧洗浄や防カビ施工をご検討ください。
""")

        elif moss_ratio < 50:

            st.warning("""
コケの繁殖範囲が広がっています。

屋根材の劣化が進行している可能性があります。

専門業者による点検を推奨します。
""")

        else:

            st.error("""
広範囲にコケが発生しています。

屋根材の劣化や防水性能の低下が考えられます。

早急な点検・洗浄・補修をご検討ください。
""")

    else:

        st.success("コケは検出されませんでした。")