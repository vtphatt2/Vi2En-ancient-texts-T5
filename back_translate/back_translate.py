import time
import logging
from dataclasses import dataclass
from enum import Enum
from datetime import datetime, timedelta
from collections import deque
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
    after_log
)
import google.api_core.exceptions
import json
from typing import Dict, List
import google.generativeai as genai
import nltk
import os
from transformers import pipeline
from tqdm import tqdm
import requests
import torch
from nltk.translate.bleu_score import sentence_bleu, SmoothingFunction
from typing import Tuple
import numpy
import py_vncorenlp
from transformers import AutoModel, AutoTokenizer
nltk.download('punkt_tab')


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# API_KEY = "AIzaSyAISyP5zG-7NIV5F6xesUveTRDmtQ_6eyU"
# API_KEY = "AIzaSyAlgAWun2JG6ws1ThKqUwYzX8I4aBCmNbk"
# API_KEY = "AIzaSyCdH1RVi5Rki_cm_ypw3RX8Bgy4YsIBHtI"
# API_KEY = "AIzaSyClasB_b7S4LbjrcqZvQc74RAdPIazcCM0"
# API_KEY = "AIzaSyAVYRXQUEZTfaqAPsvwARhZC6vCmjEyQGk"
# API_KEY = "AIzaSyDEhc7c7LgEppWsV2T7AJgjA1jmAsrXV9o"
# API_KEY = "AIzaSyAyTYahX2pyJCbtAkVgZXhd56G69yN9TDc"
# API_KEY = "AIzaSyBc4l4JTyS03cGnulk_I-Ak-GvVnMDKHEo"
# API_KEY = "AIzaSyBZBza9CmKBNYNjfHl2Ai5tWY8hi-PpFVQ"
API_KEY = "AIzaSyCn7PvfXQqLlMOq5_Pj3I-B85qsvHt--ZE"
# API_KEY = "AIzaSyDMUd29MMduSTwhCWbBd8EzId-DmtVsdKo"

PHOBERT_THRESHOLD = 0.7

SCRIPT_PATH = os.path.abspath(__file__)
SCRIPT_DIR = os.path.dirname(SCRIPT_PATH)
PROJECT_ROOT = SCRIPT_DIR
INPUT_FOLDER_DIR = os.path.join(PROJECT_ROOT, "backtranslate_data")
OUTPUT_FOLDER_DIR = os.path.join(PROJECT_ROOT, "augmented_data_ver03")
LOAD_FOLDER_DIR = os.path.join(PROJECT_ROOT, "augmented_progress_data_ver03")
SAVE_MODEL_DIR = os.path.join(PROJECT_ROOT, "vncorenlp")


def ensure_directory_exists(directory_path: str):
    """Create directory if it doesn't exist."""
    try:
        if not os.path.exists(directory_path):
            os.makedirs(directory_path)
            logging.info(f"Created directory: {directory_path}")
    except Exception as e:
        logging.error(f"Error creating directory {directory_path}: {e}")
        raise

class GeminiModel(Enum):
    GEMINI_PRO = "gemini-pro"
    GEMINI_1_5_FLASH = "gemini-1.5-flash-latest"
    GEMINI_1_5_PRO = "gemini-1.5-pro-latest"
    GEMINI_2_FLASH = "gemini-2.0-flash-exp"
    GEMINI_1_5_PRO_002 = "gemini-1.5-pro-002"\
    
@dataclass
class ModelConfig:
    model: GeminiModel
    rpm_limit: int
    rpd_limit: int
    tpm_limit: int

    @classmethod
    def get_config(cls, model: GeminiModel):
        if model == GeminiModel.GEMINI_PRO:
            return cls(model, 15, 1_500, 1_000_000)
        elif model == GeminiModel.GEMINI_1_5_FLASH:
            return cls(model, 15, 1_500, 1_000_000)
        elif model == GeminiModel.GEMINI_1_5_PRO:
            return cls(model, 2, 50, 32_000)
        elif model == GeminiModel.GEMINI_2_FLASH:
            return cls(model, 10, 1_500, 1_000_000)
        elif model == GeminiModel.GEMINI_1_5_PRO_002:
            return cls(model, 6, 1_500, 1_000_000)
        else:
            raise ValueError(f"Unsupported model: {model}")

CURRENT_CONFIG = ModelConfig.get_config(GeminiModel.GEMINI_1_5_FLASH)
MODEL = CURRENT_CONFIG.model.value
RPM_LIMIT = CURRENT_CONFIG.rpm_limit
RPD_LIMIT = CURRENT_CONFIG.rpd_limit
TPM_LIMIT = CURRENT_CONFIG.tpm_limit

