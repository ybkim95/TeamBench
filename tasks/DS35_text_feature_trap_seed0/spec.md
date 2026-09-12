# DS35: TF-IDF vs Embeddings on Small Dataset

## Task
Compare TF-IDF+SVD vs embeddings for **product review sentiment classification**
and select the better approach for this small dataset (218 samples).

## The Trap
High-dimensional embeddings (384 dims) are powerful for large datasets.
On **small datasets** (n=218 << 384), they severely **overfit** because
there are far more embedding dimensions than training samples.

**Rule of thumb**: when `n_samples < 10 × embedding_dim`, prefer TF-IDF+SVD.

## Fix: Compare Both Methods with Cross-Validation
1. **TF-IDF + LSA/SVD** (50 components):
   ```python
   from sklearn.feature_extraction.text import TfidfVectorizer
   from sklearn.decomposition import TruncatedSVD
   tfidf = TfidfVectorizer(max_features=2000)
   svd = TruncatedSVD(n_components=50, random_state=42)
   X_tfidf_svd = svd.fit_transform(tfidf.fit_transform(texts))
   ```
2. **Simulated Embeddings** (384 dims):
   Use the existing random-projection approach (already in buggy script)

3. **Compare with 5-fold CV** using `LogisticRegression`:
   ```python
   from sklearn.model_selection import cross_val_score
   tfidf_cv = cross_val_score(clf, X_tfidf_svd, labels, cv=5).mean()
   embed_cv = cross_val_score(clf, X_embed, labels, cv=5).mean()
   ```
4. Select winner (for n=218, TF-IDF+SVD should win)

## Data
File: `data/texts.csv`
- `review_text`: text to classify
- `sentiment`: binary label (0/1)

## Requirements
Save to `results.json`:
- `method_used`: `"tfidf_svd"` (correct choice for small n)
- `embedding_dim`: 384
- `tfidf_svd_dim`: 50
- `embed_cv_accuracy`: embedding CV accuracy (float)
- `tfidf_cv_accuracy`: TF-IDF+SVD CV accuracy (float, should be HIGHER)
- `winner`: `"tfidf_svd"`
- `n_samples`: 218
- `n_exceeds_embed_dim`: `false` (n=218 < 384)
Fix `analysis.py`.

## Deliverables
- Fixed `analysis.py` that compares both methods
- `results.json` showing TF-IDF+SVD beats embeddings on small dataset
