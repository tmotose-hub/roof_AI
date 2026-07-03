import os

from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

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