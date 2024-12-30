import json
vi_file = open("vietnamese_poem_yearning2.txt", "r", encoding="utf-8")
en_file = open("english_poem_yearning2.txt", "r", encoding="utf-8")
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
    with open("poem25.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

vi_file.close()
en_file.close()
