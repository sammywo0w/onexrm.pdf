import fitz  # PyMuPDF
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse
import os

app = FastAPI()

TEMPLATE_PATH = "onexrm-external-resource-triage-report.pdf"

@app.post("/generate-pdf")
async def generate_pdf(data: dict):
    old_date = "30/07/2025"
    new_date = data.get("date", "01/08/2025")
    output_path = "/tmp/updated.pdf"

    if not os.path.exists(TEMPLATE_PATH):
        return {"error": "Template PDF not found"}

    doc = fitz.open(TEMPLATE_PATH)

    for page in doc:
        matches = page.search_for(old_date)
        for box in matches:
            # Затереть белым
            page.draw_rect(box, color=(1, 1, 1), fill=(1, 1, 1))
            # Вставить новый текст
            page.insert_text(box.tl, new_date, fontsize=10, color=(0, 0, 0))

    doc.save(output_path)
    return FileResponse(output_path, filename="filled_report.pdf", media_type="application/pdf")
