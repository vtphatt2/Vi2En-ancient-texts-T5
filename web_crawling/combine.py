import json
import glob
import os

def main():
    # Change to your folder path if needed:
    folder_path = ''
    
    # Use glob to get all .json files in the folder
    json_files = glob.glob(os.path.join(folder_path, '*.json'))
    
    combined_data = []
    
    for file_path in json_files:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # Append all items from this file into the combined list
            combined_data.extend(data)
    
    # Save to a new file
    with open(os.path.join(folder_path, 'combined.json'), 'w', encoding='utf-8') as out_file:
        json.dump(combined_data, out_file, ensure_ascii=False, indent=2)

if __name__ == '__main__':
    main()
