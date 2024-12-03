# pip install --upgrade pip
# pip install transformers
# pip install tensorflow
# pip install tf-keras
# pip install sentencepiece

from transformers import pipeline

corrector = pipeline("text2text-generation", model="bmd1905/vietnamese-correction-v2", device = -1)
# Example
MAX_LENGTH = 512

def get_text_list_from_file(file_path):
    text_list = []
    with open(file_path, 'r', encoding='utf-8') as file:
        for line in file:
            text_list.append(line.strip())
    return text_list

def write_predictions_to_file(predictions, file_path):
    with open(file_path, 'w', encoding='utf-8') as file:
        for pred in predictions:
            corrected_text = pred['generated_text'].rstrip('.')
            # Add '.' at the end of the sentence if it does not have punctuation at the end
            if corrected_text[-1] not in ['.', '!', '?', ';', ':', ',']:
                corrected_text += '.'
            file.write(corrected_text + '\n')

text_list = get_text_list_from_file('vietnamese.txt')

# Batch prediction
predictions = corrector(text_list, max_length=MAX_LENGTH)

# Print predictions
write_predictions_to_file(predictions, 'output_corrected_vietnamese_spelling.txt')
