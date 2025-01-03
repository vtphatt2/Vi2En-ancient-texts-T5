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
import numpy as np
import evaluate

os.environ["CUDA_VISIBLE_DEVICES"] = "3"


model_name = "NlpHUST/t5-vi-en-base"
tokenizer = T5Tokenizer.from_pretrained(model_name)
model = T5ForConditionalGeneration.from_pretrained(model_name)
model.to('cuda') if torch.cuda.is_available() else model.to('cpu')


DATA_FOLDER = "data"  
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

data_dict = {
    "vi": vi_texts,
    "en": en_texts
}

train_dataset = Dataset.from_dict(data_dict)


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
    evaluation_strategy="epoch",
    learning_rate=1e-4,
    num_train_epochs=20,
    weight_decay=0.01,
    per_device_train_batch_size=32,
    per_device_eval_batch_size=16,
    predict_with_generate=True,
    save_strategy="epoch",
    save_total_limit=1,
    fp16=True,
)

def postprocess_text(preds, labels):
    preds = [pred.strip() for pred in preds]
    labels = [[label.strip()] for label in labels]
    return preds, labels

metric = evaluate.load("sacrebleu")

def compute_metrics(eval_preds):
    # preds, labels = eval_preds

    # if isinstance(preds, tuple):
    #     preds = preds[0]
    # labels = np.where(labels != -100, labels, tokenizer.pad_token_id)

    # decoded_preds = tokenizer.batch_decode(preds, skip_special_tokens=True)
    # decoded_labels = tokenizer.batch_decode(labels, skip_special_tokens=True)
    # decoded_preds, decoded_labels = postprocess_text(decoded_preds, decoded_labels)

    # result = metric.compute(predictions=decoded_preds, references=decoded_labels)
    result = {"bleu": 1}

    return result

data_collator = DataCollatorForSeq2Seq(tokenizer=tokenizer, model=model)

trainer = Seq2SeqTrainer(
    model=model,
    args=training_args,
    train_dataset=train_dataset,
    eval_dataset=eval_dataset,
    data_collator=data_collator,
    compute_metrics=compute_metrics
)

trainer.train()


trainer.save_model("results_nlphust/")
tokenizer.save_pretrained("results_nlphust/")
