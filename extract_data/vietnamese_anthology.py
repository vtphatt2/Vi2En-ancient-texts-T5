import fitz
import csv
import re

file_path = '../raw_dataset/Vietnamese_Anthology.pdf'
csv_file = '../raw_dataset/Vietnamese_Anthology.csv'

doc = fitz.open(file_path)

remove_chars = ['®', ';', '"', '-', '‘', '.', '“', '”', '…', '•', '–', '—', '!', ':', '_', ',', '?', '*', '}']
remove_patterns = [
    r"vietnam and china",
    r"1 Vietnam and China",
    r"Ly Thudng Kiét",
    r"\(King\) Tran Minhténg",
    r"Nguyén Trai",
    r"The Hing Ditc Anthology",
    r"The Héng Ditc Anthology",
    r"The Hong Ditc Anthology",
    r"\(King\) Lé Thanhténg",
    r"Nguyén Binh Khiém",
    r"Anonymous",
    r"Phing Khac Khoan",
    r"Nguyén Cong Trt",
    r"Cao Ba Quat",
    r"the buddhist ethos",
    r"Nguyén Dinh Chieu",
    r"Huynh Man Dat"
]

def clean_text(text):
    for char in remove_chars:
        text = text.replace(char, '')
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

with open(csv_file, mode='w', newline='', encoding='utf-8') as file:
    writer = csv.writer(file)
    for page_num in range(101, 115):
        page = doc.load_page(page_num)
        lines = page.get_text().split('\n')
        
        for line in lines:
            cleaned_line = clean_text(line.strip())
            
            if any(re.search(pattern, cleaned_line, re.IGNORECASE) for pattern in remove_patterns):
                continue
            
            if cleaned_line.isdigit():
                continue
            
            if cleaned_line:
                writer.writerow([cleaned_line])

print(f"Data has been saved to {csv_file}.")

with open(csv_file, mode='r', encoding='utf-8') as file:
    lines = file.readlines()

processed_lines = []
skip_lines = False

for line in lines:
    line = line.strip()
    
    if line.lower().startswith("note"):
        skip_lines = True
    
    if skip_lines:
        if line and line[0].isdigit():
            skip_lines = False
            processed_lines.append(line)
        continue
    
    processed_lines.append(line)

with open(csv_file, mode='w', newline='', encoding='utf-8') as file:
    writer = csv.writer(file)
    for line in processed_lines:
        writer.writerow([line])

print(f"Processed data has been saved back to {csv_file}.")
