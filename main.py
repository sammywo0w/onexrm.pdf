import fitz  # PyMuPDF
from fastapi import FastAPI
from fastapi.responses import FileResponse
import os
import re

app = FastAPI()
TEMPLATE_PATH = "onexrm-external-resource-triage-report.pdf"


def parse_formatting(text: str):
    text = re.sub(r'\[h2\](.*?)\[/h2\]', r'\1\n' + '='*60, text)
    text = re.sub(r'\[url=(.*?)\](.*?)\[/url\]', r'\2: \1', text)
    text = re.sub(r'\[indent data=\d+\]', '    ', text)
    text = re.sub(r'\[/indent\]', '', text)
    text = re.sub(r'✅', '✔️', text)
    text = re.sub(r'⚠️', '⚠️', text)
    text = re.sub(r'💡', '💡', text)
    return text


@app.post("/generate-pdf")
async def generate_pdf(data: dict):
    old_date = "30/07/2025"
    new_date = data.get("date", "01/08/2025")
    new_text_block = data.get("recommendation", "Your custom recommendation goes here.")
    output_path = "/tmp/updated.pdf"

    if not os.path.exists(TEMPLATE_PATH):
        return {"error": "Template PDF not found"}

    doc = fitz.open(TEMPLATE_PATH)
    formatted_text = parse_formatting(new_text_block)

    # === ЗАМЕНА ДАТЫ НА ВСЕХ СТРАНИЦАХ ===
    for page in doc:
        matches = page.search_for(old_date)
        for box in matches:
            page.draw_rect(box, color=(1, 1, 1), fill=(1, 1, 1))  # затереть
            x, y = box.tl
            page.insert_text((x + 10, y + 2), new_date, fontsize=10, color=(0, 0, 0))

    # === ВСТАВКА ТЕКСТА НА ВТОРУЮ СТРАНИЦУ ===
    second_page = doc[1] if len(doc) > 1 else doc.new_page()

    x = 72  # отступ слева (1 inch)
    y = 400  # начало блока (подгоняется под шаблон)
    max_width = 460
    font_size = 10
    line_height = 14
    current_page = second_page

    for paragraph in formatted_text.split('\n'):
        words = paragraph.split()
        line = ""
        for word in words:
            test_line = line + (" " if line else "") + word
            if fitz.get_text_length(test_line, fontsize=font_size) < max_width:
                line = test_line
            else:
                current_page.insert_text((x, y), line, fontsize=font_size, color=(0, 0, 0))
                y += line_height
                line = word
                if y > current_page.rect.height - 50:
                    current_page = doc.new_page()
                    y = 50
        if line:
            current_page.insert_text((x, y), line, fontsize=font_size, color=(0, 0, 0))
            y += line_height
            if y > current_page.rect.height - 50:
                current_page = doc.new_page()
                y = 50

    doc.save(output_path)
    return FileResponse(output_path, filename="filled_report.pdf", media_type="application/pdf")


    doc.save(output_path)
    return FileResponse(output_path, filename="filled_report.pdf", media_type="application/pdf")
