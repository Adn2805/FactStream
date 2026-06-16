import os
import torch
import numpy as np
from transformers import BertTokenizer, BertForSequenceClassification, Trainer, TrainingArguments
from sklearn.metrics import classification_report
from dataset import load_and_prepare_data, FALLACY_CLASSES

def compute_metrics(eval_pred):
    logits, labels = eval_pred
    predictions = np.argmax(logits, axis=-1)
    
    # Return basic metrics for Trainer, but print full sklearn report
    report = classification_report(labels, predictions, target_names=FALLACY_CLASSES, output_dict=True, zero_division=0)
    
    # Also print the text report to stdout for human review
    print("\n--- Evaluation Report ---")
    print(classification_report(labels, predictions, target_names=FALLACY_CLASSES, zero_division=0))
    print("-------------------------\n")
    
    return {
        "accuracy": report["accuracy"],
        "macro_f1": report["macro avg"]["f1-score"],
        "weighted_f1": report["weighted avg"]["f1-score"]
    }

def main():
    model_name = "bert-base-uncased"
    # Ensure models dir exists outside the nlu_service directory
    output_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "models", "fallacy_bert"))
    
    print("Loading tokenizer...")
    tokenizer = BertTokenizer.from_pretrained(model_name)

    def tokenize_function(examples):
        return tokenizer(examples["text"], padding="max_length", truncation=True, max_length=128)

    print("Loading and preparing dataset...")
    dataset = load_and_prepare_data()
    tokenized_datasets = dataset.map(tokenize_function, batched=True)

    print("Initializing model...")
    model = BertForSequenceClassification.from_pretrained(
        model_name, 
        num_labels=len(FALLACY_CLASSES)
    )

    training_args = TrainingArguments(
        output_dir="./results",
        evaluation_strategy="epoch",
        save_strategy="epoch",
        learning_rate=2e-5,
        per_device_train_batch_size=16,
        per_device_eval_batch_size=16,
        num_train_epochs=3,
        weight_decay=0.01,
        load_best_model_at_end=True,
        metric_for_best_model="macro_f1"
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=tokenized_datasets["train"],
        eval_dataset=tokenized_datasets["test"],
        compute_metrics=compute_metrics,
    )

    print("Starting training...")
    trainer.train()

    print(f"Saving fine-tuned model to {output_dir}...")
    os.makedirs(output_dir, exist_ok=True)
    model.save_pretrained(output_dir)
    tokenizer.save_pretrained(output_dir)
    print("Training complete!")

if __name__ == "__main__":
    main()
