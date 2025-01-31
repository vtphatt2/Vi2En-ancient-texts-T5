from glob import glob 
import os
import json
import random

DATA_FOLDER = "data"

data = []

data_json_files = glob(os.path.join(DATA_FOLDER, '*.json'))
data_json_files.sort()

for json_file in data_json_files:
    with open(json_file, 'r', encoding='utf-8') as f:
        json_data = json.load(f)
        for item in json_data['data']:
            data.append({
                "vi": item['vi'],
                "en": item['en']
            })

print(len(data))

# train_data_path = os.path.join("train_test", "train.json")
# test_data_path = os.path.join("train_test", "test.json")

# # set seed for reproducibility
# random.seed(42)
# random.shuffle(data)

# train_data = data[:int(len(data) * 0.9)]
# test_data = data[int(len(data) * 0.9):]

# with open(train_data_path, 'w', encoding='utf-8') as f:
#     json.dump(train_data, f, ensure_ascii=False, indent=4)

# with open(test_data_path, 'w', encoding='utf-8') as f:
#     json.dump(test_data, f, ensure_ascii=False, indent=4)
