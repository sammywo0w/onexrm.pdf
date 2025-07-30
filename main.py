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
            erase_rect = fitz.Rect(box.x0, box.y0, box.x0 + 370, box.y0 + 200)
            page.draw_rect(erase_rect, color=(1, 1, 1), fill=(1, 1, 1))

            # Вставка текста с переносами
            x, y = box.x0, box.y0
            max_width = 370
            font_size = 10
            line_height = 14

            current_page = page
            for line in formatted_text.split("\n"):
                words = line.split()
                current_line = ""
                for word in words:
                    test_line = current_line + (" " if current_line else "") + word
                    bbox = current_page.get_textbox(fitz.Rect(x, y, x + max_width, y + 100), flags=1)
                    if current_page.get_text_length(test_line, fontsize=font_size) < max_width:
                        current_line = test_line
                    else:
                        current_page.insert_text((x, y), current_line, fontsize=font_size, color=(0, 0, 0))
                        y += line_height
                        current_line = word

                    if y > current_page.rect.height - 50:
                        current_page = doc.new_page()
                        y = 50
                if current_line:
                    current_page.insert_text((x, y), current_line, fontsize=font_size, color=(0, 0, 0))
                    y += line_height
            break

    doc.save(output_path)
    return FileResponse(output_path, filename="filled_report.pdf", media_type="application/pdf")