class GeminiRateLimiter:
    def __init__(self):
        # Queue length matches time window
        self.minute_requests = deque(maxlen=RPM_LIMIT)
        self.daily_requests = deque(maxlen=RPD_LIMIT)
        self.minute_tokens = deque(maxlen=TPM_LIMIT)

        # Track current window start times
        self.last_cleanup = datetime.now()
        
    def _clean_old_requests(self):
        """Remove outdated entries to maintain sliding window limits."""
        now = datetime.now()
        minute_ago = now - timedelta(minutes=1)
        day_ago = now - timedelta(days = 1)
        
        # Remove requests older than 1 minute
        while self.minute_requests and self.minute_requests[0] <= minute_ago:
            self.minute_requests.popleft()
        
        # Remove tokens older than 1 minute
        while self.minute_tokens and self.minute_tokens[0][0] <= minute_ago:
            self.minute_tokens.popleft()
            
        # Remove requests older than 1 day
        while self.daily_requests and self.daily_requests[0] <= day_ago:
            self.daily_requests.popleft()

        self.last_cleanup = now
    
    def _calculate_sleep_time(self, deque_list, time_delta) -> float:
        """Calculate the sleep time to respect rate limits."""
        if not deque_list:
            return 0

        now = datetime.now()
        if len(deque_list) >= deque_list.maxlen:
            sleep_time = (deque_list[0] + time_delta - now).total_seconds()
            return max(0, sleep_time)
        return 0

    def _wait_if_exceeded(self, condition, sleep_time, limit_type):
        """Pause execution if a rate limit is exceeded."""
        if condition and sleep_time > 0:
            logger.warning(f"{limit_type} limit reached. Sleeping for {sleep_time:.2f} seconds")
            time.sleep(sleep_time)
    
    def wait_if_needed(self, estimated_tokens=1000):
        """
        Check all rate limits and wait if necessary.
        Args:
            estimated_tokens: Estimated token count for this request
        """
        # Only clean if significant time has passed (e.g., every 5 seconds)
        now = datetime.now()
        if (now - self.last_cleanup).total_seconds() > 5:
            self._clean_old_requests()
        
        # Check RPM limit
        rpm_sleep_time = self._calculate_sleep_time(self.minute_requests, timedelta(minutes=1))
        self._wait_if_exceeded(len(self.minute_requests) >= RPM_LIMIT, rpm_sleep_time, "RPM")
        
        # Check RPD limit
        rpd_sleep_time = self._calculate_sleep_time(self.daily_requests, timedelta(days=1))
        self._wait_if_exceeded(len(self.daily_requests) >= RPD_LIMIT, rpd_sleep_time, "RPD")
        
        # Check TPM limit
        current_tokens = sum(tokens for _, tokens in self.minute_tokens)
        tpm_sleep_time = self._calculate_sleep_time(self.minute_tokens, timedelta(minutes=1))
        self._wait_if_exceeded(
            current_tokens + estimated_tokens > TPM_LIMIT, tpm_sleep_time, "TPM"
        )
        
        # Record new request and tokens
        now = datetime.now()
        self.minute_requests.append(now)
        self.daily_requests.append(now)
        self.minute_tokens.append((now, estimated_tokens))
        
        # Debugging logs
        logger.info(
            f"Current: {len(self.minute_requests)} RPM, {len(self.daily_requests)} RPD, {current_tokens} Tokens/Min"
        )

def setup_gemini(api_key):
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(MODEL)
    return model

@retry(
    retry=retry_if_exception_type((
        google.api_core.exceptions.ResourceExhausted,
        google.api_core.exceptions.ServiceUnavailable,
        google.api_core.exceptions.TooManyRequests
    )),
    wait=wait_exponential(multiplier=2, min=4, max=60),
    stop=stop_after_attempt(5),
    before_sleep=before_sleep_log(logger, logging.INFO),
    after=after_log(logger, logging.INFO)
)

class VietnameseSentenceSimilarity:
  def __init__(self, path):
    self.model = AutoModel.from_pretrained("vinai/phobert-base-v2")
    self.tokenizer = AutoTokenizer.from_pretrained("vinai/phobert-base-v2")
    self.rdrsegmenter = py_vncorenlp.VnCoreNLP(annotators=["wseg"], save_dir= path)
  def segmentation(self, sentence1, sentence2):

    segment1 = self.rdrsegmenter.word_segment(sentence1)
    segment2 = self.rdrsegmenter.word_segment(sentence2)
    return segment1, segment2
  def get_sentence_embedding(self, segment, pooling="mean"):
    inputs = self.tokenizer(segment, return_tensors="pt", padding=True, truncation=True)

    with torch.no_grad():
        outputs = self.model(**inputs)

    if pooling == "cls":
        # Use [CLS] token embedding
        embeddings = outputs.last_hidden_state[:, 0, :]
    else:
        # Use mean pooling
        embeddings = outputs.last_hidden_state.mean(dim=1)

    return embeddings[0].numpy()
  def cosine_similarity(self, sentence1, sentence2):
    segment1, segment2 = self.segmentation(sentence1, sentence2)
    embedding1 = self.get_sentence_embedding(segment1)
    embedding2 = self.get_sentence_embedding(segment2)
    dot_product = numpy.dot(embedding1, embedding2)
    norm1 = numpy.linalg.norm(embedding1)
    norm2 = numpy.linalg.norm(embedding2)
    similarity = dot_product / (norm1 * norm2)
    return similarity

