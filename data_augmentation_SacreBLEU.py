import time
from datetime import datetime, timedelta
import logging
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
import sacrebleu
import torch
from nltk.translate.bleu_score import sentence_bleu, SmoothingFunction
from transformers import pipeline
from tqdm import tqdm
from bleurt_pytorch import BleurtConfig, BleurtForSequenceClassification, BleurtTokenizer
# from bleurt_pytorch.tokenization import BleurtSPTokenizer
from typing import Tuple
nltk.download('punkt_tab')


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# API_KEY = "AIzaSyAISyP5zG-7NIV5F6xesUveTRDmtQ_6eyU"
# API_KEY = "AIzaSyAlgAWun2JG6ws1ThKqUwYzX8I4aBCmNbk"
# API_KEY = "AIzaSyCdH1RVi5Rki_cm_ypw3RX8Bgy4YsIBHtI"
API_KEY = "AIzaSyClasB_b7S4LbjrcqZvQc74RAdPIazcCM0"

THRESHOLD = 0.55
INPUT_FOLDER_DIR = "remaining_data"
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

# MODEL = "gemini-1.5-pro-latest"
# RPM_LIMIT = 2
# RPD_LIMIT = 50
# TPM_LIMIT = 32_000

# MODEL = "gemini-2.0-flash-exp"
# RPM_LIMIT = 10
# RPD_LIMIT = 1_500
# TPM_LIMIT = 1_000_000

# ## Experimental Models
# MODEL = "gemini-1.5-pro-002"
# RPM_LIMIT = 6
# RPD_LIMIT = 1_500
# TPM_LIMIT = 1_000_000

# gemini-1.5-pro-002: strong
# gemini-1.5-pro-exp-0827
# gemini-exp-1206


class BleurtScorer:
    def __init__(self, model_name: str = 'lucadiliello/BLEURT-20', device: str = None):
        """Initialize BLEURT components."""
        self.device = device or ('cuda' if torch.cuda.is_available() else 'cpu')
        self.config = BleurtConfig.from_pretrained(model_name)
        self.model = BleurtForSequenceClassification.from_pretrained(model_name).to(self.device)
        self.tokenizer = BleurtTokenizer.from_pretrained(
            model_name,
            truncation=True,
            max_length=512,
            padding=True
        )
        self.model.eval()

    @torch.no_grad()
    def score(self, references: list, candidates: list) -> list:
        """Calculate BLEURT scores for pairs of references and candidates."""
        # Ensure inputs are properly formatted
        if not isinstance(references, list) or not isinstance(candidates, list):
            references = [references]
            candidates = [candidates]
            
        try:
            inputs = self.tokenizer(
                references, 
                candidates,
                padding='longest',
                truncation=True,
                max_length=512,
                return_tensors='pt'
            ).to(self.device)
            
            scores = self.model(**inputs).logits.flatten().cpu().tolist()
            return scores
            
        except Exception as e:
            print(f"Error during tokenization or scoring: {e}")
            return [0.0] * len(references)  # Return default scores on error

