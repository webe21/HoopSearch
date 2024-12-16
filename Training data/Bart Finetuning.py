from transformers import BartTokenizer, BartForConditionalGeneration, Trainer, TrainingArguments, EarlyStoppingCallback
from datasets import load_dataset
from sklearn.model_selection import train_test_split
import pandas as pd

# Load tokenizer and model for BART
tokenizer = BartTokenizer.from_pretrained("facebook/bart-large")
model = BartForConditionalGeneration.from_pretrained("facebook/bart-large")

# Load the custom dataset
dataset = pd.read_csv("./Training data/data training/sample_indosum_indonesian.csv")  # Pastikan file berada di direktori yang sama

# Split the dataset into train and validation sets (80% train, 20% validation)
train_data, val_data = train_test_split(dataset, test_size=0.2, random_state=42)

# Save the train and validation sets as temporary CSV files
train_data.to_csv("train_data.csv", index=False)
val_data.to_csv("val_data.csv", index=False)

# Load the train and validation datasets using load_dataset
train_dataset = load_dataset('csv', data_files='train_data.csv', split='train')
val_dataset = load_dataset('csv', data_files='val_data.csv', split='train')

# Preprocess the dataset
def preprocess_function(examples):
    inputs = [doc for doc in examples["text"]]
    model_inputs = tokenizer(inputs, max_length=1024, padding=True, truncation=True)  # Added padding=True

    # Setup the tokenizer for targets
    with tokenizer.as_target_tokenizer():
        labels = tokenizer(examples["summary"], max_length=128, padding=True, truncation=True)  # Added padding=True

    model_inputs["labels"] = labels["input_ids"]
    return model_inputs

tokenized_train = train_dataset.map(preprocess_function, batched=True)
tokenized_val = val_dataset.map(preprocess_function, batched=True)

# Define training arguments
training_args = TrainingArguments(
    output_dir="./results",
    evaluation_strategy="epoch",  # Set evaluation and save strategy to 'epoch'
    save_strategy="epoch",        # This saves the model at the end of each epoch
    learning_rate=3e-5,
    per_device_train_batch_size=8,
    per_device_eval_batch_size=8,
    weight_decay=0.01,
    save_total_limit=3,
    num_train_epochs=5,
    logging_dir='./logs',
    load_best_model_at_end=True  # Load the best model at the end of training
)

# Initialize the Trainer with early stopping
trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=tokenized_train,
    eval_dataset=tokenized_val,
    tokenizer=tokenizer,
    callbacks=[EarlyStoppingCallback(early_stopping_patience=3)]
)

# Train the model
trainer.train()

# Save the trained model and tokenizer
model.save_pretrained("fine_tuned_BART")
tokenizer.save_pretrained("fine_tuned_BART")
print("Model and tokenizer saved successfully!")
