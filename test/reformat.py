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

file_name = "chinese_poem"

def reformat_json(input_file, output_file, base_filename):
    # Read input JSON
    with open(input_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    # Create new format
    reformatted = {
        "file_name": f"{base_filename}.pdf",
        "data": []
    }
    
    # Add data entries with IDs
    for idx, item in enumerate(data):
        reformatted["data"].append({
            "id": idx,
            "vi": item["vi"],
            "en": item["en"]
        })
    
    # Write reformatted JSON
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(reformatted, f, ensure_ascii=False, indent=2)

input_file = "chinese_translate.json"
output_file = f"{file_name}.json"
reformat_json(input_file, output_file, file_name) 

