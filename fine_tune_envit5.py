# # Import necessary libraries
# from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
# from datasets import Dataset
# from transformers import DataCollatorForSeq2Seq
# from transformers import Seq2SeqTrainingArguments, Seq2SeqTrainer
# from glob import glob
# import os
# import json
# import evaluate
# import numpy as np
# import shutil
# import torch

# if os.path.exists('./results_envit5'):
#     shutil.rmtree('./results_envit5')

# os.environ["CUDA_VISIBLE_DEVICES"] = "7"
# device = 'cuda' if torch.cuda.is_available() else 'cpu'



# # Load the model and tokenizer
# model_name = "VietAI/envit5-translation"
# tokenizer = AutoTokenizer.from_pretrained(model_name)
# model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
# model.to(device) 



# # Define the data folder
# DATA_FOLDER = "data"

# # Prepare data
# vi_texts = []
# en_texts = []

# data_json_files = glob(os.path.join(DATA_FOLDER, '*.json'))
# data_json_files.sort()

# for json_file in data_json_files:
#     with open(json_file, 'r', encoding='utf-8') as f:
#         json_data = json.load(f)
#         for item in json_data['data']:
#             vi_texts.append(item['vi'])
#             en_texts.append(item['en'])


# with open("test.json", "r", encoding="utf-8") as f:
#     test_data = json.load(f)

# for item in test_data['data']:
#     index = en_texts.index(item['en'])
#     del vi_texts[index]
#     del en_texts[index]

# data_dict = {
#     "vi": vi_texts,
#     "en": en_texts
# }

# train_dataset = Dataset.from_dict(data_dict)
# train_dataset = train_dataset.shuffle(seed=54)



# # Preprocess the data
# def preprocess_function(examples):
#     inputs = ["vi: " + example.strip() for example in examples["vi"]]
#     targets = ["en: " + example.strip() for example in examples["en"]]
#     model_inputs = tokenizer(inputs, max_length=128, truncation=True)

#     with tokenizer.as_target_tokenizer():
#         labels = tokenizer(targets, max_length=128, truncation=True)

#     model_inputs["labels"] = labels["input_ids"]
    
#     return model_inputs

# train_dataset = train_dataset.map(preprocess_function, batched=True)


# # Data collator
# data_collator = DataCollatorForSeq2Seq(tokenizer=tokenizer, model=model)


# # Split the train dataset into train and eval datasets (90% train, 10% eval)
# train_dataset, eval_dataset = train_dataset.train_test_split(test_size=0.005).values()


# # Fine-tuning
# training_args = Seq2SeqTrainingArguments(
#     output_dir="./results_envit5",
#     evaluation_strategy="epoch",
#     learning_rate=1e-4,
#     num_train_epochs=100,
#     weight_decay=0.01,
#     per_device_train_batch_size=128,
#     per_device_eval_batch_size=16,
#     predict_with_generate=True,
#     save_strategy="epoch",
#     save_total_limit=1,
#     fp16=True
# )

# def postprocess_text(preds, labels):
#     preds = [pred.strip() for pred in preds]
#     labels = [[label.strip()] for label in labels]
#     return preds, labels

# metric = evaluate.load("sacrebleu")

# def compute_metrics(eval_preds):
#     preds, labels = eval_preds

#     if isinstance(preds, tuple):
#         preds = preds[0]
#     labels = np.where(labels != -100, labels, tokenizer.pad_token_id)

#     decoded_preds = tokenizer.batch_decode(preds, skip_special_tokens=True)
#     decoded_labels = tokenizer.batch_decode(labels, skip_special_tokens=True)
#     decoded_preds, decoded_labels = postprocess_text(decoded_preds, decoded_labels)

#     result = metric.compute(predictions=decoded_preds, references=decoded_labels)
#     result = {"bleu": round(result["score"], 4)}

#     return result

