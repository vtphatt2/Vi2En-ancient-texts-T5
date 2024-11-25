import fitz  # PyMuPDF
import os
import re
import json
from langdetect import detect, DetectorFactory

# Ensure consistent language detection results
DetectorFactory.seed = 0

# Precompiled patterns for efficiency
SPECIAL_CHARS_PATTERN = re.compile(r"[^a-zA-ZÀ-ỹ\s\'\’-]")
LEADING_ARABIC_NUMBERS_PATTERN = re.compile(r"^\s*(\d+)\s+")
LEADING_ROMAN_NUMERALS_PATTERN = re.compile(r"^\s*[IVXLCDM]+\n")
CHARACTER_NAMES_PATTERN = re.compile(
    r"(Kiều|Thúy Kiều|Thúy Vân|Kim Trọng|Thúc Sinh|Tú Bà|Mã Giám Sinh|Từ Hải|Vương|Mã Kiều|Thúc|Bạc Hạnh|Trạc Tuyền|Hồ Tôn Hiến|Giác Duyên|Đạm Tiên|Kỳ Tâm|Tích Việt|Kiều's|Tú|Mã|Bạc|Bạc Tú)"
)
REMOVE_PATTERNS = {
    "Truyện Kiều",
    "Tác giả Nguyễn Du",
    "Translated by Ngô Bình Anh Khoa",
    "The Tale of Kiều",
}


def extract_text_from_pdf(pdf_file, start_page=10, end_offset=4):
    """Extract and clean text from the PDF file."""
    all_texts = []

    for page_index in range(start_page, len(pdf_file) - end_offset):
        page = pdf_file.load_page(page_index)
        text = page.get_text("text")
        cleaned_lines = clean_text(text)
        all_texts.extend(cleaned_lines)

    return all_texts


def clean_text(text):
    """Clean text by removing unwanted characters and patterns."""
    text = text.replace("\t", " ")
    text = text.replace("’", "'")
    cleaned_text = SPECIAL_CHARS_PATTERN.sub("", text)
    lines = cleaned_text.splitlines()

    cleaned_lines = []
    for line in lines:
        # Remove leading numbers and Roman numerals
        line = LEADING_ARABIC_NUMBERS_PATTERN.sub("", line)
        line = LEADING_ROMAN_NUMERALS_PATTERN.sub("", line)
        line = line.strip()

        if not line or any(pattern in line for pattern in REMOVE_PATTERNS):
            continue

        cleaned_lines.append(line)

    return cleaned_lines


def is_vietnamese(text):
    """Determine if the text contains Vietnamese characters through diacritics."""
    vietnamese_pattern = re.compile(
        r'[ÀÁÂÃÈÉÊÌÍÒÓÔÕÙÚĂĐĨŨƠàáâãèéêìíòóôõùúăđĩũơ'
        r'ĂẠẢẤẦẨẪẬẮẰẲẴẶẸẺẼỀỀỂỄỆỈỊỌỎỐỒỔỖỘỚỜỞỠỢỤỦỨỪỬỮỰỲỴÝỶỸ'
        r'àáảãạâấầẩẫậăắằẳẵặèéẻẽẹêếềểễệíìỉĩịòóỏõọôốồổỗộơớờởỡợùúủũụưứừửữựỳýỷỹỵ]'
    )
    return bool(vietnamese_pattern.search(text))


def contains_character_name(line):
    """Check if a line contains a character name."""
    return bool(CHARACTER_NAMES_PATTERN.search(line))


def separate_languages(all_texts):
    """Separate texts into English and Vietnamese."""
    eng_texts, vie_texts = [], []

    for line in all_texts:
        if contains_character_name(line):
            # Remove character names from the line
            no_character_name_line = CHARACTER_NAMES_PATTERN.sub("", line).strip()
            if is_vietnamese(no_character_name_line):
                vie_texts.append(line)
            else:
                eng_texts.append(line)
            continue

        try:
            lang = detect(line)
            if lang == "en":
                eng_texts.append(line)
            elif lang == "vi":
                vie_texts.append(line)
        except Exception:
            print(f"Skipping undetectable line: {line}")

    return eng_texts, vie_texts


def save_text_to_file(file_path, texts):
    """Save a list of texts to a file."""
    with open(file_path, "w", encoding="utf-8") as file:
        file.write("\n".join(texts))


def create_json_file(file_name, vietnamese_lines, english_lines, output_file):
    max_length = max(len(vietnamese_lines), len(english_lines))

    data = []
    for idx in range(max_length):
        vi = vietnamese_lines[idx].rstrip(',').strip() if idx < len(vietnamese_lines) else ""
        en = english_lines[idx].rstrip(',').strip() if idx < len(english_lines) else ""
        data.append({
            "id": idx + 1,
            "vi": vi,
            "en": en
        })

    output = {
        "file_name": file_name,
        "data": data
    }

    with open(output_file, "w", encoding="utf-8") as json_file:
        json.dump(output, json_file, ensure_ascii=False, indent=4)


if __name__ == "__main__":
    # File path
    pdf_path = os.path.join("..", "raw_dataset", "kieu2.pdf")

    # Process PDF file
    pdf_file = fitz.open(pdf_path)
    all_texts = extract_text_from_pdf(pdf_file)

    # Separate languages
    eng_texts, vie_texts = separate_languages(all_texts)

    # Clean up Vietnamese texts (e.g., replace hyphens). No need to clean English texts.
    vie_texts = [re.sub(r'\s*-\s*', ' ', line).strip() for line in vie_texts]

    # Save results to files 
    save_text_to_file("full_poem.txt", all_texts)
    save_text_to_file("english_poem.txt", eng_texts)
    save_text_to_file("vietnamese_poem.txt", vie_texts)
    create_json_file("kieu2.pdf", vie_texts, eng_texts, os.path.join("..", "data", "kieu2.json"))

    # Close the PDF file
    pdf_file.close()
