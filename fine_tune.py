import json
import glob
import logging
from datasets import Dataset
from transformers import T5Tokenizer, T5ForConditionalGeneration, Trainer, TrainingArguments
import torch

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()

DATA_FOLDER = 'data'  # Folder containing all the .json files

def load_data_from_files(data_folder):
    inputs = []  # To store all input texts
    targets = []  # To store all target texts
    
    # Get all .json files in the data folder using glob
    json_files = glob.glob(f"{data_folder}/*.json")
    logger.info(f"Found {len(json_files)} JSON files in {data_folder}.")
    
    for file_path in json_files:
        logger.info(f"Loading file: {file_path}")
        
        # Open and load each JSON file
        with open(file_path, 'r', encoding='utf-8') as f:
            data_json = json.load(f)
        
        # Extract the relevant data
        data = data_json['data']
        
        # Prepare the inputs and targets (translations)
        for item in data:
            inputs.append(f"translate Vietnamese to English: {item['vi'].replace('.', '').replace(',', '')}")
            targets.append(item['en'].replace('.', '').replace(',', ''))
        
    return {'input_text': inputs, 'target_text': targets}

# Load and merge all JSON files
data_dict = load_data_from_files(DATA_FOLDER)
dataset = Dataset.from_dict(data_dict)

# Split the dataset into training and evaluation sets
split_dataset = dataset.train_test_split(test_size=0.1)
train_dataset = split_dataset['train']
eval_dataset = split_dataset['test']

# Use VietAI/vit5-base model and tokenizer
model_name = 'VietAI/vit5-base'  # Change model to VietAI/vit5-base
tokenizer = T5Tokenizer.from_pretrained(model_name)  # Use tokenizer for VietAI/vit5-base
model = T5ForConditionalGeneration.from_pretrained(model_name)  # Load the model

# Move model to GPU if available
if torch.cuda.is_available():
    model = model.to('cuda')
    logger.info("GPU is available. Using GPU for training.")
else:
    logger.info("No GPU found. Using CPU for training.")

# Preprocessing function for tokenization
def preprocess_function(examples):
    inputs = examples['input_text']
    targets = examples['target_text']
    model_inputs = tokenizer(inputs, max_length=512, truncation=True, padding='max_length')

    with tokenizer.as_target_tokenizer():
        labels = tokenizer(targets, max_length=128, truncation=True, padding='max_length')
    
    model_inputs['labels'] = labels['input_ids']
    return model_inputs

# Tokenize the train and eval datasets
tokenized_train = train_dataset.map(preprocess_function, batched=True)
tokenized_eval = eval_dataset.map(preprocess_function, batched=True)

# Training arguments
training_args = TrainingArguments(
    output_dir='./vit5_vi_en_translation',          
    evaluation_strategy='epoch',
    learning_rate=5e-5,
    per_device_train_batch_size=4,      
    per_device_eval_batch_size=4,
    num_train_epochs=3,
    weight_decay=0.01,
    save_total_limit=2,
    logging_dir='./logs',
    logging_steps=10,
    save_strategy='epoch',
    # Enable FP16 mixed precision for better performance on supported GPUs
    fp16=True,  # You can also set fp16=True if your GPU supports mixed precision
)

# Initialize Trainer
trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=tokenized_train,
    eval_dataset=tokenized_eval,
    tokenizer=tokenizer,
)

# Start training
trainer.train()

# Save the model and tokenizer
model_save_path = './vit5_vi_en_translation'
model.save_pretrained(model_save_path)
tokenizer.save_pretrained(model_save_path)
