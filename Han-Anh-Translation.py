import json
from deep_translator import GoogleTranslator

def read_dict_from_file(file_path):
    han_viet_dict = {}
    with open(file_path, 'r', encoding='utf-8') as file:
        for line in file:
            line = line.strip()
            if ": " in line:
                han, viet = line.split(": ", 1)
                han_viet_dict[han] = viet
            else:
                print(f"Error: {line}")
    return han_viet_dict

def convert_han_viet_to_han_anh(han_viet_dict):
    han_anh_dict = {}
    
    for han, viet in han_viet_dict.items():
        try:
            translated = GoogleTranslator(source='vi', target='en').translate(viet)
            han_anh_dict[han] = translated
        except Exception as e:
            print(f"Error translating {han}: {e}")
            han_anh_dict[han] = "Translation Error"
    
    return han_anh_dict

han_viet_dict = read_dict_from_file('./extract_data/Han-Viet.txt')

han_anh_dict = convert_han_viet_to_han_anh(han_viet_dict)

data = []
for han, eng in han_anh_dict.items():
    data.append({
        "id": len(data),
        "vi": han,
        "en": eng
    })

output = {
    "file_name": "SinoNom_Vietnamese_Dictionary_p7",
    "data": data
}

with open('sinonom_vietnamese_dictionary_p7.json', 'w', encoding='utf-8') as json_file:
    json.dump(output, json_file, ensure_ascii=False, indent=4)

print("100%")
