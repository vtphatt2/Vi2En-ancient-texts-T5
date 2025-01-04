from transformers import T5ForConditionalGeneration, T5Tokenizer
import torch
import json
import sacrebleu
from bleurt import score
import os

os.environ["CUDA_VISIBLE_DEVICES"] = "1"

if torch.cuda.is_available():
    device = "cuda"
else:
    device = "cpu"

model = T5ForConditionalGeneration.from_pretrained("NlpHUST/t5-vi-en-base")
tokenizer = T5Tokenizer.from_pretrained("NlpHUST/t5-vi-en-base")
model.to(device)
model.eval()  

def translate(text, model, tokenizer):
    tokenized_text = tokenizer.encode(text, return_tensors="pt").to(device)
    
    with torch.no_grad():
        translated_ids = model.generate(
            tokenized_text,
            max_length=256, 
            num_beams=5,
            repetition_penalty=2.5, 
            length_penalty=1.0, 
            early_stopping=True
        )
    
    translated_text = tokenizer.decode(translated_ids[0], skip_special_tokens=True)
    
    return translated_text


with open("test.json", "r", encoding="utf-8") as f:
    test_data = json.load(f)

source_texts = [item["vi"] for item in test_data["data"]]
reference_texts = [item["en"] for item in test_data["data"]]

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
print(f"BLEU Score: {bleu.score}")


# Initialize BLEURT scorer
bleurt_checkpoint = "BLEURT-20"
bleurt_scorer = score.BleurtScorer(bleurt_checkpoint)

print("Calculating BLEURT scores...")
bleurt_scores = bleurt_scorer.score(references=reference_texts, candidates=predictions)

# Compute average BLEURT score
average_bleurt = sum(bleurt_scores) / len(bleurt_scores)
print(f"Average BLEURT Score: {average_bleurt}")