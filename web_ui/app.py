from flask import Flask, render_template, request, jsonify
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import torch



# Device
if torch.cuda.is_available():
    device = 'cuda'
else:
    device = 'cpu'

# Load the fine-tuned model and tokenizer
model_name = "../results"  
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForSeq2SeqLM.from_pretrained(model_name).to(device)

def translate(text, model, tokenizer):
    input_text = "vi: " + text.lower()
    outputs = model.generate(tokenizer(input_text, return_tensors="pt", padding=True).input_ids.to(device), max_length=512)
    return tokenizer.batch_decode(outputs, skip_special_tokens=True)



app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/translate', methods=['POST'])
def translate_text():
    data = request.get_json()
    text = data.get('text', '')
    if text:
        try:
            translation = translate(text, model, tokenizer)  # Giả sử trả về list

            if isinstance(translation, list):
                translation = translation[0]
            
            if isinstance(translation, str) and translation.startswith("en:"):
                translation = translation[len("en:"):].strip()
            
            return jsonify({'translation': translation})
        except Exception as e:
            print(e)
            return jsonify({'translation': 'Error occurs during translating the text'}), 500
    return jsonify({'translation': ''})

if __name__ == '__main__':
    app.run(debug=True)
