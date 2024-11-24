import pytesseract
from PIL import Image, ImageFilter
import fitz
import io
import os
import PIL.ImageOps
from spellchecker import SpellChecker
import json

def crop_right_half(image):
    width, height = image.size

    left = width // 2
    upper = 95
    right = width - 100
    lower = height - 50

    right_half = image.crop((left, upper, right, lower))
    return right_half

def crop_right_half_for_page_one(image):
    width, height = image.size

    left = width // 2 + 30
    upper = 95
    right = width - 100
    lower = height - 80

    right_half = image.crop((left, upper, right, lower))
    return right_half

def extract_images_pdf_file(pdf_path):
    images = []

    pdf_document = fitz.open(pdf_path)

    discarded_pages = [75, 93]

    for page_number in range(23, 108):
        if page_number in discarded_pages:
            continue

        page = pdf_document[page_number - 1]  
        img_refs = page.get_images(full=True)  
        for img in img_refs:
            xref = img[0]  
            base_image = pdf_document.extract_image(xref) 
            image_bytes = base_image["image"] 
            image = Image.open(io.BytesIO(image_bytes))  

            if page_number == 23:
                image = crop_right_half_for_page_one(image.rotate(90, expand=True))
            else:
                image = crop_right_half(image.rotate(90, expand=True))

            # image_ext = base_image["ext"]
            # output_file = f"page_{page_number}.{image_ext}"
            # image.save(output_file)
            
            image = image.filter(ImageFilter.SHARPEN)
            image = PIL.ImageOps.invert(image)

            images.append(image)  

    pdf_document.close()
    return images

# def correct_spelling(input_text):
#     spell = SpellChecker()
#     corrected_text = []
#     for word in input_text.split():
#         corrected_word = spell.correction(word)
#         if corrected_word is None:
#             corrected_word = word
#         corrected_text.append(corrected_word)
#     return ' '.join(corrected_text)

def process_text(text):
    chars_to_remove = ['*', '"', '-', '‘', '.', '’', '“', 
                       '”', '…', '•', '–', '—', '™', '[', '_',
                       ]
    for char in chars_to_remove:
        text = text.replace(char, ' ')
    
    normalized_text = ' '.join(text.split())

    normalized_text = normalized_text.replace("Kiểu", "Kiều")
    normalized_text = normalized_text.replace("Kiếu", "Kiều")
    normalized_text = normalized_text.replace("(", "t")

    return normalized_text

def extract_english_text(image):
    text = pytesseract.image_to_string(image, lang='eng+vie')
    
    lines = text.split('\n')
    lines = [line.strip() for line in lines if line.strip()]
    lines = [line for line in lines if len(line.split()) >= 3]
    lines = [process_text(line) for line in lines]
    
    return lines


pdf_path = os.path.join('./', '..', 'raw_dataset', 'kieu1.pdf')
images = extract_images_pdf_file(pdf_path)

english_kieu = []
for image in images:
    print(f"Parsing image {images.index(image) + 1}/{len(images)}")
    lines = extract_english_text(image)
    english_kieu.extend(lines)

output_file = os.path.join('./', '..', 'raw_dataset', 'english_kieu_cleaned.txt')
with open(output_file, 'w', encoding='utf-8') as fout:
    for line in english_kieu:
        fout.write(line + '\n')

vietnamese_kieu = []
truyen_kieu_cleaned_txt_path = os.path.join('./', '..', 'raw_dataset', 'truyen_kieu_cleaned.txt')
with open(truyen_kieu_cleaned_txt_path, 'r', encoding='utf-8') as file:
    vietnamese_kieu = [line.strip() for line in file if line.strip()]

max_length = max(len(vietnamese_kieu), len(english_kieu))


data = []
for idx in range(max_length):
    if idx < len(vietnamese_kieu):
        vi = vietnamese_kieu[idx].rstrip(',').strip()
    else:
        vi = ""
        print(f"[Debug] Dòng tiếng Việt thứ {idx + 1} không tồn tại.")
    
    if idx < len(english_kieu):
        en = english_kieu[idx].rstrip(',').strip()
    else:
        en = ""
        print(f"[Debug] Dòng tiếng Anh thứ {idx + 1} không tồn tại.")
    
    data.append({
        "id": idx + 1,
        "vi": vi,
        "en": en
    })

output = {
    "file_name": "kieu1.pdf",
    "data": data
}

output_json_file = os.path.join('./', '..', 'data', 'kieu1.json')
with open(output_json_file, "w", encoding="utf-8") as json_file:
    json.dump(output, json_file, ensure_ascii=False, indent=4)