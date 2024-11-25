import fitz  # PyMuPDF
import os
import re
from langdetect import detect, DetectorFactory

DetectorFactory.seed = 0  # For consistent results

def extract_text_from_pdf(pdf_file):
    """Extract text from the PDF file."""
    all_texts = []
    # Compile pattern to remove special characters
    # special_chars_pattern = re.compile(r'[^a-zA-ZÀ-ỹ0-9\s.,!?;:\'\"()-]')
    special_chars_pattern = re.compile(r'[^a-zA-ZÀ-ỹ\s\'-]')
    # Compile pattern to remove leading numbers (Arabic and Roman numerals)
    leading_numbers_pattern = re.compile(
        r'^(\d+|[IVXLCDM]+)\s+', re.IGNORECASE
    )
    remove_patterns = [
        "Truyện Kiều",
        "Tác giả Nguyễn Du",
        "Translated by Ngô Bình Anh Khoa",
    ]

    for page_index in range(10, len(pdf_file) - 4):
        page = pdf_file.load_page(page_index)
        text = page.get_text("text")
        text = text.replace('\t', ' ')
        cleaned_text = special_chars_pattern.sub('', text)
        lines = cleaned_text.splitlines()
        for line in lines:
            line = line.strip()
            # Skip empty lines
            if not line:
                continue
            # Skip lines that contain the remove patterns
            if any(pattern in line for pattern in remove_patterns):
                continue
            # Remove leading numbers
            line = leading_numbers_pattern.sub('', line)
            # Append the cleaned line to all_texts
            all_texts.append(line)
    return all_texts

def separate_languages(all_texts):
    """Separate English and Vietnamese texts."""
    eng_texts = []
    vie_texts = []
    for line in all_texts:
        try:
            lang = detect(line)
            if lang == 'en':
                eng_texts.append(line)
            elif lang == 'vi':
                vie_texts.append(line)
        except:
            print(line)
            continue  # Skip lines that cannot be detected
    return eng_texts, vie_texts

if __name__ == "__main__":
    pdf_path = os.path.join('..', 'raw_dataset', 'kieu2.pdf')
    pdf_file = fitz.open(pdf_path)
    all_texts = extract_text_from_pdf(pdf_file)
    eng_texts, vie_texts = separate_languages(all_texts)

    with open("full_poem.txt", "w", encoding="utf-8") as f:
        for line in all_texts:
            f.write(line + "\n")

    with open("english_poem.txt", "w", encoding="utf-8") as f:
        for line in eng_texts:
            f.write(line + "\n")

    with open("vietnamese_poem.txt", "w", encoding="utf-8") as f:
        for line in vie_texts:
            f.write(line + "\n")

    pdf_file.close()