import os
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# =========================
# フォント設定（Render対応）
# =========================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FONT_PATH = os.path.join(BASE_DIR, "fonts", "NotoSansJP-Regular.ttf")

# フォント登録（存在チェック付き）
if os.path.exists(FONT_PATH):
    pdfmetrics.registerFont(TTFont("NotoJP", FONT_PATH))
    FONT_NAME = "NotoJP"
else:
    FONT_NAME = "Helvetica"  # フォールバック

# =========================
# PDF生成メイン関数
# =========================
def create_report(output_path="report.pdf", text="YOLO Report"):
    """
    PDFレポートを生成する関数（Render用）
    """

    c = canvas.Canvas(output_path)

    # フォント設定
    c.setFont(FONT_NAME, 14)

    # タイトル
    c.drawString(100, 800, "YOLO Detection Report")

    # テキスト
    c.setFont(FONT_NAME, 11)
    c.drawString(100, 770, text)

    # ここに将来的にYOLO結果を追加できる
    c.drawString(100, 740, "Status: OK")

    c.save()

    return output_path