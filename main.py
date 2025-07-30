import fitz  # PyMuPDF
from fastapi import FastAPI
from fastapi.responses import FileResponse
import os

app = FastAPI()

TEMPLATE_PATH = "onexrm-external-resource-triage-report.pdf"

@app.post("/generate-pdf")
async def generate_pdf(data: dict):
    old_date = "30/07/2025"
    new_date = data.get("date", "01/08/2025")
    new_text_block = data.get("recommendation", "Your custom recommendation goes here.")
    output_path = "/tmp/updated.pdf"

    if not os.path.exists(TEMPLATE_PATH):
        return {"error": "Template PDF not found"}

    doc = fitz.open(TEMPLATE_PATH)

    # === ЗАМЕНА ДАТЫ ===
    for page in doc:
        matches = page.search_for(old_date)
        for box in matches:
            page.draw_rect(box, color=(1, 1, 1), fill=(1, 1, 1))
            x, y = box.tl
            page.insert_text((x + 10, y + 2), new_date, fontsize=10, color=(0, 0, 0))

    # === ВСТАВКА ТЕКСТОВОГО БЛОКА ===
    base_page = doc[1]
    insert_rect = fitz.Rect(60, 420, 540, 780)
    font_size = 10
    line_height = font_size + 4

    font_args = {"fontsize": font_size, "color": (0, 0, 0)}

    lines = []
    for raw_line in new_text_block.split("\n"):
        if raw_line.strip():
            lines.append(raw_line.strip())

    cursor_y = insert_rect.y0
    for line in lines:
        if cursor_y + line_height > insert_rect.y1:
            base_page = doc.new_page()
            cursor_y = 60

        base_page.insert_text((insert_rect.x0, cursor_y), line, **font_args)
        cursor_y += line_height

    doc.save(output_path)
    return FileResponse(output_path, filename="filled_report.pdf", media_type="application/pdf")
