import json

file_name = "kieu1.json"

vietnamese = []
english = []
with open(file_name, "r", encoding="utf-8") as f:
    js = json.load(f)
    data = js["data"]
    for item in data:
        vietnamese.append(item["vi"])
        english.append(item["en"])
        
with open("kieu1_vietnamese.txt", "w", encoding="utf-8") as f:
    for item in vietnamese:
        f.write(item + "\n")

with open("kieu1_english.txt", "w", encoding="utf-8") as f:
    for item in english:
        f.write(item + "\n")