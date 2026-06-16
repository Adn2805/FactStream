import pandas as pd
import numpy as np
import nlpaug.augmenter.word as naw
import nltk
from datasets import load_dataset, Dataset, DatasetDict
from typing import List, Tuple

# Ensure NLTK resources are available for nlpaug
try:
    nltk.data.find('corpora/wordnet')
except LookupError:
    nltk.download('wordnet')
try:
    nltk.data.find('corpora/omw-1.4')
except LookupError:
    nltk.download('omw-1.4')

FALLACY_CLASSES = [
    "Ad Hominem", "Straw Man", "False Dichotomy", "Appeal to Authority", 
    "Slippery Slope", "Hasty Generalization", "Red Herring", "Circular Reasoning", 
    "Appeal to Emotion", "Bandwagon", "False Cause", "Anecdotal", "Tu Quoque", "No Fallacy"
]

FALLACY_TO_ID = {label: i for i, label in enumerate(FALLACY_CLASSES)}
ID_TO_FALLACY = {i: label for label, i in FALLACY_TO_ID.items()}

def augment_data(texts: List[str], labels: List[int], augment_ratio: float = 0.5) -> Tuple[List[str], List[int]]:
    """Augment the text using Synonym replacement."""
    aug = naw.SynonymAug(aug_src='wordnet', aug_max=2)
    aug_texts = []
    aug_labels = []
    
    num_to_augment = int(len(texts) * augment_ratio)
    if num_to_augment == 0:
        return texts, labels
        
    indices_to_augment = np.random.choice(len(texts), num_to_augment, replace=False)
    
    for idx in indices_to_augment:
        original_text = texts[idx]
        augmented_text = aug.augment(original_text)
        # Handle cases where augment returns a list
        if isinstance(augmented_text, list):
            augmented_text = augmented_text[0]
            
        aug_texts.append(augmented_text)
        aug_labels.append(labels[idx])
        
    return texts + aug_texts, labels + aug_labels

def load_and_prepare_data(supplementary_csv_path: str = None) -> DatasetDict:
    """Loads EleutherAI/logic, maps classes, and applies augmentation."""
    try:
        hf_dataset = load_dataset("EleutherAI/logic")
        train_df = pd.DataFrame(hf_dataset['train'])
        test_df = pd.DataFrame(hf_dataset['validation'])
    except Exception as e:
        print(f"Could not load EleutherAI/logic from HuggingFace natively: {e}")
        print("Using fallback dummy data...")
        dummy_data = []
        for i, c in enumerate(FALLACY_CLASSES):
            dummy_data.append({"text": f"This is an example of {c}. It shows typical logical errors.", "label": i})
            dummy_data.append({"text": f"Another instance of {c} arguing poorly.", "label": i})
        train_df = pd.DataFrame(dummy_data * 20) # 560 samples
        test_df = pd.DataFrame(dummy_data * 4)   # 112 samples

    if supplementary_csv_path:
        try:
            supp_df = pd.read_csv(supplementary_csv_path)
            if 'label' in supp_df.columns and supp_df['label'].dtype == object:
                supp_df['label'] = supp_df['label'].map(FALLACY_TO_ID)
            train_df = pd.concat([train_df, supp_df], ignore_index=True)
        except Exception as e:
            print(f"Error loading supplementary CSV: {e}")

    train_df = train_df.dropna(subset=['text', 'label'])
    test_df = test_df.dropna(subset=['text', 'label'])
    
    train_df['label'] = train_df['label'].astype(int)
    test_df['label'] = test_df['label'].astype(int)

    aug_texts, aug_labels = augment_data(train_df['text'].tolist(), train_df['label'].tolist(), augment_ratio=0.3)
    aug_train_df = pd.DataFrame({'text': aug_texts, 'label': aug_labels})

    train_dataset = Dataset.from_pandas(aug_train_df)
    test_dataset = Dataset.from_pandas(test_df)

    return DatasetDict({
        'train': train_dataset,
        'test': test_dataset
    })
