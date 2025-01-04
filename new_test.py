from glob import glob
import os
import json
import random

DATA_FOLDER = "data"
AUGMENTED_DATA_FOLDER = "augmented_data"

# Prepare data
vi_texts = []
en_texts = []

data_json_files = glob(os.path.join(DATA_FOLDER, '*.json'))
data_json_files.sort()

for json_file in data_json_files:
    with open(json_file, 'r', encoding='utf-8') as f:
        json_data = json.load(f)
        for item in json_data['data']:
            vi_texts.append(item['vi'])
            en_texts.append(item['en'])

augmented_data_json_files = glob(os.path.join(AUGMENTED_DATA_FOLDER, '*.json'))
augmented_data_json_files.sort()

for json_file in augmented_data_json_files:
    with open(json_file, 'r', encoding='utf-8') as f:
        json_data = json.load(f)
        for item in json_data['data']:
            vi_texts.append(item['vi'])
            en_texts.append(item['en'])


random.seed(42)
test_data = []

cnt = 1
test_data_indicies = set()

while len(test_data) < 1524:
    idx = random.randint(0, len(vi_texts) - 1)

    if idx not in test_data_indicies and vi_texts.count(vi_texts[idx]) == 1:
        test_data_indicies.add(idx)

        test_data.append({
            "id": cnt,
            "vi": vi_texts.pop(idx),
            "en": en_texts.pop(idx)
        })

        cnt += 1

with open('test.json', 'w', encoding='utf-8') as f:
    json.dump({"data": test_data}, f, ensure_ascii=False, indent=4)
