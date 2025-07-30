import fitz  # PyMuPDF
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse
import os

app = FastAPI()

TEMPLATE_PATH = "onexrm-external-resource-triage-report.pdf"
OUTPUT_PATH = "/tmp/updated.pdf"

@app.post("/generate-pdf")
async def generate_pdf(data: dict):
    new_text_block = data.get("recommendation", "")

    if not os.path.exists(TEMPLATE_PATH):
        return {"error": "Template PDF not found"}

    # Шрифт и отступы
    font_name = "helv"  # Helvetica
    header_size = 18
    body_size = 12
    line_spacing = 16
    margin_left = 72  # 1 inch
    margin_top = 620  # нижняя часть первой страницы
    max_width = 450

    # Очистка от тэгов и символов
    def parse_lines(text):
        lines = []
        for raw_line in text.splitlines():
            line = raw_line.strip()
            if not line:
                continue
            if line.startswith("[h2]") and line.endswith("[/h2]"):
                lines.append((line[4:-5].strip(), True))
            elif line.startswith("[indent"):
                content = line.split("]", 1)[1].strip("[/indent]").strip()
                lines.append(("    " + content, False))
            elif line.startswith("[url="):
                # Преобразовать в простой текст
                parts = line.split("]")
                url = parts[0].replace("[url=", "").rstrip("/")
                text = parts[1].replace("[/url]", "").strip()
                lines.append((f"{text}: {url}", False))
            else:
                line = line.replace("✅", "").replace("⚠️", "").replace("💡", "").replace("·", "").replace("··", "").strip(". ")
                lines.append((line, False))
        return lines

    lines = parse_lines(new_text_block)
    doc = fitz.open(TEMPLATE_PATH)
    page = doc[-1]  # последняя страница
    y = margin_top

    for text, is_header in lines:
        font_size = header_size if is_header else body_size
        rect = fitz.Rect(margin_left, y, margin_left + max_width, y + line_spacing)
        page.insert_textbox(rect, text, fontsize=font_size, fontname=font_name, color=(0, 0, 0), align=0)
        y += line_spacing

        # если не помещается — новая страница
        if y > 800:
            page = doc.new_page()
            y = 72

    doc.save(OUTPUT_PATH)
    return FileResponse(OUTPUT_PATH, filename="filled_report.pdf", media_type="application/pdf")
