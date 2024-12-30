import json
vi_file = open("../raw_dataset/Vietnamese_dataset.txt", "r", encoding="utf-8")
en_file = open("../raw_dataset/Vietnamese_Anthology_p1.txt", "r", encoding="utf-8")
vi_lines = vi_file.readlines()
en_lines = en_file.readlines()

if len(vi_lines) != len(en_lines):
    print("The number of lines in the two poems don't match.")
else:
    data = []
    for i, (vi, en) in enumerate(zip(vi_lines, en_lines)):
        data.append({
            "id": i,
            "vi": vi.strip(),
            "en": en.strip()
        })
    format = {
        "file_name": "Vietnamese_Anthology_P1",
        "data": data
    }
    with open("Vietnamese_Anthology_P1.json", "w", encoding="utf-8") as f:
        json.dump(format, f, ensure_ascii=False, indent=4)

vi_file.close()
en_file.close()
