import fitz
import os
import re
import json


# Precompiled patterns for efficiency
SPECIAL_CHARS_PATTERN = re.compile(r"[^a-zA-ZÀ-ỹ\s\'\’\"-]")
LEADING_ARABIC_NUMBERS_PATTERN = re.compile(r"^\s*(\d+)\n")
LEADING_ROMAN_NUMERALS_PATTERN = re.compile(r"^\s*[IVXLCDM]+\n")
CHARACTER_NAMES_PATTERN = re.compile(
    r"(Kiều|Thúy Kiều|Thúy Vân|Kim Trọng|Thúc Sinh|Tú Bà|Mã Giám Sinh|Từ Hải|Vương|Mã Kiều|Thúc|Bạc Hạnh|Trạc Tuyền|Hồ Tôn Hiến|Giác Duyên|Đạm Tiên|Kỳ Tâm|Tích Việt|Kiều's|Tú|Mã|Bạc|Bạc Tú)"
)
REMOVE_PATTERNS = {
    "https://thuviensach.vn",
    "VU TRQNG PHl,JN",
    "-e-",
    "Mr. and Mrs. Civilization",
    "MINH+VĂN=VĂN MINH"
}


def clean_text(text):
    """Clean text by removing unwanted characters and patterns."""
    text = text.replace("\t", " ")
    text = text.replace("’", "'")
    # cleaned_text = SPECIAL_CHARS_PATTERN.sub("", text)
    cleaned_text = LEADING_ARABIC_NUMBERS_PATTERN.sub("", cleaned_text)
    cleaned_text = LEADING_ROMAN_NUMERALS_PATTERN.sub("", text)
    lines = cleaned_text.splitlines()

    cleaned_lines = []
    for line in lines:
        line = line.strip()

        if not line or any(pattern in line for pattern in REMOVE_PATTERNS):
            continue

        cleaned_lines.append(line)

    return cleaned_lines


def extract_text_from_pdf(pdf_file, start_page=10, end_offset=4):
    """Extract and clean text from the PDF file."""
    all_texts = []

    for page_index in range(start_page, len(pdf_file) - end_offset):
        page = pdf_file.load_page(page_index)
        text = page.get_text("text")
        cleaned_lines = clean_text(text)
        # cleaned_lines = text.splitlines()
        all_texts.extend(cleaned_lines)

    return all_texts


def save_text_to_file(file_path, texts):
    """Save a list of texts to a file."""
    with open(file_path, "w", encoding="utf-8") as file:
        file.write("\n".join(texts))


if __name__ == "__main__":
    # File path
    vie_pdf_path = os.path.join("..", "raw_dataset", "dumb-luck-vie.pdf")
    eng_pdf_path = os.path.join("..", "raw_dataset", "dumb-luck-eng.pdf")

    # Process PDF file
    vie_pdf_file = fitz.open(vie_pdf_path)
    eng_pdf_file = fitz.open(eng_pdf_path)

    # Extract text from PDF
    vie_texts = extract_text_from_pdf(vie_pdf_file, start_page=3, end_offset=0)
    eng_texts = extract_text_from_pdf(eng_pdf_file, start_page=36, end_offset=0)

    # Save the extracted texts 
    save_text_to_file("english.txt", eng_texts)
    save_text_to_file("vietnamese.txt", vie_texts)

    # Close the PDF file
    vie_pdf_file.close()
    eng_pdf_file.close()
