from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import torch
import json
import sacrebleu
from bleurt import score
import os

os.environ["CUDA_VISIBLE_DEVICES"] = "4"

# Device
if torch.cuda.is_available():
    device = 'cuda'
else:
    device = 'cpu'

model_name = "./results_envit5"  
# model_name = "VietAI/envit5-translation"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForSeq2SeqLM.from_pretrained(model_name).to(device)
model.eval()

def translate(text, model, tokenizer):
    input_text = "vi: " + text.lower()
    outputs = model.generate(tokenizer(input_text, return_tensors="pt", padding=True).input_ids.to(device), max_length=512)
    # Decode and clean the output
    decoded_text = tokenizer.batch_decode(outputs, skip_special_tokens=True)[0]
    if isinstance(decoded_text, str) and decoded_text.startswith("en:"):
        decoded_text = decoded_text[len("en:"):].strip()
    return decoded_text

# Load the test data
with open("test.json", "r", encoding="utf-8") as f:
    test_data = json.load(f)

# Extract source and reference translations
source_texts = [item["vi"] for item in test_data["data"]]
reference_texts = [item["en"] for item in test_data["data"]]

# clear txt file
open('save.txt', 'w').close()

# Generate predictions
predictions = []
for idx, text in enumerate(source_texts):
    print(f"Translating sentence {idx + 1}/{len(source_texts)}...")
    prediction = translate(text, model, tokenizer)
    predictions.append(prediction)
    print(f"Translated: {text} -> {prediction}")

    with open('save.txt', 'a', encoding='utf-8') as f:
        f.write(f"Translated: {text} -> {prediction}\n")

# Calculate BLEU score
print("Calculating BLEU score...")
bleu = sacrebleu.corpus_bleu(predictions, [reference_texts])

# Print BLEU score
print(f"BLEU Score: {bleu.score}")

# Initialize BLEURT scorer
bleurt_checkpoint = "BLEURT-20"
bleurt_scorer = score.BleurtScorer(bleurt_checkpoint)

print("Calculating BLEURT scores...")
bleurt_scores = bleurt_scorer.score(references=reference_texts, candidates=predictions)

# Compute average BLEURT score
average_bleurt = sum(bleurt_scores) / len(bleurt_scores)
print(f"Average BLEURT Score: {average_bleurt:.7f}")
