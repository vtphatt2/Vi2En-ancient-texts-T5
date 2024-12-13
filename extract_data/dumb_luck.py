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
    "\"All alone on an autumn night, my tender heart is sinking.\"",
    "Xuan was suspicious.",
    "sternly to Xuan."
}
IGNORE_PATTERNS = {
    "Chương",
    "Chapter",
    "Dumb Luck",
    "Dumb luck",
    "VU",
}
ENG_WRONG_NEWLINE_PATTERN = re.compile(r'([^":\'])[\s*\n\s*]([^"\'])')
VIE_WRONG_NEWLINE_PATTERN = re.compile(r'([^-?!.":\'])[\s*\n\s*]([^-?!.":\'])')
QUOTE_START_PATTERN = re.compile(r'(:)\s*([\"])')


def process_wrong_newline_char_eng(text):
    """Process wrong newline characters in the text."""
    text = '\n'.join(text)
    text = ENG_WRONG_NEWLINE_PATTERN.sub(r'\1 \2', text)
    return text.splitlines()


def process_wrong_newline_char_vie(text):
    """Process wrong newline characters in the text."""
    text = '\n'.join(text)
    text = VIE_WRONG_NEWLINE_PATTERN.sub(r'\1 \2', text)
    return text.splitlines()


def process_wrong_newline_char_vie(text):
    """Process wrong newline characters in the text."""
    text = '\n'.join(text)
    text = VIE_WRONG_NEWLINE_PATTERN.sub(r'\1 \2', text)
    return text.splitlines()


def pre_map_wrong_text_to_correct_text(text):
    """Map wrong text to correct text."""
    replacement_pairs = [
        ("\t", " "),
        ("–", '-'),
        ("‘", "'"),
        ("’", "'"),
        ("·", '.'),
        ("…", '...'),
        ("'Tm", "\"I'm"),
        ("asmall", "a small"),
        ("stalk. He", "stalk, he"),
        ("to the pavement.", "to the pavement,"),
        ("God damn my mother's milk!", "God damn my mother's milk. All alone on an autumn night, my tender heart is sinking."),
        ("song:", "song,"),
        ("term,\" he blurted out.", "term.\""),
        ("first time.", "first time and blurted out."),
        ("earthly state.", "earthly state,"),
        ("the nether-world.", "the nether-world,"),
        ("He continued to chant:", "He continued to chant,"),
        ("at hand.", "at hand,"),
        ("n.ame", "name"),
        ("seventy kilogram!", "seventy kilogram,"),
        ("scarf.", "scarf,"),
        ("tourist.", "tourist,"),
        ("still inside.", "still inside,"),
        ("her hair up in a bun.", "her hair up in a bun,"),
        ("\"She's here?\" Red-Haired Xuan repeated quizzically.", "Red-Haired Xuan repeated quizzically: \"She's here?\""),
        ("\"My aunt does not approve of such formal language,\" he said", "He said sternly to Xuan: \"My aunt does not approve of such formal language.\""),


        ("dod6i", 'đôi'),
        ("dod65", 'độ'),
        ("dodòi", 'đời'),
        ("mẫu, thỉnh", 'mẫu. Thỉnh'),
        ("lợn,", "lợn."),
        ("thinh,", "thinh."),
        ("bồ côi", "mồ côi"),
        ("miếng hay.", "miếng hay,"),
        ("thiếu nữ,", "thiếu nữ."),
        ("mẩu,", "mẩu."),
        ("quăn.", "quăn,"),
        ("du lịch,", "du lịch."),
        ("côi.", "côi,")

    ]

    for old_text, new_text in replacement_pairs:
        text = text.replace(old_text, new_text)

    return text


def post_map_wrong_text_to_correct_text(text):
    """Map wrong text to correct text."""
    replacement_pairs = [
        ("Move-ment...", "Movement and"),
        ("Popular Movement...", "Popular Movement"),
        ("chimed in bit-terly.", "chimed in bitterly.\n"),
        ("\"You stupid ass!\" Mrs. Deputy Customs Officer chimed in bitterly.","Mrs. Deputy Customs Officer chimed in bitterly:\n \"You stupid ass!"),
        ("\"Who are you calling","Who are you calling"),
        ("Bop!","Bop,")
    ]

    for old_text, new_text in replacement_pairs:
        text = text.replace(old_text, new_text)

    return text


def clean_text(text):
    """Clean text by removing unwanted characters and patterns."""
    text = pre_map_wrong_text_to_correct_text(text)

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
    cleaned_text = QUOTE_START_PATTERN.sub(r'\1\n\2', cleaned_text)

    cleaned_text = post_map_wrong_text_to_correct_text(cleaned_text)
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


def split_into_sentences_quotes_eng(text):
    """Split text into sentences, efficiently handling quotes and preserving honorifics."""
    honorifics = {'Mr.', 'Mrs.', 'Ms.', 'Dr.', 'Prof.', 'Sr.', 'Jr.', 'St.', 'Rev.'}
    sentences = []
    current = []
    quote_stack = []

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

            if quote_stack and char == '"':
                sentence = ''.join(current).strip()
                sentence += line[i+1:]
                sentences.append(sentence.strip())
                quote_stack.pop()
                current = []
                break
            elif quote_stack:
                i += 1
                continue

            # Quote
            if (char == '"'):
                quote_stack.append(char)

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
                # ":" at the end of a line
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
    eng_pdf_path = os.path.join("..", "raw_dataset", "dumb-luck-eng.pdf")

    # Process PDF file
    # vie_pdf_file = fitz.open(vie_pdf_path)
    eng_pdf_file = fitz.open(eng_pdf_path)

    # Extract text from PDF
    vie_texts = read_text_from_file("vietnamese.txt")
    vie_texts = clean_text(vie_texts)
    eng_texts = extract_text_from_pdf(eng_pdf_file, start_page=36, end_offset=0)

    # Save the extracted texts 
    save_text_to_file("english.txt", eng_texts)


    # Split the extracted texts into sentences
    eng_texts = process_wrong_newline_char_eng(eng_texts)
    eng_texts = split_into_sentences_quotes_eng(eng_texts)

    vie_texts = process_wrong_newline_char_vie(vie_texts)
    vie_texts = split_into_sentences_quotes_vie(vie_texts)

    save_text_to_file("english_sentences.txt", eng_texts)
    save_text_to_file("vietnamese_sentences.txt", vie_texts)

    # Close the PDF file
    # vie_pdf_file.close()
    eng_pdf_file.close()