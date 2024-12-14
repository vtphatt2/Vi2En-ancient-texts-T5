import fitz
import PyPDF2
import re

file_path = "Nhat ky trong tu.pdf"
# Regex to detect sentences with no words
RE_NO_WORDS = r'^[^a-zA-Z]*$'
RE_MATCH_NUMER = r'^(I|II|III|IV|V|VI|VII|VIII|IX)$'
RE_ALL_CAPS = r'^[AÁÀẠẢÃĂẮẰẶẲẴÂẤẦẬẨẪBCDĐEÉÈẸẺẼÊẾỀỆỂỄGHIÌÍỈĨỊKLMNOÓÒỌỎÕÔỐỒỘỔỖƠỚỜỢỞỠPQRSTUÚÙỤỦŨƯỨỪỰỬỮVXYỲÝỶỸỴ\s0123456789.,“!”()-+:-]+$'
RE_FIRST_WORD_CAPITAL = r'^[AĂÂBCDĐEÊGHIKLMNOÔƠPQRSTUƯVXYÁÀẠẢÃĂẮẰẶẲẴÂẤẦẬẨẪÉÈẸẺẼÊẾỀỆỂỄÓÒỌỎÕÔỐỒỘỔỖƠỚỜỢỞỠÚÙỤỦŨƯỨỪỰỬỮÝỲỴỶỸ].*$'
RE_SUB_PARENTHESES = r'\S*[\(\)]\S*'
# Print the extracted text to text file using PyPDF2
def extract_text(file_path):
    # Open the PDF file
    with open(file_path, "rb") as file:
        reader = PyPDF2.PdfReader(file)
        text = []

        # Iterate through each page
        for page_num in range(len(reader.pages)):
            page = reader.pages[page_num]
            page_text = page.extract_text()
            text.append(page_text)

    return text

    
def split_sentences(text):
    new_text = []
    # Split the text into sentences based on "\n"
    sentences = text.split("\n")
    for sentence in sentences:
        if re.match(RE_NO_WORDS, sentence) or re.match(RE_MATCH_NUMER, sentence):
            continue
        new_text.append(sentence)
    return new_text

def extract_poem(text):
    poem = []
    index = 0
    while index < len(text):
        line = text[index]
        if line[0:3] == "Bài": # Detect the start of a poem
            if line == "Bài 101":
                index += 5 # Skip 5 lines of this poem
                continue
            else:
                index += 1
                # Increment to check the title spans 2 lines
                if re.match(RE_ALL_CAPS, text[index]):
                    index += 1 
                    if re.match(RE_ALL_CAPS, text[index]): # Title spans 2 lines -> skip
                        index += 1
                while index < len(text):
                    line = text[index]
                    if re.match(RE_ALL_CAPS, line):
                        poem.append("\n")
                        break
                    poem.append(line)
                    index += 1
        else:
            index += 1
    return poem

def remove_footnotes(text):
    new_text = []
    index = 0 
    while index < len(text):
        line = text[index]
        if line[0:2] == "1.": 
            index += 1
            while index < len(text):
                if re.match(RE_ALL_CAPS, text[index]):
                    break
                index += 1
        else:
            new_text.append(line)
            index += 1
    return new_text
            
def process_text(text):
    processed_text = []
    for line in text:
        if re.match(RE_FIRST_WORD_CAPITAL, line) or line == "\n":
            processed_text.append(line)
    return processed_text
def add_space_after_punctuation(text):
    punctuation_list = [".", ",", ":", ";", "!", "?"]
    new_text = []
    for line in text:
        new_line = ""
        for i in range(len(line)):
            if line[i] in punctuation_list and i != len(line) - 1 and line[i + 1] != " ":
                new_line += line[i] + " "
            else:
                new_line += line[i]
        new_text.append(new_line)
    return new_text

