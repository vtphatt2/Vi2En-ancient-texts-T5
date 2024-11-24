import json
from datasets import Dataset
from transformers import T5Tokenizer, T5ForConditionalGeneration, Trainer, TrainingArguments

DATA_PATH = 'data/kieu1.json'

def load_data(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        data_json = json.load(f)
    
    data = data_json['data']
    inputs = [
        f"translate Vietnamese to English: {item['vi'].replace('.', '').replace(',', '')}"
        for item in data
    ]
    targets = [
        item['en'].replace('.', '').replace(',', '')
        for item in data
    ]
    
    return {'input_text': inputs, 'target_text': targets}

data_dict = load_data(DATA_PATH)
dataset = Dataset.from_dict(data_dict)

split_dataset = dataset.train_test_split(test_size=0.1)
train_dataset = split_dataset['train']
eval_dataset = split_dataset['test']

model_name = 't5-small' 
tokenizer = T5Tokenizer.from_pretrained(model_name)
model = T5ForConditionalGeneration.from_pretrained(model_name)

def preprocess_function(examples):
    inputs = examples['input_text']
    targets = examples['target_text']
    model_inputs = tokenizer(inputs, max_length=512, truncation=True, padding='max_length')

    with tokenizer.as_target_tokenizer():
        labels = tokenizer(targets, max_length=128, truncation=True, padding='max_length')
    
    model_inputs['labels'] = labels['input_ids']
    return model_inputs

tokenized_train = train_dataset.map(preprocess_function, batched=True)
tokenized_eval = eval_dataset.map(preprocess_function, batched=True)

training_args = TrainingArguments(
    output_dir='./t5_vi_en_translation',          
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
)

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=tokenized_train,
    eval_dataset=tokenized_eval,
    tokenizer=tokenizer,
)

trainer.train()

model_save_path = './t5_vi_en_translation'
model.save_pretrained(model_save_path)
tokenizer.save_pretrained(model_save_path)
