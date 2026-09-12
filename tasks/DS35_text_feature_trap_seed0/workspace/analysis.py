"""
Text feature engineering for product review sentiment classification.
BUG: Uses simulated high-dimensional embeddings (384 dims) on a small dataset.
When n_samples << embedding_dim, embeddings overfit severely.
TF-IDF with LSA/SVD dimensionality reduction to 50 dims outperforms
embeddings on small datasets.

Fix:
1. Implement BOTH: TF-IDF+SVD(50 dims) AND simulated embeddings
2. Compare via 5-fold cross-validation
3. Report which method wins and select it for the final model
4. For datasets where n < 500, TF-IDF+SVD should win
"""
import pandas as pd
import numpy as np
import json
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import TruncatedSVD
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import cross_val_score

df = pd.read_csv("data/texts.csv")
texts = df["review_text"].values
labels = df["sentiment"].values
n = len(texts)

# BUG: simulates using raw high-dim embeddings (bad for small n)
# Simulate 384-dim embeddings as random projections (overfits badly)
np.random.seed(42)
# Use TF-IDF as base but project to 384 dims (simulating embeddings)
tfidf_full = TfidfVectorizer(max_features=500)
X_tfidf = tfidf_full.fit_transform(texts)
# BUG: project to 384 dims (embedding-like high dim for small dataset)
from sklearn.random_projection import GaussianRandomProjection
if X_tfidf.shape[1] < 384:
    # Pad with random noise to simulate high-dim embeddings
    noise = np.random.randn(n, 384 - X_tfidf.shape[1]) * 0.01
    X_embed = np.hstack([X_tfidf.toarray(), noise])
else:
    X_embed = X_tfidf.toarray()[:, :384]

clf = LogisticRegression(max_iter=500, random_state=42)
embed_cv = cross_val_score(clf, X_embed, labels, cv=5, scoring="accuracy").mean()

results = {
    "method_used": "embeddings",  # BUG: should compare and pick tfidf_svd for small n
    "embedding_dim": 384,
    "tfidf_svd_dim": None,  # BUG: not tried
    "embed_cv_accuracy": float(embed_cv),
    "tfidf_cv_accuracy": None,  # BUG: not compared
    "winner": "embeddings",  # BUG: should be tfidf_svd for n={}'.format(n)
    "n_samples": n,
    "n_exceeds_embed_dim": n > 384,
}
with open("results.json", "w") as f:
    json.dump(results, f, indent=2)
print(f"Embedding CV accuracy ({n} samples, 384 dims): {embed_cv:.4f}")
print(f"WARNING: n={n} << 384 dims — embeddings likely overfit!")
print("Saved results.json")