def ignore_edge_case(text):
    new_text = []
    ignore_list = ["Bài 108", "Bài 109", "ĐỖ VĂN HỶ dịch", "NAM TRÂN dịch", 
                   "Cực khổ không đâu mất bốn mươi ngày rồi, Bốn mươi ngày khổ không nói xiết; Nay lại phải giải trở về Liễu Châu, Thực khiến cho người ta bực bội lại buồn phiền."
                   "Không đâu khổ đã bốn mươi ngày,", "Bốn chục ngày qua xiết đọa đày; Nay lại giải về châu Liễu nữa, Khiến người đã bực lại buồn thay!",
                   "Liễu Châu, Quế Lâm lại Liễu Châu, Đá qua đá lại như quả bóng da; Ngậm oan đi khắp đất Quảng Tây, Không biết giải đến bao giờ mới thôi?"
                   , "Liễu Châu, Quế Lâm lại Liễu Châu,", "Đá qua đá lại, bóng chuyền nhau; Quảng Tây đi khắp, lòng oan ức, Giải đến bao giờ, giải tới đâu?"
                   , "Cực khổ không đâu mất bốn mươi ngày rồi, Bốn mươi ngày khổ không nói xiết; Nay lại phải giải trở về Liễu Châu, Thực khiến cho người ta bực bội lại buồn phiền.", 
                   "Không đâu khổ đã bốn mươi ngày,", "Văn học trong lần xuất bản trước viết là xích, đơn vị", ]
    for line in text:
        if line in ignore_list:
            continue
        new_text.append(line)
    return new_text

def remove_parenthetical_words(line):
    # Remove text within parentheses (including parentheses themselves)
    line = re.sub(r'\([^)]*\)', '', line)
    # Normalize extra spaces
    line = ' '.join(line.split())
    # Remove space before punctuation
    line = re.sub(r'\s+([.,;:!?])', r'\1', line)
    return line

def postprocess_poem(text):
    punctuation_list = [".", ",", ":", ";", "!", "?"]
    processed_lines = []
    
    for line in text:
        words = line.strip().split()
        if not words:
            processed_lines.append(line)
            continue
        
        pattern = None
        result_words = []
        word_count = 0

        for w in words:
            word_count += 1
            # Check if the current word ends with punctuation
            last_char = w[-1]
            
            if last_char in punctuation_list:
                # Determine the pattern if not already set
                if pattern is None:
                    if word_count == 7:
                        pattern = 7
                    elif word_count == 5:
                        pattern = 5
                    else:
                        # Default to 7 if not exactly at 5 or 7
                        pattern = 7
                
                # Append the word
                result_words.append(w)
                
                # If the current word_count matches a multiple of the pattern,
                # insert a newline after this word.
                if word_count % pattern == 0:
                    # Add a newline after this punctuation
                    result_words[-1] += '\n'
            else:
                # Just a normal word
                result_words.append(w)
        
        # Join the processed words for this line
        processed_line = ' '.join(result_words)
        processed_lines.append(processed_line)
    
    # Return the processed lines joined by newline
    # The user can handle the final newline outside if they want.
    return processed_lines

def export(text):
    with open("prison_diary_vi.txt", "w", encoding="utf-8") as f:
        for i, p in enumerate(text):
            f.write(p)    
                