class GeminiRateLimiter:
    def __init__(self):
        # Track requests per minute (15 RPM limit)
        self.minute_requests = deque()
        self.RPM_LIMIT = RPM_LIMIT
        
        # Track daily requests (1,500 RPD limit)
        self.daily_requests = deque()
        self.RPD_LIMIT = RPD_LIMIT
        
        # Track token usage per minute (1M TPM limit)
        self.minute_tokens = deque()
        self.TPM_LIMIT = TPM_LIMIT 
        
    def _clean_old_requests(self):
        """Remove expired entries from tracking deques"""
        now = datetime.now()
        
        # Clean minute-based trackers
        while self.minute_requests and (now - self.minute_requests[0]) > timedelta(minutes=1):
            self.minute_requests.popleft()
        while self.minute_tokens and (now - self.minute_tokens[0][0]) > timedelta(minutes=1):
            self.minute_tokens.popleft()
            
        # Clean daily tracker
        while self.daily_requests and (now - self.daily_requests[0]) > timedelta(days=1):
            self.daily_requests.popleft()
    
    def wait_if_needed(self, estimated_tokens=1000):
        """
        Check all rate limits and wait if necessary.
        Args:
            estimated_tokens: Estimated token count for this request
        """
        self._clean_old_requests()
        now = datetime.now()
        
        # Check RPM limit
        if len(self.minute_requests) >= self.RPM_LIMIT:
            sleep_time = (self.minute_requests[0] + timedelta(minutes=1) - now).total_seconds()
            if sleep_time > 0:
                logger.info(f"RPM limit reached. Sleeping for {sleep_time:.2f} seconds")
                time.sleep(sleep_time)
                self._clean_old_requests()  # Clean again after sleeping
        
        # Check RPD limit
        if len(self.daily_requests) >= self.RPD_LIMIT:
            sleep_time = (self.daily_requests[0] + timedelta(days=1) - now).total_seconds()
            if sleep_time > 0:
                logger.warning(f"Daily request limit reached. Sleeping for {sleep_time:.2f} seconds")
                time.sleep(sleep_time)
                self._clean_old_requests()
        
        # Check TPM limit
        current_tokens = sum(tokens for _, tokens in self.minute_tokens)
        if current_tokens + estimated_tokens > self.TPM_LIMIT:
            sleep_time = (self.minute_tokens[0][0] + timedelta(minutes=1) - now).total_seconds()
            if sleep_time > 0:
                logger.info(f"TPM limit reached. Sleeping for {sleep_time:.2f} seconds")
                time.sleep(sleep_time)
                self._clean_old_requests()
        
        # Record this request
        self.minute_requests.append(now)
        self.daily_requests.append(now)
        self.minute_tokens.append((now, estimated_tokens))

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
def translate_with_gemini(model, text, rate_limiter, source_lang='Vietnamese', target_lang='English'):
    """Translate text using Gemini model with comprehensive rate limiting"""
    try:
        # Estimate tokens (roughly 4 chars per token for Vietnamese/English)
        estimated_tokens = len(text) // 4 * 2  # Input + output tokens
        
        # Wait if we're approaching rate limits
        rate_limiter.wait_if_needed(estimated_tokens)
        
        prompt = f"""Translate this classical Vietnamese literature to formal {target_lang}. 
        Maintain the literary style and poetic elements while ensuring accuracy:

        Original {source_lang} text:
        {text}

        Translation:"""
        
        generation_config = {
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

def evaluate_translation(reference: str, candidate: str, threshold: float = 0.4) -> Tuple[bool, float]:
    """
    Evaluate translation quality using sacreBLEU score.
    Args:
        reference: Reference translation
        candidate: Generated translation to evaluate
        threshold: Minimum acceptable score (normalized)
    Returns:
        Tuple of (bool acceptable, float score)
    """
    try:
        # Calculate sacreBLEU score
        bleu = sacrebleu.sentence_bleu(
            candidate,
            [reference],
            smooth_method='exp',  # Exponential smoothing for sentence-level
            smooth_value=0.0,
            tokenize='13a'  # Standard tokenization
        )
        
        # Normalize score to [0,1] range
        normalized_score = bleu.score / 100.0
        
        return normalized_score >= threshold, normalized_score
        
    except Exception as e:
        print(f"Error calculating sacreBLEU score: {e}")
        return False, 0.0

def augment_data(input_file: str, output_file: str, load_file: str, api_key: str, threshold: float = 0.6):
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
    
    processed_count = len(augmented_data['data'])

    # Create a set of processed indices for faster lookup
    processed_indices = set(augmented_data["processed_indices"])
    
    # Create progress bar for remaining items
    remaining_items = [i for i in range(len(data["data"])) if i not in processed_indices]
    pbar = tqdm(remaining_items, initial=len(processed_indices), total=len(data["data"]))
    
    for idx in remaining_items:
        try:
            item = data["data"][idx]
            corrected_vi = item["vi"]
            translated_en = translate_with_gemini(model, corrected_vi, rate_limiter)
            
            if translated_en:
                acceptable, score = evaluate_translation(item["en"], translated_en, threshold)
                logger.info(f"Item {idx}: Translation score: {score:.4f} (threshold: {threshold})")
                
                if acceptable:
                    augmented_data["data"].append({
                        "vi": corrected_vi,
                        "en": translated_en
                    })
            
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

def process_all_json_files(input_folder_dir: str, output_folder_dir: str, load_folder_dir: str, api_key: str, threshold: float = 0.6):
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
            augment_data(input_path, output_path, load_path, api_key, threshold)
            
        except Exception as e:
            logger.error(f"Error processing {input_file}: {str(e)}")

def main():
    process_all_json_files(INPUT_FOLDER_DIR, OUTPUT_FOLDER_DIR, LOAD_FOLDER_DIR, API_KEY, THRESHOLD)

if __name__ == "__main__":
    main()