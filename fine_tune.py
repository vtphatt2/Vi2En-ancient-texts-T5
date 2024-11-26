import os
import json
import torch
from glob import glob
from transformers import T5ForConditionalGeneration, T5Tokenizer, AdamW
from torch.utils.data import DataLoader, TensorDataset
from tqdm import tqdm

# Check if CUDA (GPU) is available
if torch.cuda.is_available():
    device = torch.device("cuda")
    print('There are %d GPU(s) available.' % torch.cuda.device_count())
    print('We will use the GPU:', torch.cuda.get_device_name(0))
else:
    print('No GPU available, using the CPU instead.')
    device = torch.device("cpu")

# Define the folder where your .json files are stored
DATA_FOLDER = 'data'    # Folder containing all the .json files

# Load and tokenize the data from JSON files
def load_data_from_files(data_folder):
    inputs = []         # To store all input texts (Vietnamese)
    targets = []        # To store all target texts (English)
    
    # Initialize tokenizer
    tokenizer = T5Tokenizer.from_pretrained("NlpHUST/t5-vi-en-base")
    
    # Get all .json files in the data folder using glob
    json_files = glob(os.path.join(f"{data_folder}", "*.json"))
    
    for file_path in json_files:
        # Open and load each JSON file
        with open(file_path, 'r', encoding='utf-8') as f:
            data_json = json.load(f)
        
        # Extract the relevant data
        data = data_json['data']
        
        # Prepare the inputs and targets (translations)
        for item in data:
            # Format the input as "translate Vietnamese to English: <text>"
            inputs.append(f"translate Vietnamese to English: {item['vi'].replace('.', '').replace(',', '')}")
            targets.append(item['en'].replace('.', '').replace(',', ''))
        
    # Tokenize the inputs and targets
    tokenized_inputs = tokenizer(inputs, padding=True, truncation=True, return_tensors="pt")
    tokenized_targets = tokenizer(targets, padding=True, truncation=True, return_tensors="pt")

    return tokenized_inputs, tokenized_targets

# Load the data and tokenize it
tokenized_inputs, tokenized_targets = load_data_from_files(DATA_FOLDER)

# Prepare the DataLoader for batching
def create_dataloader(tokenized_inputs, tokenized_targets, batch_size=8):
    input_ids = tokenized_inputs['input_ids']
    attention_mask = tokenized_inputs['attention_mask']
    labels = tokenized_targets['input_ids']
    
    # Create the TensorDataset
    dataset = TensorDataset(input_ids, attention_mask, labels)
    
    # Create DataLoader
    dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=True)
    
    return dataloader

# Create the DataLoader
dataloader = create_dataloader(tokenized_inputs, tokenized_targets)

# Load the pre-trained model
model = T5ForConditionalGeneration.from_pretrained("NlpHUST/t5-vi-en-base")
model.to(device)

# Define the optimizer
optimizer = AdamW(model.parameters(), lr=5e-5)

# Define the training loop
def fine_tune_model(dataloader, model, optimizer, num_epochs=3):
    model.train()
    
    for epoch in range(num_epochs):
        total_loss = 0
        for batch in tqdm(dataloader, desc=f"Epoch {epoch+1}/{num_epochs}"):
            # Move the batch to the appropriate device
            input_ids, attention_mask, labels = [x.to(device) for x in batch]

            # Forward pass
            outputs = model(input_ids=input_ids, attention_mask=attention_mask, labels=labels)
            loss = outputs.loss

            # Backward pass
            loss.backward()
            
            # Update parameters
            optimizer.step()
            optimizer.zero_grad()

            # Track the loss
            total_loss += loss.item()

        avg_loss = total_loss / len(dataloader)
        print(f"Epoch {epoch+1} - Average Loss: {avg_loss:.4f}")

# Start fine-tuning
fine_tune_model(dataloader, model, optimizer, num_epochs=3)

# Save the fine-tuned model
model.save_pretrained("fine_tuned_t5_vi_en")
T5Tokenizer.from_pretrained("NlpHUST/t5-vi-en-base").save_pretrained("fine_tuned_t5_vi_en")
