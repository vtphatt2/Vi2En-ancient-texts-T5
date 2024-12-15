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
        ("blossom wherever he goes.", "blossom wherever he goes"),
        ("passionate embrace.", " passionate embrace:"),
        ("ceiling. He", "ceiling, he"),
        ("coffee table.", "coffee table:"),
        ("entered the room. The", "entered the room, which made The"),
        ("warm greeting.", "warm greeting:"),
        ("coughing. It", "coughing, which"),
        ("ate. He", "ate, he"),
        ("from a diploma", "from a diploma\""),
        ("If it did", "\"If it did"),
        ("uneducated\" He", "uneducated.\"\nHe"),
        ("legal framework. This", "legal framework, which"),
        ("executed. He", "executed and he"),
        ("several moments.", "several moments:"),
        ("explained apologetically.", "explained apologetically:"),
        ("high-tech assassination.", "high-tech assassination:"),
        ("the question.", "the question:"),
        ("She paused for a moment.", "She paused for a moment:"),
        ("turned to Grandpa H6ng.", "turned to Grandpa Hong:"),
        ("\"W\"hines", "Whines"),
        ("entered the conversation.", "entered the conversation:"),
        ("diagnostic machine.", "diagnostic machine,"),
        ("cut him off.", "cut him off:"),
        ("How unexpected, indeed!", "How unexpected, indeed,"),
        ("closed his eyes.", "closed his eyes,"),
        ("a rickshaw coolie.", "a rickshaw coolie,"),
        ("time that evening.", "time that evening:"),
        ("Grandma ignored him.", "Grandma ignored him:"),
        ("Grandma held her tongue.", ""),
        ("silence any longer.", "silence any longer:"),
        ("she wanted. And", "she wanted and"),
        ("continued to retch.", "continued to retch:"),
        ("and peeked inside.", "and peeked inside,"),
        ("during the funeral. Everyone", "during the funeral, everyone"),
        ("past exploits.", "past exploits:"),
        ("listened to him. They", "listened to him, they"),
        ("less impressed.", "less impressed:"),
        ("His eyes welled up with hatred. ", ""),
        ("Only the homed senior clerk was silent.", "Only the homed senior clerk was silent, his eyes welled up with hatred."),
        ("herbalists/'", "herbalists\""),
        (" attack his younger sister.", " attack his younger sister:"),
        ("she protested.", "she protested,"),
        ("to do.\"", "to do\""),
        ("offered a suggestion.", "offered a suggestion:"),
        ("is really sick.", "is really sick"),
        ("attention to himself.", "attention to himself:"),
        ("h-.", "h-"),
        ("prince. They", "prince, they"),
        ("the sacred medicine.", "the sacred medicine"),
        ("-;-", " - "),
        ("toward the stairs,", "toward the stairs..."),
        ("day and night.", "day and night to"),
        ("He helped his father", "help his father"),
        ("his spittoon,", "his spittoon..."),
        ("the leaves.", "the leaves:"),
        ("the light.", "the light:"),
        ("Bia Pagoda!", "Bia Pagoda,"),
        ("Are you talking to me?", "\n\"Are you talking to me?"),
        ("Lung. \"Let", "Lung: \"Let"),
        ("his mistake.", "his mistake:"),
        ("palms defensively.", "palms defensively:"),
        ("did not flinch.", "did not flinch:"),
        ("stuffed snails.", "stuffed snails:"),
        ("usual whining.", "usual whining:"),
        ("from his sleep. He", "from his sleep, he"),
        ("beside the bed.", "beside the bed:"),
        ("Xuan began,", "Xuan began."),
        ("Civilization winked at Xuan.", "Civilization winked at Xuan,"),
        ("his strength. He", "his strength, he"),
        (" quietly. He", " quietly, he"),
        ("boldly broke the silence.", "boldly broke the silence:"),
        ("waiting game;", "waiting game..."),
        ("pointed out repeatedly Xuan's youthful promise", "pointed out repeatedly"),
        ("Shut up, already).", "Shut up, already) that Xuan's youthful promise."),
        ("consumed Mrs. Civilization.", "consumed Mrs. Civilization,"),
        ("continued to rise.", "continued to rise,"),
        ("kept silent.", "kept silent,"),
        ("H6ng (I know! What a pain!) was", "Hong was"),
        ("daughter, Miss Snow.", "daughter, Miss Snow;"),
        ("Joseph Thie\"t", "Joseph Thiet"),
        ("at the tailor shop.", "at the tailor shop,"),
        ("at West Lake.", "at West Lake,"),
        ("shop by himself.", "shop by himself:"),
        ("was silent for a moment.", "was silent for a moment:"),
        ("fully grasped.", "fully grasped:"),
        ("day's plans.", "day's plans:"),
        ("dirty item.", "dirty item;"),
        ("\"No ways!\"", "\"No ways!\"."),
        ("bide his time.", "bide his time,"),
        ("felt nothing.", "felt nothing,"),
        ("sprang to his feet.", "sprang to his feet:"),
        ("up to explain.", "up to explain:"),
        ("hesitated for a moment.", "hesitated for a moment,"),
        ("hand to the horned senior clerk.", "hand to the horned senior clerk:"),
        ("and eagerly.", "and eagerly:"),
        ("of rubber breasts.", "of rubber breasts:"),
        ("her chest forward.", "her chest forward:"),
        ("boldly toward Xuan.", "boldly toward Xuan:"),
        ("behind his back.", "behind his back:"),
        ("out the window.", "out the window:"),
        ("authenticity.", "authenticity,"),
        ("on the hand.", "on the hand:"),
        ("affiliation.", "affiliation;"),
        ("of each other's families.", "of each other's families;"),
        ("of the lake.", "of the lake;"),
        ("be dishonored.", "be dishonored;"),
        ("in the tailor shop.", "in the tailor shop:"),
        ("fashionable women.", "fashionable women:"),
        ("castle.", "castle"),
        ("courts and several", "courts. Several"),
        ("the other guests.", "the other guests:"),
        ("introduce them.", "introduce them:"),
        ("disease.", "disease;"),
        ("and gonorrhea.", "and gonorrhea;"),
        ("beyond belief!", "beyond belief that"),
        ("by one of the modern girls.", "by one of the modern girls:"),
        ("turned to Miss Snow.", "turned to Miss Snow:"),
        ("girl. \"Let's", "girl: \"Let's"),
        ("excused himself.", "excused himself then"),
        ("addressed Xuan.", "addressed Xuan:"),
        ("the commotion.", "the commotion,"),
        ("forever. It's too dangerous.", "forever, it's too dangerous"),
        ("m6ng ma rrri!' \"", "mong ma rrrit\"."),
        ("Miss Snow jealous.", "Miss Snow jealous:"),
        ("on the mouth.", "on the mouth:"),
        ("pushed them away.", "pushed them away:"),
        ("ultimate favor.", "ultimate favor,"),
        ("Conservatism of Mrs. Deputy Customs Officer", "Conservatism of Mrs. Deputy Customs Officer."),
        ("for a response.", "for a response:"),
        ("stopped him.", "stopped him:"),
        ("on her fingers.", "on her fingers:"),
        ("people! There", "people!\"\n\"There"),
        ("lit up.", "lit up:"),
        ("how to respond.", "how to respond,"),
        ("face of a poet.", "face of a poet;"),
        ("elephant style.", "elephant style and"),
        ("''Here!", "\"Here!"),
        ("as air.", "as air,"),
        ("rival beauty.", "rival beauty,"),
        ("life's bitterness.", "life's bitterness;"),
        ("hands with joy.", "hands with joy:"),


        

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
        ("ruột, vì", "ruột.\n- Vì"),
        ("gì đâu! Bao", "gì đâu!\n- Bao"),
        ("ạ. Dì", "ạ.\n- Dì"),
        ("cả, đến", "cả. Đến"),
        ("lắm! Mới", "lắm!\n- Mới"),
        ("sao? Việc", "sao!\n- Việc"),
        ("bàn - cái bàn lùn tìn tịt - đài các", "bàn, cái bàn lùn tìn tịt, đài các"),
        ("nước! Mở", "nước!\n- Mở"),
        ("Cụ đã là một người dân bảo hộ trung thành, một viên chức gương mẫu, một người cha nhân từ vì sợ sệt con cái như một người nô lệ.", ""),
        ("phòng. Trên ngực", "phòng, trên ngực"),
        ("Xưa kia, cụ là một ông phán.", "Xưa kia, cụ là một ông phán, cụ đã là một người dân bảo hộ trung thành, một viên chức gương mẫu, một người cha nhân từ vì sợ sệt con cái như một người nô lệ."),
        ("chết: ra", "chết. Ra"),
        ("sù; trước", "sù. Trước"),
        ("lộn; nằm", "lộn. Nằm"),
        ("về đi, là vì", "về đi.\n- Là vì"),
        ("thôi. Toa", "thôi.\n- Toa"),
        ("- Phải đấy", "- Phải đấy!"),
        ("tuổi, bây", "tuổi.\n- Bây"),
        ("ba, nếu", "ba.\n- Nếu"),
        ("mọc sừng!” Lúc", "mọc sừng!”.\n Lúc"),
        ("lắm! Ho", "lắm!\n- Ho"),
        ("thở, có", "thở.\n- Có"),
        ("bệnh, chắc", "bệnh.\n- Chắc"),
        ("kỳ quái, không", "kỳ quái!\n Không"),
        ("lại. Trên cái", "lại, trên cái"),
        ("đông lắm. Ngoài", "đông lắm, ngoài"),
        ("một người ốm nặng.", "một người ốm nặng,"),
        ("nên giàu, âu", "nên giàu. Âu"),
        ("Thiết - một bạn thân của Văn Minh - thì", "Thiết, một bạn thân của Văn Minh, thì"),
        ("Bainville chết, lúc", "Bainville chết.\n- Lúc"),
        ("đương bàn:", "đương bàn."),
        ("nhất! Thế", "nhất!\n- Thế"),
        ("vỗ vào nhau", "vỗ vào nhau."),
        ("bước vào. Cô", "bước vào, cô"),
        ("lang, tôi", "lang.\n- Tôi"),
        ("Chết! Sao", "Chết!\n- Sao"),
        ("lang? Người", "lang?\n- Người"),
        ("Ồ! Toa", "Ồ!\n- Toa"),
        ("Chính thế! Ông", "Chính thế!\n- Ông"),
        ("Ồ! Phiền", "Ồ!\n- Phiền"),
        ("lúc, để", "lúc. Để"),
        ("thế, nhưng", "thế.\n- Nhưng"),
        ("toi! Ðã", "toi!\n- Ðã"),
        ("xem! Nước", "xem!\n- Nước"),
        ("thế? Cụ", "thế!\n- Cụ"),
        ("rồi! Cả", "rồi!\n- Cả"),
        ("nhìn nhau. Sự", "nhìn nhau, sự"),
        ("thang, ông", "thang. Ông"),
        ("này? Tôi", "này!\n- Tôi"),
        ("Thưa cụ con", "Thưa cụ,\n- Con"),
        ("ngồi câm làm", "ngồi câm. Làm"),
        ("thuốc”.", "thuốc”"),
        ("ra. Ảnh hưỏong", "ra, ảnh hưởng"),
        ("ấy lắm. Nó", "ấy lắm, nó"),
        ("Chao ôi! Thế", "Chao ôi, thế"),
        ("Thánh đền Bia - một", "Thánh đền Bia, một"),
        ("thú được - ông", "thứ được, ông"),
        ("con rể cụ - ông phán mọc sừng - vẫn", "con rể cụ, ông phán mọc sừng, vẫn"),
        ("thói quaen...", "thói quen"),
        ("cái đặc ân.", "cái đặc ân,"),
        ("một cái đặc ân. Bọn", "một cái đặc ân, bọn"),
        ("được cụ bà...", "được cụ bà"),
        ("(Biết rồi! Khổ lắm!) đưong", "đương"),
        ("nhỉ? Sao", "nhỉ!\n- Sao"),
        ("hẳn? Họ", "hẳn!\n- Họ"),
        ("thế, tay", "thế. Tay"),
        ("rộng - sự ấy thật hãn hữu - nên", "rộng, sự ấy thật hãn hữu, nên"),
        ("mình, bà", "mình. Bà"),
        ("nỗi! Nhưng", "nỗi!\n- Nhưng"),
        ("nguẩy đầu:", "nguẩy đầu."),
        ("tỉnh - và cũng có cơ hội - nên", "tỉnh, và cũng có cơ hội, nên"),
        ("việc, em", "việc.\n- Em"),
        ("“BAN SỬ NỮ”", "“BAN SỬ NỮ”."),
        ("cả, thành", "cả. Thành"),
        ("...” là", "...”. Là"),
        ("lên, rồi đến", "lên. Rồi đến"),
        ("lối Nhật,", "lối Nhật."),
        ("phòng! Chúng", "phòng!\n- Chúng"),
        ("nước, có", "nước. Có"),
        ("đoan, ông", "đoan. Ông"),
        ("ông đốc! Thật", "ông đốc; Thật"),
        ("nhất! Vì", "nhất!\n- Vì"),
        ("nhau, may", "nhau. May"),
        ("này! Ông", "này!\n- Ông"),    
        ("Ai? Bà", "Ai?\n- Bà"),
        ("Hở? Hở ", "Hở?\n- Hở "),
        ("hạnh! Xứng", "hạnh!\n- Xứng"),
        ("minh, mấy", "minh.\n- Mấy"),
        ("Tuyết nhưng", "Tuyết. Nhưng"),
        ("đáng khen:", "đáng khen."),
        ("yên! Không", "yên!\n- Không"),
        ("Vierge! Nghĩa", "Vierge!\n- Nghĩa"),
        ("gì! Chú", "gì!\n- Chứ"),
        ("BẢO THỦ CỦA BÀ PHÓ ÐOAN", "BẢO THỦ CỦA BÀ PHÓ ÐOAN."),
        ("nhỉ! Khi", "nhỉ!\n- Khi"),
        ("khổ mà", "khổ.\n- Mà"),
        ("lắm! Thật", "lắm!\n- Thật"),
        ("đốc ạ. Nếu", "đốc ạ!\n- Nếu"),
        ("đi! Ðể", "đi!\n- Ðể"),
        ("thật sự. Thỉnh", "thật sự, thỉnh"),
        ("cả mặt.", "cả mặt,"),
        ("anh! Một", "anh!\n- Một"),
        ("chim, Tuyết", "chim. Tuyết"),
        ("nga rất to:", "nga rất to."),
        ("hoa - Hoài", "hoa Hoài."),
        ("lại ngâm:", "lại ngâm."),
        ("tơi thay,", "tơi thay."),

        ("bent down.", "bent down,"),
        ("with both arms.", "with both arms,"),
        ("low to Xuan.", "low to Xuan,"),
        ("his own.", "his own:"),
        ("Snow blanched.", "Snow blanched:"),
        ("elegant way.", "elegant way;"),
        ("senior clerk's wife.", "senior clerk's wife:"),
        ("wife. If not,", "wife, if not,"),
        ("stuck out his chest.", "stuck out his chest:"),
        ("clerk turned pale.", "clerk turned pale:"),
        ("even paler.", "even paler:"),
        ("fully dressed.", "fully dressed:"),
        ("he said gently.", ""),
        ("head respectfully.", "head respectfully,"),
        (" to break down.", " to break down:"),
        ("clerk's reasoning.", "clerk's reasoning,"),
        ("different approach.", "different approach:"),
        ("protest.", "protest:"),
        ("the lover.", "the lover,"),
        ("another solution.", "another solution:"),
        ("Xuan bowed his head.", "Xuan bowed his head:"),
        ("presence in the Fairyland Hotel.", "presence in the Fairyland Hotel;"),
        ("tarnished.", "tarnished;"),
        ("lover red-handed.", "lover red-handed;"),
        ("to his wife's.", "to his wife's:"),
        ("to lawyers.", "to lawyers,"),
        ("upon Miss Snow.", "upon Miss Snow:"),
        ("the name of Miss Snow.", "the name of Miss Snow:"),
        ("pointed at Xuan.", "pointed at Xuan:"),
        ("rickshaw. She", "rickshaw, she"),
        ("like a mussel.", "like a mussel:"),
        ("Officer smiled.", "Officer smiled:"),
        ("face of M.", "face of Mr."),
        ("lower and lower.", "lower and lower;"),
        ("glass. \"Ladies", "glass: \"Ladies"),
        ("hour. He spoke", "hour"),
        ("tend to do.", "tend to do;"),
        ("court. She", "court, she"),
        ("him on as well.", "him on as well:"),
        ("well. \"That", "well: \"That"),
        ("deeply for several minutes.", "deeply for several minutes;"),
        ("and Mr. ILL.", "and Mr. ILL that"),
        ("in the country.", "in the country,"),
        ("eyes tightly.", "eyes tightly:"),
        ("hotel room.", "hotel room,"),
        ("eyes. \"What", "eyes: \"What"),
        ("louder.", "louder:"),
        ("dismissal of the opium servant.", "dismissal of the opium servant,"),
        ("Grandma's face.", "Grandma's face:"),
        ("the servant.", "the servant,"),
        ("her fist down on the table.", "her fist down on the table:"),
        ("Grandpa sat up.", "Grandpa sat up:"),
        ("of Fate", "of Fate."),
        ("in the morning.", "in the morning,"),
        ("seen. Glancing", "seen, glancing"),
        ("intellectuals. He", "intellectuals, he"),
        ("layer of powder.", "layer of powder,"),
        ("fashionable face.", "fashionable face:"),
        ("on the bed.", "on the bed:"),
        ("control herself.", "control herself:"),
        ("powder his face.", "powder his face:"),
        ("Grandma asked.", ""),
        ("\"Is that true?\"", ""),
        ("surprised him.", "surprised him:"),
        ("Civilization shook his head.", "Civilization shook his head:"),
        ("in his face.", "in his face:"),
        ("face. \"There", "face: \"There"),
        ("thunderbolt.", "thunderbolt,"),
        ("/1 Are you", "\"Are you"),
        ("thought for a while.", "thought for a while:"),
        ("of evil spirits.", "of evil spirits;"),
        ("to Heaven.", "to Heaven;"),
        ("characters.", "characters;"),


        ("hủ, muốn", "hủ.\n- Muốn"),
        ("anh? Ấy", "anh?\n- Ấy"),
        ("chịu hàng:", "chịu hàng."),
        ("ngài! Thế", "ngài!\n- Thế"),
        ("cựu, trông", "cựu.\n- Trông"),
        ("nói, nó", "nói. Nó"),
        ("kia mà rằng!", "kia mà rằng:"),
        ("à! Nếu", "à!\n- Nếu"),
        (" Sao? Ngay", " Sao?\n- Ngay"),
        ("cẳng đi ngay.", "cẳng đi ngay;"),
        ("lên: “Giời ơi! chồng tôi!”.", "lên.\n- Giời ơi! chồng tôi!\n"),
        ("ở hồ cả.", "ở hồ cả;"),
        ("ngài! Bẩm", "ngài!\n- Bẩm"),
        ("mục xã giao:", "mục xã giao."),
        ("hổ thẹn cãi:", "hổ thẹn cãi."),
        ("hại... Vậy", "hại...\n- Vậy"),
        ("ngay không", "ngay.\n- Không"),
        ("giờ! Tuy", "giờ!\nTuy"),
        ("nẫy, lại", "nẫy. Lại"),
        ("chồng, Xuân", "chồng. Xuân"),
        ("cho, nếu", "cho.\n- Nếu"),
        ("nước đại.", "nước đại,"),
        ("sừng - nguyên là cô Hoàng Hôn - và", "sừng, nguyên là cô Hoàng Hôn, và"),
        ("trị và một", "trị. Với một"),
        ("đứng lên...", "đứng lên"),
        ("thao, bà", "thao.\n Về bà"),
        ("đình, trào", "đình.\nVề trào"),
        ("ten - nít", "ten-nít"),
        ("đời, không", "đời. Nó không"),
        ("chòng chọc.", "chòng chọc;"),
        ("mấy câu:]", "mấy câu:"),
        ("đốc! Nói", "đốc!\n- Nói"),
        ("trách nhiệm.", "trách nhiệm"),
        ("vừa nghĩ:", "vừa nghĩ."),
        ("tế, chẳng", "tế. Chẳng"),
        ("tốt chua", "tốt. Chưa"),
        ("đấy! Gọi", "đấy!\n- Gọi"),
        ("ố mà rằng:", "ố."),
        ("KỲ... NGÔN", "KỲ NGÔN"),
        ("SỐ PHẬN", "SỐ PHẬN."),
        ("tiếng chuông.", "tiếng chuông;"),
        ("cửa phòng.", "cửa phòng,"),
        ("ra, làm", "ra. Điều này làm"),
        ("gõ của.", "gõ cửa,"),
        ("đáp, điếu", "đáp. Điếu"),
        ("cốt yếu. Ðiều", "cốt yếu, điều"),
        ("Ôi! Thật", "Thật"),
        ("đành! Ðâý", "đành!\n- Ðấy"),
        ("sức. Nhưng", "sức, nhưng"),
        ("nỗi! Sao", "nỗi!\n- Sao"),
        ("của mẹ.", "của mẹ,"),
        ("đối! Mà", "đối!\n- Mà"),
        ("ghế, hai", "ghế. Hai"),
        ("gối, chốc", "gối. Chốc"),
        ("gở, bà", "gở! Bà"),
        ("ra miệng.", "ra miệng,"),
        ("con - mà", "con, mà"),
        ("lắm, hay", "lắm. Hay"),
        ("mẹ. Nhất", "mẹ, nhất"),
        ("đã là cùng.", "đã là cùng,"),
        ("tấu: thôi", "tấu. Thôi"),
        ("Phú chăng? Hay", "Phú hay"),
        ("bọn đánh quần. Bà", "bọn đánh quần, bà"),
        ("biết, vì bà", "biết. Vì bà"),
        ("nõn thì ông", "nõn. Thì ông"),
        ("nữa, và muốn", "nữa. Và muốn"),
        ("vơ, ông", "vơ. Ông"),
        ("CÁCH PHẬT GIÁO", "CÁCH PHẬT GIÁO."),
        ("ấy. sở", "ấy, sở"),
        ("Xuân, và tuy", "Xuân. Tuy"),
        ("“Mẹ kiếp! Chẳng nước mẹ gì cả!”", "“Mẹ kiếp, Chẳng nước mẹ gì cả”"),
        ("vân vân...", "vân vân,"),
        ("khác! Ðộng", "khác!\n- Ðộng"),
        ("biết! Những", "biết!\n- Những"),
        ("chán, vì", "chán.\n- Vì"),
        ("nói mà đúng.", "nói mà đúng,"),
        ("thế! Dễ", "thế!\n- Dễ"),
        ("để thì thào:", "để thì thào."),
        ("lắm. Này", "lắm.\n- Này"),
        ("thôi. Lắm", "thôi.\n- Lắm"),
        ("ba, thế", "ba.\n- Thế"),
        ("lên miệng, khẽ đáp:", "lên miệng, khẽ đáp."), 
        ("mầu; Thằng", "mầu. Thằng"),
        ("à? Hoàn", "à!\n- Hoàn"),
        ("sổ... Ông", "sổ, ông"),
        ("cả! Cậu", "cả!\n- Cậu"),
        ("lệnh. Ðể", "lệnh.\n- Ðể"),
        (", điều ấy không cần phải nói...", ". Điều ấy không cần phải nói,"),
        ("nhân, Xuân", "nhân. Xuân"),
        ("lự thì có", "lự. Có"),
        ("ông sư.", "ông sư,"),
        # ("nâu, đi", "nâu. Đi"),
        # ("hàm hỏi:", "hàm hỏi."), 
        ("minh vì", "minh. Vì"),
        ("gì? Mời", "gì!\n- Mời"),
        ("mõ à? Sao", "mõ à!\n- Sao"),
        ("ạ. Duyên", "ạ.\n- Duyên"),
        ("Phật! Ở", "Phật!\n- Ở"),
        ("thời trang:", "thời trang."),
        ("ngài, vậy nếu", "ngài.\n- Vậy nếu"),
        ("Xuân, nguyên", "Xuân.\n- Nguyên là"),
        ("cách... Nếu", "cách.\n- Nếu"),
        ("bàn tay:", "bàn tay."),
        ("NỔI GIẬN", "NỔI GIẬN."),



        ("white legs.", "white legs;"),
        ("eyes wide.", "eyes wide:"),
        ("head. \"We", "head: \"We"),
        ("Reforms Buddhism", "Reforms Buddhism."),
        ("ease. They", "ease, they"),
        ("\"Damn it!\"", "'Damn it!'"),
        ("\"God-damn my mother's milk.\"\n", "\"God-damn my mother's milk.\""),
        ("struggle.", "struggle:"),
        ("or Buddha.", "or Buddha;"),
        ("constitution.", "constitution;"),
        ("Blessing. \"It's", "Blessing: \"It's"),
        ("out loud.", "out loud:"),
        ("private. They moved", "private, they moved"),
        ("horny!\"","horny!"),
        ("window. His", "window, his"),
        ("roof and two", "roof. Two"),
        ("doctor's question.", "doctor's question:"),
        ("at. Seeing", "at, seeing"),
        ("manner.", "manner:"),
        ("normal person.", "normal person,"),
        ("lustful!", "lustful"),
        ("Blessing. He", "Blessing, he"),
        ("environment.\"", "environment\""),
        ("the hallway.", "the hallway:"),
        ("rubber heels.", "rubber heels,"),
        ("sensual look about him.", "sensual look about him:"),
        ("gold teeth.", "gold teeth,"),
        ("blushed.", "blushed:"),
        ("to another.", "to another:"),
        ("\"Wow!\" said Xuan.", ""),
        ("interrupted the monk.", "interrupted the monk:"),
        ("winked at Xuan.", "winked at Xuan:"),
        ("on the table.", "on the table:"),
        ("Officer entered the room.", "Officer entered the room:"),
        ("the room. She", "the room, she"),
        ("Gets Angry", "Gets Angry."),


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
        ("Offi-cer.", "Officer:"),
        ("H6ng Lo T,t Thie'u Khanh medaJ", "Hồng Lô Tự Thiếu Khanh medal"),
        ("hiệu - có", "hiệu, có"),
        ("pains.\"At that", "pains.\"\nAt that"),
        ("daugh-ter-entered the room.", "daughter entered the room,"),
        ("she an-nounced, ", "she announced.\n"),
        ("it is,\"\nXuan", "it is,\" Xuan"),
        ("is well under way...", "is well under way...\""),
        ("com-plain.", "complain"),
        ("syphilis... \"", "syphilis...\"."),
        ("red hair.", "red hair:"),
        ("Ze... da... da... mua.", "\"Ze... da... da... mua.\""),
        ("Mong pe' y ~ Pa ri! .", "\"Mông Pế y ề Pa rí! ...\""),
        ("adjacent room.", "adjacent room:"),
        ("cửa, phút,", "cửa. Sau 15 phút,"),
        ("say... ?", "say..."),
        ("\"My dear girlfriends and boyfriends... \"", "\"My dear girlfriends\"\n\"My dear boyfriends...\""),
        ("Lip, lip, lc:J... Hua rra!\"", "\"Lip, lip, lo... Hua rra!\""),
        ("concluded his speech.", "concluded his speech:"),
        ("socialist Leon Blum.", "socialist Leon Blum;"),
        ("a summit.", "a summit,"), 
        ("from lace.", "from lace,"),
        ("laun-dry woman.", "laundry woman:"),
        ("ai biết...", "ai biết,"),
        ("xem...", "xem,"),
        ("đúng! Tôi", "đúng!\n- Tôi"),
        ("peculiar conditions...", "peculiar conditions...\""),

    ]

    for old_text, new_text in replacement_pairs:
        text_block = text_block.replace(old_text, new_text)

    return text_block.splitlines()