def translate_with_gemini(model, text, rate_limiter, source_lang='English', target_lang='Vietnamese'):
    """Translate text using Gemini model with comprehensive rate limiting"""
    try:
        # Estimate tokens (roughly 4 chars per token for Vietnamese/English)
        estimated_tokens = len(text) // 4 * 2  # Input + output tokens
        
        # Wait if we're approaching rate limits
        rate_limiter.wait_if_needed(estimated_tokens)

        prompt = f"""Translate this {source_lang} literature to classical {target_lang} text.
        Instructions:
        - Provide exactly ONE translation
        - Maintain literary style and poetic elements
        - Keep the original meaning and cultural context
        - Translate in two styles: the Nom script style and the Han script style but use Vietnamese words (do not use Nom and Han characters)
        - Do not provide multiple versions or alternatives of one style
        - Do not include explanatory text
        - Keep the named entities in the original language

        Here is an example of Nom script style: 
        en: By lamplight, I peruse the tales of Tây Minh.
        vi: Dạ quang, duyệt Tây Minh truyện. 
        
        Here is an example of Han script style:
        en: At the age of twenty-eight, his vocation was the pursuit of learning.
        vi: Vân lai nhị bát, chí tại kinh thư.
        
        Original {source_lang} text:
        {text}

        Return the classical {target_lang} translation in JSON format: 
        {{
            \"nom\": \"Your Nom script style translation here\",
            \"han\": \"Your Han script style translation here\"
        }}
        """
        
        generation_config = {
            "response_mime_type": "application/json",
            "temperature": 0.3,
            "top_p": 0.85,
            "top_k": 40,
            "max_output_tokens": 1024,
            "stop_sequences": ["\n\n"]
        }

        safety_settings = {
            "HARM_CATEGORY_HARASSMENT": "BLOCK_NONE",
            "HARM_CATEGORY_HATE_SPEECH": "BLOCK_NONE",
            "HARM_CATEGORY_SEXUALLY_EXPLICIT": "BLOCK_NONE",
            "HARM_CATEGORY_DANGEROUS_CONTENT": "BLOCK_NONE"
        }

        response = model.generate_content(
            prompt,
            generation_config=generation_config,
            safety_settings=safety_settings
        )

        if response and response.text:
            return response.text.strip()
        return None
    
    except Exception as e:
        logger.error(f"Translation error: {str(e)}")
        raise


