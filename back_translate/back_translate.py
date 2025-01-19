import time
from datetime import datetime, timedelta
import logging
from collections import deque
import google.api_core.exceptions
import json
from typing import Dict, List
import google.generativeai as genai
import nltk
import os
from tqdm import tqdm
# from bleurt_pytorch.tokenization import BleurtSPTokenizer
from typing import Tuple
nltk.download('punkt_tab')
import google.generativeai as genai
from typing import List


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

API_KEY = "AIzaSyAISyP5zG-7NIV5F6xesUveTRDmtQ_6eyU"
# API_KEY = "AIzaSyAlgAWun2JG6ws1ThKqUwYzX8I4aBCmNbk"
# API_KEY = "AIzaSyCdH1RVi5Rki_cm_ypw3RX8Bgy4YsIBHtI"
# API_KEY = "AIzaSyClasB_b7S4LbjrcqZvQc74RAdPIazcCM0"

THRESHOLD = 0.55
INPUT_FOLDER_DIR = "data"
OUTPUT_FOLDER_DIR = "augmented_data"
LOAD_FOLDER_DIR = "augmented_progress_data"

# MODEL = "gemini-pro"
# RPM_LIMIT = 15
# RPD_LIMIT = 1_500
# TPM_LIMIT = 1_000_000

MODEL = "gemini-1.5-flash-latest"
RPM_LIMIT = 15
RPD_LIMIT = 1_500
TPM_LIMIT = 1_000_000

import google.generativeai as genai

genai.configure(api_key=API_KEY)
model = genai.GenerativeModel(MODEL)

def translate_text(text: str) -> str:
    prompt = f"""
    Translate this sentence to Vietnamese ancient text using literature style that is similar to the given example, ONLY GIVE YOUR BEST ANSWER, NO FURTHER EXPLANATION:
    {text}
    For example: "I have long been consumed by a yearning from you" can be translated to "Biết là ta nhớ nhung đã lâu nay"
    """
    
    response = model.generate_content(prompt)
    return response.text.strip()

# Test
if __name__ == "__main__":
    test_text = "I pray you, sir, return and gaze upon your own bright reflection"
    translation = translate_text(test_text)
    print(f"Original: {test_text}")
    print(f"Translation: {translation}")

