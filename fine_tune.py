# Import necessary libraries
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
from datasets import Dataset
from transformers import DataCollatorForSeq2Seq
from transformers import Seq2SeqTrainingArguments, Seq2SeqTrainer


# Load the model and tokenizer
model_name = "VietAI/envit5-translation"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForSeq2SeqLM.from_pretrained(model_name)


# Prepare data
data_dict = {
    "vi": ["Trăm năm trong cõi người ta"],
    "en": ["Through hundred years in life"]
}

train_dataset = Dataset.from_dict(data_dict)

prefix = "translate Vietnamese to English: "

def preprocess_function(examples):
    inputs = [prefix + example for example in examples["vi"]]
    targets = [example for example in examples["en"]]
    model_inputs = tokenizer(inputs, max_length=128, truncation=True)

    with tokenizer.as_target_tokenizer():
        labels = tokenizer(targets, max_length=128, truncation=True)

    model_inputs["labels"] = labels["input_ids"]
    
    return model_inputs

train_dataset = train_dataset.map(preprocess_function, batched=True)


# Data collator
data_collator = DataCollatorForSeq2Seq(tokenizer=tokenizer, model=model)


# Fine-tuning
training_args = Seq2SeqTrainingArguments(
    output_dir="./results",
    evaluation_strategy="epoch",
    learning_rate=2e-5,
    per_device_train_batch_size=16,
    per_device_eval_batch_size=16,
    weight_decay=0.01,
    save_total_limit=3,
    num_train_epochs=1,
    fp16=True,
)

trainer = Seq2SeqTrainer(
    model=model,
    args=training_args,
    train_dataset=train_dataset,
    eval_dataset=train_dataset,
    tokenizer=tokenizer,
    data_collator=data_collator,
)

trainer.train()