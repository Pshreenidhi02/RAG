# Cell 4 — File parser
from pathlib import Path
from pypdf import PdfReader
from docx import Document

def extract_text_from_pdf(file_path: str) -> str:
    reader = PdfReader(file_path)

    pages = []

    for page in reader.pages:
        text = page.extract_text()

        if text:
            pages.append(text)


    print("Characters extracted:", len(text))
    print()
    print(text[:2000])
    return "\n\n".join(pages)


def extract_text_from_docx(file_path: str) -> str:
    document = Document(file_path)

    paragraphs = [
        paragraph.text
        for paragraph in document.paragraphs
        if paragraph.text.strip()
    ]

    return "\n".join(paragraphs)


def extract_text_from_txt(file_path: str) -> str:
    with open(
        file_path,
        "r",
        encoding="utf-8",
        errors="ignore"
    ) as file:
        return file.read()


def parse_file(file_path: str) -> str:
    path = Path(file_path)
    extension = path.suffix.lower()

    if extension == ".pdf":
        return extract_text_from_pdf(file_path)

    elif extension == ".docx":
        return extract_text_from_docx(file_path)

    elif extension in {".txt", ".md", ".csv"}:
        return extract_text_from_txt(file_path)

    else:
        raise ValueError(
            f"Unsupported file type: {extension}"
        )
    