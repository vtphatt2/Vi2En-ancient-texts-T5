import google.generativeai as genai
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_gemini_version(api_key: str):
    """Check Gemini API version and available models."""
    try:
        # Configure the API
        genai.configure(api_key=api_key)
        
        # List available models
        models = genai.list_models()
        
        # Filter for Gemini models
        gemini_models = [model for model in models if 'gemini' in model.name.lower()]
        
        for model in gemini_models:
            logger.info(f"Model: {model.name}")
            logger.info(f"Version: {model.version}")
            logger.info(f"Display Name: {model.display_name}")
            logger.info(f"Description: {model.description}")
            logger.info(f"Generation Methods: {model.supported_generation_methods}")
            logger.info("---")
            
        return gemini_models
        
    except Exception as e:
        logger.error(f"Error checking Gemini version: {e}")
        return None

# Test the function
if __name__ == "__main__":
    API_KEY = "AIzaSyAlgAWun2JG6ws1ThKqUwYzX8I4aBCmNbk"
    models = check_gemini_version(API_KEY)