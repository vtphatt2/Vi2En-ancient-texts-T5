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


# def split_into_sentences(text):
#     """Split text into sentences while preserving honorifics and titles."""
#     honorifics = {'Mr.', 'Mrs.', 'Ms.', 'Dr.', 'Prof.', 'Sr.', 'Jr.', 'St.', 'Rev.'}
#     sentences = []
#     current = []
#     quote_stack = []

#     def is_honorific(index):
#         """Check if a period at the current index is part of an honorific."""
#         if index == 0 or text[index - 1] == ' ':
#             return False
#         word_start = index
#         while word_start > 0 and text[word_start - 1].isalpha():
#             word_start -= 1
#         return text[word_start:index + 1] in honorifics

#     i = 0
#     while i < len(text):
#         char = text[i]
#         current.append(char)

#         # Handle honorific cases
#         if char == '.' and is_honorific(i):
#             i += 1
#             continue

#         # Manage quote stack for proper sentence boundary detection
#         if char == '"':
#             if quote_stack and quote_stack[-1] == '"':
#                 quote_stack.pop()
#             else:
#                 quote_stack.append(char)

#         # Handle ellipses
#         if char == '.' and text[i:i+3] == '...':
#             current.extend(text[i+1:i+3])
#             i += 2
#             continue

#         # Sentence boundaries outside of quotes
#         if char in '.!?:' and not quote_stack:
#             if i + 1 == len(text) or text[i + 1] in ' \n"':
#                 sentences.append(''.join(current).strip())
#                 current = []

#         i += 1

#     # Add remaining text as a sentence
#     if current:
#         sentences.append(''.join(current).strip())

#     return [sentence for sentence in sentences if sentence]


# def split_into_sentences(text):
#     """Split text into sentences, efficiently handling quotes and preserving honorifics."""
#     text = ' '.join(text)  # Normalize whitespace
#     # Define a set of honorifics that should not be split
#     honorifics = {'Mr.', 'Mrs.', 'Ms.', 'Dr.', 'Prof.', 'Sr.', 'Jr.', 'St.', 'Rev.'}
#     sentences = []      # List to hold the final sentences
#     current = []        # List to accumulate characters for the current sentence
#     quote_stack = []    # Stack to keep track of quotes

#     def is_honorific(index):
#         """Check if a period at the current index is part of an honorific."""
#         if index == 0 or text[index - 1] == ' ':
#             return False
#         word_start = index
#         while word_start > 0 and text[word_start - 1].isalpha():
#             word_start -= 1
#         return text[word_start:index + 1] in honorifics

#     i = 0
#     while i < len(text):
#         char = text[i]
#         if quote_stack:
#             quote_stack.append(char)
#         else:
#             current.append(char)

#         # Detect quotes and manage the quote stack
#         if char == '"':
#             if quote_stack:
#                 quote_stack.append(char)
#                 sentences.append(quote_stack.pop().strip())
#                 current = []
#             else:
#                 quote_stack.append(char)

#         # Handle honorifics
#         elif char == '.' and is_honorific(i):
#             i += 1
#             continue

#         # Handle sentence boundaries outside quotes
#         elif char in '.!?:' and not quote_stack:
#             if i + 1 == len(text) or text[i + 1] in '\n"':
#                 sentences.append(''.join(current).strip())
#                 current = []

#         i += 1

#     # Add any remaining text
#     if current:
#         sentences.append(''.join(current).strip())

#     return [sentence for sentence in sentences if sentence]


def split_into_sentences(text):
    """Split text into sentences, efficiently handling quotes and preserving honorifics."""
    text = ' '.join(text)  # Normalize whitespace
    honorifics = {'Mr.', 'Mrs.', 'Ms.', 'Dr.', 'Prof.', 'Sr.', 'Jr.', 'St.', 'Rev.'}
    sentences = []
    current = []
    quote_stack = []

    def is_honorific(index):
        """Check if a period at the current index is part of an honorific."""
        if index == 0 or text[index - 1] == ' ':
            return False
        word_start = index
        while word_start > 0 and text[word_start - 1].isalpha():
            word_start -= 1
        return text[word_start:index + 1] in honorifics

    i = 0
    while i < len(text):
        char = text[i]
        current.append(char)

        # Detect quotes and manage stack
        if char == '"':
            if quote_stack and quote_stack[-1] == '"':
                quote_stack.pop()
                sentences.append(''.join(current).strip())
                current = []
            else:
                quote_stack.append(char)

        # Handle honorifics
        elif char == '.' and is_honorific(i):
            i += 1
            continue

        # Handle sentence boundaries outside quotes
        elif char in '.!?' and not quote_stack:
            if i + 1 == len(text) or text[i + 1] in ' \n"':
                sentences.append(''.join(current).strip())
                current = []

        i += 1

    # Add any remaining text
    if current:
        sentences.append(''.join(current).strip())

    return [sentence for sentence in sentences if sentence]



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

    # Append all english texts to a single string
    save_text_to_file("english_sentences.txt", split_into_sentences(eng_texts))
    save_text_to_file("vietnamese_sentences.txt", split_into_sentences(vie_texts))

    # Close the PDF file
    vie_pdf_file.close()
    eng_pdf_file.close()