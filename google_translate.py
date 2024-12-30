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

def main():
    # Test the translation
    sentence = "Đại diện tại Việt Nam có thẩm quyền ký hợp đồng."
    en_translation, back_vi = back_translate(sentence)
    
    if en_translation and back_vi:
        print("Original:", sentence)
        print("English Translation:", en_translation)
        print("Back Translation:", back_vi)
    else:
        print("Translation failed")

if __name__ == "__main__":
    main()