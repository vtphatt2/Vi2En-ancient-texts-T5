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
import torch
from bleurt_pytorch import BleurtConfig, BleurtForSequenceClassification, BleurtTokenizer
from nltk.translate.bleu_score import sentence_bleu, SmoothingFunction
import sacrebleu
from typing import Tuple
from bert_score import BERTScorer
from comet import download_model, load_from_checkpoint
nltk.download('punkt_tab')


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# API_KEY = "AIzaSyAISyP5zG-7NIV5F6xesUveTRDmtQ_6eyU"
# API_KEY = "AIzaSyAlgAWun2JG6ws1ThKqUwYzX8I4aBCmNbk"
# API_KEY = "AIzaSyCdH1RVi5Rki_cm_ypw3RX8Bgy4YsIBHtI"
API_KEY = "AIzaSyClasB_b7S4LbjrcqZvQc74RAdPIazcCM0"
# API_KEY = "AIzaSyAVYRXQUEZTfaqAPsvwARhZC6vCmjEyQGk"
# API_KEY = "AIzaSyDEhc7c7LgEppWsV2T7AJgjA1jmAsrXV9o"
# API_KEY = "AIzaSyAyTYahX2pyJCbtAkVgZXhd56G69yN9TDc"
# API_KEY = "AIzaSyBc4l4JTyS03cGnulk_I-Ak-GvVnMDKHEo"
# API_KEY = "AIzaSyBZBza9CmKBNYNjfHl2Ai5tWY8hi-PpFVQ"
# API_KEY = "AIzaSyCn7PvfXQqLlMOq5_Pj3I-B85qsvHt--ZE"
# API_KEY = "AIzaSyDMUd29MMduSTwhCWbBd8EzId-DmtVsdKo"

BLEURT_THRESHOLD = 0.55
SACREBLEU_THRESHOLD = 0.1
BLEU_THRESHOLD = 0.1
BERTSCORE_THRESHOLD = 0.3
COMET_THRESHOLD = 0

SCRIPT_PATH = os.path.abspath(__file__)
SCRIPT_DIR = os.path.dirname(SCRIPT_PATH)
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
INPUT_FOLDER_DIR = os.path.join(PROJECT_ROOT, "data")
OUTPUT_FOLDER_DIR = os.path.join(PROJECT_ROOT, "augmented_data_ver04")
LOAD_FOLDER_DIR = os.path.join(PROJECT_ROOT, "augmented_progress_data_ver04")


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

