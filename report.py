from reportlab.platypus import *
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

pdfmetrics.registerFont(
    TTFont(
        "Meiryo",
        "C:/Windows/Fonts/meiryo.ttc"
    )
)

def create_report(
    filename,
    moss_ratio,
    moss_area,
    score,
    rank,
    comment
):

    doc = SimpleDocTemplate(filename)

    style = getSampleStyleSheet()["Normal"]

    style.fontName = "Meiryo"

    elements = []

    elements.append(
        Paragraph("<b>屋根AI診断レポート</b>", style)
    )

    elements.append(Spacer(1,20))

    elements.append(
        Paragraph(f"コケ率：{moss_ratio:.1f}%", style)
    )

    elements.append(
        Paragraph(f"コケ面積：{moss_area:.1f}㎡", style)
    )

    elements.append(
        Paragraph(f"健康スコア：{score:.0f}", style)
    )

    elements.append(
        Paragraph(f"判定：{rank}", style)
    )

    elements.append(Spacer(1,20))

    elements.append(
        Paragraph(comment, style)
    )

    doc.build(elements)