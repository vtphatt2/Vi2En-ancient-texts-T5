import json
import os


def align_translations(viet_file, eng_file):
    # Read files
    with open(viet_file, 'r', encoding='utf-8') as vf:
        viet_lines = [line.strip() for line in vf.readlines() if line.strip()]
        
    with open(eng_file, 'r', encoding='utf-8') as ef:
        eng_lines = [line.strip() for line in ef.readlines() if line.strip()]
        print(eng_lines)

    # Create aligned pairs
    aligned_pairs = []
    
    for v_line, e_line in zip(viet_lines, eng_lines):
        if v_line and e_line:
            aligned_pairs.append({
                'vi': v_line,
                'en': e_line
            })
    
    return aligned_pairs


def create_json_file(file_name, aligned_translations, output_file):
    data = []
    for idx, translation in enumerate(aligned_translations):
        data.append({
            "id": idx + 1,
            "vi": translation["vi"],
            "en": translation["en"]
        })
    
    output = {
        "file_name": file_name,
        "data": data
    }

    with open(output_file, "w", encoding="utf-8") as json_file:
        json.dump(output, json_file, ensure_ascii=False, indent=4)


if __name__ == '__main__':
    # Execute alignment and write to JSON file
    vie_file_path = os.path.join("..", "provided_cleaned_dataset", "KieuTale1871_vie.txt")
    en_file_path = os.path.join("..", "provided_cleaned_dataset", "KieuTale_eng_1.txt")
    output_file_path = os.path.join("..", "data", "kieu3.json")
    aligned_translations = align_translations(vie_file_path, en_file_path)
    create_json_file("KieuTale1871_vie.txt_and_KieuTale_eng_1.txt", aligned_translations, output_file_path)