class TranslationEvaluator:
    def __init__(self):
        self.bleu = pipeline("translation", model="Helsinki-NLP/opus-mt-vi-en")
        self.smoothing = SmoothingFunction().method7
        self.sacrebleu = sacrebleu.corpus_bleu
        self.bleurt = BleurtScorer()
        self.bert_scorer = BERTScorer(lang="en", rescale_with_baseline=True)
        # self.comet_kiwi = load_from_checkpoint(download_model("Unbabel/wmt22-cometkiwi-da"))
        # self.comet_base = load_from_checkpoint(download_model("Unbabel/wmt22-comet-da"))
        # try:
        #     # Initialize COMET with CPU fallback
        #     model_path = download_model("Unbabel/wmt22-comet-da")
        #     self.comet_base = load_from_checkpoint(model_path)
        # except Exception as e:
        #     logger.error(f"Error initializing COMET: {e}")
        #     self.comet_base = None

    def evaluate(self, reference: str, candidate: str) -> tuple:
        """
        Evaluate translation using multiple metrics
        Returns: (is_acceptable, scores_dict)
        """

        try:
            # BLEURT score
            bleurt_scores = self.bleurt.score([reference], [candidate])

            # SacreBLEU score
            sacrebleu_score = self.sacrebleu([candidate], [[reference]]).score/100

            # BLEU score (using tokenized reference)
            reference_tokens = nltk.word_tokenize(reference)
            candidate_tokens = nltk.word_tokenize(candidate)
            bleu_score = sentence_bleu([reference_tokens], candidate_tokens, smoothing_function=self.smoothing)

            # BERTScore
            P, R, F1 = self.bert_scorer.score([candidate], [reference])
            bert_score = F1.mean().item()

            # COMET score
            # comet_kiwi_score = self.comet_kiwi.predict(
            #     [{"src": reference, "mt": candidate}]
            # )["scores"][0]

            # comet_base_score = self.comet_base.predict(
            #     [{"src": reference, "mt": candidate}]
            # )["scores"][0]


            scores = {
                'bleurt': bleurt_scores[0],
                'sacrebleu': sacrebleu_score,
                'bleu': bleu_score,

                'bert_score': bert_score,
                # 'comet_kiwi': comet_kiwi_score,
                # 'comet_base': comet_base_score
            }

            # Check if at least two conditions are satisfied
            conditions = [
                bleurt_scores[0] >= BLEURT_THRESHOLD,  # BLEURT score
                sacrebleu_score >= SACREBLEU_THRESHOLD,  # SacreBLEU score
                bleu_score >= BLEU_THRESHOLD,  # BLEU score

                bert_score >= BERTSCORE_THRESHOLD,  # BERTScore
                # comet_kiwi_score >= COMET_THRESHOLD,  # COMET Kiwi
                # comet_base_score >= COMET_THRESHOLD  # COMET Base
            ]

            # is_acceptable = (sum(conditions) >= 3) and (bleurt_scores[0] >= 0.4)
            is_acceptable = True

            return is_acceptable, scores

        except Exception as e:
            logging.error(f"Error evaluating translation: {e}")
            return False, {'bleurt': 0, 'sacrebleu': 0, 'bleu': 0, 'bert_score': 0, 'comet_kiwi': 0, 'comet_base': 0}
            # return False, {'bleurt': 0, 'sacrebleu': 0, 'bleu': 0}


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
def translate_with_gemini(model, text, rate_limiter, source_lang='Vietnamese', target_lang='English'):
    """Translate text using Gemini model with comprehensive rate limiting"""
    try:
        # Estimate tokens (roughly 4 chars per token for Vietnamese/English)
        estimated_tokens = len(text) // 4 * 2  # Input + output tokens
        
        # Wait if we're approaching rate limits
        rate_limiter.wait_if_needed(estimated_tokens)

        prompt = f"""Translate this classical {source_lang} literature to formal {target_lang}.
        Instructions:
        - Provide exactly ONE translation
        - Maintain literary style and poetic elements
        - Keep the original meaning and cultural context
        - Use formal, elegant English
        - Do not provide multiple versions or alternatives
        - Do not include explanatory text

        Original {source_lang} text:
        {text}

        Translate to {target_lang}:"""
        
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

def augment_data(input_file: str, output_file: str, load_file: str, api_key: str):
    """Augment data with proper rate limiting"""
    model = setup_gemini(api_key)
    rate_limiter = GeminiRateLimiter()
    evaluator = TranslationEvaluator()
    
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
            corrected_vi = item["vi"]
            translated_en = translate_with_gemini(model, corrected_vi, rate_limiter)
            
            if translated_en:
                acceptable, scores = evaluator.evaluate(item["en"], translated_en)

                logger.info(f"Item {idx} scores:")
                logger.info(f"BLEURT: {scores.get('bleurt', 0):.4f}")
                logger.info(f"SacreBLEU: {scores.get('sacrebleu', 0):.4f}")
                logger.info(f"BLEU: {scores.get('bleu', 0):.4f}")
                logger.info(f"BERTScore: {scores.get('bert_score', 0):.4f}")
                # logger.info(f"COMET Kiwi: {scores.get('comet_kiwi', 0):.4f}")
                # logger.info(f"COMET Base: {scores.get('comet_base', 0):.4f}")
                
                if acceptable:
                    augmented_data["data"].append({
                        "vi": corrected_vi,
                        "en": translated_en,
                        "augmented_index": current_augmented_index,  # Position in augmented dataset
                        "original_index": idx,  # Add index for alignment
                        "scores": {  # Add evaluation scores
                            "bleurt": float(f"{scores.get('bleurt', 0):.4f}"),
                            "sacrebleu": float(f"{scores.get('sacrebleu', 0):.4f}"),
                            "bleu": float(f"{scores.get('bleu', 0):.4f}"),
                            "bert_score": float(f"{scores.get('bert_score', 0):.4f}"),
                        }
                    })

                    current_augmented_index += 1
            
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

def process_all_json_files(input_folder_dir: str, output_folder_dir: str, load_folder_dir: str, api_key: str):
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
            augment_data(input_path, output_path, load_path, api_key)
            
        except Exception as e:
            logger.error(f"Error processing {input_file}: {str(e)}")

def main():
    ensure_directory_exists(INPUT_FOLDER_DIR)
    ensure_directory_exists(OUTPUT_FOLDER_DIR)
    ensure_directory_exists(LOAD_FOLDER_DIR)
    process_all_json_files(INPUT_FOLDER_DIR, OUTPUT_FOLDER_DIR, LOAD_FOLDER_DIR, API_KEY)

if __name__ == "__main__":
    main()