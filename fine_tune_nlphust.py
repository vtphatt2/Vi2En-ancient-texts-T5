import os
import json
from glob import glob
import torch
from datasets import Dataset
from transformers import (
    T5ForConditionalGeneration,
    T5Tokenizer,
    Seq2SeqTrainer,
    Seq2SeqTrainingArguments,
    DataCollatorForSeq2Seq
)
import shutil

os.environ["CUDA_VISIBLE_DEVICES"] = "1"

if os.path.exists('./results_nlphust'):
    shutil.rmtree('./results_nlphust')


model_name = "NlpHUST/t5-vi-en-base"
tokenizer = T5Tokenizer.from_pretrained(model_name)
model = T5ForConditionalGeneration.from_pretrained(model_name)
model.to('cuda') if torch.cuda.is_available() else model.to('cpu')


DATA_FOLDER = "data"  
AUGMENTED_DATA_FOLDER = "augmented_data"

json_files = glob(os.path.join(DATA_FOLDER, '*.json'))
json_files.sort()

vi_texts = []
en_texts = []

for json_file in json_files:
    with open(json_file, 'r', encoding='utf-8') as f:
        json_data = json.load(f)
        for item in json_data['data']:
            vi_texts.append(item['vi'])
            en_texts.append(item['en'])

# Load augmented data
json_files = glob(os.path.join(AUGMENTED_DATA_FOLDER, '*.json'))
json_files.sort()

for json_file in json_files:
    with open(json_file, 'r', encoding='utf-8') as f:
        json_data = json.load(f)
        for item in json_data['data']:
            vi_texts.append(item['vi'])
            en_texts.append(item['en'])

data_dict = {
    "vi": vi_texts,
    "en": en_texts
}

train_dataset = Dataset.from_dict(data_dict)
train_dataset = train_dataset.shuffle(seed=54)


def preprocess_function(examples):
    inputs = [vi for vi in examples['vi']]
    targets = [en for en in examples['en']]
    
    model_inputs = tokenizer(
        inputs, max_length=128, truncation=True, padding='max_length'
    )
    
    with tokenizer.as_target_tokenizer():
        labels = tokenizer(
            targets, max_length=128, truncation=True, padding='max_length'
        )
    
    model_inputs["labels"] = labels["input_ids"]
    return model_inputs

train_dataset = train_dataset.map(preprocess_function, batched=True)
train_dataset, eval_dataset = train_dataset.train_test_split(test_size=0.01).values()


training_args = Seq2SeqTrainingArguments(
    output_dir="results_nlphust/",
    learning_rate=1e-4,
    num_train_epochs=100,
    weight_decay=0.01,
    per_device_train_batch_size=64,
    predict_with_generate=True,
    save_strategy="epoch",
    save_total_limit=1,
    fp16=True,
)

data_collator = DataCollatorForSeq2Seq(tokenizer=tokenizer, model=model)

trainer = Seq2SeqTrainer(
    model=model,
    args=training_args,
    train_dataset=train_dataset,
    data_collator=data_collator,
)

trainer.train()


trainer.save_model("results_nlphust/")
tokenizer.save_pretrained("results_nlphust/")
