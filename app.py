import os
import tempfile
from PIL import Image
import numpy as np
import streamlit as st
from ultralytics import YOLO
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors

# ==========================================
# 日本語フォント登録（Render対応）
# ==========================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

font_path = os.path.join(
    BASE_DIR,
    "fonts",
    "NotoSansJP-Regular.ttf"
)

pdfmetrics.registerFont(
    TTFont(
        "NotoJP",
        font_path
    )
)

# ==========================================
# YOLOモデル（1回だけ読み込む）
# ==========================================
@st.cache_resource
def load_model():
    return YOLO("runs/segment/train-2/weights/best.pt")

model = load_model()

# ==========================================
# ④ PDF作成関数
# ==========================================
def create_diagnostic_pdf(output_path, moss_ratio, score, rank, comment, roof_area, moss_area, cost_min, cost_max):
    # A4サイズ・上下左右20mmのマージンでドキュメントを作成
    doc = SimpleDocTemplate(
        output_path, 
        pagesize=A4,
        leftMargin=56.7, rightMargin=56.7, 
        topMargin=56.7, bottomMargin=56.7
    )
    
    styles = getSampleStyleSheet()
    
    # 日本語用カスタムスタイルの追加
    title_style = ParagraphStyle(
        'DocTitle', parent=styles['Heading1'], 
        fontName='NotoJP', fontSize=24, leading=28, 
        alignment=1, spaceAfter=20
    )
    h2_style = ParagraphStyle(
        'SectionHeader', parent=styles['Heading2'], 
        fontName='NotoJP', fontSize=14, leading=18, 
        spaceBefore=15, spaceAfter=10, textColor=colors.HexColor("#1A365D")
    )
    body_style = ParagraphStyle(
        'BodyTextCustom', parent=styles['Normal'], 
        fontName='NotoJP', fontSize=10, leading=15, spaceAfter=8
    )
    
    story = []
    
    # タイトル
    story.append(Paragraph("屋根AI診断レポート", title_style))
    story.append(Spacer(1, 15))
    
    # 診断結果まとめデータテーブル
    data = [
        [Paragraph("<b>項目</b>", body_style), Paragraph("<b>診断結果</b>", body_style)],
        [Paragraph("屋根面積", body_style), Paragraph(f"{roof_area:.1f} ㎡", body_style)],
        [Paragraph("コケ検出率", body_style), Paragraph(f"{moss_ratio:.1f} %", body_style)],
        [Paragraph("コケ推定面積", body_style), Paragraph(f"{moss_area:.1f} ㎡", body_style)],
        [Paragraph("劣化スコア", body_style), Paragraph(f"{score:.0f} 点", body_style)],
        [Paragraph("診断ランク", body_style), Paragraph(f"{rank}", body_style)],
        [Paragraph("概算メンテナンス費用", body_style), Paragraph(f"{cost_min:,}円 ～ {cost_max:,}円", body_style)]
    ]
    
    t = Table(data, colWidths=[150, 250])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (1,0), colors.HexColor("#1A365D")),
        ('TEXTCOLOR', (0,0), (1,0), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('TOPPADDING', (0,0), (-1,-1), 8),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('BACKGROUND', (0,1), (-1,-1), colors.HexColor("#F7FAFC")),
    ]))
    
    story.append(Paragraph("■ 診断概要", h2_style))
    story.append(t)
    story.append(Spacer(1, 15))
    
    # AI診断コメント
    story.append(Paragraph("■ AIアドバイス・推奨施工", h2_style))
    story.append(Paragraph(comment, body_style))
    
    if "重度" in rank:
        story.append(Paragraph("【推奨施工】高圧洗浄、および屋根全体への防カビ・遮熱塗装（早期実施を推奨）", body_style))
    elif "中度" in rank:
        story.append(Paragraph("【推奨施工】部分的な高圧洗浄、または防カビ処理を検討してください。", body_style))
    else:
        story.append(Paragraph("【推奨施工】現時点での特別な施工は不要です。定期的な点検を継続してください。", body_style))
        
    doc.build(story)

# ==========================================
# ⑥ Streamlit メイン画面構成
# ==========================================
st.title("屋根コケ診断AI — プロ仕様 Ver 2.0")

# ⑤ 顧客向け設定・前提条件の入力
st.sidebar.header("診断前提条件の設定")
roof_area = st.sidebar.number_input("屋根の総面積 (㎡)", min_value=1.0, value=120.0, step=1.0)
unit_price = st.sidebar.number_input("㎡あたりの想定洗浄・塗装単価 (円)", min_value=500, value=2500, step=100)

