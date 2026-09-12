"""Feature store with point-in-time join — contains <= leakage bug."""
import numpy as np
import pandas as pd


FEATURE_NAMES = ['session_count', 'avg_session_len', 'purchase_freq', 'support_contacts']
N_FEATURES = 4


def make_feature_store(n_entities: int = 328,
                       features_per_entity: int = 6,
                       seed: int = 42) -> pd.DataFrame:
    """
    Generate a feature store with time-stamped feature snapshots.

    Each entity (customer/transaction/loan) has multiple feature snapshots
    over time. At prediction time we must look up the feature values that
    were available BEFORE the label event occurred.

    Schema: entity_id, ts (unix timestamp), session_count, avg_session_len, purchase_freq, support_contacts
    """
    rng = np.random.RandomState(seed)
    rows = []
    base_ts = 1_000_000

    for entity_id in range(n_entities):
        # Feature snapshots at regular intervals
        for i in range(features_per_entity):
            ts = base_ts + entity_id * 1000 + i * 100
            feats = rng.randn(4).astype(np.float32)
            rows.append({
                "entity_id": entity_id,
                "ts": ts,
                **{name: float(feats[j]) for j, name in enumerate(FEATURE_NAMES)},
            })

    df = pd.DataFrame(rows)
    df.sort_values(["entity_id", "ts"], inplace=True)
    df.reset_index(drop=True, inplace=True)
    return df


def make_label_events(feature_store: pd.DataFrame,
                      n_entities: int = 328,
                      seed: int = 42) -> pd.DataFrame:
    """
    Generate label events for each entity.

    Each event has a timestamp that coincides with one of the feature snapshots
    (same ts as the LAST feature update), creating the <= vs < distinction.

    The label is set based on the LAST feature row at that exact timestamp
    (which would be leaked with <= but not with <).
    """
    rng = np.random.RandomState(seed + 1)
    events = []
    base_ts = 1_000_000

    for entity_id in range(n_entities):
        # Event timestamp = same as last feature snapshot for this entity
        max_snapshot_ts = feature_store[feature_store["entity_id"] == entity_id]["ts"].max()
        event_ts = int(max_snapshot_ts)  # SAME timestamp as last feature snapshot

        # Label: based on feature at event_ts (would be leaked with <=)
        entity_feats = feature_store[
            (feature_store["entity_id"] == entity_id) &
            (feature_store["ts"] == event_ts)
        ]
        if len(entity_feats) > 0:
            # Label is correlated with the feature at EXACTLY event_ts
            feat_val = float(entity_feats.iloc[0][FEATURE_NAMES[0]])
            label = int(feat_val > 0.0)
        else:
            label = rng.randint(0, 2)

        events.append({
            "entity_id": entity_id,
            "event_ts": event_ts,
            "label": label,
        })

    return pd.DataFrame(events)


def get_features_at(entity_id: int, event_ts: int,
                    feature_store: pd.DataFrame) -> np.ndarray:
    """
    Point-in-time feature lookup: get the most recent features for an entity
    that were available at event_ts.

    BUG: Uses <= which includes features computed AT the same timestamp as
    the event. If features at ts==event_ts were computed using information
    from the event itself, this leaks the label into the features.

    Correct: Use < to ensure only features from BEFORE the event are used.
    """
    entity_rows = feature_store[feature_store["entity_id"] == entity_id]

    # BUG: <= includes the feature row at the exact event timestamp
    available = entity_rows[entity_rows["ts"] <= event_ts]  # BUG: should be <

    if len(available) == 0:
        return np.zeros(N_FEATURES, dtype=np.float32)

    latest = available.sort_values("ts").iloc[-1]
    return latest[FEATURE_NAMES].values.astype(np.float32)


def build_feature_matrix(events: pd.DataFrame,
                         feature_store: pd.DataFrame) -> tuple:
    """Build X, y arrays using point-in-time feature lookup."""
    X_list, y_list = [], []
    for _, row in events.iterrows():
        feats = get_features_at(int(row["entity_id"]), int(row["event_ts"]), feature_store)
        X_list.append(feats)
        y_list.append(int(row["label"]))
    return np.array(X_list, dtype=np.float32), np.array(y_list, dtype=np.int64)


def check_pit_correctness() -> dict:
    """Check if point-in-time join uses strict less-than."""
    return {
        "uses_strict_lt": False,  # BUG: should be True after fix
        "operator": "<=",         # BUG: should be "<"
    }
