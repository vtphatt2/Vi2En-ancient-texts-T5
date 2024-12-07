from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

# Load the fine-tuned model and tokenizer
model_name = "./results"  # The directory where the model was saved after training
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForSeq2SeqLM.from_pretrained(model_name).to('cuda')

def translate(text, model, tokenizer):
    # Add the translation prefix
    input_text = "vi: " + text.lower()

    outputs = model.generate(tokenizer(input_text, return_tensors="pt", padding=True).input_ids.to('cuda'), max_length=512)

    return tokenizer.batch_decode(outputs, skip_special_tokens=True)

# Example sentence to translate
sentence = "Ngục trung cựu phạm nghênh tân phạm"

# Perform translation
translated_sentence = translate(sentence, model, tokenizer)
print(translated_sentence)