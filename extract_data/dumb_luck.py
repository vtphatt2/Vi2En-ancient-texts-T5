import fitz
import os
import re
import json


# Precompiled patterns for efficiency
SPECIAL_CHARS_PATTERN = re.compile(r"[^a-zA-ZÀ-ỹ\s\'\"-]")
PAGE_NUMBER_PATTERN = re.compile(r"\n\s*(\d+)\s*\n")
# PAGE_NUMBER_LINE_PATTERN = re.compile(r'^\s*\d+\s*$')
FOOTNOTE_DESCRIPTION_PATTERN = re.compile(r"\n\d+\..*?(?=\n\d+\.|$)", re.DOTALL)
FOOTNOTE_MARKER_PATTERN = re.compile(r'\s*\(\d+\)')
# FOOTNOTE_NUMBER_AFTER_TEXT_PATTERN = re.compile(r'([^\s\d:,])(\d+)\b')
FOOTNOTE_NUMBER_AFTER_TEXT_PATTERN = re.compile(r'(?<![,])([a-zA-Z])\d+\b')
FOOTNOTE_NUMBER_AFTER_PUNCTUATION_PATTERN = re.compile(r'(?<![,])([!?"\.\'])\s*\d+\b')
FOOTNOTE_NUMBER_AFTER_COMMA_PATTERN = re.compile(r'(?<!\d)(,)(?:\s*)(\d+)\b')
HYPHENATED_WORD_PATTERN = re.compile(r"(\w+)-\s*(\w+)")
PUNCTUATION_PATTERN = re.compile(r'\s*([!\'?.,;])(\s*)')
ELLIPSIS_PATTERN = re.compile(r'\s*\.\s*\.\s*\.(\s*)(\.*)')
REMOVE_TEXTS = {
    "https://thuviensach.vn",
    "-e-",
    "Mr. and Mrs. Civilization",
    "MINH+VĂN=VĂN MINH",
    "Ebook miễn phí tại : www.SachMoi.net",
    "Dumb Luck",
    "Dumb luck",
}
IGNORE_PATTERNS = {
    "Chương",
    "Chapter",
    "Dumb Luck",
    "Dumb luck",
    "VU",
}


def clean_text(text):
    """Clean text by removing unwanted characters and patterns."""
    text = text.replace("\t", " ")
    text = text.replace("’", "'")
    text = text.replace("‘", "'")
    text = text.replace("·", '.')
    text = text.replace("dod6i", 'đôi')
    text = text.replace("dod65", 'độ')
    text = text.replace("dodòi", 'đời')
    for txt in REMOVE_TEXTS:
        text = text.replace(txt, "")

    cleaned_text = FOOTNOTE_DESCRIPTION_PATTERN.sub("", text)
    cleaned_text = FOOTNOTE_MARKER_PATTERN.sub("", cleaned_text)
    cleaned_text = FOOTNOTE_NUMBER_AFTER_TEXT_PATTERN.sub(r'\1', cleaned_text)
    cleaned_text = FOOTNOTE_NUMBER_AFTER_PUNCTUATION_PATTERN.sub(r'\1', cleaned_text)
    cleaned_text = FOOTNOTE_NUMBER_AFTER_COMMA_PATTERN.sub(r'\1', cleaned_text)
    cleaned_text = PAGE_NUMBER_PATTERN.sub("", cleaned_text)
    cleaned_text = HYPHENATED_WORD_PATTERN.sub(r"\1-\2", cleaned_text)
    cleaned_text = PUNCTUATION_PATTERN.sub(r"\1\2", cleaned_text)
    cleaned_text = ELLIPSIS_PATTERN.sub(r"...\1", cleaned_text)
    lines = cleaned_text.splitlines()

    cleaned_lines = []
    for line in lines:
        line = line.strip()

        if not line:
            continue

        if any(pattern in line for pattern in IGNORE_PATTERNS):
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