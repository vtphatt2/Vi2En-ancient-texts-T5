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
WRONG_NEWLINE_PATTERN = re.compile(r'([^-":\'])[\s*\n\s*]([^-"\'])')


def process_wrong_newline_char(text):
    """Process wrong newline characters in the text."""
    text = '\n'.join(text)

    text = WRONG_NEWLINE_PATTERN.sub(r'\1 \2', text)
    return text.splitlines()


def clean_text(text):
    """Clean text by removing unwanted characters and patterns."""
    text = text.replace("\t", " ")
    text = text.replace("’", "'")
    text = text.replace("‘", "'")
    text = text.replace("·", '.')
    text = text.replace("–", '-')
    text = text.replace("dod6i", 'đôi')
    text = text.replace("dod65", 'độ')
    text = text.replace("dodòi", 'đời')
    text = text.replace("mẫu, thỉnh", 'mẫu. Thỉnh')
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


def read_text_from_file(file_path):
    """Read text from a file."""
    with open(file_path, "r", encoding="utf-8") as file:
        return file.read()


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
        # Look backwards to find word start
        while word_start > 0 and text[word_start - 1].isalpha():
            word_start -= 1
        return text[word_start:index + 1] in honorifics

    i = 0
    while i < len(text):
        char = text[i]
        current.append(char)

        # Quote handling: stack tracks quotes
        if char == '"':
            if quote_stack and quote_stack[-1] == '"':  # Closing quote
                sentences.append(''.join(current).strip())
                current = []
            else:                                       # Starting quote
                quote_stack.append(char)

        # Skip periods in honorifics (e.g., "Mr.")
        elif char == '.' and is_honorific(i):
            i += 1
            continue

        # End sentence on .!? if not in quotes and followed by space/newline/quote
        elif char in ':.!?' and not quote_stack:
            if i + 1 == len(text) or text[i + 1] in ' \n"':
                sentences.append(''.join(current).strip())
                current = []

        i += 1

    # Add any remaining text
    if current:
        sentences.append(''.join(current).strip())

    return [sentence for sentence in sentences if sentence]


def split_into_sentences_2(text):
    text = ' '.join(text)
    
    # Preprocess honorifics to avoid lookbehind
    honorifics = ['Mr.', 'Mrs.', 'Ms.', 'Dr.', 'Prof.', 'Sr.', 'Jr.', 'St.', 'Rev.']
    for h in honorifics:
        text = text.replace(h, h.replace('.', '@'))
    
    sentence_quote_endings = re.compile(
        r'([^"]+?(?:[.!?…:](?=\s)|$))'
    )

    sentences = []
    buffer = ''
    in_quotes = False

    for match in sentence_quote_endings.finditer(text):
        sentence = match.group(1).strip()
        
        # Restore honorifics
        for h in honorifics:
            sentence = sentence.replace(h.replace('.', '@'), h)

        if sentence.startswith('"'):
            in_quotes = True
            buffer = sentence
            continue

        if in_quotes:
            buffer += ' ' + sentence
            if sentence.endswith(('"', '"')):
                sentences.append(buffer.strip())
                buffer = ''
                in_quotes = False
            continue

        sentences.append(sentence)

    if buffer:
        sentences.append(buffer.strip())

    return [s for s in sentences if s]


def split_into_sentences_quotes_eng(text):
    """Split text into sentences, efficiently handling quotes and preserving honorifics."""
    honorifics = {'Mr.', 'Mrs.', 'Ms.', 'Dr.', 'Prof.', 'Sr.', 'Jr.', 'St.', 'Rev.'}
    sentences = []
    current = []

    def is_honorific(index):
        """Check if a period at the current index is part of an honorific."""
        if index == 0 or line[index - 1] == ' ':
            return False
        word_start = index
        # Look backwards to find word start
        while word_start > 0 and line[word_start - 1].isalpha():
            word_start -= 1
        return line[word_start:index + 1] in honorifics

    for line in text:
        i = 0
        while i < len(line):
            char = line[i]
            current.append(char)

            # Quote
            if char == '"':
                sentences.append(line) # Combine each character to form a sentence
                current = []
                break

            # Skip periods in honorifics (e.g., "Mr.")
            elif char == '.' and is_honorific(i):
                i += 1
                continue

            # End sentence on .!? if not in quotes and followed by space/newline
            elif char in '.!?':
                if i + 1 == len(line) or line[i + 1] in ' \n':
                    sentences.append(''.join(current).strip())
                    current = []

            elif char == ':':
                if i + 1 == len(line) or line[i + 1] in '\n':
                    sentences.append(''.join(current).strip())
                    current = []
            
            i += 1

    # Add any remaining text
    if current:
        sentences.append(''.join(current).strip())

    return [sentence for sentence in sentences if sentence]


def split_into_sentences_quotes_vie(text):
    sentences = []
    current = []

    for line in text:
        i = 0
        while i < len(line):
            char = line[i]
            current.append(char)

            # Quote
            if char == '-' and len(current) == 1:
                sentences.append(line) # Combine each character to form a sentence
                current = []
                break

            # End sentence on .!? if not in quotes and followed by space/newline
            elif char in '.!?':
                if i + 1 == len(line) or line[i + 1] in ' \n':
                    sentences.append(''.join(current).strip())
                    current = []
            
            elif char == '-':
                if i + 1 == len(line) or line[i + 1] in ' \n':
                    sentences.append((''.join(current))[0:len(current) - 1].strip())
                    current = []
                    current.append('-')

            elif char == ':':
                if i + 1 == len(line) or line[i + 1] in '\n':
                    sentences.append(''.join(current).strip())
                    current = []
            
            i += 1

    # Add any remaining text
    if current:
        sentences.append(''.join(current).strip())

    return [sentence for sentence in sentences if sentence]


if __name__ == "__main__":
    # File path
    # vie_pdf_path = os.path.join("..", "raw_dataset", "dumb-luck-vie.pdf")
    # eng_pdf_path = os.path.join("..", "raw_dataset", "dumb-luck-eng.pdf")

    # Process PDF file
    # vie_pdf_file = fitz.open(vie_pdf_path)
    # eng_pdf_file = fitz.open(eng_pdf_path)

    # Extract text from PDF
    vie_texts = read_text_from_file("vietnamese.txt")
    vie_texts = clean_text(vie_texts)
    # eng_texts = extract_text_from_pdf(eng_pdf_file, start_page=36, end_offset=0)

    # Save the extracted texts 
    save_text_to_file("vietnamese.txt", vie_texts)
    # save_text_to_file("english.txt", eng_texts)


    # Split the extracted texts into sentences
    # eng_texts = process_wrong_newline_char(eng_texts)
    # eng_texts = split_into_sentences_quotes_eng(eng_texts)
    print(vie_texts)
    vie_texts = process_wrong_newline_char(vie_texts)
    print(vie_texts)
    vie_texts = split_into_sentences_quotes_vie(vie_texts)
    print(vie_texts)

    # save_text_to_file("english_sentences.txt", eng_texts)
    save_text_to_file("vietnamese_sentences.txt", vie_texts)

    # Close the PDF file
    # vie_pdf_file.close()
    # eng_pdf_file.close()