import os
import tempfile

import numpy as np
import streamlit as st
from PIL import Image
from ultralytics import YOLO


# ======================================
# ページ設定
# ======================================

st.set_page_config(
    page_title="屋根コケ診断AI",
    layout="wide"
)


# ======================================
# YOLOモデル
# ======================================

@st.cache_resource
def load_model():
    return YOLO("models/best.pt")


model = load_model()


# ======================================
# タイトル
# ======================================

st.title("🏠 屋根コケ診断AI")

st.write("屋根画像をアップロードしてください。")


uploaded_file = st.file_uploader(

    "画像アップロード",

    type=["jpg", "jpeg", "png"]

)


# ======================================
# 画像アップロード
# ======================================

if uploaded_file is not None:

    image = Image.open(uploaded_file).convert("RGB")

    # Renderメモリ対策
    image.thumbnail((320, 320))

    col1, col2 = st.columns(2)

    with col1:

        st.subheader("アップロード画像")

        st.image(
            image,
            use_container_width=True
        )

    # ===========================
    # 一時保存
    # ===========================

    try:

        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=".jpg"
        ) as tmp:

            image.save(tmp.name)

            with st.spinner("AI解析中..."):

                results = model.predict(

                    source=tmp.name,

                    imgsz=320,

                    conf=0.25,

                    verbose=False

                )

    finally:

        if os.path.exists(tmp.name):

            os.remove(tmp.name)

    # ===========================
    # AI画像表示
    # ===========================

    result_img = results[0].plot()

    with col2:

        st.subheader("AI解析結果")

        st.image(
            result_img,
            use_container_width=True
        )
    # ======================================
    # コケ率計算
    # ======================================

    if results[0].masks is None:

        st.success("コケは検出されませんでした。")

    else:

        masks = results[0].masks.data.cpu().numpy()

        # 重複マスク除去
        merged_mask = np.any(masks, axis=0)

        moss_pixels = np.sum(merged_mask)

        total_pixels = merged_mask.shape[0] * merged_mask.shape[1]

        moss_ratio = moss_pixels / total_pixels * 100

        # ======================================
        # 劣化スコア
        # ======================================

        score = max(0, 100 - moss_ratio)

        st.divider()

        st.subheader("📊 AI診断結果")

        colA, colB = st.columns(2)

        with colA:

            st.metric(

                "コケ率",

                f"{moss_ratio:.1f}%"

            )

        with colB:

            st.metric(

                "劣化スコア",

                f"{score:.0f}点"

            )

        st.progress(score / 100)

        # ======================================
        # ランク判定
        # ======================================

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
                # ======================================
        # AI診断コメント
        # ======================================

        st.divider()

        st.subheader("🤖 AI診断コメント")

        if moss_ratio < 5:

            st.success("""
屋根の状態は非常に良好です。

現時点では洗浄の必要性は低く、
半年〜1年後の定期点検を推奨します。
""")

        elif moss_ratio < 15:

            st.info("""
軽度のコケが確認されました。

現時点で緊急性はありませんが、
今後徐々に広がる可能性があります。

1年以内の再点検を推奨します。
""")

        elif moss_ratio < 30:

            st.warning("""
コケの繁殖が確認されました。

屋根材に水分が滞留し始めている可能性があります。

高圧洗浄や防カビ施工をご検討ください。
""")

        elif moss_ratio < 50:

            st.warning("""
コケが広範囲に確認されました。

屋根材の劣化が進行している可能性があります。

専門業者による点検・洗浄を推奨します。
""")

        else:

            st.error("""
広範囲にコケが発生しています。

屋根材の防水性能が低下している可能性があります。

早急な点検・洗浄・補修をご検討ください。
""")

        # ======================================
        # 詳細情報
        # ======================================

        st.divider()

        with st.expander("診断データ詳細"):

            st.write(f"画像サイズ：{merged_mask.shape[1]} × {merged_mask.shape[0]} px")

            st.write(f"コケ画素数：{moss_pixels:,}")

            st.write(f"全画素数：{total_pixels:,}")

            st.write(f"コケ率：{moss_ratio:.2f}%")

            st.write(f"劣化スコア：{score:.1f}")

            st.write(f"診断ランク：{rank}")

        st.success("✅ AI診断が完了しました。")
                # ======================================
        # Step2
        # 屋根情報入力
        # ======================================

        st.divider()

        st.subheader("🏠 屋根情報")

        roof_area = st.number_input(

            "屋根面積（㎡）",

            min_value=10,

            max_value=500,

            value=120,

            step=5

        )

        unit_price = st.number_input(

            "洗浄単価（円/㎡）",

            min_value=500,

            max_value=8000,

            value=2500,

            step=100

        )

        # ======================================
        # コケ面積計算
        # ======================================

        moss_area = roof_area * moss_ratio / 100

        st.metric(

            "推定コケ面積",

            f"{moss_area:.1f}㎡"

        )

        # ======================================
        # 概算費用
        # ======================================

        estimate = moss_area * unit_price

        if estimate < 30000 and moss_ratio > 0:

            estimate = 30000

        st.metric(

            "概算施工費",

            f"¥{estimate:,.0f}"

        )

        # ======================================
        # メンテナンス提案
        # ======================================

        st.divider()

        st.subheader("🛠 推奨メンテナンス")

        if moss_ratio < 5:

            st.success("現在施工の必要はありません。")

        elif moss_ratio < 15:

            st.info("半年〜1年以内の再点検をおすすめします。")

        elif moss_ratio < 30:

            st.warning("高圧洗浄をご検討ください。")

        elif moss_ratio < 50:

            st.warning("高圧洗浄＋防カビ施工を推奨します。")

        else:

            st.error("屋根塗装を含めたメンテナンスを推奨します。")

        # ======================================
        # お客様向けサマリー
        # ======================================

        st.divider()

        st.subheader("📋 AI診断サマリー")

        st.write(f"屋根面積：**{roof_area}㎡**")

        st.write(f"コケ率：**{moss_ratio:.1f}%**")

        st.write(f"推定コケ面積：**{moss_area:.1f}㎡**")

        st.write(f"劣化スコア：**{score:.0f}点**")

        st.write(f"診断ランク：**{rank}**")

        st.write(f"概算施工費：**¥{estimate:,.0f}**")