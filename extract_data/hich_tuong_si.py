import fitz
import csv
import json
import re

file_path = '../raw_dataset/hich_tuong_si.pdf'
doc = fitz.open(file_path)

data = ''
for page_num in range(6, 21):
    page = doc.load_page(page_num)
    data += page.get_text()

lines = data.split('\n')
lines = lines[9:]

remove_chars = [';', '"', '-', '‘', '.', '“', '”', '…', '•', '–', '—', '!', ':', '_', ',', '?']

def clean_text(text):
    for char in remove_chars:
        text = text.replace(char, '')
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

csv_file = '../raw_dataset/hich_tuong_si.csv'
with open(csv_file, mode='w', newline='', encoding='utf-8') as file:
    writer = csv.writer(file)
    for line in lines:
        if line.strip():
            cleaned_line = clean_text(line.strip())
            if cleaned_line:
                writer.writerow([cleaned_line])

json_file = '../data/hich_tuong_si.json'

data_list = []

with open(csv_file, mode='r', encoding='utf-8') as file:
    reader = csv.reader(file)
    
    current_id = None
    current_vi_an = None
    current_vi = None
    current_en = []

    for line in reader:
        if line:
            text = line[0].strip()
            
            if text[0].isdigit():
                if current_id is not None and current_vi_an is not None and current_en:
                    data_list.append({
                        "id": current_id,
                        "vi": current_vi_an.strip(),
                        "en": ' '.join(current_en).strip()
                    })
                
                parts = text.split(' ', 1)
                current_id = int(parts[0].strip().rstrip('.'))
                
                current_vi_an = None
                current_vi = None
                current_en = []
            
            elif current_vi_an is None:
                current_vi_an = re.sub(r'\s+', ' ', text.strip())
            elif current_vi is None:
                current_vi = text
            else:
                current_en.append(re.sub(r'\s+', ' ', text.strip()))

    if current_id is not None and current_vi_an is not None and current_en:
        data_list.append({
            "id": current_id,
            "vi": current_vi_an.strip(),
            "en": ' '.join(current_en).strip()
        })

output_data = {
    "file_name": "hich_tuong_si.pdf",
    "data": data_list
}

with open(json_file, 'w', encoding='utf-8') as json_out:
    json.dump(output_data, json_out, ensure_ascii=False, indent=4)

print(f"Data has been saved to file.")
