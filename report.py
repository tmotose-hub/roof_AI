import os
from PIL import Image
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as RLImage, Table, TableStyle
from reportlab.lib import colors

# ======================================
# 日本語フォント（プロジェクト内）
# ======================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

font_path = os.path.join(
    BASE_DIR,
    "fonts",
    "NotoSansJP-Regular.ttf"
)

pdfmetrics.registerFont(
    TTFont("NotoJP", font_path)
)


# ======================================
# PDF生成メイン関数
# ======================================
def create_report(
    output_path,
    original_image_path,
    result_image_path,
    moss_ratio,
    moss_area,
    roof_area,
    score,
    rank,
    comment,
    cost_min,
    cost_max
):

    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40
    )

    styles = getSampleStyleSheet()

    # =========================
    # スタイル定義
    # =========================
    title_style = ParagraphStyle(
        "title",
        parent=styles["Heading1"],
        fontName="NotoJP",
        fontSize=22,
        alignment=1,
        spaceAfter=20
    )

    h_style = ParagraphStyle(
        "h",
        parent=styles["Heading2"],
        fontName="NotoJP",
        fontSize=14,
        textColor=colors.HexColor("#1f4e79"),
        spaceBefore=10,
        spaceAfter=10
    )

    body = ParagraphStyle(
        "body",
        parent=styles["Normal"],
        fontName="NotoJP",
        fontSize=10,
        leading=14
    )

    story = []

    # =========================
    # タイトル
    # =========================
    story.append(Paragraph("屋根コケ診断レポート", title_style))
    story.append(Spacer(1, 10))

    # =========================
    # 画像表示
    # =========================
    if os.path.exists(original_image_path):
        story.append(Paragraph("■ 診断対象画像", h_style))
        story.append(RLImage(original_image_path, width=240, height=160))
        story.append(Spacer(1, 10))

    if os.path.exists(result_image_path):
        story.append(Paragraph("■ AI解析結果", h_style))
        story.append(RLImage(result_image_path, width=240, height=160))
        story.append(Spacer(1, 10))

    # =========================
    # サマリー表
    # =========================
    story.append(Paragraph("■ 診断サマリー", h_style))

    data = [
        ["項目", "結果"],
        ["屋根面積", f"{roof_area:.1f} ㎡"],
        ["コケ率", f"{moss_ratio:.1f} %"],
        ["コケ面積", f"{moss_area:.1f} ㎡"],
        ["劣化スコア", f"{score:.0f} / 100"],
        ["診断ランク", rank],
        ["概算費用", f"{cost_min:,}円 ～ {cost_max:,}円"]
    ]

    table = Table(data, colWidths=[120, 200])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
        ("FONTNAME", (0, 0), (-1, -1), "NotoJP"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
    ]))

    story.append(table)
    story.append(Spacer(1, 10))

    # =========================
    # AIコメント
    # =========================
    story.append(Paragraph("■ AI診断コメント", h_style))
    story.append(Paragraph(comment, body))
    story.append(Spacer(1, 10))

    # =========================
    # ランク別提案
    # =========================
    story.append(Paragraph("■ 推奨メンテナンス", h_style))

    if rank.startswith("軽度"):
        advice = "現時点では大きな問題はありません。定期点検を推奨します。"
    elif rank.startswith("中度"):
        advice = "コケの拡大が見られます。高圧洗浄を推奨します。"
    else:
        advice = "劣化が進行しています。早急な洗浄・塗装工事を推奨します。"

    story.append(Paragraph(advice, body))

    # =========================
    # PDF生成
    # =========================
    doc.build(story)