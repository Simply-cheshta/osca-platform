"""
Train a lightweight Logistic Regression difficulty classifier.
Requires: python scripts/collect_training_data.py first.
"""
import json
from pathlib import Path

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
import joblib


def load_data(path: str = "data/issues_training.jsonl") -> tuple[list[str], list[str]]:
    texts, labels = [], []
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Run collect_training_data.py first. Missing {path}")
    for line in p.read_text().splitlines():
        row = json.loads(line)
        text = f"{row['title']} {' '.join(row['labels'])}"
        texts.append(text)
        labels.append(row["difficulty"])
    return texts, labels


def train(output: str = "app/ml/models/difficulty_classifier.pkl"):
    texts, labels = load_data()
    pipeline = Pipeline([
        ("tfidf", TfidfVectorizer(max_features=500)),
        ("clf", LogisticRegression(max_iter=1000, multi_class="ovr")),
    ])
    pipeline.fit(texts, labels)
    out = Path(output)
    out.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipeline, out)
    print(f"Model saved to {out} ({len(texts)} samples)")


if __name__ == "__main__":
    train()