def adjustment(text):
    new_text = []
    with open("prison_diary_vi.txt", "r", encoding="utf-8") as f:
        for line in f:
            new_text.append(line)
            
    with open("prison_diary_vi_2.txt", "w", encoding="utf-8") as f:
        for i, p in enumerate(new_text):
            if p == "Dạ vãn thường thường “ngũ vị kê ”;Sắt lãnh thừa cơ lai giáp kích,\n":
                f.write("Dạ vãn thường thường “ngũ vị kê;" + "\n")
                f.write("Sắt lãnh thừa cơ lai giáp kích," + "\n")
            elif p == " Mỗi cá lung tiền nhất cá táoThành thiên chử phạn dữ điều canh.\n":
                f.write("Mỗi cá lung tiền nhất cá táo\n")
                f.write("Thành thiên chử phạn dữ điều canh." + "\n")
            elif p == " U ám tàn dư nhất tảo khôngNoãn khí bao la toàn vũ trụ,\n":
                f.write("U ám tàn dư nhất tảo không\n")
                f.write("Noãn khí bao la toàn vũ trụ," + "\n")
            elif p == " Hạnh năng dược xuất liễu thâm khanhThừa chu thuận thuỷ vãng Ung Ninh,\n":
                f.write("Hạnh năng dược xuất liễu thâm khanh\n")
                f.write("Thừa chu thuận thuỷ vãng Ung Ninh," + "\n")
            elif p == " Di, Tề ngã tử Thú DươngĐổ phạm ngã tử công gia ngục.\n":
                f.write("Di, Tề ngã tử Thú Dương sơn,\n")
                f.write("Đổ phạm ngã tử công gia ngục." + "\n")
            elif p == " “Phụng thử ”, “đẳng nhân” kim thuỷ học,Đa đa bác đắc cảm ân từ.\n":
                f.write("“Phụng thử ”, “đẳng nhân” kim thuỷ học,\n")
                f.write("Đa đa bác đắc cảm ân từ." + "\n")
            elif p == " Tội khôi tựu thị ác Nadi.Trung Hoa kháng chiến tương lục tải,\n":
                f.write("Tội khôi tựu thị ác Nadi.\n")
                f.write("Trung Hoa kháng chiến tương lục tải," + "\n")
            elif p == "Chiếu lệ sơ lai chư nạn hữuTất tu thụy tại xí khanh biên;\n":
                f.write("Chiếu lệ sơ lai chư nạn hữu\n")
                f.write("Tất tu thụy tại xí khanh biên;" + "\n")
            elif p == "Ung báo, Xích đạo tấn 14-11Ninh tử, bất cam nô lệ khổ,\n":
                f.write("Ninh tử, bất cam nô lệ khổ," + "\n")
            elif p == "Oa...! Oa...! Oaa...!Gia phạ đương binh cứu quốc gia;\n":
                f.write("Oa...! Oa...! Oaa...!\n")
                f.write("Gia phạ đương binh cứu quốc gia;" + "\n")
            elif p == "Tỉnh hậu tài phân thiện,\n":
                f.write("Tỉnh hậu tài phân thiện, ác nhân;\n")
            elif p == " ác nhân; Thiện, ác nguyên lai vô định tính, Đa do giáo dục đích nguyên nhân.Tưởng giá nan quan thị tối hậu,\n":
                f.write("Thiện, ác nguyên lai vô định tính,\n Đa do giáo dục đích nguyên nhân.\n")
                f.write("Tưởng giá nan quan thị tối hậu," + "\n")
            elif p == "Thái dương mỗi tảo tòng sơn thượngChiếu đắc toàn sơn xứ xứ hồng;\n":
                f.write("Thái dương mỗi tảo tòng sơn thượng\n")
                f.write("Chiếu đắc toàn sơn xứ xứ hồng;" + "\n")
            elif p == " “Thành hỏa trì ngư ” kham hạo thán,Nhi kim nhĩ hựu khái thành lao.\n":
                f.write("“Thành hỏa trì ngư ” kham hạo thán,\n")
                f.write("Nhi kim nhĩ hựu khái thành lao." + "\n")
            elif p == " Bất tri hà nhật xuất lao lungBách chiết bất hồi, hướng tiền tiến,\n":
                f.write("Bất tri hà nhật xuất lao lung\n")
                f.write("Bách chiết bất hồi, hướng tiền tiến," + "\n")
            elif p == "Tích nhật huy quân Tương,\n":
                f.write("Tích nhật huy quân Tương, Chiết địa, \n")
            elif p == " Chiết địa,Kim niên, kháng địch Miến, Điền biên;\n":
                f.write("Kim niên, kháng địch Miến, Điền biên;" + "\n")
            elif p == " “Phản lai, bất chuẩn tái trì diên ”.Môn tiền vệ sĩ chấp thương lập,\n":
                f.write("“Phản lai, bất chuẩn tái trì diên ”.\n")
                f.write("Môn tiền vệ sĩ chấp thương lập," + "\n")
            elif p == " Mộc sắt tung hoành như thản khắcMân trùng tụ tán tự phi ky;\n":
                f.write("Mộc sắt tung hoành như thản khắc\n")
                f.write("Mân trùng tụ tán tự phi ky;" + "\n")
            elif p == " Tâm hoài cố quốc thiên đường lộMộng nhiễu tân sầu, vạn lũ ti;\n":
                f.write("Tâm hoài cố quốc thiên đường lộ\n")
                f.write("Mộng nhiễu tân sầu, vạn lũ ti;" + "\n")
            else:
                f.write(p) 
     
text = extract_text(file_path)
new_text = []
for page_text in text:
    page_text = split_sentences(page_text)
    new_text.extend(page_text)
    
poem = extract_poem(new_text)
poem = remove_footnotes(poem)
poem = process_text(poem)
poem = add_space_after_punctuation(poem)
poem = ignore_edge_case(poem)
poem = [remove_parenthetical_words(line) for line in poem]
poem = postprocess_poem(poem)
export(poem)
adjustment(poem)
# The file is then examined and manually adjusted to ensure the poem is correctly formatted