def augment_data(input_file: str, output_file: str, load_file: str, api_key: str, 
                 instance: VietnameseSentenceSimilarity):
    """Augment data with proper rate limiting"""
    model = setup_gemini(api_key)
    rate_limiter = GeminiRateLimiter()
    
    if not model:
        logger.error("Failed to initialize Gemini model.")
        return
    
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    augmented_data = {
        "file_name": data["file_name"],
        "data": [],
        "processed_indices": []  # Track all processed indices
    }
    
    progress_file = load_file
    
    # Try to load progress if exists
    try:
        with open(progress_file, 'r', encoding='utf-8') as f:
            progress_data = json.load(f)
            augmented_data["data"] = progress_data["data"]
            augmented_data["processed_indices"] = progress_data.get("processed_indices", [])
            logger.info(f"Resumed from progress: {len(augmented_data['data'])} augmented items, "
                        f"{len(augmented_data['processed_indices'])} processed items")
    except FileNotFoundError:
        pass
    

    # Create a set of processed indices for faster lookup
    processed_indices = set(augmented_data["processed_indices"])
    
    # Create progress bar for remaining items
    remaining_items = [i for i in range(len(data["data"])) if i not in processed_indices]
    pbar = tqdm(remaining_items, initial=len(processed_indices), total=len(data["data"]))

    current_augmented_index = len(augmented_data.get("data", []))
    
    for idx in remaining_items:
        try:
            item = data["data"][idx]
            english_sentence = item["en"]
            vietnamese_sentence = item["vi"]
            translation_result = json.loads(translate_with_gemini(model, english_sentence, rate_limiter))

            if translation_result: 
                nom_score = instance.cosine_similarity(vietnamese_sentence, translation_result["nom"])
                if nom_score >= PHOBERT_THRESHOLD:
                    augmented_data["data"].append({
                        "original_vi": vietnamese_sentence,
                        "augmented_vi": translation_result["nom"],
                        "en": english_sentence,
                        "score": nom_score,
                        "augmented_index": current_augmented_index,  # Position in augmented dataset
                        "original_index": idx,  # Add index for alignment
                    })
                    current_augmented_index += 1
                han_score = instance.cosine_similarity(vietnamese_sentence, translation_result["han"])
                if han_score >= PHOBERT_THRESHOLD:
                    augmented_data["data"].append({
                        "original_vi": vietnamese_sentence,
                        "style": "Han",
                        "augmented_vi": translation_result["han"],
                        "en": english_sentence,
                        "score": han_score,
                        "augmented_index": current_augmented_index,  # Position in augmented dataset
                        "original_index": idx,  # Add index for alignment
                    })
                    current_augmented_index += 1
                logger.info(f"Item {idx} scores:")
                logger.info(f"PhoBERT score on Nom text : {round(nom_score, 3)}")
                logger.info(f"PhoBERT score on Han text : {round(han_score, 3)}")                
            
            # Track this index as processed regardless of success
            augmented_data["processed_indices"].append(idx)
            processed_indices.add(idx)
            
            # Save progress every 5 items
            if len(processed_indices) % 5 == 0:
                with open(progress_file, 'w', encoding='utf-8') as f:
                    json.dump(augmented_data, f, ensure_ascii=False, indent=4)
            
            pbar.update(1)
                    
        except Exception as e:
            logger.error(f"Error processing item {idx}: {str(e)}")
            # Save progress before continuing
            with open(progress_file, 'w', encoding='utf-8') as f:
                json.dump(augmented_data, f, ensure_ascii=False, indent=4)
            continue
    
    pbar.close()

    # Prepare final output data (without processed_indices)
    final_output = {
        "file_name": data["file_name"],
        "data": augmented_data["data"]
    }
    
    # Save final output
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(final_output, f, ensure_ascii=False, indent=4)
    
    # Keep progress file for potential future runs
    with open(progress_file, 'w', encoding='utf-8') as f:
        json.dump(augmented_data, f, ensure_ascii=False, indent=4)
    
    logger.info(f"Completed processing with {len(augmented_data['data'])} augmented items "
               f"out of {len(augmented_data['processed_indices'])} processed items")
    
def process_all_json_files(input_folder_dir: str, output_folder_dir: str, load_folder_dir: str, api_key: str,
                           instance: VietnameseSentenceSimilarity):
    excluded_patterns = ['_augmented', '_progress']
    json_files = [
        f for f in os.listdir(input_folder_dir) 
        if f.endswith('.json') and 
        not any(pattern in f for pattern in excluded_patterns)
    ]
    
    if not json_files:
        logger.info(f"No non-augmented JSON files found in {input_folder_dir}")
        return
    
    for input_file in json_files:
        try:
            input_path = os.path.join(input_folder_dir, input_file)
            output_file = input_file.replace('.json', '_augmented_1.json')
            output_path = os.path.join(output_folder_dir, output_file)
            load_file = output_file.replace('.json', '_progress.json')
            load_path = os.path.join(load_folder_dir, load_file)
            
            logger.info(f"\nProcessing: {input_file}")
            augment_data(input_path, output_path, load_path, api_key, instance)
            
        except Exception as e:
            logger.error(f"Error processing {input_file}: {str(e)}")

def check_model_exists(model_dir):
    # VnCoreNLP model file pattern
    model_file = os.path.join(model_dir, "VnCoreNLP-1.2.jar")
    return os.path.exists(model_file)

def ensure_vncorenlp_setup():
    # Create vncorenlp directory inside the project
    vncorenlp_dir = os.path.join(PROJECT_ROOT, "vncorenlp")
    if not os.path.exists(vncorenlp_dir):
        os.makedirs(vncorenlp_dir)
    return vncorenlp_dir

def main():
    # Create required directories
    ensure_directory_exists(INPUT_FOLDER_DIR)
    ensure_directory_exists(OUTPUT_FOLDER_DIR)
    ensure_directory_exists(LOAD_FOLDER_DIR)
    ensure_directory_exists(SAVE_MODEL_DIR)
    # print("Path:", SAVE_MODEL_DIR)
    # Check if VnCoreNLP model exists
    if not check_model_exists(SAVE_MODEL_DIR):
        py_vncorenlp.download_model(save_dir=SAVE_MODEL_DIR)
    instance = VietnameseSentenceSimilarity(SAVE_MODEL_DIR)
    process_all_json_files(INPUT_FOLDER_DIR, OUTPUT_FOLDER_DIR, LOAD_FOLDER_DIR, API_KEY, instance)

if __name__ == "__main__":
    main()