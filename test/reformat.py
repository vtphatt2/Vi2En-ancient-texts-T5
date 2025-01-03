import json
"""
Reformat the json file to this format:
{
"file_name": "chinh_phu_ngam.pdf",
"data": [
    {
        "id": 0,
        "vi": "nhẽ trời đất thường khi gió bụi",
        "en": "In time of turmoil, when earthly storms arise,"
    },
"""

file_name = "CPN2_auto"
with open(file_name + ".json", 'r', encoding='utf-8') as f:
    original_data = json.load(f)

# Create new structure
new_format = {
    "file_name": "",
    "data": []
}

# Transform each entry
for idx, item in enumerate(original_data):
    new_entry = {
        "id": idx,
        "vi": item["vie_sentence"],
        "en": item["eng_sentence"]
    }
    new_format["data"].append(new_entry)

# Write to new file
with open(file_name + ".json", 'w', encoding='utf-8') as f:
    json.dump(new_format, f, ensure_ascii=False, indent=2)

