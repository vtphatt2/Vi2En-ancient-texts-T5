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
FOOTNOTE_NUMBER_AFTER_COLON_PATTERN = re.compile(r'(?<!\d)(:)(?:\s*)(\d+)\b')
FOOTNOTE_NUMBER_AFTER_QUOTATION_PATTERN = re.compile(r'(?<!\d)(\")\s*(\d+)\b')
HYPHENATED_WORD_PATTERN = re.compile(r"(\w+)-\s*(\w+)")
PUNCTUATION_PATTERN = re.compile(r'\s*([!\'?.,;])(\s*)')
ELLIPSIS_PATTERN = re.compile(r'\s*\.\s*\.\s*\.(\s*)(\.*)')
REMOVE_TEXTS = {
    "https://thuviensach.vn",
    "-e-",
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
    replacement_pairs_1 = [
        ("\t", " "),
        ("–", '-'),
        ("‘", "'"),
        ("’", "'"),
        ("·", '.'),
        ("…", '...'),
        ("'Tm", "\"I'm"),
        ("asmall", "a small"),
        ("modem", "modern"),
        ("stalk. He", "stalk, he"),
        ("to the pavement.", "to the pavement,"),
        ("God damn my mother's milk!", "God damn my mother's milk. All alone on an autumn night, my tender heart is sinking."),
        ("song:", "song,"),
        ("term,\" he blurted out.", "term.\""),
        ("first time.", "first time and blurted out:"),
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
        ("heroic.", "heroic:"),
        ("scowl.","scowl:"),
        ("muttering under his breath.", "muttering under his breath:"),
        ("ink pot.","ink pot:"),
        ("astrological verse.", "astrological verse:"),
        ("Miss Sugar Cane.","Miss Sugar Cane:"),
        ("to the old man.","to the old man:"),
        ("cross-examine the old man.","cross-examine the old man:"),
        ("thick ears.","thick ears:"),
        ("her teeth.","her teeth:"),
        ("rich wife.","rich wife."),
        ("\"civilization\"-", "civilization.\n"),   
        ("noth-ing at all.","nothing at all,"),
        ("reform movement.", "reform movement,"),
        ("body-and thus", "body. Thus"),
        ("for Europeanization.","for Europeanization,"),
        (", targeting",". He targeted"),
        ("deputy customs officer and died ten years later.", "deputy customs officer. He died ten years later,"),
        ("side, and Xuan","side. Xuan"),
        ("fire him like that!\".", "fire him like that!\".\n"),
        ("small ward.", "small ward,"),
        ("for them to enter.", "for them to enter:"),
        ("piasters in fines;", "piasters in fines."),
        ("Over the next several weeks", "Then... Over the next several weeks"),
        ("the captain.", "the captain,"),
        ("Confucian scholar.", "Confucian scholar:"),
        ("traditional Confucian scholar:", "traditional Confucian scholar."),
        ("dO'.", "do:"),
        ("nerve and tried", "nerve. He tried"),
        ("change the subject.", "change the subject"),
        ("He ordered Min dO'", "by ordering Min dO'"),
        ("Ra cả! Ra lấy", "Ra cả!\n- Ra lấy"),
        ("gave him a kick.", "gave him a kick:"),
        ("turned to him first.", "turned to him first:"),    
        ("fist on the table.", "fist on the table:"),
        ("turned to the fortune-teller.", "turned to the fortune-teller:"),
        ("at the fortune-teller.", "at the fortune-teller:"),
        ("frowned at Red-Haired Xuan.", "frowned at Red-Haired Xuan:"),
        ("one more time.", "one more time:"),
        ("officers, who", "officers. They"),
        ("called out after the car, \"Thank you so much! Please come again!\"", "called out after the car."),
        ("them off at the gate.", "them off at the gate: \"Thank you so much! Please come again!\"\n"),
        ("wife, he", "wife when he"),
        ("Quy C6c Ta", "Quy Coc Tu"),
        ("A Suspicious Case", "."),
        ("He sensed the", "For the first time! He sensed the"),
        ("exited last,", "exited last..."),
        ("Three.", "Three:"),
        ("whistled twice.", "whistled twice,"),
        ("front paws.", "front paws,"),
        ("down her dog.", "down her dog:"),
        ("frowned.", "frowned:"),
        ("Officer hesitated for a moment.", "Officer hesitated for a moment:"),
        ("\"uncouth\"", " 'uncouth'"),
        ("\"equipment\"", "  'equipment' "),
        ("yell.", "yell:"),
        ("piggyback style.", "piggyback style,"),
        ("riding a horse.", "riding a horse:"),
        ("fortune-teller entered the living room.", "fortune-teller entered the living room,"),
        ("toward the sofa.", "toward the sofa:"),
        ("no pants. He", "no pants and he"),
        ("paper-thin pants. This made", "paper-thin pants, which made"),
        ("left.", "left,"),
        ("got up and left,", "got up and left."),
        ("politely and left,", "politely and left."),
        ("frightened.", "frightened:"),
        ("I was frightened:", "I was frightened."),
        ("worried, and frightened:", "worried, and frightened."),
        ("Xuan's face turned red.", "Xuan's face turned red:"),
        ("could muster.", "could muster:"),
        ("to anger, an", "to anger... An"),
        ("the album.", "the album,"),
        ("opened the door.", "opened the door:"),
        ("full of hope.", "full of hope,"),
        ("of Europeanization", "of Europeanization."),
        ("plate-glass window. Although", "plate-glass window, although"),
        ("He smiled to himself.", "He smiled to himself then"),
        ("workers.", "workers:"),
        ("scolded him again.", "scolded him again:"),
        ("letter U.", "letter U"),
        ("she asked the journalist.", ""),
        ("briskly and turned to Xuan.", "briskly and turned to Xuan:"),
        ("blushed and rubbed his hands together.", "blushed and rubbed his hands together:"),
        ("interrupted him.", "interrupted him:"),
        ("glass window. She", "glass window, she"),
        ("a long while.", "a long while:"),
        ("eyes wide in agreement.", "eyes wide in agreement:"),
        ("pitch.", "pitch,"),
        ("calm her down.", "calm her down:"),
        ("Civilization shrugged her shoulders.", "Civilization shrugged her shoulders:"),
        ("utter satisfaction.", "utter satisfaction,"),
        ("appeared unconvinced.", "appeared unconvinced:"),
        ("artist retorted,", "artist retorted."),
        ("face of her customer.", "face of her customer:"),
        ("a glass case.", "a glass case,"),
        ("head vigorously.", "head vigorously:"),
        ("to the artist.", "to the artist:"),
        ("his head very low.", "his head very low:"),
        ("his chair.", "his chair and"),
        ("A Horned Husband", "A Horned Husband."),
        ("The clock struck twelve.", ""),
        ("Out on the street cicadas", "The clock struck twelve. Out on the street cicadas"),
        ("right words.", "right words:"),
        ("vang dcr", "vendour"),
        ("tay 0'", "taylor"),
        ("for an exam.", "for an exam:"),
        ("to another mannequin.", "to another mannequin:"),
        ("again and again.", "again and again:"),
        ("With that,", "With that..."),
        ("god-daIIU1ed", "god-damned"),
        ("God-daIIU", "God-damn"),
        ("in surprise.", "in surprise:"),
        ("behind his back. \"", "behind his back: \""),
        ("do dili", "áo dài"),
        ("nodded insistently.", "nodded insistently:"),
        ("teeth together.", "teeth together:"),
        ("Xuan bowed low.", "Xuan bowed low:"),
        ("woman smiled.", "woman smiled:"),
        ("open and the", "open. The"),
        ("head. \"Oh!", "head: \"Oh!"),
        ("speaking to Red-Haired Xuan.", "speaking to Red-Haired Xuan"),
        ("to interrupt.", "to interrupt:"),
        ("grow angry.", "grow angry:"),
        ("\nsaid the designer.", "said the designer."),
        ("be quiet.", "be quiet:"),
        ("for help.", "for help:"),
        ("inspired the designer.", "inspired the designer:"),
        ("into Xuan's face.", "into Xuan's face:"),
        ("Iwarn", "I warn"),
        ("to the door.", "to the door:"),
        ("entered the shop. He", "entered the shop, he"),
        ("low whisper.", "low whisper:"),
        ("to him again.", "to him again:"),
        ("man's head.", "man's head:"),
        ("hand and moving", "hand. He moved"),
    
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
        ("côi.", "côi,"),
        ("ông là:", "ông là"),
        ("nịnh đầm.", "nịnh đầm,"),
        ("vợ giàu.", "vợ giàu,"),
        ("thì giờ!", "thì giờ,"),
        ("tư lự, trong", "tư lự. Trong"),
        ("gỗ, và ba", "gỗ. Ba"),
        ("đứng lại, hai", "đứng lại. Hai"),
        ("chả bóp!", "chả bóp!\n"),
        ("Phòng giam thì", "- Phòng giam thì"),
        ("nào! Người", "nào!\n- Người"),
        ("thái bình.", "thái bình,"),
        ("Hà Nội - Sơn Tây, Hà Nội - Bắc Ninh", "Hà Nội-Sơn Tây, Hà Nội-Bắc Ninh"),
        ("đâu cả!", "đâu cả;"),
        ("ngoài đường.", "ngoài đường;"),
        ("cả, làm", "cả. Làm"), 
        ("nhiệm mầu.", "nhiệm mầu;"),
        ("đường, hay", "đường. Hay"),
        ("toà, còn", "toà\n- Còn"),
        ("đơ thầy", "đơ.\n- Thầy"),
        ("đánh, tôi", "đánh\n- Tôi"),
        ("biết! Cung", "biết!\n- Cung"),
        ("nhà. Nó", "nhà.\n- Nó"),
        ("không hiểu...","không hiểu,"),
        ("lớn, sao", "lớn\n- Sao"),
        ("nhé? Bảo", "nhé?\n- Bảo"),
        ("thật! Cụ", "thật!\n- Cụ"),
        ("đã xong.", "đã xong,"),
        ("quảnh ở nhà", "quảnh ở nhà."),
        ("MỘT CÁI GHI ÂN", "."),
        ("rừng kỳ quái,", "rừng kỳ quái."),
        ("Trần truồng, nồng nỗng, cậu đứng lên cao tồng ngồng mà hôn mẹ.", ""),
        ("Tức thì cậu bé đứng lên...", "Tức thì cậu bé đứng lên, trần truồng, nồng nỗng, cậu đứng lên cao tồng ngồng mà hôn mẹ."),
        ("tự, chỉ", "tự. Chỉ"),
        ("vào nhà. Chưa", "vào nhà, chưa"),
        ("Mau lên, lau", "Mau lên!\n- Lau"),
        ("“Nhong! nhong! nhong!”", "\n- Nhong! Nhong! Nhong!"),
        ("“Mẹ kiếp! chứ con với chả cái!”", "\n- Mẹ kiếp! chứ con với chả cái!\n"),
        ("nhỉ! Trông", "nhỉ!\n- Trông"),
        ("giọng bà Phó:", "giọng bà Phó."),
        (" dây. Cái", " dây, cái"),
        ("đâu. Tự nhiên", "đâu\n- Tự nhiên"),
        ("bẩm ông ấy", "bẩm\n - Ông ấy"),
        ("theo người, lâu", "theo người. Lâu"),
        ("ước được - bị", "ước được bị"),
        ("thật - nói", "thật, nói"),
        ("giám - bà", "giám, bà"),
        ("được - bị", "được bị"),
        ("cầu tự, bà", "cầu tự. Bà"),
        ("rồi đi... Bà", "rồi đi, bà"),
        ("thang. Đến", "thang, đến"),
        ("khách nữa, bà", "khách nữa. Bà"),
        ("Rồi bà, than ôi! trái ngược - bà", "Rồi bà"),
        ("CUỘC ÂU HOÁ", "CUỘC ÂU HÓA."),
        ("hôm ấy, Xuân", "hôm ấy. Xuân"),
        ("nghĩa!”", "nghĩa!”."),
        ("gì thế? Dạo", "gì thế!\n- Dạo"),
        ("lụa. Nào là", "lụa, nào là"),
        ("chính thế, bây", "chính thế.\n- Bây"),
        ("bà! Nếu", "bà!\n- Nếu"),
        ("Chinh phục! Tôi", "Chinh phục!\n- Tôi"),
        ("Thưa bà, những", "Thưa bà.\n- Những"),
        ("đấy! Dễ", "đấy!\n- Dễ"),
        ("mẹ gì?”", "mẹ gì?”."),
        ("chỉ bảo Xuân:", "chỉ bảo Xuân."),
        ("thế. Giản", "thế, giản"),
        ("thích, cái...", "thích.\n- Cái..."),
        ("trỏ mặt Xuân:", "trỏ mặt Xuân."),
        ("kính rồi", "kính.\n- Rồi"),
        ("bao giờ... rồi.", "bao giờ rồi..."),
        ("“Chả nước mẹ gì cả!”", "“Chả nước mẹ gì cả!”."),
        ("vậy. Có điều", "vậy, có điều"),
        ("mới hỏi lại:", "mới hỏi lại."),
        ("dị, cổ", "dị. Cổ"),
        ("rather old-fashioned.", "rather old-fashioned:"),
        ("bẻ, cái", "bẻ. Cái"),
        ("đáo, đôi", "đáo. Đôi"),
        ("viết báo. Ông", "viết báo, ông"),
        ("tuông. Ông", "tuông, ông"),
        ("- Thật không thể tha thứ được", "- Thật không thể tha thứ được!"),
        ("bở! Đòi", "bở!\n- Đòi"),
        ("ngay! Về", "ngay!\n- Về"),
        ("suỵt. Rồi", "suỵt, rồi"),
        ("xem! Ba công", "xem!\n- Ba công"),

    ]

    for old_text, new_text in replacement_pairs_1:
        text = text.replace(old_text, new_text)

    return text


def post_map_wrong_text_to_correct_text(text):
    """Map wrong text to correct text."""
    text_block = '\n'.join(text)
    replacement_pairs = [
        ("Move-ment...", "Movement and"),
        ("Popular Movement...", "Popular Movement"),
        ("chimed in bit-terly.", "chimed in bitterly.\n"),
        ("\"You stupid ass!\" Mrs. Deputy Customs Officer chimed in bitterly.","Mrs. Deputy Customs Officer chimed in bitterly:\n \"You stupid ass!"),
        ("\"Who are you calling","Who are you calling"),
        ("Bop!","Bop,"),
        ("name.", "name:"),
        ("his new name:", "his new name."),
        ("hik-ing outfit.", "hiking outfit,"),
        ("gingerly en-tered the shop.", "gingerly entered the shop,"),
        ("mur-muring to himself.", "murmuring to himself:"),
        ("\"Mr. ILL...", "\"Mr. ILL...\""),
        ("just stepped out.", "just stepped out\""),
    ]

    for old_text, new_text in replacement_pairs:
        text_block = text_block.replace(old_text, new_text)

    return text_block.splitlines()


def post_fix(text):
    text_block = '\n'.join(text)
    replacement_pairs = [
        ("Nhưng nhà mỹ thuật lại hiểu câu ấy theo ý riêng chứ không phải do lòng ghen tuông, ông vồ lấy câu ấy mà nói: - Thật không thể tha thứ được!\n", ""),
        ("confu-sion.\nHe", "confusion, he"),
    ]

    for old_text, new_text in replacement_pairs:
        text_block = text_block.replace(old_text, new_text)
    return text_block.splitlines()

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
    cleaned_text = FOOTNOTE_NUMBER_AFTER_COLON_PATTERN.sub(r'\1', cleaned_text)
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

    cleaned_lines = post_map_wrong_text_to_correct_text(cleaned_lines)

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
                # sentence += line[i+1:]
                i += 1
                while i < len(line):
                    char = line[i]
                    current.append(char)
                    i += 1
                    if char in "!?":
                        break
                    if (char == '.' and not is_honorific(i-1)):
                        break

                sentence = ''.join(current).strip()
                sentences.append(sentence.strip())
                quote_stack.pop()
                current = []
                continue
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
            
            i += 1

    # Add any remaining text
    if current:
        sentences.append(''.join(current).strip())

    return [sentence for sentence in sentences if sentence]


def split_into_sentences_quotes_vie(text):
    sentences = []
    current = []
    start_quote = False

    for line in text:
        i = 0

        if start_quote:
            start_quote = False
            sentence = ''.join(current).strip()
            sentence += " " + line
            sentences.append(sentence)
            current = []
            continue

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
                if i+1 == len(line) or line[i+1] in '\n':
                    start_quote = True
                    break
            
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
    eng_texts = post_fix(eng_texts)

    vie_texts = process_wrong_newline_char_vie(vie_texts)
    vie_texts = split_into_sentences_quotes_vie(vie_texts)
    vie_texts = post_fix(vie_texts)

    save_text_to_file("english_sentences.txt", eng_texts)
    save_text_to_file("vietnamese_sentences.txt", vie_texts)

    # Close the PDF file
    # vie_pdf_file.close()
    eng_pdf_file.close()