from transformers import MT5ForConditionalGeneration, T5Tokenizer

def translate_vi_to_en(input_text):
    model_name = "google/mt5-small"
    tokenizer = T5Tokenizer.from_pretrained(model_name, use_fast=False)
    model = MT5ForConditionalGeneration.from_pretrained(model_name)

    task_prefix = "translate Vietnamese to English: "
    input_ids = tokenizer(task_prefix + input_text, return_tensors="pt", padding=True).input_ids

    outputs = model.generate(input_ids, max_length=128, num_beams=5, early_stopping=True)
    translated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)

    return translated_text

vietnamese_text = "Xin chào, bạn khỏe không?"
english_translation = translate_vi_to_en(vietnamese_text)
print("Vietnamese:", vietnamese_text)
print("English Translation:", english_translation)
