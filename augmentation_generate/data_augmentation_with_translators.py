from transformers import MarianMTModel, MarianTokenizer
from glob import glob
import os
import json
from bleurt import score
import sacrebleu
from nltk.translate.bleu_score import sentence_bleu
import torch
# from deep_translator import GoogleTranslator
# from transformers import M2M100ForConditionalGeneration, M2M100Tokenizer
from transformers import MBartForConditionalGeneration, MBart50TokenizerFast

os.environ["CUDA_VISIBLE_DEVICES"] = "4"

SCRIPT_PATH = os.path.abspath(__file__)
SCRIPT_DIR = os.path.dirname(SCRIPT_PATH)
PROJECT_ROOT = os.path.dirname(os.path.dirname(SCRIPT_DIR))
DATA_FOLDER = os.path.join(PROJECT_ROOT, "data")

device = 'cuda' if torch.cuda.is_available() else 'cpu'  

# translator = GoogleTranslator(source='vi', target='en')
# tokenizer = M2M100Tokenizer.from_pretrained("facebook/m2m100_418M")
# model = M2M100ForConditionalGeneration.from_pretrained("facebook/m2m100_418M").to(device)
tokenizer = MBart50TokenizerFast.from_pretrained("facebook/mbart-large-50-many-to-many-mmt")
model = MBartForConditionalGeneration.from_pretrained("facebook/mbart-large-50-many-to-many-mmt").to(device)
source_lang = "vi_VN"
target_lang = "en_XX"
tokenizer.src_lang = source_lang

# def translate(src_text):
#     tokenized = tokenizer(src_text, return_tensors="pt").to(device)
#     translated_tokens = model.generate(**tokenized, forced_bos_token_id=tokenizer.get_lang_id("en"))
#     translation = tokenizer.decode(translated_tokens[0], skip_special_tokens=True)
#     return translation

def translate(src_text):
    encoded_input = tokenizer(src_text, return_tensors="pt").to(device)
    generated_tokens = model.generate(
        **encoded_input,
        forced_bos_token_id=tokenizer.lang_code_to_id[target_lang],
        max_length=100,
        num_beams=5,
        early_stopping=True
    )

    translated_text = tokenizer.decode(generated_tokens[0], skip_special_tokens=True)

    return translated_text

# Load json files
json_files = glob(os.path.join(DATA_FOLDER, '*.json'))
json_files.sort()

vi_texts = []
en_texts = []

for json_file in json_files:
    with open(json_file, 'r', encoding='utf-8') as f:
        json_data = json.load(f)
        for item in json_data['data']:
            vi_texts.append(item['vi'])
            en_texts.append(item['en'])

# Initialize BLEURT scorer
scorer_BLEURT = score.BleurtScorer("BLEURT-20")

cnt = 0
chosen_data = []
output_file = "augmented_data_facebook_mbart.json"

for i in range(len(vi_texts)):
    vi_text = vi_texts[i]
    en_text = en_texts[i]

    print(f"Processing {i + 1}/{len(vi_texts)}")
    print(f"Original Vietnamese: {vi_text}")
    print(f"Original English: {en_text}")

    # Translate Vietnamese to English
    translated_text = translate(vi_text)
    print(f"Translation: {translated_text}")

    # BLEURT score
    scores = scorer_BLEURT.score(references=[en_text], candidates=[translated_text])
    print(f"Score BLEURT: {scores[0]}")
    
    # SacreBLEU score
    sacrebleu_score = sacrebleu.corpus_bleu([translated_text], [[en_text]]).score
    print(f"Score SacreBLEU: {sacrebleu_score}")
    
    # BLEU score (using tokenized reference)
    en_tokens = sentence_bleu([en_text.split()], translated_text.split())
    print(f"Score BLEU: {en_tokens}")

    # Check if at least two conditions are satisfied
    conditions = [
        scores[0] >= 0.55, # BLEURT score
        sacrebleu_score >= 10, # SacreBLEU score
        en_tokens >= 0.1 # BLEU score
    ]

    if sum(conditions) >= 2:
        chosen_data.append({
            "id": cnt,
            "vi": vi_text,
            "en": translated_text
        })
        cnt += 1

        # Write to file after processing
        output_data = {"data": chosen_data}
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=4)

    print("")

print("Finished processing all texts.")