# trainer = Seq2SeqTrainer(
#     model=model,
#     args=training_args,
#     train_dataset=train_dataset,
#     eval_dataset=eval_dataset,
#     data_collator=data_collator,
#     compute_metrics=compute_metrics
# )

# trainer.train()


# # Save the fine-tuned model
# model.save_pretrained("./results_envit5")
# tokenizer.save_pretrained("./results_envit5")


# Import necessary libraries
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
from datasets import Dataset
from transformers import DataCollatorForSeq2Seq
from transformers import Seq2SeqTrainingArguments, Seq2SeqTrainer
from glob import glob
import os
import json
import evaluate
import numpy as np
import shutil
import torch

if os.path.exists('./results_envit5'):
    shutil.rmtree('./results_envit5')

device = 'cuda' if torch.cuda.is_available() else 'cpu'

torch.cuda.empty_cache()
os.environ['PYTORCH_CUDA_ALLOC_CONF'] = 'expandable_segments:True'

# Load the model and tokenizer
model_name = "VietAI/envit5-translation"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
model.to(device) 




# Prepare data
vi_texts = []
en_texts = []

with open("train_test/train.json", "r", encoding="utf-8") as f:
    train_data = json.load(f)
    for item in train_data:
        vi_texts.append(item["vi"])
        en_texts.append(item["en"])

data_dict = {
    "vi": vi_texts,
    "en": en_texts
}

train_dataset = Dataset.from_dict(data_dict)
train_dataset = train_dataset.shuffle(seed=54)


# Preprocess the data
def preprocess_function(examples):
    inputs = ["vi: " + example.strip() for example in examples["vi"]]
    targets = ["en: " + example.strip() for example in examples["en"]]
    model_inputs = tokenizer(inputs, max_length=128, truncation=True)

    with tokenizer.as_target_tokenizer():
        labels = tokenizer(targets, max_length=128, truncation=True)

    model_inputs["labels"] = labels["input_ids"]
    
    return model_inputs

train_dataset = train_dataset.map(preprocess_function, batched=True)


# Data collator
data_collator = DataCollatorForSeq2Seq(tokenizer=tokenizer, model=model)


# Split the train dataset into train and eval datasets (90% train, 10% eval)
train_dataset, eval_dataset = train_dataset.train_test_split(test_size=0.0005).values()


# Fine-tuning
training_args = Seq2SeqTrainingArguments(
    output_dir="./results_envit5",
    evaluation_strategy="epoch",
    learning_rate=1e-4,
    num_train_epochs=100,
    weight_decay=0.01,
    per_device_train_batch_size=128,
    per_device_eval_batch_size=16,
    predict_with_generate=True,
    save_strategy="epoch",
    save_total_limit=1,
    fp16=True
)

def postprocess_text(preds, labels):
    preds = [pred.strip() for pred in preds]
    labels = [[label.strip()] for label in labels]
    return preds, labels

metric = evaluate.load("sacrebleu")

def compute_metrics(eval_preds):
    preds, labels = eval_preds

    if isinstance(preds, tuple):
        preds = preds[0]
    labels = np.where(labels != -100, labels, tokenizer.pad_token_id)

    decoded_preds = tokenizer.batch_decode(preds, skip_special_tokens=True)
    decoded_labels = tokenizer.batch_decode(labels, skip_special_tokens=True)
    decoded_preds, decoded_labels = postprocess_text(decoded_preds, decoded_labels)

    result = metric.compute(predictions=decoded_preds, references=decoded_labels)
    result = {"bleu": round(result["score"], 4)}

    return result

trainer = Seq2SeqTrainer(
    model=model,
    args=training_args,
    train_dataset=train_dataset,
    eval_dataset=eval_dataset,
    data_collator=data_collator,
    compute_metrics=compute_metrics
)

torch.cuda.empty_cache()

trainer.train()


# Save the fine-tuned model
model.save_pretrained("./results_envit5")
tokenizer.save_pretrained("./results_envit5")