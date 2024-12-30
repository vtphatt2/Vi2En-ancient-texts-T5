import google.generativeai as genai
import nltk
import ssl
import json
import os
from nltk.translate.bleu_score import sentence_bleu, SmoothingFunction
from transformers import pipeline
from tqdm import tqdm
nltk.download('punkt_tab')

# 2. Use Vietnamese spelling correction model
corrector = pipeline("text2text-generation", 
                    model="bmd1905/vietnamese-correction-v2", 
                    device=-1)

def correct_vie_grammar(sentence):
    """Correct Vietnamese grammar and spelling."""
    # Generate correction with max length of 512
    correction = corrector(sentence, max_length=512)
    # Extract corrected text from pipeline output
    corrected_text = correction[0]['generated_text']
    # Remove trailing period if present
    corrected_text = corrected_text.rstrip('.')
    # Add period if no punctuation at end
    if corrected_text[-1] not in ['.', '!', '?', ';', ':', ',']:
        corrected_text += '.'
    return corrected_text

# 3. Use Google Gemini to translate Vietnamese to English
def setup_gemini(api_key):
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-pro')
    return model

API_KEY = "AIzaSyAISyP5zG-7NIV5F6xesUveTRDmtQ_6eyU"

def translate_with_gemini(model, text, source_lang='Vietnamese', target_lang='English'):
    """Translate text using Gemini model."""
    try:
        prompt = f"Translate the following {source_lang} text to {target_lang}:\n{text}\n\nTranslation:"
        response = model.generate_content(prompt)
        if response and response.text:
            return response.text.strip()
        return None
    except Exception as e:
        print(f"Translation error: {str(e)}")
        return None

# 4. Use BLEU score to evaluate translation quality and as the threshold to keep the augmented dataset
def setup_nltk():
    """Setup NLTK and download required resources."""
    try:
        # Handle SSL certificate verification for NLTK downloads
        try:
            _create_unverified_https_context = ssl._create_unverified_context
        except AttributeError:
            pass
        else:
            ssl._create_default_https_context = _create_unverified_https_context
        
        # Download required NLTK data
        nltk.download('punkt', quiet=True)
        return True
    except Exception as e:
        print(f"Failed to setup NLTK: {e}")
        return False
    
def evaluate_translation(reference, candidate, threshold=0.4):
    """Evaluate translation using smoothed BLEU score."""
    try:
        # Initialize smoothing
        smoothie = SmoothingFunction().method1
        
        # Tokenize
        ref_tokens = nltk.word_tokenize(reference.lower())
        cand_tokens = nltk.word_tokenize(candidate.lower())
        
        # Calculate BLEU with smoothing
        score = sentence_bleu([ref_tokens], cand_tokens, 
                            weights=(0.25, 0.25, 0.25, 0.25),
                            smoothing_function=smoothie)
        return score >= threshold, score
    except Exception as e:
        print(f"Error calculating BLEU score: {e}")
        return False, 0.0

# example function to demonstrate the data augmentation pipeline
def example_augmentation_pipeline(vi_sentence, reference_en_sentence):
    # # Example usage
    # reference_en_sentence = "The representative in Vietnam has the authority to sign contracts."
    # vi_sentence = "Đại dien tại Việt Nm có tham quyền ký hợp đồng."
    corrected_sentence = correct_vie_grammar(vi_sentence)
    print("Original:", vi_sentence)
    print("Corrected:", corrected_sentence)

    # Initialize Google Gemini
    model = setup_gemini(API_KEY)
    if model:
        translated_en_sentence = translate_with_gemini(model, corrected_sentence)
        if translated_en_sentence:
            print("English translation:", translated_en_sentence)
            print("Reference English:", reference_en_sentence)
            
            # Evaluate translation quality
            acceptable, score = evaluate_translation(reference_en_sentence, translated_en_sentence)
            print(f"BLEU Score: {score:.4f}")
            print(f"Quality Check: {'PASS' if acceptable else 'FAIL'}")
        else:
            print("Translation failed")

# 6. Pass json file to the pipeline then create a new json file with augmented data
def augment_data(input_file: str, output_file: str, api_key: str, threshold: float = 0.6):
    """
    Augment parallel data from input JSON and save to new JSON file.
    
    Args:
        input_file: Path to input JSON
        output_file: Path to output JSON 
        api_key: Google API key
        threshold: Quality threshold for translations
    """
    # Initialize models
    model = setup_gemini(api_key)

    if not model:
        print("Failed to initialize Gemini model.")
        return
    
    # Load input data
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    augmented_data = {
        "file_name": data["file_name"],
        "data": []
    }
    
    # Process each sentence pair
    for item in tqdm(data["data"]):
        # Original pair
        # augmented_data["data"].append(item)
        
        # Grammar correction
        corrected_vi = correct_vie_grammar(item["vi"]) if "vi" in item else None
        
        if not corrected_vi:
            print("Failed to correct Vietnamese grammar.")
            return
    
        # Generate new translation
        translated_en = translate_with_gemini(model, corrected_vi)
        
        if not translated_en:
            print("Failed to translate Vietnamese to English.")
            return

        # Evaluate translation quality
        acceptable, score = evaluate_translation(item["en"], translated_en)

        print("Translation: ", translated_en)
        print("Reference: ", item["en"])
        print(f"BLEU Score: {score:.4f}")
        print(f"Quality Check: {'PASS' if acceptable else 'FAIL'}")
        
        # if acceptable:
            # Add augmented pair
        augmented_data["data"].append({
            "vi": corrected_vi,
            "en": translated_en
        })
    
    # Save augmented data
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(augmented_data, f, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    input_file_path = os.path.join("data", "nam_quoc_son_ha_1.json")
    print("Input file:", input_file_path)
    output_file_path = os.path.join("data", "nam_quoc_son_ha_1_augmented.json")
    print("Output file:", output_file_path)
    augment_data(input_file_path, output_file_path, API_KEY, 0)