def post_fix(text):
    text_block = '\n'.join(text)
    replacement_pairs = [
        ("Nhưng nhà mỹ thuật lại hiểu câu ấy theo ý riêng chứ không phải do lòng ghen tuông, ông vồ lấy câu ấy mà nói: - Thật không thể tha thứ được!\n", ""),
        ("confu-sion.\nHe", "confusion, he"),
        ("son and offered up", "son.\nHe offered up"),
        ("Ph<;i.m Quynh and Nguy~n Viin VInh", "Phạm Quỳnh and Nguyễn Văn Vĩnh"),
        ("uneducated.\" He", "uneducated.\"\nHe"),
        ("suit.\nHe had bought it", "suit that he had bought"),
        ("Venereal Disease Treatment.\nIt was", "Venereal Disease Treatment, it was"),
        ("Th~p h,r L{:ral", "Thập Tự Lửa"),
        ("Conservatism of Mrs. Deputy Customs Officer After", "Conservatism of Mrs. Deputy Customs Officer.\nAfter"),
        ("immediately,\"\nhe", "immediately,\" he"),
        ("ngài, Ấy", "ngài.\nẤy"),
        ("l.\nHip, hip, hip...\nHoura 1", ""),
        ("Civilization.\n\"Maybe", "Civilization \"Maybe"),
        ("responded.\n\"No", "responded. \"No"),
        ("immediately!\"\nsaid", "immediately!\" said"),


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