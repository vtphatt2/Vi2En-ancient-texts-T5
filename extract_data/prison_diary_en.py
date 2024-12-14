import json

# We already have the cleaned English text of Prison Diary
def alignment():
    vi_text = []
    en_text = []
    with open("prison_diary_vi_1.txt", "r", encoding="utf-8") as file:
        vi_text = file.readlines()
    with open("prison_diary_en.txt", "r", encoding = "utf-8") as file:
        en_text = file.readlines()
    file_name = "Nhat ky trong tu.pdf"
    # Export in the json format: 
    data = []
    for i in range(len(vi_text)):
        data.append({
            "id": i,
            "vi": vi_text[i],
            "en": en_text[i]
        })
    with open('../data/prison_diary.json', 'w', encoding='utf-8') as f:
        json.dump({"file_name": file_name, "data": data}, f, ensure_ascii=False, indent=4)

alignment()
    



