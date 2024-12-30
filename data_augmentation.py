import google.generativeai as genai
import nltk
from nltk.translate.bleu_score import sentence_bleu, SmoothingFunction
from transformers import pipeline
import ssl
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
    
# def evaluate_translation(reference, candidate, threshold=0.4):
#     """
#     Evaluate translation quality using BLEU score
#     Args:
#         reference: Reference translation (ground truth)
#         candidate: Generated translation to evaluate
#         threshold: Minimum acceptable BLEU score
#     Returns:
#         tuple: (bool acceptable, float score)
#     """
#     if not setup_nltk():
#         return False, 0.0
    
#     try:
#         # Tokenize sentences
#         ref_tokens = nltk.word_tokenize(reference.lower())
#         cand_tokens = nltk.word_tokenize(candidate.lower())
        
#         # Calculate BLEU score
#         score = sentence_bleu([ref_tokens], cand_tokens)
        
#         return score >= threshold, score
#     except Exception as e:
#         print(f"Error calculating BLEU score: {e}")
#         return False, 0.0
    
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

# 5. example function to demonstrate the data augmentation pipeline
def example_augmentation_pipeline():
    # Example usage
    reference_en_sentence = "The representative in Vietnam has the authority to sign contracts."
    vi_sentence = "Đại dien tại Việt Nm có tham quyền ký hợp đồng."
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

def main () :
    # Example usage
    reference_en_sentence = "The representative in Vietnam has the authority to sign contracts."
    vi_sentence = "Đại dien tại Việt Nm có tham quyền ký hợp đồng."
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

if __name__ == "__main__":
    main()