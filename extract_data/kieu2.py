import fitz  # PyMuPDF
import os
import re

def extract_text_from_pdf(pdf_file):
    """Extract text from the PDF file."""
    all_texts = []
    # Patterns to identify unwanted lines
    remove_patterns = [
        "Truyện Kiều",
        "Tác giả Nguyễn Du",
        "Translated by Ngô Bình Anh Khoa",
    ]

    for page_index in range(10, len(pdf_file) - 4):
        page = pdf_file.load_page(page_index)
        text = page.get_text("text")
        # Replace tabs with spaces
        text = text.replace('\t', ' ')
        lines = text.splitlines()
        for line in lines:
            line = line.strip()
            if line:
                # Skip lines containing any of the remove patterns
                if any(pattern in line for pattern in remove_patterns):
                    continue
                all_texts.append(line)
    return all_texts

def separate_texts_by_roman_numerals(all_texts):
    """Separate Vietnamese and English texts using Roman numerals as markers."""
    eng_texts = []
    vie_texts = []
    current_language = 'vi'  # Starting language can be set based on your document
    # Pattern to detect standalone Roman numerals
    roman_numeral_pattern = re.compile(r'^[IVXLCDM]+$', re.IGNORECASE)
    # Pattern to remove leading numbers (Arabic and Roman numerals)
    leading_numbers_pattern = re.compile(r'^(\d+|[IVXLCDM]+)\s+', re.IGNORECASE)

    for line in all_texts:
        # Check if line is a standalone Roman numeral
        if roman_numeral_pattern.match(line):
            # Toggle the current language
            current_language = 'en' if current_language == 'vi' else 'vi'
            continue  # Skip the line with the Roman numeral
        # Remove leading numbers
        line = leading_numbers_pattern.sub('', line).strip()
        if line:
            if current_language == 'vi':
                vie_texts.append(line)
            else:
                eng_texts.append(line)
    return eng_texts, vie_texts

if __name__ == "__main__":
    file_path = os.path.join('..', 'raw_dataset', 'kieu2.pdf')
    pdf_file = fitz.open(file_path)
    all_texts = extract_text_from_pdf(pdf_file)
    pdf_file.close()

    eng_texts, vie_texts = separate_texts_by_roman_numerals(all_texts)

    # Write Vietnamese lines to a file
    with open("vietnamese_poem.txt", "w", encoding="utf-8") as f:
        for line in vie_texts:
            f.write(line + "\n")

    # Write English lines to a file
    with open("english_poem.txt", "w", encoding="utf-8") as f:
        for line in eng_texts:
            f.write(line + "\n")