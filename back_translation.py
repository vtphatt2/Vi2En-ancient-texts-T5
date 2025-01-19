import json
import os
from tqdm import tqdm
from typing import Dict, List
from deep_translator import GoogleTranslator
import time
from typing import Tuple

def back_translate(sentence: str, source_lang='vi', target_lang='en', max_retries=3) -> Tuple[str, str]:
    """
    Perform back translation with retry mechanism
    """
    for attempt in range(max_retries):
        try:
            # Initialize translators
            to_english = GoogleTranslator(source=source_lang, target=target_lang)
            to_vietnamese = GoogleTranslator(source=target_lang, target=source_lang)
            
            # Translate to English
            translated = to_english.translate(sentence)
            # Add delay to avoid rate limits
            time.sleep(1)
            # Translate back to Vietnamese
            back_translated = to_vietnamese.translate(translated)
            
            return translated, back_translated
            
        except Exception as e:
            if attempt == max_retries - 1:
                print(f"Translation failed after {max_retries} attempts: {str(e)}")
                return None, None
            time.sleep(2 ** attempt)  # Exponential backoff
            continue

# def main():
#     # Test the translation
#     sentence = "Đại diện tại Việt Nam có thẩm quyền ký hợp đồng."
#     en_translation, back_vi = back_translate(sentence)
    
#     if en_translation and back_vi:
#         print("Original:", sentence)
#         print("English Translation:", en_translation)
#         print("Back Translation:", back_vi)
#     else:
#         print("Translation failed")

def augment_data(input_file: str, output_file: str):
    """Process JSON file using Google Translate for augmentation."""
    
    # Load input data
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    augmented_data = {
        "file_name": data["file_name"],
        "data": []
    }
    
    # Process each sentence pair
    for item in tqdm(data.get("data", [])):
        # Generate variant with back translation
        if "vi" in item:
            en_translation, back_vi = back_translate(item["vi"])
            print("en_translation: ", en_translation)
            print("back_vi: ", back_vi)
            if en_translation and back_vi and back_vi != item["vi"]:
                # Add augmented pair if different from original
                augmented_data["data"].append({
                    "vi": back_vi,
                    "en": item["en"]
                })
    
    # Save augmented dataset
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(augmented_data, f, ensure_ascii=False, indent=2)

def process_all_json_files(folder_dir: str):
    """Process all JSON files in data directory."""
    excluded_patterns = ['_augmented']

    json_files = [
        f for f in os.listdir(folder_dir) 
        if f.endswith('.json') and 
        not any(pattern in f for pattern in excluded_patterns)
    ]
    
    if not json_files:
        print(f"No non-augmented JSON files found in {folder_dir}")
        return
    
    for input_file in json_files:
        try:
            input_path = os.path.join(folder_dir, input_file)
            output_file = input_file.replace('.json', '_augmented_2.json')
            output_path = os.path.join(folder_dir, output_file)
            
            print(f"\nProcessing: {input_file}")
            augment_data(input_path, output_path)
            
        except Exception as e:
            print(f"Error processing {input_file}: {str(e)}")

if __name__ == "__main__":
    augment_data("data/nam_quoc_son_ha_1.json", "test.json")
    # process_all_json_files("data")