uploaded_file = st.file_uploader(
    "屋根画像をアップロードしてください", type=["jpg", "jpeg", "png"]
)

if uploaded_file:
    image = Image.open(uploaded_file)
    image = image.convert("RGB")

    # Render Free高速化
    image.thumbnail((512, 512))
    
    col1, col2 = st.columns(2)
    with col1:
        st.image(image,caption="アップロード画像",width="stretch")

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
            image.save(tmp.name)


            results = model.predict(
                source=tmp.name,
                conf=0.35,
                imgsz=512,
                verbose=False
            )

    finally:
        if os.path.exists(tmp.name):
            os.remove(tmp.name)

    result_img = results[0].plot()
    
    with col2:
        st.image(
            result_img,
            caption="AI解析・コケ検出結果",
            width="stretch"
        )

    if results[0].masks is not None:
        # STEP1: 重複マスクを除去して正確な画素数を計算
        masks = results[0].masks.data.cpu().numpy()
        merged_mask = np.any(masks, axis=0)
        moss_pixels = np.sum(merged_mask)
        image_pixels = merged_mask.shape[0] * merged_mask.shape[1]

        # コケ率の計算
        moss_ratio = (moss_pixels / image_pixels) * 100
        
        # ⑤ ㎡換算 & 劣化スコア計算
        moss_area = roof_area * (moss_ratio / 100)
        score = max(0, 100 - moss_ratio)
        
        # ⑤ 想定費用の算出 (コケの面積、または最低基本料金などをベースにした概算)
        cost_min = int(moss_area * unit_price)
        cost_max = int(moss_area * (unit_price + 1200)) # 上幅をもたせる計算
        if cost_min < 30000 and moss_ratio > 0: # 最低施工費用を3万円にセット
            cost_min = 30000
            cost_max = 60000

        # 結果表示
        st.markdown("---")
        st.subheader("📊 診断アナリティクス")
        
        m_col1, m_col2, m_col3 = st.columns(3)
        m_col1.metric("AI判定 コケ率", f"{moss_ratio:.1f} %")
        m_col2.metric("コケ推定面積", f"{moss_area:.1f} ㎡")
        m_col3.metric("屋根総合健康スコア", f"{score:.0f} 点")

        # STEP3: 判定ランク & コメント
        if moss_ratio < 10:
            rank = "軽度 (Aランク)"
            comment = "状態は非常に良好です。現時点では屋根材自体の大きな劣化は見られません。定期的なメンテナンスチェックをお勧めします。"
            st.success(f"判定: {rank}")
        elif moss_ratio < 30:
            rank = "中度 (Bランク)"
            comment = "一部に広がりつつあるコケ・藻の群生が確認されました。これ以上の拡大を防ぐため、高圧洗浄や防カビ施工を計画することをお勧めします。"
            st.warning(f"判定: {rank}")
        else:
            rank = "重度 (Cランク)"
            comment = "広範囲にわたる深刻なコケの付着が確認されました。水分の滞留により屋根材本体の耐久性が低下している危険性があります。専門業者による早期の洗浄および補修塗装を強く推奨します。"
            st.error(f"判定: {rank}")

        # ⑤ お客様向け診断レポートビュー
        st.info(f"【AI診断アドバイス】\n{comment}")
        
        st.markdown("### 💰 推奨されるメンテナンスプラン")
        st.write(f"・**推奨施工:** {'定期点検継続' if moss_ratio < 10 else 'バイオ高圧洗浄 / 屋根塗装'}")
        st.write(f"・**概算提案費用:** 約 **{cost_min:,}円 ～ {cost_max:,}円** (面積、単価連動)")

        # ⑤ PDFダウンロードボタン（ワンクリック作成）
        st.markdown("---")
        st.subheader("📄 顧客提出用PDFレポート出力")
        
        pdf_filename = "屋根AI診断報告書.pdf"
        if st.button("PDF診断書を生成する"):
            create_diagnostic_pdf(
                pdf_filename, moss_ratio, score, rank, comment, 
                roof_area, moss_area, cost_min, cost_max
            )
            
            with open(pdf_filename, "rb") as f:
                st.download_button(
                    label="📥 PDFをダウンロード",
                    data=f,
                    file_name=pdf_filename,
                    mime="application/pdf"
                )
    else:
        st.success("コケは検出されませんでした！屋根は非常にクリーンな状態です。")