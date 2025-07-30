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

    for page in doc:
        # === ЗАМЕНА ДАТЫ ===
        matches = page.search_for(old_date)
        for box in matches:
            page.draw_rect(box, color=(1, 1, 1), fill=(1, 1, 1))  # затереть
            x, y = box.tl
            page.insert_text((x + 10, y + 2), new_date, fontsize=10, color=(0, 0, 0))

        # === ЗАМЕНА ТЕКСТОВОГО БЛОКА ===
        key_phrase = "This is because you are requiring a wholly outsourced"
        text_boxes = page.search_for(key_phrase)
        for box in text_boxes:
            # Прямоугольник, перекрывающий весь блок
            erase_rect = fitz.Rect(box.x0, box.y0, box.x0 + 370, box.y0 + 200)
            page.draw_rect(erase_rect, color=(1, 1, 1), fill=(1, 1, 1))

            # Вставка нового текста (построчно)
            x, y = box.x0, box.y1 + 5
            for i, line in enumerate(new_text_block.split("\n")):
                page.insert_text((x, y - 12 * i), line.strip(), fontsize=10, color=(0, 0, 0))

    doc.save(output_path)
    return FileResponse(output_path, filename="filled_report.pdf", media_type="application/pdf")
