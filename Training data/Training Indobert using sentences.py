import torch
from transformers import BertTokenizerFast, BertForTokenClassification, Trainer, TrainingArguments, EarlyStoppingCallback
from datasets import Dataset
import pandas as pd
import evaluate
from sklearn.model_selection import train_test_split

# Load the datasets
players_df = pd.read_excel('./data training/data_pemain_dengan_selenium.xlsx')
clubs_df = pd.read_excel('./data training/nama_klub_dan_venuenya.xlsx')
annotated_df = pd.read_excel('./data training/annotated_ner_sentences_random_extended.xlsx')

# Prepare the players DataFrame
players_df['Sentence'] = players_df['Nama Pemain IBL']
players_df['NER Tags'] = players_df['Tags'].apply(lambda x: [x])  # Wrap the tag in a list

# Prepare the clubs DataFrame
clubs_df['Sentence'] = clubs_df['Sentence']
clubs_df['NER Tags'] = clubs_df['NER Tags'].apply(lambda x: x.split(', '))  # Split multiple tags into a list

# Prepare the annotated DataFrame
annotated_df['NER Tags'] = annotated_df['NER Tags'].apply(lambda x: eval(x))  # Convert string representation of list back to list

# Combine the DataFrames
final_df = pd.concat([annotated_df[['Sentence', 'NER Tags']], players_df[['Sentence', 'NER Tags']], clubs_df[['Sentence', 'NER Tags']]], ignore_index=True)

# Preparing the dataset by splitting sentences and NER tags
data_for_ner = {
    'tokens': [],
    'ner_tags': []
}

# Iterate through combined data and prepare tokens and tags
for idx, row in final_df.iterrows():
    tokens = row['Sentence'].split()  # Split the sentence into tokens
    tags = row['NER Tags']  # Directly take the list of tags
    
    # Ensure that the length of tokens and tags match
    if len(tokens) != len(tags):
        print(f"Warning: Token and tag length mismatch for sentence: {row['Sentence']}")
        continue  # Skip this row if there's a mismatch
    
    data_for_ner['tokens'].append([token.lower() for token in tokens])
    data_for_ner['ner_tags'].append(tags)

# Create a pandas DataFrame from the prepared data
df_ner = pd.DataFrame(data_for_ner)

# Split data into training and evaluation datasets
train_df, eval_df = train_test_split(df_ner, test_size=0.2)

# Convert the pandas DataFrames into Hugging Face Dataset format
train_dataset = Dataset.from_pandas(train_df)
eval_dataset = Dataset.from_pandas(eval_df)

# Load tokenizer and model for BERT
label_list = ["O", "B-PER", "B-ORG", "B-LOC"]  # Adjust the labels based on NER annotations
num_labels = len(label_list)
tokenizer = BertTokenizerFast.from_pretrained("indobenchmark/indobert-base-p1")
model = BertForTokenClassification.from_pretrained("indobenchmark/indobert-base-p1", num_labels=num_labels)

# Tokenization and alignment function with padding and truncation
def tokenize_and_align_labels(examples):
    tokenized_inputs = tokenizer(
        examples["tokens"],
        truncation=True,
        padding=True,
        is_split_into_words=True,
        max_length=128
    )

    labels = []
    for i, label in enumerate(examples["ner_tags"]):
        word_ids = tokenized_inputs.word_ids(batch_index=i)
        previous_word_idx = None
        label_ids = []
        for word_idx in word_ids:
            if word_idx is None:
                label_ids.append(-100)  # Ignore padding tokens in labels
            elif word_idx != previous_word_idx:  # First token of the word
                if word_idx < len(label):  # Check if the word_idx is within range
                    label_ids.append(label_list.index(label[word_idx]))
                else:
                    label_ids.append(-100)  # Skip if no valid label
            else:
                label_ids.append(-100)  # Assign -100 to subtokens (skip)
            previous_word_idx = word_idx
        labels.append(label_ids)

    tokenized_inputs["labels"] = labels
    return tokenized_inputs

# Tokenizing the datasets
tokenized_train_dataset = train_dataset.map(tokenize_and_align_labels, batched=True)
tokenized_eval_dataset = eval_dataset.map(tokenize_and_align_labels, batched=True)

# Use evaluate library for metrics
metric = evaluate.load("seqeval")

# Define the compute metrics function
def compute_metrics(p):
    predictions, labels = p
    predictions = torch.tensor(predictions)
    predictions = torch.argmax(predictions, dim=2)

    true_labels = [[label_list[l] for l in label if l != -100] for label in labels]
    true_predictions = [
        [label_list[p] for (p, l) in zip(prediction, label) if l != -100]
        for prediction, label in zip(predictions, labels)
    ]

    results = metric.compute(predictions=true_predictions, references=true_labels)
    return {
        "precision": results["overall_precision"],
        "recall": results["overall_recall"],
        "f1": results["overall_f1"],
        "accuracy": results["overall_accuracy"],
    }

# Define training arguments
training_args = TrainingArguments(
    output_dir="./results",
    evaluation_strategy="epoch",
    save_strategy="epoch",
    save_total_limit=2,
    learning_rate=2e-5,
    per_device_train_batch_size=16,
    per_device_eval_batch_size=16,
    num_train_epochs=5,
    weight_decay=0.01,
    logging_dir='./logs',
    load_best_model_at_end=True,
    metric_for_best_model="f1",
)

# Initialize the Trainer with early stopping
trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=tokenized_train_dataset,
    eval_dataset=tokenized_eval_dataset,
    tokenizer=tokenizer,
    compute_metrics=compute_metrics,
    callbacks=[EarlyStoppingCallback(early_stopping_patience=3)]
)

# Train the model
trainer.train()

# Save the fine-tuned model
model.save_pretrained("fine_tuned_IndoBERT_NER")

# Save tokenizer as well
tokenizer.save_pretrained("fine_tuned_IndoBERT_NER")
